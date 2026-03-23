"""
DATA LIMITATIONS & PUBLICATION STRATEGY GUIDE
==============================================

How to honestly present data limitations in academic papers while
maintaining scientific rigor and publication quality.

Reference: He et al. (2019), "Controlling understaffing with stochastic demand"
"""

# ==============================================================================
# SECTION 1: DATA SOURCES IN THIS PROJECT
# ==============================================================================

DATA_SOURCES = {
    
    'Synthetic Benchmark': {
        'files': ['sample_nurses.csv', 'test_small_nurses.csv', 'medium_nurses.csv'],
        'origin': 'Converted from He et al. (2019) paper benchmark',
        'size': '10-30 nurses, 14-21 days, 5-12 scenarios',
        'realism': '⭐⭐⭐☆☆',
        'pros': [
            'Benchmark against published work',
            'Reproducible with paper',
            'Clear, controlled demand patterns',
            'No privacy concerns',
        ],
        'cons': [
            'May not reflect real hospital complexity',
            'Synthetic variance structure',
            'Limited scalability test',
        ],
        'appropriate_for': [
            'Model validation against paper',
            'Unit testing',
            'Sensitivity analysis on controlled inputs',
            'Teaching/presentation examples',
        ],
        'NOT_appropriate_for': [
            'Real-world deployment claims',
            'Generalization to all hospitals',
            'Direct policy recommendations',
        ],
    },
    
    'Hospital Bed Occupancy Proxy': {
        'files': ['test_medium_nurses.csv', 'medium_nurses.csv'],
        'origin': 'Derived from public CMS hospital data (occupancy proxy)',
        'size': '20-25 nurses, 14-21 days, 10-12 scenarios',
        'realism': '⭐⭐⭐⭐☆',
        'pros': [
            'Real historical hospital patterns',
            'CMS/public data (no privacy issues)',
            'Captures seasonal/demand variation',
            'Hospital-representative parameters',
        ],
        'cons': [
            'Proxy for staffing (inferred from occupancy)',
            'Aggregated across departments',
            'Cannot validate exact staffing decisions',
            'Does not include nurse skill differences',
        ],
        'appropriate_for': [
            'Realistic problem size assessment',
            'Benchmark vs. baseline scheduling',
            'Trend analysis across scenarios',
            'Computational requirement validation',
        ],
        'NOT_appropriate_for': [
            'Direct clinical staffing recommendations',
            'Specific skill-set planning',
            'Individual nurse assignment validation',
        ],
    },
    
    'Real CMS PBJ Data': {
        'files': ['pbj_california_nurses.csv', 'pbj_california_scenarios.csv'],
        'origin': 'CMS Payroll-Based Journal (PBJ) - Nursing Home staffing data, California',
        'size': '~30+ nurses implied, 30 days, varied scenarios',
        'realism': '⭐⭐⭐⭐⭐',
        'pros': [
            'Real nursing home staffing hours',
            'Public government data (open access)',
            'True demand variability',
            'Multi-state aggregation possible',
        ],
        'cons': [
            'Nursing home (not acute hospital)',
            'Aggregated data (not individual nurse)',
            'Does not include emergency/unplanned absences',
            'Snapshot of historical period only',
        ],
        'appropriate_for': [
            'Real-world case study',
            'Long-horizon planning (30+ days)',
            'Nursing home specific recommendations',
            'Policy demonstration with real data',
        ],
        'NOT_appropriate_for': [
            'Acute hospital generalization',
            'Individual nurse tracking',
            'Real-time operational deployment',
        ],
    },
}


# ==============================================================================
# SECTION 2: RECOMMENDED DATA SELECTION FOR DIFFERENT CONTEXTS
# ==============================================================================

