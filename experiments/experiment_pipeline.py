"""
Reproducible Experiment Pipeline for NSS Model
===============================================

Standardized workflow for running publication-quality experiments:
1. Data selection and loading
2. Parameter definition
3. Model execution with validation
4. Result collection and archiving
5. Reproducibility verification

Usage:
    python experiments/experiment_pipeline.py --dataset sample --config baseline
    python experiments/experiment_pipeline.py --dataset medium --config cvar_risk
    python experiments/experiment_pipeline.py --mode validate_all
"""

import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import hashlib
import argparse
from typing import Dict, List, Tuple, Optional, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import model_2
from validation_framework import PreRunValidator, ResultValidator, run_complete_validation


# ==============================================================================
# EXPERIMENT CONFIGURATION REGISTRY
# ==============================================================================

DATASET_REGISTRY = {
    """
    Dataset configurations with realistic parameters.
    Format:
    - key: Dataset identifier
    - nurses_file: CSV in data/ folder (columns: nurse_id, skill_level, availability)
    - scenarios_file: CSV in data/ folder (columns: scenario, day, shift, demand)
    - description: Use case description
    - recommended_params: Suggested parameter set
    """
    
    'sample': {
        'nurses_file': 'data/sample_nurses.csv',
        'scenarios_file': 'data/sample_scenarios.csv',
        'num_nurses': 10,
        'num_days': 14,
        'num_scenarios': 5,
        'description': 'Small benchmark: quick testing, validation',
        'realistic': False,
        'data_source': 'Synthetic benchmark conversion',
    },
    
    'test_small': {
        'nurses_file': 'data/test_small_nurses.csv',
        'scenarios_file': 'data/test_small_scenarios.csv',
        'num_nurses': 15,
        'num_days': 14,
        'num_scenarios': 8,
        'description': 'Small-medium synthetic: unit testing',
        'realistic': False,
        'data_source': 'Synthetic benchmark conversion',
    },
    
    'test_medium': {
        'nurses_file': 'data/test_medium_nurses.csv',
        'scenarios_file': 'data/test_medium_scenarios.csv',
        'num_nurses': 20,
        'num_days': 14,
        'num_scenarios': 10,
        'description': 'Medium realistic: typical hospital unit',
        'realistic': True,
        'data_source': 'Hospital bed occupancy proxy + CMS PBJ data',
    },
    
    'medium': {
        'nurses_file': 'data/medium_nurses.csv',
        'scenarios_file': 'data/medium_scenarios.csv',
        'num_nurses': 25,
        'num_days': 21,
        'num_scenarios': 12,
        'description': 'Medium-large: 3-week planning horizon',
        'realistic': True,
        'data_source': 'Hospital bed occupancy proxy + CMS PBJ data',
    },
    
    'nss_benchmark': {
        'nurses_file': 'data/nss_benchmark_nurses.csv',
        'scenarios_file': 'data/nss_benchmark_scenarios.csv',
        'num_nurses': 30,
        'num_days': 30,
        'num_scenarios': 15,
        'description': 'Paper benchmark: He et al. (2019) case study',
        'realistic': True,
        'data_source': 'He et al. (2019) publication',
    },
}


