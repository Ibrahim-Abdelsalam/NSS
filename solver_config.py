"""
Solver Configuration Module

This module provides intelligent automatic solver selection for the nurse scheduling model.
Supports Gurobi (commercial - fastest), HiGHS (open-source - fast), and CBC (fallback).

The framework automatically detects and selects the best available solver without user intervention.
Priority: Gurobi > HiGHS > CBC
"""

import pulp

def get_available_solvers():
    """
    Detect which solvers are available on this system.
    
    Returns:
        dict: Available solvers with their display names and status
    """
    available = {}
    
    # Test Gurobi - commercial solver (fastest)
    try:
        solver = pulp.GUROBI(msg=False)
        if solver.available():
            available['GUROBI'] = {
                'name': 'Gurobi (Commercial)',
                'speed': 'Fastest (10-20× faster than CBC)',
                'cost': 'Commercial (free academic license)',
                'available': True,
                'priority': 1  # Highest priority
            }
        else:
            raise Exception("Gurobi not available")
    except (ImportError, Exception):
        available['GUROBI'] = {
            'name': 'Gurobi (Not Installed)',
            'speed': 'Fastest',
            'cost': 'Commercial - get free academic license',
            'available': False,
            'priority': 1
        }
    
    # Test HiGHS - modern open-source solver
    try:
        solver = pulp.HiGHS(msg=False)
        if solver.available():
            available['HiGHS'] = {
                'name': 'HiGHS (Open-source)',
                'speed': 'Fast (3-5× faster than CBC)',
                'cost': 'Free',
                'available': True,
                'priority': 2
            }
        else:
            raise Exception("HiGHS not available")
    except (ImportError, Exception):
        available['HiGHS'] = {
            'name': 'HiGHS (Not Installed)',
            'speed': 'Fast (3-5× faster than CBC)',
            'cost': 'Free - pip install highspy',
            'available': False,
            'priority': 2
        }
    
    # Test CBC (always available with PuLP)
    try:
        solver = pulp.PULP_CBC_CMD(msg=False)
        if solver.available():
            available['CBC'] = {
                'name': 'CBC (Open-source)',
                'speed': 'Standard',
                'cost': 'Free',
                'available': True,
                'priority': 3  # Lowest priority
            }
    except:
        # CBC is always available with PuLP
        available['CBC'] = {
            'name': 'CBC (Open-source)',
            'speed': 'Standard',
            'cost': 'Free',
            'available': True,
            'priority': 3
        }
    
    return available


def auto_select_solver():
    """
    Automatically select the best available solver.
    
    Priority order:
    1. Gurobi (fastest commercial solver)
    2. HiGHS (fast free solver)
    3. CBC (reliable fallback)
    
    Returns:
        str: Name of the best available solver
    """
    available = get_available_solvers()
    
    # Filter to only available solvers
    available_solvers = {name: info for name, info in available.items() if info['available']}
    
    if not available_solvers:
        # This should never happen as CBC is always available
        return 'CBC'
    
    # Sort by priority (lower number = higher priority)
    sorted_solvers = sorted(available_solvers.items(), key=lambda x: x[1]['priority'])
    
    # Return the highest priority solver
    return sorted_solvers[0][0]


def create_solver(solver_name, time_limit, mip_gap, verbose=False):
    """
    Create and configure a solver instance.
    
    Args:
        solver_name (str): Name of solver ('GUROBI', 'HiGHS', 'CBC', or 'AUTO' for auto-selection)
        time_limit (int): Maximum solving time in seconds
        mip_gap (float): MIP gap tolerance (0.0 = optimal, 0.05 = 5% gap)
        verbose (bool): Whether to show solver output
        
    Returns:
        pulp.Solver: Configured solver instance
    """
    
    # Auto-select best solver if requested
    if solver_name == 'AUTO' or solver_name is None:
        solver_name = auto_select_solver()
    
    if solver_name == 'GUROBI':
        # Gurobi - commercial solver (fastest)
        return pulp.GUROBI(
            msg=verbose,
            timeLimit=time_limit,
            gapRel=mip_gap,
            options=[
                ('Threads', 8),
                ('Presolve', 2),      # Aggressive presolve
                ('MIPFocus', 1),      # Focus on finding good solutions
                ('Cuts', 2),          # Aggressive cuts
                ('Heuristics', 0.1),  # 10% time on heuristics
            ]
        )
    
    elif solver_name == 'HiGHS':
        # HiGHS - modern open-source solver
        return pulp.HiGHS(
            msg=verbose,
            timeLimit=time_limit,
            gapRel=mip_gap,
            threads=8,
            options={
                'presolve': 'on',
                'parallel': 'on',
            }
        )
    
    elif solver_name == 'CBC':
        return pulp.PULP_CBC_CMD(
            msg=verbose,
            timeLimit=time_limit,
            gapRel=mip_gap,
            threads=8,
            options=[
                'preprocess on',
                'cuts on',
                'heuristics on',
                'passP 100',          # More preprocessing passes
                'strongB 20',         # Strong branching
                'combine on',         # Combine solutions
                'rounding on',        # Rounding heuristic
                'feasibilityPump on', # Feasibility pump heuristic
            ]
        )
    
    else:
        # Fallback: try auto-selection
        best_solver = auto_select_solver()
        return create_solver(best_solver, time_limit, mip_gap, verbose)


