"""Solver configuration utilities for the NSS core layer."""

from __future__ import annotations

from typing import Any, Dict, Tuple

import pulp


class SolverConfig:
    """Create and describe solver backends for the nurse scheduling model."""

    @staticmethod
    def get_available_solvers() -> Dict[str, Dict[str, Any]]:
        """Detect which solvers are available on this system."""
        available: Dict[str, Dict[str, Any]] = {}

        try:
            import gurobipy  # noqa: F401
            solver = pulp.GUROBI(msg=False)
            gurobi_available = solver.available()
        except Exception:
            gurobi_available = False

        if gurobi_available:
            available["GUROBI"] = {
                "name": "Gurobi (Commercial)",
                "speed": "Fastest (10-20x faster than CBC)",
                "cost": "Commercial (free academic license)",
                "available": True,
                "priority": 1,
            }
        else:
            available["GUROBI"] = {
                "name": "Gurobi (Not Installed)",
                "speed": "Fastest",
                "cost": "Commercial - get free academic license",
                "available": False,
                "priority": 1,
            }

        try:
            solver = pulp.HiGHS(msg=False)
            if solver.available():
                available["HiGHS"] = {
                    "name": "HiGHS (Open-source)",
                    "speed": "Fast (3-5× faster than CBC)",
                    "cost": "Free",
                    "available": True,
                    "priority": 2,
                }
            else:
                raise Exception("HiGHS not available")
        except (ImportError, Exception):
            available["HiGHS"] = {
                "name": "HiGHS (Not Installed)",
                "speed": "Fast (3-5× faster than CBC)",
                "cost": "Free - pip install highspy",
                "available": False,
                "priority": 2,
            }

        try:
            solver = pulp.PULP_CBC_CMD(msg=False)
            if solver.available():
                available["CBC"] = {
                    "name": "CBC (Open-source)",
                    "speed": "Standard",
                    "cost": "Free",
                    "available": True,
                    "priority": 3,
                }
        except Exception:
            available["CBC"] = {
                "name": "CBC (Open-source)",
                "speed": "Standard",
                "cost": "Free",
                "available": True,
                "priority": 3,
            }

        return available

    @staticmethod
    def auto_select_solver() -> str:
        """Automatically select the best available solver."""
        available = SolverConfig.get_available_solvers()
        available_solvers = {name: info for name, info in available.items() if info["available"]}

        if not available_solvers:
            return "CBC"

        sorted_solvers = sorted(available_solvers.items(), key=lambda item: item[1]["priority"])
        return sorted_solvers[0][0]

    @staticmethod
    def get_solver(solver_name: str, time_limit: int, mip_gap: float, verbose: bool = False):
        """Create and configure a solver instance."""
        if solver_name == "AUTO" or solver_name is None:
            solver_name = SolverConfig.auto_select_solver()

        if solver_name == "GUROBI":
            return pulp.GUROBI(
                msg=verbose,
                timeLimit=time_limit,
                gapRel=mip_gap,
                Threads=8,
                Presolve=2,
                MIPFocus=1,
                Cuts=2,
                Heuristics=0.1,
            )

        if solver_name == "HiGHS":
            return pulp.HiGHS(
                msg=verbose,
                timeLimit=time_limit,
                gapRel=mip_gap,
                threads=8,
                options={
                    "presolve": "on",
                    "parallel": "on",
                },
            )

        if solver_name == "CBC":
            return pulp.PULP_CBC_CMD(
                msg=verbose,
                timeLimit=time_limit,
                gapRel=mip_gap,
                threads=8,
                options=[
                    "preprocess on",
                    "cuts on",
                    "heuristics on",
                    "passP 100",
                    "strongB 20",
                    "combine on",
                    "rounding on",
                    "feasibilityPump on",
                ],
            )

        best_solver = SolverConfig.auto_select_solver()
        return SolverConfig.get_solver(best_solver, time_limit, mip_gap, verbose)

    @staticmethod
    def get_solver_info(solver_name: str) -> Dict[str, Any]:
        """Get detailed information about a solver."""
        info = {
            "HiGHS": {
                "full_name": "HiGHS - High Performance Software for Linear Optimization",
                "website": "https://highs.dev/",
                "license": "MIT (Open Source)",
                "install": "pip install highspy",
                "speed_rating": 3,
                "typical_speedup": "3-5× faster than CBC",
                "best_for": "Small to large problems (5-100 nurses)",
                "limitations": "None - completely free and fast",
            },
            "CBC": {
                "full_name": "COIN-OR Branch and Cut",
                "website": "https://github.com/coin-or/Cbc",
                "license": "EPL (Open Source)",
                "install": "Included with PuLP (pip install pulp)",
                "speed_rating": 1,
                "typical_speedup": "1× (baseline)",
                "best_for": "Small to medium problems (< 20 nurses)",
                "limitations": "Slower than HiGHS for large instances",
            },
        }

        return info.get(solver_name, info["HiGHS"])

    @staticmethod
    def recommend_solver(num_nurses: int, num_days: int, num_scenarios: int) -> Tuple[str, str]:
        """Recommend the best free solver based on problem size."""
        problem_size = num_nurses * num_days * num_scenarios
        available = SolverConfig.get_available_solvers()

        if available.get("HiGHS", {}).get("available"):
            if problem_size < 1000:
                return "HiGHS", "Small problem: HiGHS will solve quickly (< 30 seconds)"
            if problem_size < 5000:
                return "HiGHS", "Medium problem: HiGHS will solve in 30-60 seconds"
            return "HiGHS", "Large problem: HiGHS recommended (may take 2-5 minutes)"

        if problem_size < 1000:
            return (
                "CBC",
                "Small problem: CBC will solve in < 1 minute. For faster results, install HiGHS (pip install highspy)",
            )
        if problem_size < 5000:
            return (
                "CBC",
                "Medium problem: CBC may take 2-5 minutes. Consider installing HiGHS (pip install highspy) for 3-5× speedup",
            )
        return (
            "CBC",
            "⚠️ Large problem: CBC may take 10-30 minutes. Strongly recommend installing HiGHS (pip install highspy)",
        )

    @staticmethod
    def get_installation_instructions(solver_name: str) -> str:
        """Get installation instructions for free, open-source solvers."""
        instructions = {
            "HiGHS": """
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
            "CBC": """
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
        """,
        }

        return instructions.get(solver_name, instructions["HiGHS"])


def get_available_solvers() -> Dict[str, Dict[str, Any]]:
    """Backward-compatible wrapper for solver detection."""
    return SolverConfig.get_available_solvers()


def auto_select_solver() -> str:
    """Backward-compatible wrapper for auto solver selection."""
    return SolverConfig.auto_select_solver()


def create_solver(solver_name: str, time_limit: int, mip_gap: float, verbose: bool = False):
    """Backward-compatible wrapper for solver creation."""
    return SolverConfig.get_solver(solver_name, time_limit, mip_gap, verbose)


def get_solver_info(solver_name: str) -> Dict[str, Any]:
    """Backward-compatible wrapper for solver metadata."""
    return SolverConfig.get_solver_info(solver_name)


def recommend_solver(num_nurses: int, num_days: int, num_scenarios: int) -> Tuple[str, str]:
    """Backward-compatible wrapper for solver recommendation."""
    return SolverConfig.recommend_solver(num_nurses, num_days, num_scenarios)


def get_installation_instructions(solver_name: str) -> str:
    """Backward-compatible wrapper for solver installation guidance."""
    return SolverConfig.get_installation_instructions(solver_name)