PARAMETER_PRESETS = {
    """
    Parameter presets for different optimization strategies.
    Format:
    - key: Preset name
    - params: Complete parameter dictionary
    - description: Use case and motivation
    - model_type: 'SDM' or 'SDM-CVaR'
    """
    
    'baseline': {
        'description': 'Pure cost minimization (expected value model)',
        'model_type': 'SDM',
        'params': {
            'c1': 100.0,      # Regular shift cost
            'c2': 150.0,      # Overtime cost
            'q_plus': 200.0,  # Emergency staff cost
            'q_minus': 0.0,   # Shift cancellation cost
            'c3': 10.0,       # Stand-alone shift penalty
            'c4': 15.0,       # Unwanted pattern penalty
            'n1': None,       # Will be set based on data
            'n2': None,       # Will be auto-derived
            'n3': 0,          # No minimum commitment (flexible)
            'sigma': 0.95,
            'mu': 50.0,
        }
    },
    
    'conservative': {
        'description': 'Risk-averse: controls worst-case shortages (CVaR)',
        'model_type': 'SDM-CVaR',
        'params': {
            'c1': 100.0,
            'c2': 150.0,
            'q_plus': 200.0,
            'q_minus': 0.0,
            'c3': 10.0,
            'c4': 15.0,
            'n1': None,
            'n2': None,
            'n3': 0,
            'sigma': 0.90,    # 90% confidence → tighter control of tail
            'mu': 30.0,       # Max 30-shift shortage in worst 10% of scenarios
        }
    },
    
    'paper_replication': {
        'description': 'He et al. (2019) paper parameters (requires 30-day horizon)',
        'model_type': 'SDM-CVaR',
        'params': {
            'c1': 100.0,
            'c2': 150.0,
            'q_plus': 200.0,
            'q_minus': 2.0,   # Paper uses cancellation cost
            'c3': 10.0,
            'c4': 15.0,
            'n1': 20,         # Paper constraint: ≤20 shifts in 30 days
            'n2': 5,          # Paper constraint: ≤5 night shifts
            'n3': 12,         # Paper constraint: ≥12 regular shifts
            'sigma': 0.95,
            'mu': 50.0,
        },
        'requirements': ['30-day horizon', 'sufficient nurses']
    },
    
    'fatigue_aware': {
        'description': 'Includes patient safety via fatigue modeling',
        'model_type': 'SDM',
        'params': {
            'c1': 100.0,
            'c2': 150.0,
            'q_plus': 200.0,
            'q_minus': 0.0,
            'c3': 10.0,
            'c4': 15.0,
            'n1': None,
            'n2': None,
            'n3': 0,
            'sigma': 0.95,
            'mu': 50.0,
            # Fatigue parameters (Jaber et al. 2013 - LFFR model)
            'patient_safety_enabled': True,
            'patient_safety_weight': 50.0,  # Cost per fatigue unit ($)
            'fatigue_lambda': 0.03,         # Fatigue accumulation rate
            'recovery_mu': 0.05,            # Recovery rate
            'max_fatigue_threshold': 0.70,  # Max fatigue before forced rest
        }
    },
}


# ==============================================================================
# EXPERIMENT CLASS
# ==============================================================================

