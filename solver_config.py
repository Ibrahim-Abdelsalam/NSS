"""
Solver Configuration Module

This module provides flexible solver selection for the nurse scheduling model.
Supports: CBC (free), Gurobi (free academic), HiGHS (free open-source).
"""

import pulp

def get_available_solvers():
    """
    Detect which solvers are available on this system.
    
    Returns:
        dict: Available solvers with their display names and status
    """
    available = {}
    
    # Test CBC (always available with PuLP)
    try:
        solver = pulp.PULP_CBC_CMD(msg=False)
        if solver.available():
            available['CBC'] = {
                'name': 'CBC (Open-source)',
                'speed': 'Slow',
                'cost': 'Free',
                'available': True
            }
    except:
        # CBC is always available with PuLP
        available['CBC'] = {
            'name': 'CBC (Open-source)',
            'speed': 'Slow',
            'cost': 'Free',
            'available': True
        }
    
    # Test Gurobi - check both Python API and module
    try:
        import gurobipy
        # Also verify PuLP can use it
        solver = pulp.GUROBI(msg=False)
        if solver.available():
            available['GUROBI'] = {
                'name': 'Gurobi (Commercial/Academic)',
                'speed': 'Very Fast (10-100× faster)',
                'cost': 'Free for academic use',
                'available': True
            }
        else:
            raise Exception("Gurobi not available in PuLP")
    except (ImportError, Exception):
        available['GUROBI'] = {
            'name': 'Gurobi (Not Installed)',
            'speed': 'Very Fast (10-100× faster)',
            'cost': 'Free for academic use',
            'available': False
        }
    
    # Test HiGHS - modern open-source solver (faster than CBC)
    try:
        solver = pulp.HiGHS(msg=False)
        if solver.available():
            available['HiGHS'] = {
                'name': 'HiGHS (Open-source)',
                'speed': 'Fast (3-5× faster than CBC)',
                'cost': 'Free',
                'available': True
            }
        else:
            raise Exception("HiGHS not available")
    except (ImportError, Exception):
        available['HiGHS'] = {
            'name': 'HiGHS (Not Installed)',
            'speed': 'Fast (3-5× faster than CBC)',
            'cost': 'Free - pip install highspy',
            'available': False
        }
    
    return available