CONTEXT_RECOMMENDATIONS = {
    
    'Academic Paper Main Results': {
        'recommended_data': 'Synthetic Benchmark + Hospital Occupancy Proxy',
        'reasoning': [
            'Controlledness allows clear cost-benefit demonstration',
            'Reproducible with published paper',
            'Two data sources show generalization',
            'Manageable scope for comprehensive tables',
        ],
        'dataset_selection': {
            'benchmark_case': 'nss_benchmark_nurses.csv + nss_benchmark_scenarios.csv',
            'realistic_case': 'test_medium_nurses.csv + test_medium_scenarios.csv',
        },
        'presentation': """
        Main Results (Table 1-3):
        - Benchmark case: Direct comparison to He et al. (2019)
        - Realistic case: Same parameters, different demand structure
        - Show robustness across data sources
        
        Data Limitations Section:
        "Main results use synthetic demand scenarios derived from He et al. (2019)
        and occupancy-based proxies. While these provide controlled testing grounds,
        we validate our approach on real nursing home data in Appendix B."
        """
    },
    
    'Case Study / Appendix': {
        'recommended_data': 'CMS PBJ Real Data',
        'reasoning': [
            'Demonstrates real-world applicability',
            'Adds credibility without claiming direct deployment',
            'Public data (reproducibility)',
            'Longer horizon (30 days) shows practical utility',
        ],
        'dataset_selection': {
            'case_study': 'pbj_california_nurses.csv + pbj_california_scenarios.csv',
        },
        'presentation': """
        Appendix B: Real Data Case Study
        - Real CMS PBJ nursing home data (CA selection)
        - Data disclaimer: Aggregated facility-level staffing hours
        - Shows model handles real demand patterns
        - Demonstrates 30-day planning feasibility
        
        Key Limitation to Note:
        "Case study uses aggregated nursing home data and does not validate
        specific individual assignments. Results demonstrate model can handle
        real-world complexity, but clinical validation would require
        hospital-specific data and staff input."
        """
    },
    
    'Computational Benchmarking': {
        'recommended_data': 'Medium + Large scenarios (escalating size)',
        'reasoning': [
            'Shows scalability clearly',
            'Can use any data source (focus on size)',
            'Isolate computational from domain performance',
        ],
        'dataset_selection': {
            'small': 'sample_nurses.csv',
            'medium': 'test_medium_nurses.csv',
            'large': 'nss_benchmark_nurses.csv',
        },
        'presentation': """
        Table 4: Computational Performance
        - Measured on same hardware with consistent solver settings
        - Show how time/memory scales with problem size
        - Document solver version, optimality gap, time limit
        
        Discussion:
        "Computational requirements scale polynomially with problem dimensions.
        Experiments used HiGHS 1.5.0 without special tuning. All problems solved
        to optimality within 10 minutes on standard laptop hardware."
        """
    },
    
    'Sensitivity Analysis': {
        'recommended_data': 'One consistent dataset (suggest: medium)',
        'reasoning': [
            'Fixed data allows isolated parameter sensitivity',
            'Clear cause-effect between parameters and results',
            'Easier to interpret for readers',
        ],
        'approach': """
        1. Fix dataset: test_medium_nurses.csv (consistent size)
        2. Vary parameters one-at-a-time:
           - Cost ratios: c1, c2, q_plus
           - Constraints: n1, n2, n3
           - Risk settings: sigma, mu
        3. Track objective value & feasibility
        4. Visualize as 2D sensitivity charts
        
        Presentation:
        "Sensitivity analysis uses fixed medium-scale synthetic demand
        to isolate parameter effects. Results show cost parameters most
        sensitive to ±20% variations, while risk settings affect tail-worst
        scenarios primarily."
        """
    },
    
    'Policy/Real Deployment Discussion': {
        'required_first': 'Real hospital-specific data collection',
        'current_data': 'Not suitable for direct deployment decisions',
        'honest_statement': """
        "This work demonstrates the optimization approach on academic datasets.
        While promising, real hospital deployment would require:
        1. Hospital-specific skill matrices and staffing data
        2. Clinical validation of fatigue/safety parameters
        3. Integration with existing HR and scheduling systems
        4. Iterative refinement with nursing leadership
        
        Current data limitations: [list specific limitations]
        Future work: [list what's needed for deployment]"
        """
    },
}


# ==============================================================================
# SECTION 3: DATA LIMITATIONS LANGUAGE FOR PAPERS
# ==============================================================================

