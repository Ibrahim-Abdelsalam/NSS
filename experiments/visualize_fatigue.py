"""
Fatigue Visualization Module

Creates comprehensive visualizations of nurse fatigue over time:
1. Individual nurse fatigue trajectories
2. Heatmap of fatigue levels across all nurses
3. Distribution of max fatigue levels
4. Fatigue vs shift patterns correlation

Usage:
    from visualize_fatigue import plot_fatigue_results
    plot_fatigue_results(results, output_dir='results/figures/')
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, Any
import os


def plot_fatigue_results(results: Dict[str, Any], output_dir: str = 'results/figures/'):
    """
    Create comprehensive fatigue visualizations
    
    Args:
        results: Dictionary from extract_results() with fatigue metrics
        output_dir: Directory to save plots
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract data
    roster_df = results['roster_df']
    fatigue_metrics = results.get('fatigue_metrics', {})
    
    # Create 2x2 subplot layout
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Nurse Fatigue Analysis', fontsize=16, fontweight='bold')
    
    # ========================================================================
    # Plot 1: Fatigue Trajectories (Top 5 Most Fatigued Nurses)
    # ========================================================================
    ax1 = axes[0, 0]
    
    # Get fatigue columns
    fatigue_cols = [col for col in roster_df.columns if col.startswith('Fatigue_D')]
    
    if fatigue_cols:
        # Sort by max fatigue
        roster_df_sorted = roster_df.sort_values('Max_Fatigue', ascending=False)
        top_5_nurses = roster_df_sorted.head(5)
        
        for idx, row in top_5_nurses.iterrows():
            nurse = row['Nurse']
            fatigue_values = [row[col] for col in fatigue_cols]
            days = range(1, len(fatigue_values) + 1)
            
            ax1.plot(days, fatigue_values, marker='o', label=nurse, linewidth=2, markersize=4)
        
        # Add threshold line
        ax1.axhline(y=0.70, color='red', linestyle='--', linewidth=2, label='Safety Threshold')
        
        ax1.set_xlabel('Day', fontsize=12)
        ax1.set_ylabel('Fatigue Level', fontsize=12)
        ax1.set_title('Fatigue Trajectories (Top 5 Most Fatigued)', fontsize=14, fontweight='bold')
        ax1.legend(loc='best', fontsize=9)
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim([0, 1.0])
    
    # ========================================================================
    # Plot 2: Fatigue Heatmap (All Nurses × All Days)
    # ========================================================================
    ax2 = axes[0, 1]
    
    if fatigue_cols:
        # Create fatigue matrix
        fatigue_matrix = roster_df[fatigue_cols].values
        nurse_names = roster_df['Nurse'].values
        
        # Create heatmap
        im = ax2.imshow(fatigue_matrix, cmap='YlOrRd', aspect='auto', vmin=0, vmax=1.0)
        
        # Set ticks
        ax2.set_xticks(range(len(fatigue_cols)))
        ax2.set_xticklabels([f'D{i+1}' for i in range(len(fatigue_cols))], fontsize=8)
        ax2.set_yticks(range(len(nurse_names)))
        ax2.set_yticklabels(nurse_names, fontsize=8)
        
        ax2.set_xlabel('Day', fontsize=12)
        ax2.set_ylabel('Nurse', fontsize=12)
        ax2.set_title('Fatigue Heatmap (All Nurses)', fontsize=14, fontweight='bold')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax2)
        cbar.set_label('Fatigue Level', fontsize=10)
    
    # ========================================================================
    # Plot 3: Distribution of Max Fatigue Levels
    # ========================================================================
    ax3 = axes[1, 0]
    
    max_fatigue_values = roster_df['Max_Fatigue'].values
    
    ax3.hist(max_fatigue_values, bins=20, color='steelblue', edgecolor='black', alpha=0.7)
    ax3.axvline(x=0.70, color='red', linestyle='--', linewidth=2, label='Safety Threshold (0.70)')
    ax3.axvline(x=np.mean(max_fatigue_values), color='green', linestyle='--', linewidth=2, 
               label=f'Mean ({np.mean(max_fatigue_values):.2f})')
    
    ax3.set_xlabel('Max Fatigue Level', fontsize=12)
    ax3.set_ylabel('Number of Nurses', fontsize=12)
    ax3.set_title('Distribution of Peak Fatigue Levels', fontsize=14, fontweight='bold')
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # ========================================================================
    # Plot 4: Fatigue vs Total Shifts (Correlation Analysis)
    # ========================================================================
    ax4 = axes[1, 1]
    
    total_shifts = roster_df['Total_Shifts'].values
    
    ax4.scatter(total_shifts, max_fatigue_values, alpha=0.6, s=100, c='steelblue', edgecolors='black')
    
    # Add trend line
    z = np.polyfit(total_shifts, max_fatigue_values, 1)
    p = np.poly1d(z)
    ax4.plot(total_shifts, p(total_shifts), "r--", linewidth=2, label=f'Trend: y={z[0]:.3f}x+{z[1]:.3f}')
    
    # Calculate correlation
    correlation = np.corrcoef(total_shifts, max_fatigue_values)[0, 1]
    
    ax4.axhline(y=0.70, color='red', linestyle='--', linewidth=1, alpha=0.5)
    ax4.set_xlabel('Total Shifts Worked', fontsize=12)
    ax4.set_ylabel('Max Fatigue Level', fontsize=12)
    ax4.set_title(f'Fatigue vs Workload (r={correlation:.3f})', fontsize=14, fontweight='bold')
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'fatigue_analysis.png'), dpi=300, bbox_inches='tight')
    print(f"✅ Fatigue visualization saved to: {output_dir}fatigue_analysis.png")
    
    plt.close()


