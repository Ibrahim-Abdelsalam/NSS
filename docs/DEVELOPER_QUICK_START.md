# NSS Quick Reference for Developers

## Importing Core Modules

```python
# ✓ Correct imports (use these)
from core import SolveResult, ValidationResult, ExperimentResult
from core.model import create_model, NurseSchedulingModel
from core.scheduler import ResultExtractor
from core.validator import ParameterValidator
from core.data_generator import generate_sample_data
from core.solver_config import auto_select_solver

# ✗ Avoid these imports (internal delegates)
from model_2 import build_and_solve_model  # Don't do this
import model_2  # Don't do this

# ✓ OK from Streamlit apps
from ui.sidebar import render_sidebar
from ui.upload_view import render_upload_section
from ui.results_view import render_results

# ✓ OK from research scripts
from experiments.pipeline import ExperimentPipeline
from experiments.presets import DATASET_REGISTRY, PARAMETER_PRESETS
```

## Common Workflows

### Workflow 1: Simple Optimization

```python
from core.model import create_model
from core.scheduler import ResultExtractor
from core.validator import ParameterValidator

# Define parameters
params = {
    "c1": 100, "c2": 150, "q_plus": 200, "q_minus": 0,
    "c3": 50, "c4": 30, "n1": 20, "n2": 4, "n3": 10, "n4": 1,
}

# Validate
validator = ParameterValidator()
result = validator.validate_inputs(params, nurses_list, scenarios_df)
if not result.is_valid:
    print("Errors:", result.errors)
    exit(1)

# Solve
model = create_model(result.sanitized_params, nurses_list, scenarios_df)
model.build()
solve_result = model.solve()

# Extract
extractor = ResultExtractor(model, solve_result)
output = extractor.extract()

print(f"Objective: {solve_result.objective_value}")
print(f"Schedule shape: {output['schedule_df'].shape}")
```

### Workflow 2: Generate Sample Data

```python
from core.data_generator import generate_sample_data

nurses, scenarios = generate_sample_data(
    num_nurses=50,
    num_days=30,
    num_scenarios=10
)

print(f"Generated {len(nurses)} nurses")
print(f"Generated {len(scenarios)} scenario rows")
```

### Workflow 3: Run Experiments

```python
from experiments.pipeline import ExperimentPipeline

config = {
    "dataset_key": "medium",
    "preset_key": "baseline",
    "param_overrides": {"c1": 120}  # Optional
}

pipeline = ExperimentPipeline(config, output_dir="results/")
result = pipeline.run()
pipeline.archive(result)
```

---

**Last Updated**: July 2026
