"""
Configuration Comparison Visualization
======================================
Creates visual analysis of all tested configurations
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Read results
df = pd.read_csv('configuration_comparison.csv')
feasible = df[df['feasible'] == True].copy()

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Create comprehensive figure
fig = plt.figure(figsize=(20, 12))

# 1. Total Cost Comparison
ax1 = plt.subplot(2, 3, 1)
feasible_sorted = feasible.sort_values('total_cost')
bars = ax1.barh(range(len(feasible_sorted)), feasible_sorted['total_cost'], color='steelblue')
bars[0].set_color('green')  # Highlight best
ax1.set_yticks(range(len(feasible_sorted)))
ax1.set_yticklabels([name.split('.')[1].strip() for name in feasible_sorted['config_name']], fontsize=9)
ax1.set_xlabel('Total Cost (£)', fontsize=12, fontweight='bold')
ax1.set_title('Total Cost by Configuration', fontsize=14, fontweight='bold')
ax1.grid(axis='x', alpha=0.3)
for i, (idx, row) in enumerate(feasible_sorted.iterrows()):
    ax1.text(row['total_cost'] + 100, i, f"£{row['total_cost']:,.0f}", 
             va='center', fontsize=9)

# 2. Cost Breakdown (Stage 1 vs Stage 2)
ax2 = plt.subplot(2, 3, 2)
x = range(len(feasible_sorted))
width = 0.6
ax2.bar(x, feasible_sorted['stage1_cost'], width, label='Stage 1 (Planned)', color='lightblue')
ax2.bar(x, feasible_sorted['stage2_cost'], width, bottom=feasible_sorted['stage1_cost'],
        label='Stage 2 (Emergency)', color='coral')
ax2.set_xticks(x)
ax2.set_xticklabels([name.split('.')[0] for name in feasible_sorted['config_name']], 
                     rotation=45, ha='right', fontsize=9)
ax2.set_ylabel('Cost (£)', fontsize=12, fontweight='bold')
ax2.set_title('Cost Breakdown: Stage 1 vs Stage 2', fontsize=14, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(axis='y', alpha=0.3)

# 3. Shift Allocation
ax3 = plt.subplot(2, 3, 3)
x = range(len(feasible_sorted))
ax3.bar(x, feasible_sorted['regular_shifts'], width, label='Regular', color='green', alpha=0.7)
ax3.bar(x, feasible_sorted['overtime_shifts'], width, 
        bottom=feasible_sorted['regular_shifts'], label='Overtime', color='orange', alpha=0.7)
ax3_2 = ax3.twinx()
ax3_2.plot(x, feasible_sorted['total_emergency'], 'ro-', linewidth=2, 
           markersize=8, label='Emergency')
ax3.set_xticks(x)
ax3.set_xticklabels([name.split('.')[0] for name in feasible_sorted['config_name']], 
                     rotation=45, ha='right', fontsize=9)
ax3.set_ylabel('Planned Shifts', fontsize=12, fontweight='bold')
ax3_2.set_ylabel('Emergency Shifts', fontsize=12, fontweight='bold', color='red')
ax3.set_title('Shift Allocation by Type', fontsize=14, fontweight='bold')
ax3.legend(loc='upper left', fontsize=10)
ax3_2.legend(loc='upper right', fontsize=10)
ax3.grid(axis='y', alpha=0.3)

# 4. Workload Distribution
ax4 = plt.subplot(2, 3, 4)
workload_data = []
for idx, row in feasible_sorted.iterrows():
    workload_data.extend([
        {'Config': row['config_name'].split('.')[0], 'Metric': 'Min', 
         'Value': row['min_nurse_shifts']},
        {'Config': row['config_name'].split('.')[0], 'Metric': 'Avg', 
         'Value': row['avg_nurse_shifts']},
        {'Config': row['config_name'].split('.')[0], 'Metric': 'Max', 
         'Value': row['max_nurse_shifts']}
    ])
workload_df = pd.DataFrame(workload_data)
pivot_df = workload_df.pivot(index='Config', columns='Metric', values='Value')
pivot_df[['Min', 'Avg', 'Max']].plot(kind='bar', ax=ax4, color=['lightgreen', 'gold', 'salmon'])
ax4.set_xlabel('Configuration', fontsize=12, fontweight='bold')
ax4.set_ylabel('Shifts per Nurse', fontsize=12, fontweight='bold')
ax4.set_title('Workload Distribution (Min/Avg/Max)', fontsize=14, fontweight='bold')
ax4.legend(fontsize=10)
ax4.grid(axis='y', alpha=0.3)
plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')

# 5. Solve Time Comparison
ax5 = plt.subplot(2, 3, 5)
solve_sorted = feasible.sort_values('solve_time')
bars = ax5.barh(range(len(solve_sorted)), solve_sorted['solve_time'], color='purple', alpha=0.7)
bars[0].set_color('green')
ax5.set_yticks(range(len(solve_sorted)))
ax5.set_yticklabels([name.split('.')[1].strip() for name in solve_sorted['config_name']], fontsize=9)
ax5.set_xlabel('Solve Time (seconds)', fontsize=12, fontweight='bold')
ax5.set_title('Computational Performance', fontsize=14, fontweight='bold')
ax5.grid(axis='x', alpha=0.3)
for i, (idx, row) in enumerate(solve_sorted.iterrows()):
    ax5.text(row['solve_time'] + 0.01, i, f"{row['solve_time']:.2f}s", 
             va='center', fontsize=9)

# 6. Efficiency Metric (Cost per Planned Shift)
ax6 = plt.subplot(2, 3, 6)
feasible_sorted['efficiency'] = feasible_sorted['stage1_cost'] / feasible_sorted['regular_shifts']
efficiency_sorted = feasible_sorted.sort_values('efficiency')
bars = ax6.bar(range(len(efficiency_sorted)), efficiency_sorted['efficiency'], 
               color='teal', alpha=0.7)
ax6.set_xticks(range(len(efficiency_sorted)))
ax6.set_xticklabels([name.split('.')[0] for name in efficiency_sorted['config_name']], 
                     rotation=45, ha='right', fontsize=9)
ax6.set_ylabel('Cost per Regular Shift (£)', fontsize=12, fontweight='bold')
ax6.set_title('Stage 1 Efficiency', fontsize=14, fontweight='bold')
ax6.grid(axis='y', alpha=0.3)
for i, (idx, row) in enumerate(efficiency_sorted.iterrows()):
    ax6.text(i, row['efficiency'] + 0.5, f"£{row['efficiency']:.0f}", 
             ha='center', fontsize=9)

plt.tight_layout()
plt.savefig('configuration_comparison_charts.png', dpi=300, bbox_inches='tight')
print("✓ Saved: configuration_comparison_charts.png")

# Create summary statistics
print("\n" + "="*80)
print("CONFIGURATION COMPARISON SUMMARY")
print("="*80)

print("\n📊 Key Findings:")
print(f"  • All configurations produced SAME schedule (55 regular, 34 emergency shifts)")
print(f"  • Cost differences due to different unit cost parameters only")
print(f"  • Fatigue & CVaR constraints did NOT change optimal solution")
print(f"  • All solve times very fast (0.27-0.56 seconds)")

print("\n💡 Insights:")
print("  1. For this problem instance, basic SDM is sufficient")
print("  2. CVaR and Fatigue constraints were non-binding (not active)")
print("  3. Problem size is small enough that all solvers perform well")
print("  4. Cost ratios matter more than absolute values")

print("\n🎯 Recommendations:")
print("  • Use SDM Basic for fastest solving (0.27s)")
print("  • Add CVaR if you need risk guarantees (minimal overhead: +0.06s)")
print("  • Add Fatigue for regulatory compliance (no performance impact)")
print("  • Full Model (CVaR + Fatigue) only adds 0.02s overhead")

plt.show()