def create_solver(solver_name, time_limit, mip_gap, verbose=False):
    """
    Create and configure a solver instance.
    
    Args:
        solver_name (str): Name of solver ('CBC', 'GUROBI', 'HiGHS')
        time_limit (int): Maximum solving time in seconds
        mip_gap (float): MIP gap tolerance (0.0 = optimal, 0.05 = 5% gap)
        verbose (bool): Whether to show solver output
        
    Returns:
        pulp.Solver: Configured solver instance
    """
    
    if solver_name == 'GUROBI':
        # Use GUROBI() Python API instead of GUROBI_CMD (command-line)
        # Note: GUROBI() accepts parameters directly, not as 'options' list
        return pulp.GUROBI(
            msg=verbose,
            timeLimit=time_limit,
            mip=True,
            MIPGap=mip_gap,
            Threads=8,           # Use 8 threads (adjust based on CPU)
            Presolve=2,          # Aggressive presolve
            Cuts=2,              # Aggressive cuts
            Heuristics=0.2,      # 20% time on heuristics
            Method=3,            # Concurrent optimizer
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
            threads=8,  # Increased from 4
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
        # Fallback to HiGHS if available, otherwise CBC
        try:
            solver = pulp.HiGHS(msg=False)
            if solver.available():
                return pulp.HiGHS(msg=verbose, timeLimit=time_limit, gapRel=mip_gap, threads=8)
        except:
            pass
        
        # Final fallback to CBC
        return pulp.PULP_CBC_CMD(
            msg=verbose,
            timeLimit=time_limit,
            gapRel=mip_gap,
            threads=4
        )


def get_solver_info(solver_name):
    """
    Get detailed information about a solver.
    
    Args:
        solver_name (str): Name of solver
        
    Returns:
        dict: Solver information
    """
    info = {
        'CBC': {
            'full_name': 'COIN-OR Branch and Cut',
            'website': 'https://github.com/coin-or/Cbc',
            'license': 'EPL (Open Source)',
            'install': 'Included with PuLP (pip install pulp)',
            'speed_rating': 1,
            'typical_speedup': '1× (baseline)',
            'best_for': 'Small to medium problems (< 20 nurses)',
            'limitations': 'Slow for large instances',
        },
        'HiGHS': {
            'full_name': 'HiGHS - High Performance Software for Linear Optimization',
            'website': 'https://highs.dev/',
            'license': 'MIT (Open Source)',
            'install': 'pip install highspy',
            'speed_rating': 3,
            'typical_speedup': '3-5× faster than CBC',
            'best_for': 'Small to large problems (5-100 nurses)',
            'limitations': 'Slower than commercial solvers but free',
        },
        'GUROBI': {
            'full_name': 'Gurobi Optimizer',
            'website': 'https://www.gurobi.com/',
            'license': 'Commercial (Free Academic)',
            'install': 'pip install gurobipy + license',
            'speed_rating': 10,
            'typical_speedup': '10-100× faster than CBC',
            'best_for': 'All problem sizes (5-500 nurses)',
            'limitations': 'Requires license (free for academics)',
        }
    }
    
    return info.get(solver_name, info['CBC'])


def recommend_solver(num_nurses, num_days, num_scenarios):
    """
    Recommend the best solver based on problem size.
    
    Args:
        num_nurses (int): Number of nurses
        num_days (int): Number of days
        num_scenarios (int): Number of scenarios
        
    Returns:
        str: Recommended solver name and reason
    """
    problem_size = num_nurses * num_days * num_scenarios
    
    available = get_available_solvers()
    
    if problem_size < 1000:
        # Small problems - HiGHS or CBC is fine
        if available.get('HiGHS', {}).get('available'):
            return 'HiGHS', 'Small problem: HiGHS will solve quickly (< 30 seconds)'
        else:
            return 'CBC', 'Small problem: CBC will solve quickly (< 1 minute)'
    
    elif problem_size < 5000:
        # Medium problems - prefer Gurobi, then HiGHS, then CBC
        if available.get('GUROBI', {}).get('available'):
            return 'GUROBI', 'Medium problem: Gurobi will solve in seconds (vs minutes with CBC)'
        elif available.get('HiGHS', {}).get('available'):
            return 'HiGHS', 'Medium problem: HiGHS will solve in 30-60 seconds (3-5× faster than CBC)'
        else:
            return 'CBC', 'Medium problem: CBC will work but may take 2-5 minutes. Consider installing HiGHS (pip install highspy) or Gurobi.'
    
    else:
        # Large problems - strongly recommend Gurobi
        if available.get('GUROBI', {}).get('available'):
            return 'GUROBI', 'Large problem: Gurobi highly recommended (10-100× faster than CBC)'
        elif available.get('HiGHS', {}).get('available'):
            return 'HiGHS', 'Large problem: HiGHS recommended (3-5× faster than CBC). For even faster solving, install Gurobi.'
        else:
            return 'CBC', '⚠️ Large problem: CBC may take 10-30 minutes. Strongly recommend installing HiGHS or Gurobi (free academic license available)'


def get_installation_instructions(solver_name):
    """
    Get installation instructions for a solver.
    
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

**That's it!** Restart the app and select HiGHS from the dropdown.

**Result**: 3-5× faster solving than CBC, completely free! 🚀

**About HiGHS:**
- Modern open-source solver (MIT license)
- Developed at University of Edinburgh
- Used in production by Google, Meta, and others
- Great middle ground between CBC and commercial solvers
        """,
        
        'GUROBI': """
## Install Gurobi (5 minutes)

### Step 1: Get Free Academic License
1. Go to: https://www.gurobi.com/academia/academic-program-and-licenses/
2. Register with your .edu email address
3. You'll receive a license key

### Step 2: Install Gurobi
```bash
pip install gurobipy
```

### Step 3: Activate License
```bash
# Run the command provided by Gurobi (example):
grbgetkey <REDACTED_LICENSE_KEY>
```

### Step 4: Test
```bash
python -c "import gurobipy; print('Gurobi installed!')"
```

**That's it!** Restart the app and select Gurobi from the dropdown.

**Result**: 10-100× faster solving! 🚀
        """,
        
        'CBC': """
## CBC is Already Installed!

CBC comes bundled with PuLP, so you're already set up.

### To Improve CBC Performance:
1. The app already uses optimized CBC settings
2. For even better performance, consider:
   - Reducing number of scenarios (10 → 5)
   - Shortening planning period (14 → 7 days)
   - Or install HiGHS (pip install highspy) for 3-5× speedup
   - Or install Gurobi for 10-100× speedup

**Tip**: For large problems (50+ nurses), install Gurobi for much faster results.
        """
    }
    
    return instructions.get(solver_name, instructions['CBC'])


# Example usage:
if __name__ == "__main__":
    # Test solver detection
    print("Available Solvers:")
    for name, info in get_available_solvers().items():
        status = "✅ Ready" if info['available'] else "❌ Not Installed"
        print(f"  {name}: {status} - {info['speed']}")
    
    # Test recommendation
    solver, reason = recommend_solver(num_nurses=50, num_days=14, num_scenarios=10)
    print(f"\nRecommended: {solver}")
    print(f"Reason: {reason}")
