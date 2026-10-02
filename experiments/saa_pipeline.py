import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List
import time
import sys
import os

# Ensure the core and experiments modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.advanced_data_generator import HeterogeneousNurseGenerator, ExogenousDemandGenerator
from core.frost_model import build_frost_ns_model
import pulp

class SAAPipeline:
    def __init__(self, n_replications=20, n_scenarios=50, n_eval=1000):
        self.n_replications = n_replications
        self.n_scenarios = n_scenarios
        self.n_eval = n_eval
        
    def run(self, num_nurses: int, num_days: int, base_params: Dict[str, Any],
            master_seed: int = 42, is_deterministic: bool = False) -> Dict[str, Any]:
        print(f"Running SAA Pipeline: M={self.n_replications}, N={self.n_scenarios}, N'={self.n_eval}, seed={master_seed}, determ={is_deterministic}")
        
        # 1. Generate base nurses (fixed across replications, seed-configurable)
        nurse_gen = HeterogeneousNurseGenerator(seed=master_seed)
        nurses_df = nurse_gen.generate(num_nurses, num_days=num_days)
        nurses_list = nurses_df['nurse_id'].tolist()
        qualification_matrix = nurse_gen.get_qualification_matrix(nurses_df)
        
        # Build per-nurse limits from heterogeneous contracts
        W_bar_i = {}
        N_bar_i = {}
        nurse_skill_map = {}
        for _, row in nurses_df.iterrows():
            nid = row['nurse_id']
            W_bar_i[nid] = row['max_shifts']
            N_bar_i[nid] = row['max_nights']
            nurse_skill_map[nid] = row['skill_level']
        
        # Update params with nurse-specific data
        params = base_params.copy()
        params['q'] = qualification_matrix
        params['W_bar_i'] = W_bar_i
        params['N_bar_i'] = N_bar_i
        params['nurse_skill'] = nurse_skill_map
        
        days_list = list(range(1, num_days + 1))
        shifts_list = ['E', 'D', 'L', 'N']
        skill_levels = params.get('skill_levels', ['HN', 'RN', 'CNA'])
        
        demand_gen = ExogenousDemandGenerator()
        scale_factor = num_nurses / 30.0
        
        solutions = []
        objectives = []
        solve_times = []
        extra_stats = []
        
        # Stage 1: Solve M replications
        actual_replications = 1 if is_deterministic else self.n_replications
        
        for m in range(actual_replications):
            print(f"  Running replication {m+1}/{actual_replications}...")
            # a. Generate N scenarios (seed depends on master_seed)
            seed_m = master_seed * 1000 + m
            demand_gen.rng = np.random.default_rng(seed_m)
            scenarios_df = demand_gen.generate(
                n_scenarios=self.n_scenarios, 
                num_days=num_days, 
                scale_factor=scale_factor
            )
            
            if is_deterministic:
                # Collapse all generated scenarios into a single expected-value scenario
                mean_df = scenarios_df.groupby(['day', 'shift', 'skill'])['demand'].mean().reset_index()
                # Round to nearest integer for the deterministic model
                mean_df['demand'] = mean_df['demand'].round().astype(int)
                mean_df['scenario'] = 1
                scenarios_df = mean_df
                scenarios_list = [1]
            else:
                scenarios_list = list(range(1, self.n_scenarios + 1))
            
            # Format demand as skill-indexed: (day, shift, skill, scenario) -> demand
            skill_demand = {}
            for _, row in scenarios_df.iterrows():
                key = (int(row['day']), row['shift'], row['skill'], int(row['scenario']))
                skill_demand[key] = int(row['demand'])
            
            # b. Solve FROST-NS MILP
            t_start = time.time()
            prob = build_frost_ns_model(
                nurses=nurses_list,
                days=days_list,
                shifts=shifts_list,
                scenarios=scenarios_list,
                demand=skill_demand,
                params=params
            )
            
            # Solve using CBC or available solver with time limit per replication
            time_limit = params.get('solve_time_limit')
            if time_limit == 0:
                time_limit = None
            solver_name = params.get('solver_name', 'AUTO')
            if solver_name == 'GUROBI' or (solver_name == 'AUTO' and pulp.GUROBI().available()):
                solver = pulp.GUROBI(msg=0, timeLimit=time_limit)
            else:
                solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit)
            prob.solve(solver)
            t_elapsed = time.time() - t_start
            
            status_str = pulp.LpStatus[prob.status]
            if status_str in ['Optimal', 'Feasible']:
                obj_val = pulp.value(prob.objective)
                objectives.append(obj_val)
                solve_times.append(t_elapsed)
                
                # Extract x_{ijk} solution
                x_vars = prob._vars['x']
                x_sol = {}
                for i in nurses_list:
                    for j in days_list:
                        for k in shifts_list:
                            x_sol[(i, j, k)] = pulp.value(x_vars[i][j][k])
                solutions.append(x_sol)
                
                # Extract CVaR and Fairness stats
                eta_val = pulp.value(prob._vars['eta']) if 'eta' in prob._vars else None
                z_vars = prob._vars.get('z', {})
                z_vals = [pulp.value(z_vars[omega]) for omega in scenarios_list] if z_vars else []
                
                W_vars = prob._vars.get('W', {})
                N_vars = prob._vars.get('N', {})
                W_vals = [pulp.value(W_vars[i]) for i in nurses_list] if W_vars else []
                N_vals = [pulp.value(N_vars[i]) for i in nurses_list] if N_vars else []
                
                extra_stats.append({
                    'eta_VaR': eta_val,
                    'z_max': np.max(z_vals) if z_vals else None,
                    'z_mean': np.mean(z_vals) if z_vals else None,
                    'W_min': np.min(W_vals) if W_vals else None,
                    'W_max': np.max(W_vals) if W_vals else None,
                    'W_mean': np.mean(W_vals) if W_vals else None,
                    'W_std': np.std(W_vals, ddof=1) if len(W_vals) > 1 else 0,
                    'N_min': np.min(N_vals) if N_vals else None,
                    'N_max': np.max(N_vals) if N_vals else None,
                    'N_mean': np.mean(N_vals) if N_vals else None,
                    'N_std': np.std(N_vals, ddof=1) if len(N_vals) > 1 else 0,
                })
            else:
                print(f"    Replication {m+1} failed. Status: {pulp.LpStatus[prob.status]}")

        if not solutions:
            raise ValueError("No optimal solutions found in any replication.")

        # 2. Select best solution x*
        best_idx = np.argmin(objectives)
        x_star = solutions[best_idx]
        best_obj = objectives[best_idx]
        print(f"Selected best solution from replication {best_idx+1} with objective {best_obj:.2f}")

        # 3. Evaluate x* on N' out-of-sample scenarios
        print(f"Evaluating best solution on {self.n_eval} out-of-sample scenarios...")
        eval_seed = master_seed * 100000 + 99999
        demand_gen.rng = np.random.default_rng(eval_seed)
        eval_scenarios_df = demand_gen.generate(
            n_scenarios=self.n_eval, 
            num_days=num_days, 
            scale_factor=scale_factor
        )
        
        # Evaluate with skill-aware recourse
        eval_res = self._evaluate_fixed_schedule(
            x_star, eval_scenarios_df, nurses_list, days_list, shifts_list,
            params, nurse_skill_map, skill_levels
        )
        eval_cost, eval_variance, total_planned, total_em_mean, total_un_mean = eval_res
        
        # 4. Compute statistical optimality gap
        lower_bound = np.mean(objectives)
        gap = eval_cost - lower_bound
        
        # Standard error calculation
        s_v_N_squared = np.var(objectives, ddof=1) if len(objectives) > 1 else 0
        s_N_prime_squared = eval_variance
        
        se_gap = np.sqrt(s_v_N_squared / actual_replications + s_N_prime_squared / self.n_eval)
        
        # 95% Confidence Interval (z = 1.96)
        z_alpha = 1.96
        ci_upper = gap + z_alpha * se_gap
        ci_lower = gap - z_alpha * se_gap

        ret = {
            'best_solution': x_star,
            'nurses_df': nurses_df,
            'lower_bound_mean': lower_bound,
            'eval_cost_mean': eval_cost,
            'gap': gap,
            'gap_se': se_gap,
            'ci_95': (ci_lower, ci_upper),
            'objectives': objectives,
            'solve_times': solve_times,
            'avg_solve_time': np.mean(solve_times) if solve_times else 0,
            'total_planned': total_planned,
            'total_emergency_mean': total_em_mean,
            'total_unmet_mean': total_un_mean,
        }
        
        if extra_stats:
            ret.update(extra_stats[best_idx])
            
        return ret

    def _evaluate_fixed_schedule(self, x_star, eval_scenarios_df, nurses, days, shifts,
                                  params, nurse_skill_map, skill_levels):
        """
        Evaluate fixed schedule x_star on out-of-sample scenarios.
        Uses cascading skill-aware recourse matching the model formulation.
        """
        c_planned = params.get('c_planned', 100)
        c_emergency = params.get('c_emergency', 200)
        c_unmet = params.get('c_unmet', 300)
        a_bar = params.get('a_bar', 2)
        
        # Per-skill costs (same defaults as model)
        c_emergency_skill = params.get('c_emergency_skill', {
            'HN': c_emergency * 1.5, 'RN': c_emergency * 1.0, 'CNA': c_emergency * 0.6,
        })
        c_unmet_skill = params.get('c_unmet_skill', {
            'HN': c_unmet * 3.0, 'RN': c_unmet * 2.0, 'CNA': c_unmet * 1.0,
        })
        a_bar_skill = params.get('a_bar_skill', {l: a_bar for l in skill_levels})
        
        # Calculate planned cost and total planned shifts
        planned_cost = 0
        total_planned = 0
        for i in nurses:
            for j in days:
                for k in shifts:
                    val = x_star.get((i, j, k), 0)
                    planned_cost += c_planned * val
                    total_planned += val
        
        # Calculate planned supply per skill tier per (day, shift)
        supply_by_skill = {}
        for j in days:
            for k in shifts:
                for l in skill_levels:
                    supply_by_skill[(j, k, l)] = sum(
                        x_star.get((i, j, k), 0)
                        for i in nurses if nurse_skill_map.get(i, 'RN') == l
                    )
                    
        # Evaluate recourse for each scenario using cascading coverage
        scenario_costs = []
        scenario_emergency = []
        scenario_unmet = []
        for omega in eval_scenarios_df['scenario'].unique():
            scenario_data = eval_scenarios_df[eval_scenarios_df['scenario'] == omega]
            
            # Build skill-level demand for this scenario
            skill_demand = {}
            for _, row in scenario_data.iterrows():
                key = (int(row['day']), row['shift'], row['skill'])
                skill_demand[key] = skill_demand.get(key, 0) + int(row['demand'])
            
            recourse_cost = 0
            scenario_em = 0
            scenario_un = 0
            for j in days:
                for k in shifts:
                    surplus_from_above = 0
                    
                    for l in skill_levels:
                        supply = supply_by_skill.get((j, k, l), 0) + surplus_from_above
                        d = skill_demand.get((j, k, l), 0)
                        
                        if supply >= d:
                            # Enough nurses — surplus cascades to next tier
                            surplus_from_above = supply - d
                        else:
                            # Shortage — use emergency then unmet
                            shortage = d - supply
                            surplus_from_above = 0
                            
                            a_cap = a_bar_skill.get(l, a_bar)
                            emergency_used = min(shortage, a_cap)
                            unmet_used = shortage - emergency_used
                            
                            scenario_em += emergency_used
                            scenario_un += unmet_used
                            
                            recourse_cost += (
                                c_emergency_skill.get(l, c_emergency) * emergency_used
                                + c_unmet_skill.get(l, c_unmet) * unmet_used
                            )
                    
            scenario_costs.append(planned_cost + recourse_cost)
            scenario_emergency.append(scenario_em)
            scenario_unmet.append(scenario_un)
            
        return (
            np.mean(scenario_costs), 
            np.var(scenario_costs, ddof=1),
            total_planned,
            np.mean(scenario_emergency),
            np.mean(scenario_unmet)
        )

if __name__ == "__main__":
    pipeline = SAAPipeline(n_replications=5, n_scenarios=10, n_eval=100)
    params = {
        'c_planned': 100,
        'c_emergency': 200,
        'c_unmet': 300,
        'W_bar': 10,
        'N_bar': 3,
        'C_bar': 4,
        'F_bar': 15,
        'Delta_W': 2,
        'Delta_N': 1,
        'alpha': 0.90,
        'tau': 100
    }
    res = pipeline.run(num_nurses=15, num_days=7, base_params=params)
    print(f"Gap: {res['gap']:.2f} ± {1.96*res['gap_se']:.2f}")
    print(f"Avg solve time: {res['avg_solve_time']:.2f}s")