class ExperimentRunner:
    """Manages single experiment execution with full validation and logging"""
    
    def __init__(self, output_dir: str = 'experiments/results'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results_log = []
    
    def load_data(
        self,
        dataset_key: str,
        subset: Optional[int] = None
    ) -> Tuple[List[str], pd.DataFrame]:
        """
        Load dataset.
        
        Args:
            dataset_key: Key from DATASET_REGISTRY
            subset: If set, use only first N nurses/scenarios (for quick testing)
            
        Returns:
            (nurses_list, scenarios_df)
        """
        
        if dataset_key not in DATASET_REGISTRY:
            raise ValueError(f"Unknown dataset: {dataset_key}. Available: {list(DATASET_REGISTRY.keys())}")
        
        config = DATASET_REGISTRY[dataset_key]
        
        # Load files
        nurses_file = config['nurses_file']
        scenarios_file = config['scenarios_file']
        
        nurses_df = pd.read_csv(nurses_file)
        scenarios_df = pd.read_csv(scenarios_file)
        
        # Extract nurse IDs
        nurse_id_col = 'nurse_id' if 'nurse_id' in nurses_df.columns else nurses_df.columns[0]
        nurses_list = nurses_df[nurse_id_col].astype(str).tolist()
        
        # Apply subset if requested
        if subset:
            nurses_list = nurses_list[:subset]
            scenarios_df = scenarios_df[scenarios_df['day'] <= subset]
        
        print(f"\n📊 Loaded Dataset: {dataset_key}")
        print(f"   Nurses: {len(nurses_list)}")
        print(f"   Days: {scenarios_df['day'].max()}")
        print(f"   Scenarios: {scenarios_df['scenario'].nunique()}")
        print(f"   Source: {config['data_source']}")
        
        return nurses_list, scenarios_df
    
    def prepare_parameters(
        self,
        preset_key: str,
        nurses_list: List[str],
        scenarios_df: pd.DataFrame,
        overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Prepare model parameters from preset + overrides.
        
        Auto-derives n values from data if not specified.
        """
        
        if preset_key not in PARAMETER_PRESETS:
            raise ValueError(f"Unknown preset: {preset_key}. Available: {list(PARAMETER_PRESETS.keys())}")
        
        preset = PARAMETER_PRESETS[preset_key]
        params = preset['params'].copy()
        
        # Auto-derive n1, n2 if needed
        num_days = scenarios_df['day'].max()
        if params['n1'] is None:
            # Standard: 80% of days
            params['n1'] = max(8, int(0.8 * num_days))
        
        if params['n2'] is None:
            # Standard: 30% of n1
            params['n2'] = max(2, int(0.3 * params['n1']))
        
        # Apply overrides
        if overrides:
            params.update(overrides)
        
        return params
    
    def run_experiment(
        self,
        dataset_key: str,
        preset_key: str,
        experiment_id: str,
        overrides: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None,
        solver: str = 'AUTO',
    ) -> Dict[str, Any]:
        """
        Execute single experiment with full validation pipeline.
        
        Args:
            dataset_key: Dataset from DATASET_REGISTRY
            preset_key: Parameter preset from PARAMETER_PRESETS
            experiment_id: Human-readable experiment name
            overrides: Parameter overrides (merged with preset)
            seed: Random seed for reproducibility
            solver: 'AUTO', 'HiGHS', 'CBC', 'GUROBI'
            
        Returns:
            Complete experiment result with metadata
        """
        
        print("\n" + "="*80)
        print(f"🚀 EXPERIMENT: {experiment_id}")
        print("="*80)
        
        # Step 1: Data loading
        nurses_list, scenarios_df = self.load_data(dataset_key)
        
        # Step 2: Parameter preparation
        base_params = self.prepare_parameters(preset_key, nurses_list, scenarios_df)
        if overrides:
            base_params.update(overrides)
        
        # Step 3: Comprehensive validation
        print("\n🔍 VALIDATION PHASE")
        validation_result = run_complete_validation(
            nurses_list, scenarios_df, base_params, auto_fix=True
        )
        
        if not validation_result['ready_to_run']:
            print("⛔ Experiment blocked by validation failures")
            return {
                'success': False,
                'error': 'Validation failed',
                'validation': validation_result,
            }
        
        final_params = validation_result['final_params']
        
        # Step 4: Model execution
        print("\n⚙️  MODEL EXECUTION PHASE")
        print(f"   Solving {len(nurses_list)} nurses, {scenarios_df['day'].max()} days, "
              f"{scenarios_df['scenario'].nunique()} scenarios...")
        print(f"   Model type: {PARAMETER_PRESETS[preset_key]['model_type']}")
        
        start_time = datetime.now()
        
        try:
            prob, status = model_2.build_and_solve_model(
                nurses_list,
                scenarios_df,
                final_params,
                model_type=PARAMETER_PRESETS[preset_key]['model_type'],
                solver_name=solver
            )
            
            solve_time = (datetime.now() - start_time).total_seconds()
            print(f"   ✓ Solved in {solve_time:.2f}s - Status: {status}")
            
            # Extract results
            results = model_2.extract_results(prob, nurses_list, scenarios_df, final_params)
            
            # Validate results
            result_validation = ResultValidator.validate_solution(
                prob, results, final_params, verbose=True
            )
            
        except Exception as e:
            print(f"   ❌ Solver error: {str(e)}")
            return {
                'success': False,
                'error': f"Solver failed: {str(e)}",
                'solve_time': (datetime.now() - start_time).total_seconds(),
            }
        
        # Step 5: Result archiving
        print("\n💾 ARCHIVING RESULTS")
        archive_result = self._archive_results(
            experiment_id, dataset_key, preset_key,
            nurses_list, scenarios_df, final_params,
            prob, results, status, solve_time
        )
        
        # Final result object
        final_result = {
            'success': True,
            'experiment_id': experiment_id,
            'dataset': dataset_key,
            'preset': preset_key,
            'solver': solver,
            'timestamp': datetime.now().isoformat(),
            'parameters': final_params,
            'validation': validation_result,
            'result_validation': result_validation,
            'solve_time': solve_time,
            'status': status,
            'results': results,
            'archive': archive_result,
        }
        
        self.results_log.append(final_result)
        
        print(f"\n✅ Experiment complete. Results saved to: {archive_result['results_file']}")
        print("="*80 + "\n")
        
        return final_result
    
    def _archive_results(
        self,
        experiment_id: str,
        dataset_key: str,
        preset_key: str,
        nurses_list: List[str],
        scenarios_df: pd.DataFrame,
        params: Dict[str, Any],
        prob,
        results: Dict[str, Any],
        status: str,
        solve_time: float
    ) -> Dict[str, Any]:
        """
        Archive all results for reproducibility.
        Stores: metadata, parameters, schedule, results
        """
        
        # Create experiment folder
        exp_folder = self.output_dir / experiment_id
        exp_folder.mkdir(exist_ok=True)
        
        # 1. Metadata file
        metadata = {
            'experiment_id': experiment_id,
            'timestamp': datetime.now().isoformat(),
            'dataset': dataset_key,
            'dataset_info': DATASET_REGISTRY.get(dataset_key, {}),
            'preset': preset_key,
            'num_nurses': len(nurses_list),
            'num_days': int(scenarios_df['day'].max()),
            'num_scenarios': int(scenarios_df['scenario'].nunique()),
            'solver_status': status,
            'solve_time_seconds': solve_time,
            'objective_value': float(prob.objective.value()) if hasattr(prob, 'objective') else None,
        }
        
        metadata_file = exp_folder / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # 2. Parameters file
        params_file = exp_folder / 'parameters.json'
        with open(params_file, 'w') as f:
            json.dump(params, f, indent=2, default=str)
        
        # 3. Schedule CSV
        if results and 'schedule_df' in results:
            schedule_file = exp_folder / 'schedule.csv'
            results['schedule_df'].to_csv(schedule_file, index=False)
        
        # 4. Results summary
        results_file = exp_folder / 'results.json'
        results_to_save = {
            k: v for k, v in results.items()
            if k not in ['schedule_df']  # Don't duplicate CSV
        }
        with open(results_file, 'w') as f:
            json.dump(results_to_save, f, indent=2, default=str)
        
        # 5. Validation log
        print(f"   Results saved to: {exp_folder}/")
        
        return {
            'folder': str(exp_folder),
            'metadata_file': str(metadata_file),
            'parameters_file': str(params_file),
            'results_file': str(results_file),
        }
    
    def generate_summary_report(self) -> str:
        """Generate summary of all experiments run"""
        
        if not self.results_log:
            return "No experiments run yet."
        
        report = "\n" + "="*80 + "\n"
        report += "EXPERIMENT SUMMARY REPORT\n"
        report += "="*80 + "\n\n"
        
        for result in self.results_log:
            report += f"Experiment: {result['experiment_id']}\n"
            report += f"  Dataset: {result['dataset']}\n"
            report += f"  Preset: {result['preset']}\n"
            report += f"  Solver Status: {result['status']}\n"
            report += f"  Solve Time: {result['solve_time']:.2f}s\n"
            report += f"  Archive: {result['archive']['folder']}\n\n"
        
        report += "="*80 + "\n"
        return report


# ==============================================================================
# COMMAND-LINE INTERFACE
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Run NSS model experiments with full validation'
    )
    
    parser.add_argument(
        '--dataset',
        choices=list(DATASET_REGISTRY.keys()),
        default='sample',
        help='Dataset to use'
    )
    
    parser.add_argument(
        '--preset',
        choices=list(PARAMETER_PRESETS.keys()),
        default='baseline',
        help='Parameter preset'
    )
    
    parser.add_argument(
        '--id',
        type=str,
        required=True,
        help='Experiment identifier (human readable)'
    )
    
    parser.add_argument(
        '--solver',
        choices=['AUTO', 'HiGHS', 'CBC', 'GUROBI'],
        default='AUTO',
        help='Solver to use'
    )
    
    parser.add_argument(
        '--subset',
        type=int,
        help='Use only first N days (for quick testing)'
    )
    
    args = parser.parse_args()
    
    # Run experiment
    runner = ExperimentRunner()
    result = runner.run_experiment(
        dataset_key=args.dataset,
        preset_key=args.preset,
        experiment_id=args.id,
        solver=args.solver,
    )
    
    # Print summary
    print(runner.generate_summary_report())


if __name__ == '__main__':
    main()
