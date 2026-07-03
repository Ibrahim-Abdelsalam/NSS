"""Reproducible experiment pipeline for the NSS model."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from core import ExperimentResult, RESULTS_DIR, SolveResult
from core.model import create_model
from core.scheduler import ResultExtractor
from core.validator import ParameterValidator
from experiments.presets import DATASET_REGISTRY, PARAMETER_PRESETS


class ExperimentPipeline:
    """Run, validate, and archive reproducible NSS experiments."""

    def __init__(self, config: dict):
        """Initialize the pipeline from a configuration dictionary."""
        self.config = dict(config)
        output_dir = self.config.get("output_dir", RESULTS_DIR)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results_log: list[ExperimentResult] = []

    def load_data(self, dataset_key: str, subset: Optional[int] = None) -> Tuple[List[str], pd.DataFrame]:
        """Load nurse and scenario data for a dataset key."""
        if dataset_key not in DATASET_REGISTRY:
            raise ValueError(f"Unknown dataset: {dataset_key}. Available: {list(DATASET_REGISTRY.keys())}")

        config = DATASET_REGISTRY[dataset_key]
        nurses_file = Path(config["nurses_file"])
        scenarios_file = Path(config["scenarios_file"])

        nurses_df = pd.read_csv(nurses_file)
        scenarios_df = pd.read_csv(scenarios_file)

        nurse_id_col = "nurse_id" if "nurse_id" in nurses_df.columns else nurses_df.columns[0]
        nurses_list = nurses_df[nurse_id_col].astype(str).tolist()

        if subset:
            nurses_list = nurses_list[:subset]
            scenarios_df = scenarios_df[scenarios_df["day"] <= subset]

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
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Prepare model parameters from a preset and optional overrides."""
        if preset_key not in PARAMETER_PRESETS:
            raise ValueError(f"Unknown preset: {preset_key}. Available: {list(PARAMETER_PRESETS.keys())}")

        preset = PARAMETER_PRESETS[preset_key]
        params = preset["params"].copy()

        num_days = scenarios_df["day"].max()
        if params["n1"] is None:
            params["n1"] = max(8, int(0.8 * num_days))
        if params["n2"] is None:
            params["n2"] = max(2, int(0.3 * params["n1"]))

        if overrides:
            params.update(overrides)

        return params

    def run(self) -> ExperimentResult:
        """Run the configured experiment end to end."""
        dataset_key = self.config.get("dataset_key", "sample")
        preset_key = self.config.get("preset_key", "baseline")
        experiment_id = self.config.get("experiment_id", "experiment")
        solver = self.config.get("solver", "AUTO")
        subset = self.config.get("subset")
        overrides = self.config.get("overrides")

        nurses_list, scenarios_df = self.load_data(dataset_key, subset=subset)
        base_params = self.prepare_parameters(preset_key, nurses_list, scenarios_df, overrides=overrides)

        validator = ParameterValidator(strict_mode=False)
        validation = validator.validate_inputs(base_params, nurses_list, scenarios_df)
        if not validation.is_valid:
            raise ValueError("Validation failed before solving")

        final_params = validation.sanitized_params or base_params
        model_type = self.config.get("model_type", PARAMETER_PRESETS[preset_key]["model_type"])
        model = create_model(final_params, nurses_list, scenarios_df, model_type=model_type, solver_name=solver)

        start_time = datetime.now()
        model.build()
        solve_result = model.solve()
        solve_time = (datetime.now() - start_time).total_seconds()
        solve_result = SolveResult(
            status=solve_result.status,
            objective_value=solve_result.objective_value,
            solve_time_seconds=solve_time,
            solver_name=solve_result.solver_name,
            variable_values=solve_result.variable_values,
            metadata=solve_result.metadata,
        )

        extractor = ResultExtractor(model, solve_result)
        extracted = extractor.extract()

        result = ExperimentResult(
            experiment_id=experiment_id,
            config=self.config,
            solve_result=solve_result,
            schedule_df=extracted.get("schedule_df", pd.DataFrame()),
            cost_summary=extracted.get("cost_breakdown", {}),
            timestamp=datetime.now().isoformat(),
            archived_path=None,
        )

        result = self.archive(result)
        self.results_log.append(result)
        return result

    def archive(self, result: ExperimentResult) -> ExperimentResult:
        """Archive experiment outputs to disk."""
        exp_folder = self.output_dir / result.experiment_id
        exp_folder.mkdir(parents=True, exist_ok=True)

        metadata = {
            "experiment_id": result.experiment_id,
            "timestamp": result.timestamp,
            "config": result.config,
            "solver_status": result.solve_result.status,
            "objective_value": result.solve_result.objective_value,
            "solve_time_seconds": result.solve_result.solve_time_seconds,
        }
        (exp_folder / "metadata.json").write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
        (exp_folder / "parameters.json").write_text(json.dumps(result.config.get("overrides", {}), indent=2, default=str), encoding="utf-8")

        if not result.schedule_df.empty:
            result.schedule_df.to_csv(exp_folder / "schedule.csv", index=False)

        results_payload = {
            "cost_summary": result.cost_summary,
            "solve_result": {
                "status": result.solve_result.status,
                "objective_value": result.solve_result.objective_value,
                "solve_time_seconds": result.solve_result.solve_time_seconds,
                "solver_name": result.solve_result.solver_name,
                "metadata": result.solve_result.metadata,
            },
        }
        (exp_folder / "results.json").write_text(json.dumps(results_payload, indent=2, default=str), encoding="utf-8")

        result.archived_path = str(exp_folder)
        return result

    def generate_summary_report(self) -> str:
        """Generate a short text report of completed experiments."""
        if not self.results_log:
            return "No experiments run yet."

        report = ["", "=" * 80, "EXPERIMENT SUMMARY REPORT", "=" * 80, ""]
        for result in self.results_log:
            report.append(f"Experiment: {result.experiment_id}")
            report.append(f"  Solver Status: {result.solve_result.status}")
            report.append(f"  Solve Time: {result.solve_result.solve_time_seconds:.2f}s")
            report.append(f"  Archive: {result.archived_path}")
            report.append("")
        report.append("=" * 80)
        return "\n".join(report)


def main() -> None:
    """Run the experiment pipeline from the command line."""
    parser = argparse.ArgumentParser(description="Run NSS model experiments with full validation")
    parser.add_argument("--dataset", choices=list(DATASET_REGISTRY.keys()), default="sample", help="Dataset to use")
    parser.add_argument("--preset", choices=list(PARAMETER_PRESETS.keys()), default="baseline", help="Parameter preset")
    parser.add_argument("--id", type=str, required=True, help="Experiment identifier")
    parser.add_argument("--solver", choices=["AUTO", "HiGHS", "CBC", "GUROBI"], default="AUTO", help="Solver to use")
    parser.add_argument("--subset", type=int, help="Use only first N days")
    args = parser.parse_args()

    pipeline = ExperimentPipeline(
        {
            "dataset_key": args.dataset,
            "preset_key": args.preset,
            "experiment_id": args.id,
            "solver": args.solver,
            "subset": args.subset,
        }
    )
    pipeline.run()
    print(pipeline.generate_summary_report())


if __name__ == "__main__":
    main()
