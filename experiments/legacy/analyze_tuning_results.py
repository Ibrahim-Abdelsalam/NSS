#!/usr/bin/env python3
"""
Analysis Script for Parameter Tuning Results

Analyzes the 81-configuration factorial experiment results:
1. Sensitivity analysis (main effects and interactions)
2. Cost-fatigue tradeoff curves
3. Optimal parameter identification
4. Statistical significance testing

Usage:
    python experiments/analyze_tuning_results.py --input results/parameter_tuning_results.csv
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import argparse
import os


# ====================================================================================
# DATA LOADING
# ====================================================================================

def load_results(filepath):
    """Load and validate experimental results"""
    
    print(f'Loading results from: {filepath}')
    df = pd.read_csv(filepath)
    
    print(f'\nDataset Info:')
    print(f'  Total runs: {len(df)}')
    print(f'  Unique configs: {df["config_id"].nunique()}')
    print(f'  Replications per config: {len(df) // df["config_id"].nunique()}')
    print(f'  Optimal solutions: {sum(df["status"] == "Optimal")} ({100*sum(df["status"] == "Optimal")/len(df):.1f}%)')
    
    # Filter to only optimal solutions
    df_optimal = df[df['status'] == 'Optimal'].copy()
    print(f'\nAnalyzing {len(df_optimal)} optimal solutions')
    
    return df_optimal


# ====================================================================================
# DESCRIPTIVE STATISTICS
# ====================================================================================

def compute_summary_stats(df):
    """Compute summary statistics by factor level"""
    
    print('\n' + '='*80)
    print('SUMMARY STATISTICS BY FACTOR')
    print('='*80)
    
    factors = ['lambda', 'weight', 'threshold', 'demand_level']
    
    for factor in factors:
        print(f'\n{factor.upper()}:')
        
        summary = df.groupby(factor).agg({
            'total_cost': ['mean', 'std', 'min', 'max'],
            'patient_safety_cost': ['mean', 'std'],
            'max_fatigue': ['mean', 'std'],
            'avg_fatigue': ['mean', 'std'],
            'high_fatigue_days': ['mean', 'std'],
            'working_nurses': ['mean', 'std'],
            'solve_time': ['mean', 'std']
        }).round(2)
        
        print(summary)
    
    return summary


# ====================================================================================
# SENSITIVITY ANALYSIS
# ====================================================================================

def sensitivity_analysis(df):
    """Perform sensitivity analysis on each factor"""
    
    print('\n' + '='*80)
    print('SENSITIVITY ANALYSIS (One-Way ANOVA)')
    print('='*80)
    
    factors = ['lambda', 'weight', 'threshold', 'demand_level']
    outcomes = ['total_cost', 'patient_safety_cost', 'max_fatigue', 'avg_fatigue']
    
    results = []
    
    for outcome in outcomes:
        print(f'\n{outcome.upper()}:')
        print('-' * 60)
        
        for factor in factors:
            # Group data by factor level
            groups = [group[outcome].values for name, group in df.groupby(factor)]
            
            # Perform one-way ANOVA
            f_stat, p_value = stats.f_oneway(*groups)
            
            # Effect size (eta-squared)
            grand_mean = df[outcome].mean()
            ss_between = sum(len(g) * (g.mean() - grand_mean)**2 for g in groups)
            ss_total = sum((df[outcome] - grand_mean)**2)
            eta_squared = ss_between / ss_total if ss_total > 0 else 0
            
            results.append({
                'outcome': outcome,
                'factor': factor,
                'F_statistic': f_stat,
                'p_value': p_value,
                'eta_squared': eta_squared,
                'significant': '***' if p_value < 0.001 else '**' if p_value < 0.01 else '*' if p_value < 0.05 else 'ns'
            })
            
            print(f'  {factor:15s}: F={f_stat:7.2f}, p={p_value:.4f}, η²={eta_squared:.3f} {results[-1]["significant"]}')
    
    return pd.DataFrame(results)


# ====================================================================================
# INTERACTION ANALYSIS
# ====================================================================================

def interaction_analysis(df):
    """Analyze two-way interactions between factors"""
    
    print('\n' + '='*80)
    print('TWO-WAY INTERACTION ANALYSIS')
    print('='*80)
    
    from itertools import combinations
    
    factors = ['lambda', 'weight', 'threshold', 'demand_level']
    factor_pairs = list(combinations(factors, 2))
    
    # Focus on total cost
    outcome = 'total_cost'
    
    print(f'\nOutcome: {outcome}')
    print('-' * 60)
    
    for factor1, factor2 in factor_pairs:
        # Create interaction groups
        interaction_means = df.groupby([factor1, factor2])[outcome].mean()
        
        # Compute interaction strength (variance of cell means)
        main1_effect = df.groupby(factor1)[outcome].mean().std()
        main2_effect = df.groupby(factor2)[outcome].mean().std()
        interaction_effect = interaction_means.std()
        
        # Relative interaction strength
        total_variation = main1_effect + main2_effect
        relative_strength = interaction_effect / total_variation if total_variation > 0 else 0
        
        print(f'  {factor1} × {factor2:15s}: Interaction SD=${interaction_effect:,.0f}, Relative={relative_strength:.3f}')


# ====================================================================================
# OPTIMAL CONFIGURATION
# ====================================================================================

def find_optimal_config(df, objective='cost_fatigue_balance'):
    """Identify optimal parameter configuration"""
    
    print('\n' + '='*80)
    print(f'OPTIMAL CONFIGURATION ({objective})')
    print('='*80)
    
    if objective == 'min_cost':
        # Simply minimize total cost
        best_idx = df.groupby('config_id')['total_cost'].mean().idxmin()
        
    elif objective == 'min_fatigue':
        # Minimize maximum fatigue
        best_idx = df.groupby('config_id')['max_fatigue'].mean().idxmin()
        
    elif objective == 'cost_fatigue_balance':
        # Multi-objective: normalize and combine
        df_grouped = df.groupby('config_id').agg({
            'total_cost': 'mean',
            'max_fatigue': 'mean',
            'high_fatigue_days': 'mean',
            'lambda': 'first',
            'weight': 'first',
            'threshold': 'first',
            'demand_level': 'first'
        })
        
        # Normalize to [0, 1] (lower is better)
        df_grouped['cost_norm'] = (df_grouped['total_cost'] - df_grouped['total_cost'].min()) / (df_grouped['total_cost'].max() - df_grouped['total_cost'].min())
        df_grouped['fatigue_norm'] = (df_grouped['max_fatigue'] - df_grouped['max_fatigue'].min()) / (df_grouped['max_fatigue'].max() - df_grouped['max_fatigue'].min())
        df_grouped['risk_norm'] = (df_grouped['high_fatigue_days'] - df_grouped['high_fatigue_days'].min()) / (df_grouped['high_fatigue_days'].max() - df_grouped['high_fatigue_days'].min())
        
        # Combined score (equal weights)
        df_grouped['combined_score'] = (df_grouped['cost_norm'] + df_grouped['fatigue_norm'] + df_grouped['risk_norm']) / 3
        
        best_idx = df_grouped['combined_score'].idxmin()
    
    # Get best configuration
    best_config = df[df['config_id'] == best_idx].iloc[0]
    
    print(f'\nOptimal Configuration (Config ID: {best_idx}):')
    print(f'  Lambda (λ):        {best_config["lambda"]:.3f}')
    print(f'  Safety Weight ($): {best_config["weight"]:.0f}')
    print(f'  Threshold:         {best_config["threshold"]:.2f}')
    print(f'  Demand Level:      {best_config["demand_level"]}')
    
    print(f'\nPerformance Metrics (averaged over replications):')
    config_metrics = df[df['config_id'] == best_idx].agg({
        'total_cost': ['mean', 'std'],
        'patient_safety_cost': ['mean', 'std'],
        'max_fatigue': ['mean', 'std'],
        'avg_fatigue': ['mean', 'std'],
        'high_fatigue_days': ['mean', 'std'],
        'working_nurses': 'mean',
        'solve_time': 'mean'
    })
    
    for metric in ['total_cost', 'patient_safety_cost', 'max_fatigue', 'avg_fatigue', 'high_fatigue_days']:
        mean_val = config_metrics.loc['mean', metric]
        std_val = config_metrics.loc['std', metric]
        print(f'  {metric:25s}: {mean_val:10.2f} ± {std_val:.2f}')
    
    print(f'  {"working_nurses":25s}: {config_metrics.loc["mean", "working_nurses"]:10.1f}')
    print(f'  {"solve_time":25s}: {config_metrics.loc["mean", "solve_time"]:10.2f}s')
    
    return best_idx, best_config


# ====================================================================================
# VISUALIZATION
# ====================================================================================

def create_visualizations(df, output_dir='results/figures'):
    """Create visualization plots"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f'\n' + '='*80)
    print('CREATING VISUALIZATIONS')
    print('='*80)
    
    # Set style
    sns.set_style('whitegrid')
    plt.rcParams['figure.figsize'] = (12, 8)
    
    # 1. Main Effects Plot
    print('\n1. Creating main effects plots...')
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    factors = ['lambda', 'weight', 'threshold', 'demand_level']
    
    for idx, factor in enumerate(factors):
        ax = axes[idx // 2, idx % 2]
        
        # Aggregate by factor level
        grouped = df.groupby(factor).agg({
            'total_cost': ['mean', 'std'],
            'max_fatigue': ['mean', 'std']
        })
        
        # Plot cost
        ax2 = ax.twinx()
        x_pos = range(len(grouped))
        
        ax.errorbar(x_pos, grouped['total_cost']['mean'], yerr=grouped['total_cost']['std'],
                   marker='o', linewidth=2, capsize=5, label='Total Cost', color='blue')
        ax2.errorbar(x_pos, grouped['max_fatigue']['mean'], yerr=grouped['max_fatigue']['std'],
                    marker='s', linewidth=2, capsize=5, label='Max Fatigue', color='red')
        
        ax.set_xlabel(factor.replace('_', ' ').title(), fontsize=12)
        ax.set_ylabel('Total Cost ($)', fontsize=11, color='blue')
        ax2.set_ylabel('Max Fatigue', fontsize=11, color='red')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(grouped.index)
        ax.tick_params(axis='y', labelcolor='blue')
        ax2.tick_params(axis='y', labelcolor='red')
        ax.grid(True, alpha=0.3)
        
    plt.tight_layout()
    plt.savefig(f'{output_dir}/main_effects.png', dpi=300, bbox_inches='tight')
    print(f'   Saved: {output_dir}/main_effects.png')
    plt.close()
    
    # 2. Cost vs Fatigue Tradeoff
    print('2. Creating cost-fatigue tradeoff plot...')
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Aggregate by config
    config_summary = df.groupby('config_id').agg({
        'total_cost': 'mean',
        'max_fatigue': 'mean',
        'lambda': 'first',
        'weight': 'first',
        'threshold': 'first'
    })
    
    scatter = ax.scatter(config_summary['max_fatigue'], config_summary['total_cost'],
                        c=config_summary['weight'], s=100, alpha=0.6, cmap='viridis')
    
    ax.set_xlabel('Maximum Fatigue', fontsize=12)
    ax.set_ylabel('Total Cost ($)', fontsize=12)
    ax.set_title('Cost-Fatigue Tradeoff (colored by safety weight)', fontsize=14)
    ax.grid(True, alpha=0.3)
    
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Safety Weight ($)', fontsize=11)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/cost_fatigue_tradeoff.png', dpi=300, bbox_inches='tight')
    print(f'   Saved: {output_dir}/cost_fatigue_tradeoff.png')
    plt.close()
    
    # 3. Solve Time Analysis
    print('3. Creating solve time analysis...')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    solve_time_summary = df.groupby('demand_level')['solve_time'].agg(['mean', 'std', 'min', 'max'])
    x_pos = range(len(solve_time_summary))
    
    ax.bar(x_pos, solve_time_summary['mean'], yerr=solve_time_summary['std'],
           capsize=5, alpha=0.7, color='steelblue')
    ax.set_xlabel('Demand Level', fontsize=12)
    ax.set_ylabel('Solve Time (seconds)', fontsize=12)
    ax.set_title('Average Solve Time by Demand Level', fontsize=14)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(solve_time_summary.index)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/solve_time.png', dpi=300, bbox_inches='tight')
    print(f'   Saved: {output_dir}/solve_time.png')
    plt.close()
    
    # 4. Heatmap: Lambda × Weight interaction
    print('4. Creating interaction heatmap...')
    fig, ax = plt.subplots(figsize=(10, 8))
    
    pivot_table = df.groupby(['lambda', 'weight'])['total_cost'].mean().unstack()
    
    sns.heatmap(pivot_table, annot=True, fmt='.0f', cmap='YlOrRd', ax=ax, cbar_kws={'label': 'Total Cost ($)'})
    ax.set_xlabel('Safety Weight ($)', fontsize=12)
    ax.set_ylabel('Lambda (λ)', fontsize=12)
    ax.set_title('Total Cost: Lambda × Weight Interaction', fontsize=14)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/lambda_weight_interaction.png', dpi=300, bbox_inches='tight')
    print(f'   Saved: {output_dir}/lambda_weight_interaction.png')
    plt.close()
    
    print(f'\n✓ All visualizations saved to: {output_dir}/')


