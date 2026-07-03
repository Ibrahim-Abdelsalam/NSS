# NSS Modular Architecture Guide

> Comprehensive documentation of the refactored Nurse Scheduling System (NSS) from monolithic to layered architecture.

## Quick Start

```bash
# Run the Streamlit application
streamlit run app.py

# Run integration tests
pytest tests/test_integration.py -v

# Run smoke test (quick validation)
python tests/smoke_test.py
```

## Architecture Overview

The refactored NSS consists of **3 independent layers**:

```
┌─────────────────────────────────────────────────────────┐
│  app.py (Streamlit Entry Point)                         │
│  ────────────────────────────────────────────────────   │
│  • Main orchestrator for web UI                         │
│  • Wires together all layers                            │
│  • Manages session state and reruns                     │
└─────────────────────────────────────────────────────────┘
         ↓           ↓            ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  UI LAYER    │ │  CORE LAYER  │ │ EXPERIMENTS  │
│  ────────    │ │  ──────────  │ │ ────────────  │
│  Streamlit   │ │  Business    │ │  Reproducible│
│  components  │ │  logic       │ │  pipelines   │
│  (pure view) │ │  (functions) │ │  (classes)   │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## Layer Details

### CORE LAYER (`core/`)

The **business logic layer** containing all optimization and validation code. No Streamlit or web framework dependencies.

#### Core Modules

| Module | Purpose | Key Classes/Functions |
|--------|---------|---------------------- |
| `__init__.py` | Package exports | `SolveResult`, `ValidationResult`, `ExperimentResult`, `RESULTS_DIR`, `DATA_DIR` |
| `types.py` | Data structures | `SolveResult` (status, objective, variables), `ValidationResult`, `ExperimentResult` |
| `data_generator.py` | Sample data creation | `generate_sample_data(num_nurses, num_days, num_scenarios)` |
| `solver_config.py` | Solver detection | `auto_select_solver()`, `get_available_solvers()` |
| `validator.py` | Input/output validation | `ParameterValidator` (validate_inputs, validate_outputs, sanitize) |
| `model.py` | Model building & solving | `NurseSchedulingModel`, `FatigueAwareNurseSchedulingModel`, `create_model()` factory |
| `scheduler.py` | Result extraction & caching | `ResultExtractor` (extract methods with caching), `extract_results()` legacy wrapper |

#### Design Pattern: Model Factory

The `create_model()` function dispatches to the correct model variant:

```python
from core.model import create_model

# Standard model (deterministic demand)
model = create_model(params, nurses_list, scenarios_df, model_type="SDM")

# Fatigue-aware model (with patient safety constraints)
model = create_model(
    {**params, "patient_safety_enabled": True},
    nurses_list,
    scenarios_df,
    model_type="SDM"
)

model.build()      # Construct optimization problem
solve_result = model.solve()  # Solve and extract result
```

#### Internal Delegation: model_2.py

The `core/model.py` module internally delegates to `model_2.py` (2254 lines) for the actual solver implementation. This is **NOT** part of the public API:

```python
# ✓ Correct: Use core.model as facade
from core.model import create_model
model = create_model(...)

# ✗ Avoid: Don't import model_2 directly
from model_2 import build_and_solve_model
```

**Rationale for keeping model_2.py:**
- Extracting 2254 lines of complex solver logic is high-risk and error-prone
- The facade (core.model) shields external code from implementation changes
- Future refactoring can incrementally extract solver functions without breaking the API

#### Result Extraction

The `ResultExtractor` class caches all computed aggregates to avoid recomputation:

```python
from core.scheduler import ResultExtractor

extractor = ResultExtractor(model, solve_result)
results = extractor.extract()