def plot_fatigue_comparison(results_without: Dict, results_with: Dict, output_dir: str = 'results/figures/'):
    """
    Compare fatigue metrics between models with/without fatigue optimization
    
    Args:
        results_without: Results from model without fatigue
        results_with: Results from model with fatigue
        output_dir: Directory to save plots
    """
    os.makedirs(output_dir, exist_ok=True)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('Impact of Fatigue Optimization', fontsize=16, fontweight='bold')
    
    # Extract max fatigue values
    max_fatigue_without = results_without['roster_df']['Max_Fatigue'].values
    max_fatigue_with = results_with['roster_df']['Max_Fatigue'].values
    
    # Plot 1: Side-by-side box plots
    ax1 = axes[0]
    data_to_plot = [max_fatigue_without, max_fatigue_with]
    bp = ax1.boxplot(data_to_plot, labels=['Without Fatigue\nOptimization', 'With Fatigue\nOptimization'],
                     patch_artist=True)
    
    bp['boxes'][0].set_facecolor('lightcoral')
    bp['boxes'][1].set_facecolor('lightgreen')
    
    ax1.axhline(y=0.70, color='red', linestyle='--', linewidth=2, label='Safety Threshold')
    ax1.set_ylabel('Max Fatigue Level', fontsize=12)
    ax1.set_title('Fatigue Distribution Comparison', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Plot 2: Improvement metrics
    ax2 = axes[1]
    
    metrics = ['Mean\nFatigue', 'Max\nFatigue', 'Nurses Above\nThreshold', 'Total\nCost']
    
    mean_without = np.mean(max_fatigue_without)
    mean_with = np.mean(max_fatigue_with)
    max_without = np.max(max_fatigue_without)
    max_with = np.max(max_fatigue_with)
    above_without = np.sum(max_fatigue_without > 0.70)
    above_with = np.sum(max_fatigue_with > 0.70)
    cost_without = results_without['cost_breakdown']['total_cost']
    cost_with = results_with['cost_breakdown']['total_cost']
    
    # Calculate percent changes
    changes = [
        ((mean_with - mean_without) / mean_without) * 100,
        ((max_with - max_without) / max_without) * 100,
        ((above_with - above_without) / max(1, above_without)) * 100,
        ((cost_with - cost_without) / cost_without) * 100
    ]
    
    colors = ['green' if c < 0 else 'red' for c in changes]
    bars = ax2.bar(metrics, changes, color=colors, alpha=0.7, edgecolor='black')
    
    # Add value labels
    for bar, change in zip(bars, changes):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{change:+.1f}%',
                ha='center', va='bottom' if height > 0 else 'top', fontsize=10, fontweight='bold')
    
    ax2.axhline(y=0, color='black', linewidth=1)
    ax2.set_ylabel('Percent Change (%)', fontsize=12)
    ax2.set_title('Impact of Fatigue Model', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'fatigue_comparison.png'), dpi=300, bbox_inches='tight')
    print(f"✅ Comparison plot saved to: {output_dir}fatigue_comparison.png")
    
    plt.close()


if __name__ == '__main__':
    # Example usage (will be integrated with actual results)
    print("Fatigue visualization module loaded.")
    print("Use plot_fatigue_results(results) to visualize fatigue data.")
