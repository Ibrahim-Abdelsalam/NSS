"""Sample data generation utilities for the NSS core layer."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pandas as pd


class SampleDataGenerator:
    """Generate synthetic nurse lists and demand scenarios for testing."""

    @staticmethod
    def _get_rng(seed: int | None):
        """Return a NumPy random generator or the global NumPy module."""
        if seed is None:
            return np.random
        return np.random.default_rng(seed)

    def generate_nurses(self, n: int, seed: int | None = None) -> pd.DataFrame:
        """Generate a nurse list as a DataFrame."""
        _ = self._get_rng(seed)
        nurses_list = [f"N{i + 1}" for i in range(n)]
        return pd.DataFrame({"nurse_id": nurses_list})

    def generate_scenarios(
        self,
        n: int,
        seed: int | None = None,
        num_days: int = 14,
        num_scenarios: int = 5,
    ) -> pd.DataFrame:
        """Generate synthetic demand scenarios as a DataFrame."""
        rng = self._get_rng(seed)
        shifts = ["E", "D", "L", "N"]
        scenario_data = []
        base_demand_pct = {
            "E": 0.25,
            "D": 0.30,
            "L": 0.25,
            "N": 0.15,
        }

        for scenario in range(1, num_scenarios + 1):
            for day in range(1, num_days + 1):
                for shift in shifts:
                    base = max(1, int(n * base_demand_pct[shift]))
                    variation = rng.uniform(-0.15, 0.15)
                    demand = max(1, int(base * (1 + variation)))

                    if day % 7 in [0, 6]:
                        demand = max(1, int(demand * 0.8))

                    scenario_data.append(
                        {
                            "scenario": scenario,
                            "day": day,
                            "shift": shift,
                            "demand": demand,
                        }
                    )

        return pd.DataFrame(scenario_data)

    def generate_sample_data(
        self,
        num_nurses: int = 10,
        num_days: int = 14,
        num_scenarios: int = 5,
        seed: int | None = None,
    ) -> Tuple[List[str], pd.DataFrame]:
        """Generate nurse names and demand scenarios for a sample instance."""
        nurses_df = self.generate_nurses(num_nurses, seed=seed)
        nurses_list = nurses_df["nurse_id"].astype(str).tolist()
        scenarios_df = self.generate_scenarios(
            num_nurses,
            seed=seed,
            num_days=num_days,
            num_scenarios=num_scenarios,
        )
        return nurses_list, scenarios_df


def generate_nurses(n: int, seed: int | None = None) -> pd.DataFrame:
    """Backward-compatible wrapper for generating nurses."""
    return SampleDataGenerator().generate_nurses(n, seed=seed)


def generate_scenarios(
    n: int,
    seed: int | None = None,
    num_days: int = 14,
    num_scenarios: int = 5,
) -> pd.DataFrame:
    """Backward-compatible wrapper for generating scenarios."""
    return SampleDataGenerator().generate_scenarios(
        n,
        seed=seed,
        num_days=num_days,
        num_scenarios=num_scenarios,
    )


def generate_sample_data(
    num_nurses: int = 10,
    num_days: int = 14,
    num_scenarios: int = 5,
    seed: int | None = None,
) -> Tuple[List[str], pd.DataFrame]:
    """Backward-compatible wrapper for generating a complete sample instance."""
    return SampleDataGenerator().generate_sample_data(
        num_nurses=num_nurses,
        num_days=num_days,
        num_scenarios=num_scenarios,
        seed=seed,
    )


def generate_medium_instance(output_dir: str | Path) -> None:
    """Generate and save the medium-sized testing instance."""
    from pathlib import Path
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Set seed for reproducibility
    rng_state = np.random.get_state()
    np.random.seed(42)

    num_nurses = 25
    num_days = 14
    num_scenarios = 20
    shifts = ["E", "D", "L", "N"]
    base_demand_pct = {"E": 0.25, "D": 0.30, "L": 0.25, "N": 0.15}

    nurses = [f"N{i+1}" for i in range(num_nurses)]
    nurses_df = pd.DataFrame({"nurse": nurses})
    nurses_df.to_csv(out_path / "medium_nurses.csv", index=False, header=False)

    scenario_data = []
    for scenario in range(1, num_scenarios + 1):
        for day in range(1, NUM_DAYS if "NUM_DAYS" in globals() else num_days + 1):
            for shift in shifts:
                base = max(1, int(num_nurses * base_demand_pct[shift]))
                variation = np.random.uniform(-0.15, 0.15)
                demand = max(1, int(base * (1 + variation)))
                if day % 7 in [0, 6]:
                    demand = max(1, int(demand * 0.8))
                scenario_data.append(
                    {
                        "scenario": scenario,
                        "day": day,
                        "shift": shift,
                        "demand": demand,
                    }
                )
    scenarios_df = pd.DataFrame(scenario_data)
    scenarios_df.to_csv(out_path / "medium_scenarios.csv", index=False)

    np.random.set_state(rng_state)


def generate_case_instance(output_dir: str | Path) -> None:
    """Generate and save the case-study testing instance."""
    from pathlib import Path
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Set seed for reproducibility
    rng_state = np.random.get_state()
    np.random.seed(42)

    num_nurses = 20
    num_days = 14
    num_scenarios = 10
    shifts = ["E", "D", "L", "N"]
    base_demand_pct = {"E": 0.25, "D": 0.30, "L": 0.25, "N": 0.15}

    nurses = [f"Nurse_{i+1}" for i in range(num_nurses)]
    nurses_df = pd.DataFrame({"nurse": nurses})
    nurses_df.to_csv(out_path / "case_nurses.csv", index=False, header=False)

    scenario_data = []
    for scenario in range(1, num_scenarios + 1):
        for day in range(1, num_days + 1):
            for shift in shifts:
                base = max(1, int(num_nurses * base_demand_pct[shift]))
                variation = np.random.uniform(-0.15, 0.15)
                demand = max(1, int(base * (1 + variation)))
                if day % 7 in [0, 6]:
                    demand = max(1, int(demand * 0.8))
                scenario_data.append(
                    {
                        "scenario": scenario,
                        "day": day,
                        "shift": shift,
                        "demand": demand,
                    }
                )
    scenarios_df = pd.DataFrame(scenario_data)
    scenarios_df.to_csv(out_path / "case_scenarios.csv", index=False)

    np.random.set_state(rng_state)