# Returns dict with:
# - roster_df: Full schedule table (nurses × days × shifts)
# - schedule_df: Simplified schedule
# - cost_breakdown: Objective function components
# - coverage_df: Demand vs. capacity by shift
# - risk_metrics: Shortage statistics
# - fatigue_metrics: Patient safety metrics (if enabled)
# - scenario_df: Per-scenario costs
# - kpi_metadata: Top-level KPIs
```

---

### UI LAYER (`ui/`)

**Streamlit-specific rendering components.** No business logic—pure views.

#### UI Modules

| Module | Purpose | Function Signature |
|--------|---------|-------------------|
| `__init__.py` | Package exports | `render_sidebar`, `render_upload_section`, `render_results` |
| `sidebar.py` | Configuration UI | `render_sidebar() -> Dict[str, Any]` |
| `upload_view.py` | Data input UI | `render_upload_section() -> Tuple[List[str], pd.DataFrame]` |
| `results_view.py` | Visualization UI | `render_results(results: Dict) -> None` |

#### Design Pattern: Pure Renderers

Each UI function is **stateless** and returns data (not side effects):

```python
from ui.sidebar import render_sidebar
from ui.upload_view import render_upload_section

# Get parameters from sidebar
params = render_sidebar()

# Get data from upload section
nurses_list, scenarios_df = render_upload_section()

# Both return data; UI state managed by main.py via st.session_state
```

#### Sidebar Parameters

Renders controls for:
- **Cost parameters**: c1 (regular), c2 (overtime), q_plus (emergency), q_minus (cancellation), c3, c4
- **Work rules**: n1 (max shifts), n2 (max nights), n3 (min regular), n4 (complete weekends off)
- **Fatigue settings**: Enable/disable, lambda, weight, max threshold
- **Solver selection**: Auto-detect available solvers
- **Model type**: Standard (SDM) vs. Risk-aware (SDM-CVaR)

#### Results Visualization

`render_results()` displays 6 tabbed views:

1. **Roster**: Full 3D schedule (nurses × shifts × days) with optional heatmap
2. **Cost**: Pie chart (cost distribution) + bar chart (shift allocation analysis)
3. **Coverage**: Demand vs. capacity demand by shift with pivot table
4. **Risk**: Shortage distribution histogram + risk KPIs
5. **Scenarios**: Per-scenario cost comparison + downloadable CSV
6. **Full Report**: Executive summary + PDF export with tables

---

### EXPERIMENTS LAYER (`experiments/`)

**Reproducible experiment execution** for research and validation.

#### Experiment Modules

| Module | Purpose | Key Classes/Dicts |
|--------|---------|------------------|
| `__init__.py` | Package exports | `ExperimentPipeline`, `DATASET_REGISTRY`, `PARAMETER_PRESETS` |
| `presets.py` | Configurations | `DATASET_REGISTRY` (5 datasets), `PARAMETER_PRESETS` (4 presets) |
| `pipeline.py` | Orchestration | `ExperimentPipeline` class with load_data, prepare_parameters, run, archive |

#### ExperimentPipeline Class

```python
from experiments.pipeline import ExperimentPipeline

# Initialize pipeline
config = {
    "dataset_key": "medium",      # From DATASET_REGISTRY
    "preset_key": "baseline",     # From PARAMETER_PRESETS
    "param_overrides": {"c1": 150}  # Optional parameter tweaks
}
pipeline = ExperimentPipeline(config, output_dir="results/")

# Run end-to-end
result = pipeline.run()

# Archive results
pipeline.archive(result)

# Generate report
pipeline.generate_summary_report()
```

#### Dataset Registry

```python
DATASET_REGISTRY = {
    "sample": {
        "nurses_file": "sample_nurses.csv",
        "scenarios_file": "sample_scenarios.csv",
        "num_nurses": 10,
        "num_days": 14,
        "num_scenarios": 5,
        "description": "Quick demo dataset"
    },
    "test_small": {...},
    "test_medium": {...},
    "medium": {...},
    "nss_benchmark": {...},
}
```

#### Parameter Presets

```python
PARAMETER_PRESETS = {
    "baseline": {
        "c1": 100, "c2": 150, "q_plus": 200, "q_minus": 0,
        "c3": 50, "c4": 30, "n1": 20, "n2": 4, "n3": 10, "n4": 1,
    },
    "conservative": {...},      # Higher cost penalties
    "paper_replication": {...}, # Matches He et al. (2019)
    "fatigue_aware": {...},     # With patient safety enabled
}
```

#### Workflow

1. **Load**: Read nurse and scenario data from CSV
2. **Prepare**: Apply preset parameters + overrides, auto-derive n1/n2 if needed
3. **Validate**: Run ParameterValidator
4. **Solve**: Create model, build, solve
5. **Extract**: ResultExtractor computes all metrics
6. **Archive**: Save metadata, parameters, schedule, results to disk
7. **Report**: Generate summary comparing completed experiments

---

## Workflow Examples

### Example 1: Run Optimization via Streamlit

```python
# app.py (entry point)
from core.model import create_model
from core.scheduler import ResultExtractor
from core.validator import ParameterValidator
from ui.sidebar import render_sidebar
from ui.upload_view import render_upload_section
from ui.results_view import render_results

