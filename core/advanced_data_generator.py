import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any
import datetime

class HeterogeneousNurseGenerator:
    """
    Generates nurses with skills, contracts, and eligibility based on INRC-II.
    """
    def __init__(self, seed: int = None):
        self.rng = np.random.default_rng(seed)

    def generate(self, n: int, num_days: int = 14) -> pd.DataFrame:
        nurses = []
        for i in range(n):
            # Skill level distribution: 8% HN, 63% RN, 29% CNA
            skill_rand = self.rng.random()
            if skill_rand < 0.08:
                skill = "HN"
            elif skill_rand < 0.71:
                skill = "RN"
            else:
                skill = "CNA"
            
            # Contract distribution: 60% FT, 30% PT, 10% PD
            contract_rand = self.rng.random()
            # Scale shifts based on horizon
            scale = num_days / 14.0
            if contract_rand < 0.60:
                contract = "FT"
                max_shifts = int(10 * scale)
                max_nights = int(4 * scale)
            elif contract_rand < 0.90:
                contract = "PT"
                max_shifts = int(6 * scale)
                max_nights = int(2 * scale)
            else:
                contract = "PD"
                max_shifts = int(4 * scale)
                max_nights = int(1 * scale)
                
            # Night eligibility
            if skill in ["HN", "RN"]:
                night_eligible = self.rng.random() < 0.90
            else:
                night_eligible = self.rng.random() < 0.50
                
            # Unavailable days (0-2 random days in a 14-day horizon)
            num_unavailable = self.rng.choice([0, 1, 2], p=[0.7, 0.2, 0.1])
            unavail = ",".join(map(str, self.rng.choice(range(1, 15), size=num_unavailable, replace=False))) if num_unavailable > 0 else ""
            
            # Generate contract start and end dates correctly
            import datetime
            base_date = datetime.date(2026, 1, 1)
            # Add rules and logic: ensure end date is strictly after start date
            # Ensure logical flow to prevent incorrect negative durations
            duration = self.rng.integers(30, 365) # Valid 1-12 months contract
            start_offset = self.rng.integers(0, 30)
            contract_start = base_date + datetime.timedelta(days=int(start_offset))
            contract_end = contract_start + datetime.timedelta(days=int(duration))
            
            nurses.append({
                "nurse_id": f"N{i+1:02d}",
                "skill_level": skill,
                "contract_type": contract,
                "max_shifts": max_shifts,
                "max_nights": max_nights,
                "night_eligible": night_eligible,
                "unavailable_days": unavail,
                "contract_start_date": contract_start.strftime("%Y-%m-%d"),
                "contract_end_date": contract_end.strftime("%Y-%m-%d")
            })
        return pd.DataFrame(nurses)

    def get_qualification_matrix(self, nurses_df: pd.DataFrame) -> Dict[Tuple[str, str], int]:
        """Returns dict of (nurse_id, shift_type) -> 1 if qualified, 0 otherwise"""
        q = {}
        for _, row in nurses_df.iterrows():
            i = row['nurse_id']
            skill = row['skill_level']
            night_eligible = row['night_eligible']
            
            # All can work E, D, L
            q[(i, 'E')] = 1
            q[(i, 'D')] = 1
            q[(i, 'L')] = 1
            
            # Night qualification
            if skill == "HN":
                q[(i, 'N')] = 1
            elif skill == "RN":
                q[(i, 'N')] = 1 if night_eligible else 0
            else: # CNA
                q[(i, 'N')] = 1 if night_eligible else 0
                
        return q


class ExogenousDemandGenerator:
    """
    Generates demand scenarios with AR(1) temporal correlation and day-of-week seasonality.
    """
    def __init__(self, seed: int = None):
        self.rng = np.random.default_rng(seed)
        # Base staffing for a 30-nurse unit (adjust proportional to actual unit size via scale_factor)
        self.base_staffing = {
            'E': {'HN': 1, 'RN': 3, 'CNA': 2},
            'D': {'HN': 1, 'RN': 4, 'CNA': 3},
            'L': {'HN': 1, 'RN': 3, 'CNA': 2},
            'N': {'HN': 0, 'RN': 2, 'CNA': 1}
        }
        # DOW multipliers (Mon=0, Sun=6)
        self.dow_mult = [1.15, 1.05, 1.0, 1.0, 0.95, 0.80, 0.80]
        
    def generate(self, n_scenarios: int = 50, num_days: int = 14, scale_factor: float = 1.0, start_date_str: str = "2026-01-05") -> pd.DataFrame:
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        
        data = []
        shifts = ['E', 'D', 'L', 'N']
        skills = ['HN', 'RN', 'CNA']
        
        for omega in range(1, n_scenarios + 1):
            # Initialize AR(1) state
            ar_state = 1.0 
            rho = 0.6
            
            for day in range(1, num_days + 1):
                current_date = start_date + datetime.timedelta(days=day-1)
                dow = current_date.weekday()
                dow_factor = self.dow_mult[dow]
                
                # Update AR(1)
                nu = self.rng.normal(1.0, 0.15)
                ar_state = rho * ar_state + (1 - rho) * nu
                
                for shift in shifts:
                    for skill in skills:
                        base = self.base_staffing[shift].get(skill, 0) * scale_factor
                        if base == 0:
                            # ensure demand is at least 1 even if base is 0, except for specific roles like HN at night which may be 0
                            # Let's keep it strictly non-zero if base > 0, otherwise 0
                            pass
                            
                        epsilon = self.rng.normal(0, 0.10)
                        demand = max(1, int(np.floor(base * dow_factor * ar_state + epsilon))) if base > 0 else 0
                        
                        if demand > 0:
                            data.append({
                                'scenario': omega,
                                'day': day,
                                'shift': shift,
                                'skill': skill,
                                'demand': demand
                            })
        return pd.DataFrame(data)
