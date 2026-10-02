import streamlit as st
import os
import sys
import pandas as pd
import numpy as np
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from experiments.saa_pipeline import SAAPipeline
from core.advanced_data_generator import HeterogeneousNurseGenerator, ExogenousDemandGenerator

st.set_page_config(page_title="Scientific Experiments", layout="wide")

# Global Settings Sidebar
st.sidebar.header("Global Experiment Settings")
n_replications = st.sidebar.number_input("Replications (M)", min_value=1, max_value=1000, value=1, help="The number of independent Monte Carlo replications used in the Sample Average Approximation (SAA) procedure to estimate the statistical lower bound.")
n_scenarios = st.sidebar.number_input("In-Sample Scenarios (N)", min_value=1, max_value=1000, value=5, help="The cardinality of the discrete scenario set utilized to construct the empirical cumulative distribution function for the CVaR optimization.")
n_eval = st.sidebar.number_input("Out-of-Sample Scenarios (N')", min_value=10, max_value=50000, value=50, help="The number of independent, unseen scenarios utilized for ex-post evaluation of the fixed first-stage solution to compute the true Expected Cost and Optimality Gap.")

st.sidebar.markdown("---")
st.sidebar.header("Randomization")
base_seed = st.sidebar.number_input("Master Seed", min_value=1, max_value=99999, value=42, help="The deterministic initialization seed for the pseudorandom number generator (PRNG), ensuring complete experimental reproducibility.")
num_seeds_test = st.sidebar.number_input("Number of Seeds to Test", min_value=1, max_value=1000, value=5, help="Specifies the number of independent PRNG master seeds to iterate over during the algorithmic robustness analysis.")

os.makedirs("results/test_inputs", exist_ok=True)

total_tests = 5 + num_seeds_test + 34 + 3  # Ablation(5) + Seeds(N) + Sens(34) + Scale(3)

# Main UI Container
ui_container = st.empty()

with ui_container.container():
    st.title("🧪 Scientific Experiments Dashboard")
    st.markdown("This dashboard will automatically run the complete suite of mathematical proofs required for the NILES 2026 paper.")
    
    st.info(f"**Total Tasks Queued:** {total_tests} massive MIP Matrix solves + real-world CVaR simulations.")
    
    start_button = st.button("🚀 RUN ALL EXPERIMENTS AUTOMATICALLY", type="primary", use_container_width=True)