params = render_sidebar()
nurses_list, scenarios_df = render_upload_section()

if st.button("Optimize"):
    # Validate
    validator = ParameterValidator(strict_mode=False)
    validation = validator.validate_inputs(params, nurses_list, scenarios_df)
    
    if validation.is_valid:
        # Create and solve
        model = create_model(validation.sanitized_params, nurses_list, scenarios_df)
        model.build()
        solve_result = model.solve()
        
        # Extract results
        extractor = ResultExtractor(model, solve_result)
        results = extractor.extract()
        
        # Visualize
        render_results(results)
```

### Example 2: Run Batch Experiments

```python
from experiments.pipeline import ExperimentPipeline
from experiments.presets import DATASET_REGISTRY, PARAMETER_PRESETS

# Run baseline on all datasets
for dataset_key in ["sample", "medium", "nss_benchmark"]:
    config = {
        "dataset_key": dataset_key,
        "preset_key": "baseline",
    }
    pipeline = ExperimentPipeline(config, output_dir=f"results/{dataset_key}/")
    result = pipeline.run()
    pipeline.archive(result)

pipeline.generate_summary_report()
```

### Example 3: Direct Core Usage (No UI)

```python
# Scientific computing without Streamlit
from core.data_generator import generate_sample_data
from core.model import create_model
from core.scheduler import ResultExtractor
from core.validator import ParameterValidator

# Generate synthetic data
nurses, scenarios = generate_sample_data(50, 30, 15)

# Define parameters
params = {
    "c1": 100, "c2": 150, "q_plus": 200, "q_minus": 0,
    "c3": 50, "c4": 30, "n1": 20, "n2": 4, "n3": 10, "n4": 1,
    "patient_safety_enabled": True,
}

# Validate
validator = ParameterValidator()
validation = validator.validate_inputs(params, nurses, scenarios)
assert validation.is_valid

# Solve
model = create_model(validation.sanitized_params, nurses, scenarios)
model.build()
solve_result = model.solve()

# Extract and analyze
extractor = ResultExtractor(model, solve_result)
results = extractor.extract()

print(f"Objective: {solve_result.objective_value}")
print(f"Schedule:\n{results['schedule_df']}")
print(f"Cost breakdown: {results['cost_breakdown']}")
```

---

## File Structure

```
NSS/
├── app.py                           ← Main entry point (Streamlit)
├── main.py                          ← Alternative entry point (same code)
├── model_2.py                       ← Internal solver delegate (do not import)
│
├── core/                            ← Business logic layer
│   ├── __init__.py                  ├─ Package exports
│   ├── types.py                     ├─ Data structures (SolveResult, etc.)
│   ├── data_generator.py            ├─ Sample data creation
│   ├── solver_config.py             ├─ Solver detection
│   ├── validator.py                 ├─ Input/output validation
│   ├── model.py                     ├─ Model wrapper + factory
│   └── scheduler.py                 └─ Result extraction + caching
│
├── ui/                              ← Streamlit UI layer
│   ├── __init__.py                  ├─ Package exports
│   ├── sidebar.py                   ├─ Configuration controls
│   ├── upload_view.py               ├─ Data input
│   └── results_view.py              └─ Visualization + export
│
├── experiments/                     ← Research & reproducibility
│   ├── __init__.py                  ├─ Package exports
│   ├── presets.py                   ├─ Datasets + parameter presets
│   ├── pipeline.py                  ├─ Orchestration class
│   └── experiment_pipeline_legacy.py└─ Old script (archived)
│
├── tests/                           ← Testing
│   ├── test_integration.py          ├─ Pytest suite (14 tests)
│   └── smoke_test.py                └─ Quick validation script
│
├── docs/                            ← Documentation
│   └── ARCHITECTURE.md              ← This file
│
└── data/                            ← Sample datasets
    ├── sample_nurses.csv
    ├── sample_scenarios.csv
    ├── medium_nurses.csv
    ├── medium_scenarios.csv
    └── ...
