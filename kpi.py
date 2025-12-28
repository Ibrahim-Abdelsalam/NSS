"""
Solution Quality KPIs Module

This module defines Key Performance Indicators (KPIs) for evaluating 
nurse scheduling solution quality. Each KPI includes thresholds for
Good (🟢), Warning (🟡), and Bad (🔴) classifications.

Edit the thresholds below to customize for your hospital's standards.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple


# =============================================================================
# KPI THRESHOLDS (Edit these to customize)
# =============================================================================

THRESHOLDS = {
    # Demand & Staffing
    'demand_coverage': {'good': 100, 'warning': 95},      # %
    'understaffing_rate': {'good': 5, 'warning': 15},     # %
    'overtime_ratio': {'good': 10, 'warning': 25},        # %
    
    # Fatigue
    'fatigue_rate': {'good': 0, 'warning': 10},           # % of nurses with high fatigue
    'avg_fatigue': {'good': 0.3, 'warning': 0.5},         # fatigue level (0-1)
    'max_fatigue': {'good': 0.5, 'warning': 0.7},         # fatigue level (0-1)
    
    # Workload Balance
    'workload_std': {'good': 2, 'warning': 4},            # std dev of shifts per nurse
    
    # Cost Efficiency
    'cost_per_shift': {'good': 120, 'warning': 180},      # $ per shift
}


# =============================================================================
# KPI STATUS FUNCTIONS
# =============================================================================

def get_status(value: float, kpi_name: str, lower_is_better: bool = True) -> str:
    """
    Determine KPI status based on thresholds.
    
    Args:
        value: The KPI value
        kpi_name: Name of the KPI (must be in THRESHOLDS)
        lower_is_better: If True, lower values are better (default)
        
    Returns:
        '🟢 Good', '🟡 Warning', or '🔴 Bad'
    """
    if kpi_name not in THRESHOLDS:
        return '⚪ N/A'
    
    good = THRESHOLDS[kpi_name]['good']
    warning = THRESHOLDS[kpi_name]['warning']
    
    if lower_is_better:
        if value <= good:
            return '🟢 Good'
        elif value <= warning:
            return '🟡 Warning'
        else:
            return '🔴 Bad'
    else:  # Higher is better (e.g., demand coverage)
        if value >= good:
            return '🟢 Good'
        elif value >= warning:
            return '🟡 Warning'
        else:
            return '🔴 Bad'


# =============================================================================
# KPI CALCULATION FUNCTIONS
# =============================================================================

# =============================================================================
# KPI CALCULATION FUNCTIONS
# =============================================================================

def calculate_demand_coverage(assigned_shifts: int, total_demand: int) -> Tuple[float, str]:
    """
    Calculate demand coverage percentage.
    
    Formula: (Regular + Overtime) / Total Demand * 100
    Meaning: What % of patient needs are met by planned staff?
    Goal: 100% (High is Good)
    """
    if total_demand == 0:
        return 100.0, '🟢 Good'
    value = (assigned_shifts / total_demand) * 100
    return round(value, 1), get_status(value, 'demand_coverage', lower_is_better=False)


def calculate_understaffing_rate(emergency_shifts: int, total_shifts: int) -> Tuple[float, str]:
    """
    Calculate reliance on emergency staff.
    
    Formula: Emergency Shifts / Total Shifts * 100
    Meaning: How dependent are we on expensive outside help?
    Goal: 0% (Low is Good)
    """
    if total_shifts == 0:
        return 0.0, '🟢 Good'
    value = (emergency_shifts / total_shifts) * 100
    return round(value, 1), get_status(value, 'understaffing_rate')


def calculate_overtime_ratio(overtime_shifts: int, regular_shifts: int) -> Tuple[float, str]:
    """
    Calculate overtime usage ratio.
    
    Formula: Overtime Shifts / Regular Shifts * 100
    Meaning: For every 100 regular shifts, how many overtime shifts?
    Goal: < 10% (Low is Good)
    """
    if regular_shifts == 0:
        return 0.0, '🟢 Good'
    value = (overtime_shifts / regular_shifts) * 100
    return round(value, 1), get_status(value, 'overtime_ratio')


def calculate_cost_per_shift(total_cost: float, total_shifts: int) -> Tuple[float, str]:
    """
    Calculate economic efficiency.
    
    Formula: Total Cost / Total Shifts
    Meaning: Average price to staff one shift (blended rate).
    Goal: Close to Regular Wage ($100)
    """
    if total_shifts == 0:
        return 0.0, '⚪ N/A'
    value = total_cost / total_shifts
    return round(value, 2), get_status(value, 'cost_per_shift')


def calculate_fatigue_rate(fatigue_values: List[float], threshold: float = 0.5) -> Tuple[float, str]:
    """
    Calculate high-risk fatigue prevalence.
    
    Formula: Count(F > Threshold) / Total Count * 100
    Meaning: % of shifts performed by "tired" nurses.
    Goal: 0%
    """
    if not fatigue_values:
        return 0.0, '🟢 Good'
    high_fatigue_count = sum(1 for f in fatigue_values if f > threshold)
    value = (high_fatigue_count / len(fatigue_values)) * 100
    return round(value, 1), get_status(value, 'fatigue_rate')


def calculate_avg_fatigue(fatigue_values: List[float]) -> Tuple[float, str]:
    """
    Calculate average team fatigue.
    
    Formula: Σ F_ij / Total Shifts
    Meaning: Average tiredness level (0=Fresh, 1=Exhausted).
    Goal: < 0.3
    """
    if not fatigue_values:
        return 0.0, '🟢 Good'
    value = sum(fatigue_values) / len(fatigue_values)
    return round(value, 3), get_status(value, 'avg_fatigue')


def calculate_max_fatigue(fatigue_values: List[float]) -> Tuple[float, str]:
    """
    Calculate worst-case fatigue.
    
    Formula: Max(F_ij)
    Meaning: How tired was the *most tired* nurse?
    Goal: < 0.5
    """
    if not fatigue_values:
        return 0.0, '🟢 Good'
    value = max(fatigue_values)
    return round(value, 3), get_status(value, 'max_fatigue')


def calculate_workload_balance(shifts_per_nurse: List[int]) -> Tuple[float, str]:
    """
    Calculate fairness (Standard Deviation).
    
    Formula: σ = sqrt( Σ(x - μ)² / N )
    Meaning: How unequal are the shift counts? 
    Goal: Low (e.g., < 2 means everyone works similar hours)
    """
    if not shifts_per_nurse or len(shifts_per_nurse) < 2:
        return 0.0, '🟢 Good'
    value = np.std(shifts_per_nurse)
    return round(value, 2), get_status(value, 'workload_std')


# =============================================================================
# COMPREHENSIVE KPI REPORT
# =============================================================================

def calculate_all_kpis(
    regular_shifts: int,
    overtime_shifts: int,
    emergency_shifts: int,
    total_demand: int,
    total_cost: float,
    fatigue_values: List[float] = None,
    shifts_per_nurse: List[int] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate all KPIs and return a comprehensive report.
    
    Args:
        regular_shifts: Number of regular shifts scheduled
        overtime_shifts: Number of overtime shifts scheduled
        emergency_shifts: Number of emergency shifts added
        total_demand: Total demand across all scenarios
        total_cost: Objective function value
        fatigue_values: Optional list of fatigue values F_ij
        shifts_per_nurse: Optional list of total shifts per nurse
        
    Returns:
        Dictionary with KPI names, values, statuses
    """
    total_shifts = regular_shifts + overtime_shifts + emergency_shifts
    
    kpis = {}
    
    # Demand & Staffing
    val, status = calculate_demand_coverage(regular_shifts + overtime_shifts, total_demand)
    kpis['Demand Coverage'] = {'value': f'{val}%', 'status': status}
    
    val, status = calculate_understaffing_rate(emergency_shifts, total_shifts)
    kpis['Understaffing Rate'] = {'value': f'{val}%', 'status': status}
    
    val, status = calculate_overtime_ratio(overtime_shifts, regular_shifts)
    kpis['Overtime Ratio'] = {'value': f'{val}%', 'status': status}
    
    val, status = calculate_cost_per_shift(total_cost, total_shifts)
    kpis['Cost Per Shift'] = {'value': f'${val}', 'status': status}
    
    # Fatigue (if available)
    if fatigue_values:
        val, status = calculate_fatigue_rate(fatigue_values)
        kpis['Fatigue Rate'] = {'value': f'{val}%', 'status': status}
        
        val, status = calculate_avg_fatigue(fatigue_values)
        kpis['Avg Fatigue'] = {'value': f'{val}', 'status': status}
        
        val, status = calculate_max_fatigue(fatigue_values)
        kpis['Max Fatigue'] = {'value': f'{val}', 'status': status}
    
    # Workload Balance (if available)
    if shifts_per_nurse:
        val, status = calculate_workload_balance(shifts_per_nurse)
        kpis['Workload Balance'] = {'value': f'σ={val}', 'status': status}
    
    return kpis


def print_kpi_report(kpis: Dict[str, Dict[str, Any]]) -> None:
    """Print a formatted KPI report to console."""
    print("\n" + "="*50)
    print("SOLUTION QUALITY KPIs")
    print("="*50)
    for name, data in kpis.items():
        print(f"{data['status']} {name}: {data['value']}")
    print("="*50 + "\n")


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Example data
    kpis = calculate_all_kpis(
        regular_shifts=100,
        overtime_shifts=15,
        emergency_shifts=20,
        total_demand=120,
        total_cost=15000,
        fatigue_values=[0.2, 0.3, 0.4, 0.5, 0.6, 0.3, 0.4],
        shifts_per_nurse=[10, 12, 11, 9, 13, 10, 11, 12, 10, 11]
    )
    
    print_kpi_report(kpis)