# ====================================================================================
# MAIN ANALYSIS PIPELINE
# ====================================================================================

def main(input_file, output_dir='results'):
    """Run complete analysis pipeline"""
    
    print('\n' + '='*80)
    print('PARAMETER TUNING ANALYSIS')
    print('='*80)
    
    # Load data
    df = load_results(input_file)
    
    # Compute summary statistics
    summary = compute_summary_stats(df)
    
    # Sensitivity analysis
    sensitivity_results = sensitivity_analysis(df)
    sensitivity_results.to_csv(f'{output_dir}/sensitivity_analysis.csv', index=False)
    print(f'\n✓ Sensitivity results saved to: {output_dir}/sensitivity_analysis.csv')
    
    # Interaction analysis
    interaction_analysis(df)
    
    # Find optimal configurations
    print('\n' + '='*80)
    print('IDENTIFYING OPTIMAL CONFIGURATIONS')
    print('='*80)
    
    print('\n--- Strategy 1: Minimize Cost ---')
    best_cost_id, best_cost_config = find_optimal_config(df, 'min_cost')
    
    print('\n--- Strategy 2: Minimize Fatigue ---')
    best_fatigue_id, best_fatigue_config = find_optimal_config(df, 'min_fatigue')
    
    print('\n--- Strategy 3: Balance Cost & Fatigue ---')
    best_balanced_id, best_balanced_config = find_optimal_config(df, 'cost_fatigue_balance')
    
    # Save optimal configs
    optimal_configs = pd.DataFrame([
        {'strategy': 'min_cost', 'config_id': best_cost_id, **best_cost_config.to_dict()},
        {'strategy': 'min_fatigue', 'config_id': best_fatigue_id, **best_fatigue_config.to_dict()},
        {'strategy': 'balanced', 'config_id': best_balanced_id, **best_balanced_config.to_dict()}
    ])
    optimal_configs.to_csv(f'{output_dir}/optimal_configurations.csv', index=False)
    print(f'\n✓ Optimal configurations saved to: {output_dir}/optimal_configurations.csv')
    
    # Create visualizations
    create_visualizations(df, f'{output_dir}/figures')
    
    print('\n' + '='*80)
    print('ANALYSIS COMPLETE')
    print('='*80)
    print(f'\nAll outputs saved to: {output_dir}/')
    print('  - sensitivity_analysis.csv')
    print('  - optimal_configurations.csv')
    print('  - figures/ (4 plots)')


# ====================================================================================
# CLI
# ====================================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze parameter tuning results')
    parser.add_argument('--input', default='results/parameter_tuning_results.csv',
                       help='Input CSV file with experiment results')
    parser.add_argument('--output', default='results',
                       help='Output directory for analysis results')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f'ERROR: Input file not found: {args.input}')
        print('Please run parameter_tuning.py first.')
    else:
        main(args.input, args.output)