```

---

## Design Principles

### 1. Separation of Concerns

| Layer | Responsibility | Example |
|-------|----------------|---------|
| **Core** | Optimization, validation | `create_model()`, `ParameterValidator` |
| **UI** | Web interface, visualization | `render_sidebar()`, `render_results()` |
| **Experiments** | Research workflows | `ExperimentPipeline`, presets |

✓ Each layer can be tested independently  
✓ Core layer works without Streamlit  
✓ Experiments can be run headless  

### 2. Facade Pattern

`core/model.py` is a **facade** that hides the internal `model_2.py` complexity:

```python
# Public API (stable)
from core.model import create_model, NurseSchedulingModel

# Internal delegate (NOT for external use)
from model_2 import build_and_solve_model  # ✗ Avoid this
```

Benefits:
- Easy to refactor internal implementation
- Clear ownership (core.model owns model_2.py contract)
- Future-proof API

### 3. Immutable Data Flow

Parameters flow in one direction: Sidebar → Validator → Model → Extract → Results

```
render_sidebar()
    ↓ params (Dict)
ParameterValidator.validate_inputs()
    ↓ sanitized_params (Dict)
create_model(sanitized_params)
    ↓ model (NurseSchedulingModel)
model.build() → model.solve()
    ↓ solve_result (SolveResult)
ResultExtractor.extract()
    ↓ results (Dict)
render_results()
```

No backfeeding; easy to trace data flow.

### 4. Caching in ResultExtractor

Result extraction is expensive (computing aggregates). `ResultExtractor` caches results:

```python
extractor = ResultExtractor(model, solve_result)

# First call: computes all aggregates
results1 = extractor.extract()

# Subsequent calls: returns cached dict
results2 = extractor.extract()  # ⚡ Same object (no recomputation)
```

### 5. Factory Method for Model Selection

`create_model()` dispatches to the correct variant:

```python
# User specifies model type indirectly (via patient_safety_enabled flag)
params = {"patient_safety_enabled": False}  # Use standard model
model = create_model(params, nurses, scenarios)

params = {"patient_safety_enabled": True}   # Use fatigue-aware model
model = create_model(params, nurses, scenarios)
```

No if/else in UI code; factory handles dispatch.

---

## Migration Guide: From Monolithic to Modular

### Before (Monolithic `app_legacy.py`)
```python
import model_2
import app  # Everything intertwined

# Run optimization (business logic + UI mixed)
st.sidebar.write("Configure:")
c1 = st.number_input("Regular cost", value=100)
# ... 100 more lines of config ...

prob, status = model_2.build_and_solve_model(nurses, scenarios, params)
results = model_2.extract_results(prob, nurses, scenarios, params)

# ... 50 lines of plotting code ...
```

### After (Modular `app.py`)
```python
from core.model import create_model
from core.scheduler import ResultExtractor
from core.validator import ParameterValidator
from ui.sidebar import render_sidebar
from ui.upload_view import render_upload_section
from ui.results_view import render_results

# Get parameters from sidebar
params = render_sidebar()

# Get data
nurses_list, scenarios_df = render_upload_section()

# Validate, solve, extract, visualize
validator = ParameterValidator()
validation = validator.validate_inputs(params, nurses_list, scenarios_df)

model = create_model(validation.sanitized_params, nurses_list, scenarios_df)
model.build()
solve_result = model.solve()

extractor = ResultExtractor(model, solve_result)
results = extractor.extract()

render_results(results)
```

**Benefits:**
- ✓ UI code doesn't know about optimization logic
- ✓ Validation is testable independently
- ✓ Can reuse core layer in non-Streamlit apps (research scripts, APIs, etc.)
- ✓ Results are reproducible via ExperimentPipeline

---

## Testing

### Unit Tests (Core Layer)

```bash
# Run all tests
pytest tests/test_integration.py -v