def get_solver_info(solver_name):
    """
    Get detailed information about a free, open-source solver.
    
    Args:
        solver_name (str): Name of solver
        
    Returns:
        dict: Solver information
    """
    info = {
        'HiGHS': {
            'full_name': 'HiGHS - High Performance Software for Linear Optimization',
            'website': 'https://highs.dev/',
            'license': 'MIT (Open Source)',
            'install': 'pip install highspy',
            'speed_rating': 3,
            'typical_speedup': '3-5× faster than CBC',
            'best_for': 'Small to large problems (5-100 nurses)',
            'limitations': 'None - completely free and fast',
        },
        'CBC': {
            'full_name': 'COIN-OR Branch and Cut',
            'website': 'https://github.com/coin-or/Cbc',
            'license': 'EPL (Open Source)',
            'install': 'Included with PuLP (pip install pulp)',
            'speed_rating': 1,
            'typical_speedup': '1× (baseline)',
            'best_for': 'Small to medium problems (< 20 nurses)',
            'limitations': 'Slower than HiGHS for large instances',
        },
    }
    
    return info.get(solver_name, info['HiGHS'])


def recommend_solver(num_nurses, num_days, num_scenarios):
    """
    Recommend the best free solver based on problem size.
    Automatically uses the fastest available free solver.
    
    Args:
        num_nurses (int): Number of nurses
        num_days (int): Number of days
        num_scenarios (int): Number of scenarios
        
    Returns:
        str: Recommended solver name and reason
    """
    problem_size = num_nurses * num_days * num_scenarios
    
    available = get_available_solvers()
    
    # Always prefer HiGHS if available (it's faster and free)
    if available.get('HiGHS', {}).get('available'):
        if problem_size < 1000:
            return 'HiGHS', 'Small problem: HiGHS will solve quickly (< 30 seconds)'
        elif problem_size < 5000:
            return 'HiGHS', 'Medium problem: HiGHS will solve in 30-60 seconds'
        else:
            return 'HiGHS', 'Large problem: HiGHS recommended (may take 2-5 minutes)'
    else:
        # Fall back to CBC
        if problem_size < 1000:
            return 'CBC', 'Small problem: CBC will solve in < 1 minute. For faster results, install HiGHS (pip install highspy)'
        elif problem_size < 5000:
            return 'CBC', 'Medium problem: CBC may take 2-5 minutes. Consider installing HiGHS (pip install highspy) for 3-5× speedup'
        else:
            return 'CBC', '⚠️ Large problem: CBC may take 10-30 minutes. Strongly recommend installing HiGHS (pip install highspy)'


def get_installation_instructions(solver_name):
    """
    Get installation instructions for free, open-source solvers.
    
    Args:
        solver_name (str): Name of solver
        
    Returns:
        str: Installation instructions (Markdown format)
    """
    instructions = {
        'HiGHS': """
## Install HiGHS (30 seconds)

HiGHS is a modern, open-source solver that's 3-5× faster than CBC!

### Installation (One Command):
```bash
pip install highspy
```

### Test:
```bash
python -c "import pulp; print('HiGHS available:', pulp.HiGHS(msg=False).available())"
```

**That's it!** Restart the app and HiGHS will be automatically selected.

**Result**: 3-5× faster solving than CBC, completely free! 🚀

**About HiGHS:**
- Modern open-source solver (MIT license)
- Developed at University of Edinburgh
- Used in production by Google, Meta, and others
- The best free solver available
        """,
        
        'CBC': """
## CBC is Already Installed!

CBC comes bundled with PuLP, so you're already set up.

### To Improve Performance:
1. The app already uses optimized CBC settings
2. For 3-5× better performance, install HiGHS:
   ```bash
   pip install highspy
   ```
   The app will automatically detect and use HiGHS!

**Tip**: For large problems (50+ nurses), HiGHS provides much faster results.
        """
    }
    
    return instructions.get(solver_name, instructions['HiGHS'])


# Example usage:
if __name__ == "__main__":
    # Test solver detection
    print("Available Free Solvers:")
    for name, info in get_available_solvers().items():
        status = "✅ Ready" if info['available'] else "❌ Not Installed"
        print(f"  {name}: {status} - {info['speed']}")
    
    # Test auto-selection
    best = auto_select_solver()
    print(f"\nAuto-selected solver: {best}")
    
    # Test recommendation
    solver, reason = recommend_solver(num_nurses=50, num_days=14, num_scenarios=10)
    print(f"\nRecommended: {solver}")
    print(f"Reason: {reason}")