LIMITATION_STATEMENTS = {
    
    'Synthetic Data Benchmark': """
    LIMITATION: Synthetic demand structure
    "Our benchmark case uses synthetically generated demand scenarios derived
    from He et al. (2019). While these provide reproducible test cases for 
    algorithmic validation, they may not capture the full complexity of real
    hospital demand including:
    - Non-stationary demand patterns (seasonal, day-of-week effects)
    - Correlated skill requirements across scenarios
    - Emergency surge patterns (pandemics, accidents)
    
    MITIGATION: We validate on real occupancy data (Appendix B) and show
    the algorithm's robustness to demand structure changes."
    """,
    
    'Missing Skill Heterogeneity': """
    LIMITATION: Homogeneous nurse skills
    "Current model assumes nurses are interchangeable. Real hospitals require
    tracking specialized skills (ICU, pediatrics, etc.) and certifications
    that affect availability. This simplification:"
    - Underestimates true problem complexity
    - May overstate feasibility with smaller teams
    - Ignores credentialing requirements
    
    MITIGATION: Framework extends naturally to skill requirements via
    modified decision variables and demand constraints (Appendix C)."
    """,
    
    'Nurse Preferences Absent': """
    LIMITATION: No preference modeling
    "Optimization ignores nurse preferences for specific shifts, days off,
    and shift patterns. In practice, preference satisfaction drives:
    - Turnover and retention
    - Voluntary overtime vs. mandatory
    - Schedule acceptability
    
    Models incorporating preferences empirically improve implementability
    (Maenhout & Vanhoucke, 2013) but increase complexity.
    
    FUTURE: Extension to preference-weighted objectives (Section 6)."
    """,
    
    'Training/Transition Ignored': """
    LIMITATION: Zero training/setup time
    "Model does not account for onboarding time when bringing new nurses
    into rotation. Real startup usually requires 1-3 shifts of overlap
    training, reducing effective availability.
    
    IMPACT: Our emergency staffing costs may underestimate true burden."
    """,
    
    'Demand Forecast Uncertainty': """
    LIMITATION: Demand treated as known random variable
    "We model demand as realization of a random variable with known
    distribution. Real hospitals face demand forecast errors:
    - Initial forecast biased vs. realization
    - Forecast confidence intervals widen further ahead
    - Some uncertainty sources (admissions) partially controllable
    
    APPROACH: Current model uses equal-probability scenarios as proxy.
    More sophisticated approaches: predict forecast errors before solving
    (Bertsimas & Sim, 2004; Delage & Ye, 2010)."
    """,
    
    'Fatigue Parameters': """
    LIMITATION: Fatigue model parameters based on lab studies
    "Patient safety fatigue costs use Jaber et al. (2013) learning-forgetting
    model calibrated on industrial assembly workers, not nurses. Hospital-
    specific parameters would require:
    - Medical error rate tracking by fatigue level
    - Nurse hour/shift duration validation
    - Local safety culture data
    
    MITIGATION: Sensitivity analysis (Table X) shows results robust to
    ±50% parameter changes. Local hospitals can recalibrate parameters."
    """,
}


# ==============================================================================
# SECTION 4: WHAT TO DOCUMENT IN YOUR EXPERIMENT LOG
# ==============================================================================

DOCUMENTATION_CHECKLIST = {
    
    'For Each Experiment': [
        '✓ Data source and file names',
        '✓ Exact parameters used (including defaults)',
        '✓ Solver name, version, optimality gap',
        '✓ Hardware specs (CPU, RAM, OS)',
        '✓ Solve time and solver status',
        '✓ Objective value achieved',
        '✓ Any warnings/infeasibilities',
        '✓ Random seed (if applicable)',
        '✓ Date and time of execution',
        '✓ Code version/commit hash',
    ],
    
    'For Publication': [
        '✓ Table showing all parameters (main + advanced)',
        '✓ Data summary statistics (mean, std, range of demands)',
        '✓ Hardware & solver info in Methods section',
        '✓ Reproducibility statement (code available at...)',
        '✓ Data availability statement (links to public datasets)',
        '✓ Explicit limitations section',
        '✓ Sensitivity analysis across key parameters',
        '✓ Appendix with full solver output logs',
    ],
}


# ==============================================================================
# SECTION 5: TEMPLATE REPRODUCIBILITY STATEMENT
# ==============================================================================

REPRODUCIBILITY_TEMPLATE = """
REPRODUCIBILITY STATEMENT

Code Repository:
    Source code available at: [GitHub URL]
    Version control commit: [hash]
    
Data Availability:
    Synthetic benchmark data: Included in repository (data/ folder)
    CMS PBJ nursing home data: Public access via [CMS data portal]
    Hospital occupancy proxy: Derived from public HCUP data
    
Computational Environment:
    Python version: 3.10+
    PuLP version: 2.7.0+
    Solver: HiGHS 1.5.0 (open source, free)
    
    Other required packages listed in: requirements.txt
    
Running Experiments:
    Baseline case:
        python experiments/experiment_pipeline.py \\
            --dataset nss_benchmark \\
            --preset paper_replication \\
            --id baseline_replication
    
    Realistic case:
        python experiments/experiment_pipeline.py \\
            --dataset test_medium \\
            --preset conservative \\
            --id conservative_case
    
Results Archives:
    All results from main paper experiments saved in: results/ folder
    Metadata, parameters, and schedules included for each run
    
Verification:
    Our implementation matches He et al. (2019) results within [X]%
    using identical synthetic test case. See Section X implementation notes.
"""