if start_button:
    # 1. Grey out the UI and show the GIF
    ui_container.empty() # Clear the old UI
    
    with ui_container.container():
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #888888;'>Running Master Evaluation Suite...</h2>", unsafe_allow_html=True)
        
        # Load the user's local GIF and encode it to base64
        import base64
        gif_path = "assets/loading.gif"
        if os.path.exists(gif_path):
            with open(gif_path, "rb") as f:
                gif_b64 = base64.b64encode(f.read()).decode("utf-8")
            st.markdown(f"<div style='text-align: center;'><img src='data:image/gif;base64,{gif_b64}' width='150' style='opacity: 0.9;'></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align: center;'><h2>⏳</h2></div>", unsafe_allow_html=True)
            
        st.markdown("<h3 style='text-align: center; font-family: monospace;'>Solving...</h3>", unsafe_allow_html=True)
        
        # Counters
        counter_text = st.empty()
        log_text = st.empty()
        progress_bar = st.progress(0)
        
    current_test = 0
    def start_test(msg):
        global current_test
        current_test += 1
        counter_text.markdown(f"<h3 style='text-align: center; color: #4CAF50;'>{current_test} / {total_tests} Tests Started</h3>", unsafe_allow_html=True)
        log_text.markdown(f"<p style='text-align: center; color: gray;'><i>Working on: {msg}</i></p>", unsafe_allow_html=True)
        progress_bar.progress(int(((current_test - 1) / total_tests) * 100))
        
    def end_test():
        progress_bar.progress(int((current_test / total_tests) * 100))

    pipeline = SAAPipeline(n_replications=n_replications, n_scenarios=n_scenarios, n_eval=n_eval)
    base_params = {'c_planned': 100, 'c_emergency': 200, 'c_unmet': 300, 'W_bar': 10, 'N_bar': 3, 'solve_time_limit': 15}
    
    # Generate test inputs
    n_gen = HeterogeneousNurseGenerator(seed=base_seed)
    nurses_df = n_gen.generate(15)
    nurses_df.to_csv("results/test_inputs/input_nurses.csv", index=False)
    d_gen = ExogenousDemandGenerator(seed=base_seed + 1)
    scenarios_df = d_gen.generate(n_scenarios=n_scenarios, num_days=7, scale_factor=0.5)
    scenarios_df.to_csv("results/test_inputs/input_scenarios.csv", index=False)

    # ---------------------------------------------------------
    # Test 1: Ablation Study
    # ---------------------------------------------------------
    results_ablation = []
    raw_trials = []
    
    def log_raw_trials(test_name, res):
        for m, (obj, time_s) in enumerate(zip(res['objectives'], res['solve_times'])):
            raw_trials.append({
                "Test": test_name,
                "Replication": m + 1,
                "Lower_Bound_Cost": obj,
                "Solver_Time_s": time_s
            })
    
    variants = [
        {"name": "DETERM", "is_deterministic": True, "params": {"F_bar": 15, "alpha": 0.90, "Delta_W": 2, "Delta_N": 1}},
        {"name": "FULL-CVAR", "is_deterministic": False, "params": {"F_bar": 15, "alpha": 1.0, "Delta_W": 2, "Delta_N": 1}},
        {"name": "FULL-FAIR", "is_deterministic": False, "params": {"F_bar": 15, "alpha": 0.90, "Delta_W": 999, "Delta_N": 999}},
        {"name": "FULL-FAT", "is_deterministic": False, "params": {"F_bar": 999, "alpha": 0.90, "Delta_W": 2, "Delta_N": 1}},
        {"name": "FULL", "is_deterministic": False, "params": {"F_bar": 15, "alpha": 0.90, "Delta_W": 2, "Delta_N": 1}},
    ]
    
    for variant in variants:
        start_test(f"Ablation: {variant['name']}")
        params = base_params.copy()
        params.update(variant['params'])
        t0 = time.time()
        res = pipeline.run(15, 7, params, is_deterministic=variant['is_deterministic'], master_seed=base_seed)
        end_test()
        results_ablation.append({"Model": variant['name'], "Expected Cost": res['eval_cost_mean'], "Emergency Shifts": res['total_emergency_mean'], "Optimality Gap": res['gap'], "VaR (η)": res.get('eta_VaR', 0), "Tail Risk (z)": res.get('z_mean', 0), "W_std": res.get('W_std', 0), "N_std": res.get('N_std', 0), "Solver Time (s)": res.get('avg_solve_time', 0), "Total Time (s)": time.time()-t0})
        log_raw_trials(f"Ablation: {variant['name']}", res)
    
    pd.DataFrame(results_ablation).to_csv("results/ablation_study.csv", index=False)

    # ---------------------------------------------------------
    # Test 2: Multi-Seed Robustness
    # ---------------------------------------------------------
    results_seeds = []
    dynamic_seeds = [base_seed + i * 111 for i in range(num_seeds_test)]
    for seed in dynamic_seeds:
        start_test(f"Seed Robustness (Seed {seed})")
        t0 = time.time()
        res = pipeline.run(15, 7, base_params, is_deterministic=False, master_seed=seed)
        end_test()
        results_seeds.append({"Seed": seed, "Expected Cost": res['eval_cost_mean'], "Optimality Gap": res['gap'], "Solver Time (s)": res.get('avg_solve_time', 0), "Total Time (s)": time.time()-t0})
        log_raw_trials(f"Robustness Seed: {seed}", res)
    
    pd.DataFrame(results_seeds).to_csv("results/multi_seed_robustness.csv", index=False)

    # ---------------------------------------------------------
    # Test 3: Extensive Sensitivity Analysis
    # ---------------------------------------------------------
    results_sens = []
    
    sweeps = [
        ('F_bar', [8, 12, 16, 20]),
        ('alpha', [0.80, 0.85, 0.90, 0.95]),
        ('tau', [50, 100, 150, 200]),
        ('W_bar', [8, 10, 12, 14]),
        ('N_bar', [2, 3, 4, 5]),
        ('Delta_W', [1, 2, 3, 4]),
        ('Delta_N', [1, 2, 3]),
        ('a_bar', [1, 2, 3, 4])
    ]
    
    for param_name, values in sweeps:
        for val in values:
            start_test(f"Sweep: {param_name} = {val}")
            params = base_params.copy()
            params[param_name] = val
            t0 = time.time()
            res = pipeline.run(15, 7, params, is_deterministic=False, master_seed=base_seed)
            end_test()
            results_sens.append({"Parameter Swept": param_name, "Value": val, "Expected Cost": res['eval_cost_mean'], "Optimality Gap": res['gap'], "VaR (η)": res.get('eta_VaR', 0), "Tail Risk (z)": res.get('z_mean', 0), "W_std": res.get('W_std', 0), "N_std": res.get('N_std', 0), "Solver Time (s)": res.get('avg_solve_time', 0), "Total Time (s)": time.time()-t0})
            log_raw_trials(f"Sensitivity: {param_name}={val}", res)

    # Cost Ratio Sweep
    cost_ratios = [("Standard", 100, 200, 300), ("High Emg", 100, 400, 600), ("High Unmet", 100, 200, 800)]
    for label, cp, ce, cu in cost_ratios:
        start_test(f"Sweep: Cost Ratio = {label}")
        params = base_params.copy()
        params['c_planned'] = cp
        params['c_emergency'] = ce
        params['c_unmet'] = cu
        t0 = time.time()
        res = pipeline.run(15, 7, params, is_deterministic=False, master_seed=base_seed)
        end_test()
        results_sens.append({"Parameter Swept": "Cost Ratio", "Value": label, "Expected Cost": res['eval_cost_mean'], "Optimality Gap": res['gap'], "VaR (η)": res.get('eta_VaR', 0), "Tail Risk (z)": res.get('z_mean', 0), "W_std": res.get('W_std', 0), "N_std": res.get('N_std', 0), "Solver Time (s)": res.get('avg_solve_time', 0), "Total Time (s)": time.time()-t0})
        log_raw_trials(f"Sensitivity: CostRatio={label}", res)
        
    pd.DataFrame(results_sens).to_csv("results/ui_sensitivity_results.csv", index=False)

    # ---------------------------------------------------------
    # Test 4: Scalability Test
    # ---------------------------------------------------------
    results_scale = []
    cases = [{"name": "Small Unit", "nurses": 10}, {"name": "General ICU", "nurses": 20}, {"name": "Emergency Ward", "nurses": 30}]
    for case in cases:
        start_test(f"Scalability Test ({case['name']})")
        t0 = time.time()
        res = pipeline.run(case['nurses'], 7, base_params, is_deterministic=False, master_seed=base_seed)
        end_test()
        results_scale.append({"Case Size": case['name'], "Nurses": case['nurses'], "Expected Cost": res['eval_cost_mean'], "Solver Time (s)": res.get('avg_solve_time', 0), "Total Time (s)": time.time()-t0})
        log_raw_trials(f"Scalability: {case['name']}", res)
        
    pd.DataFrame(results_scale).to_csv("results/scalability_test.csv", index=False)
    
    # Save the raw trials master log
    pd.DataFrame(raw_trials).to_csv("results/raw_trials_log.csv", index=False)

    # ---------------------------------------------------------
    # Finish and display results
    # ---------------------------------------------------------
    ui_container.empty() # Clear GIF and counters
    
    st.success("✅ All Master Experiments Completed Successfully!")
    st.balloons()
    
    st.subheader("1. Ablation Study")
    st.dataframe(pd.DataFrame(results_ablation), use_container_width=True)
    
    st.subheader("2. Algorithmic Stability")
    st.dataframe(pd.DataFrame(results_seeds), use_container_width=True)
    
    st.subheader("3. Comprehensive Sensitivity Sweeps")
    st.dataframe(pd.DataFrame(results_sens), use_container_width=True)
    
    st.subheader("4. Scalability (CPU Test)")
    st.dataframe(pd.DataFrame(results_scale), use_container_width=True)