# Run specific test class
pytest tests/test_integration.py::TestCoreLayer -v

# Run with coverage
pytest tests/test_integration.py --cov=core --cov=experiments
```

**Test Coverage:**
- `TestCoreLayer`: Data generation, solver config, validation, model creation
- `TestModelSolving`: Model solving, result extraction, fatigue variants
- `TestExperimentsLayer`: Pipeline initialization, datasets, presets
- `TestIntegration`: End-to-end workflows, session state, backward compatibility
- `TestBackwardCompatibility`: Legacy wrapper functions still work

### Smoke Test (Quick Validation)

```bash
python tests/smoke_test.py
```

Validates:
1. All imports successful
2. Data generation works
3. Model factory creates variants
4. Parameter validation functions
5. Architecture constraint (model_2 isolated)

### Manual Testing

```bash
# Start Streamlit app
streamlit run app.py

# In browser: test each UI section
# - Sidebar: tweak parameters
# - Upload: load sample data
# - Solve: run optimization
# - Results: view 6 tabs + PDF export

# Run batch experiments
python experiments/pipeline.py --dataset medium --preset baseline
```

---

## Future Improvements

### Phase 1: Solver Extraction (Optional)

Could incrementally extract `model_2.py` functions into focused modules:

```
core/
├── solver/
│   ├── objective.py           ← Cost functions
│   ├── constraints.py         ← Constraint definitions
│   ├── recourse.py            ← Two-stage recourse
│   ├── fatigue.py             ← Patient safety module
│   └── solver.py              ← Main orchestration
└── model.py                   ← Facade (imports solver/*)
```

Would maintain backward compatibility (core.model API unchanged).

### Phase 2: REST API

Could expose core layer via FastAPI:

```python
from fastapi import FastAPI
from core.model import create_model
from core.scheduler import ResultExtractor

app = FastAPI()

@app.post("/optimize")
def optimize(params: Dict, nurses_file: UploadFile, scenarios_file: UploadFile):
    nurses = parse_csv(nurses_file)
    scenarios = parse_csv(scenarios_file)
    model = create_model(params, nurses, scenarios)
    model.build()
    solve_result = model.solve()
    extractor = ResultExtractor(model, solve_result)
    return extractor.extract()
```

### Phase 3: Horizontal Scaling

Could distribute ExperimentPipeline across multiple workers:

```python
from distributed import Client

client = Client(n_workers=4)

futures = []
for dataset_key in DATASET_REGISTRY.keys():
    future = client.submit(run_experiment, dataset_key)
    futures.append(future)

results = client.gather(futures)
```

---

## FAQ

**Q: Can I use the core layer without Streamlit?**  
A: Yes! The core layer has no Streamlit dependencies. Use it in scripts, APIs, batch jobs, etc.

**Q: Why keep model_2.py instead of refactoring it?**  
A: Extracting 2254 lines of mathematical solver logic is high-risk. The facade (core.model) shields external code, allowing future refactoring without breaking the API.

**Q: How do I add a new parameter?**  
A: 1. Add to sidebar.py, 2. Add validation to validator.py, 3. Pass to create_model(), 4. Use in model building.

**Q: Can I run experiments headless (no UI)?**  
A: Yes! Use `ExperimentPipeline` directly:
```python
from experiments.pipeline import ExperimentPipeline
pipeline = ExperimentPipeline(config)
result = pipeline.run()
```

**Q: How do I add a new result visualization?**  
A: Add a new function to ui/results_view.py and call it from render_results().

**Q: What if I want to modify the solver logic?**  
A: Ideally, make changes in model_2.py (for now). Future refactoring will extract functions into core/solver/*.

---

## References

- **Paper**: He et al. (2019) - CVaR constraint formulation referenced in model_2.py
- **Framework**: Streamlit for web UI, PuLP for optimization
- **Development**: Pytest for testing, Plotly for visualization

---

**Last Updated**: July 2026  
**Architecture Version**: 2.0 (Refactored Modular)  
**Status**: ✅ Complete, All Tests Passing