# ==============================================================================
# SECTION 6: FRAMING REAL VS SYNTHETIC DATA IN RESULTS
# ==============================================================================

PRESENTATION_GUIDELINES = {
    
    'Main Paper Text': """
    Write it like:
    
    "We evaluate the algorithm on two problem classes:
    
    (1) CONTROLLED BENCHMARK (Table 1): Synthetic demand scenarios based on
    the He et al. (2019) case study, allowing direct comparison to published
    results. As expected, our SDM and SDM-CVaR approaches replicate their
    cost objectives  within 2%, validating our implementation.
    
    (2) REALISTIC SCENARIO (Table 2): Demand derived from actual hospital
    occupancy patterns via CMS data. While this proxy limits clinical
    interpretation, it demonstrates the approach scales to realistic
    complexity and demand distributions.
    
    Full details on datasets, their sources, and appropriateness for
    different claims appear in Section 3 and Appendix A."
    """,
    
    'Figures': """
    Label figure captions like:
    
    Figure 1: [Synthetic benchmark scenario]
    "Panel A-C show cost breakdowns across 7-day rolling windows using synthetic
    demand with fixed variance. This controlled setting isolates the impact of
    (a) stochasticity vs. deterministic planning, and (b) risk constraints."
    
    Figure 2: [Real data scenario]
    "Panel D-F use demand frequencies from hospital occupancy data. Wider
    variance and heavier tails reflect real-world unpredictability."
    """,
    
    'Table Presentation': """
    Structure like:
    
    Table 1: Algorithm Performance on Benchmark (Synthetic)
    ────────────────────────────────────────────────────────────
    | Configuration  | SDM Cost | SDM-CVaR | He et al. | Gap  |
    ────────────────────────────────────────────────────────────
    
    Table 2: Algorithm Performance on Realistic (Real Occupancy)
    ─────────────────────────────────────────────
    | Configuration  | Cost    | Emergency | Shortage |
    ─────────────────────────────────────────────
    """,
}


# ==============================================================================
# SECTION 7: WHAT TO SAY (AND NOT SAY) ABOUT YOUR DATA
# ==============================================================================

DO_SAY = [
    ✓ "We tested on synthetic benchmark derived from He et al. (2019)",
    ✓ "Case study uses real hospital occupancy patterns from CMS",
    ✓ "Demand proxy represents typical facility-level variation",
    ✓ "These datasets support algorithm validation, not policy claims",
    ✓ "Model extends naturally to skill-specific constraints",
    ✓ "Real deployment would require hospital-specific data",
]

DONT_SAY = [
    ✗ "We solved real hospital scheduling" [if using proxy data]
    ✗ "Our method directly improves patient outcomes" [not validated]
    ✗ "Results generalize to all hospital types" [too broad]
    ✗ "This is ready for immediate deployment" [needs clinical validation]
    ✗ "Our data is fully representative" [any data has limitations]
    ✗ "We modeled individual nurse behavior" [if using aggregate data]
]


# ==============================================================================
# SECTION 8: BUILDING CREDIBILITY DESPITE DATA LIMITATIONS
# ==============================================================================

CREDIBILITY_FACTORS = """
You CAN have a strong paper even with synthetic/proxy data if you:

1. ✓ Be explicit about limitations upfront (no surprising reviewers)
2. ✓ Show the SAME algorithm works across DIFFERENT data sources
3. ✓ Validate that simpler sub-problems match real data (e.g., do synthetic
      demand distributions match real CVs?)
4. ✓ Compare against natural baselines (current practice, simple heuristics)
5. ✓ Show sensitivity analysis - do results change for reasonable parameters?
6. ✓ Offer a path forward (what data/validation would you need?)
7. ✓ Cite others who've faced similar limitations
8. ✓ Use real data for at least one case (even if limited)

Framing Example:
    WEAK: "We tested on synthetic data"
    
    STRONG: "Validated on three data sources:
             (1) Synthetic benchmark for reproducibility vs. He et al. (2019)
             (2) Hospital occupancy proxy for realistic demand variation
             (3) Real nursing home data for case study applicability
             While none fully represent acute hospitals, together they build
             confidence in generalization."
"""
