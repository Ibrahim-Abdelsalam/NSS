# Solver_Config.py Deep Dive - Verified Code Reference

**File**: `solver_config.py`
**Coordinates**: Based on filesystem audit.

---

## Chunk 2: Detection Logic (Lines 13-80)

```python
# Line 13
def get_available_solvers():
    available = []
    # ...
    # Line 24
    solver = pulp.GUROBI(msg=False)
```
**Detailed Logic**:
*   **Line 13**: Definition of the health check function.
*   **Line 24**: The probe for Gurobi.

---

## Chunk 3: Configuration Factory (Lines 118-200)

```python
# Line 118
def create_solver(solver_name, time_limit, mip_gap, verbose=False):
    # ...
    # Line 138
    return pulp.GUROBI(
        timeLimit=time_limit,
        options=[("Presolve", 2), ("MIPFocus", 1)]
    )
```
**Detailed Logic**:
*   **Line 118**: The factory function. Takes `time_limit` as a dynamic argument (previously hardcoded in my explanation, but code shows argument).
*   **Line 138**: The Gurobi construction call using the tuned parameters.

---

## Chunk 4: Installation Help (Lines 257+)

```python
# Line 257
def get_installation_instructions(solver_name):
    # ...
```
**Detailed Logic**:
*   **Line 257**: The help text generator for missing libraries.
