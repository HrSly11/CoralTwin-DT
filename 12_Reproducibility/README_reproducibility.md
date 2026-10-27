# Scientific Reproducibility & Open Science Manifest: CoralTwin-DT

**Repository:** https://github.com/HrSly11/CoralTwin-DT.git  
**Standard Compliance:** FAIR Principles (Findable, Accessible, Interoperable, Reusable)  
**Certification Standard:** Nature / Elsevier Reproducibility Guidelines  
**Master Execution Script:** `python run_all.py` (Complete execution time: ~96 seconds)  
**Scientific Attribution:** *Resultado obtenido mediante prototipo computacional del gemelo digital.*

---

## 1. Reproducibility Overview

**CoralTwin-DT** is built from the ground up to achieve **100% deterministic, push-button computational reproducibility**. Any independent researcher with Python 3.10+ or an active Conda environment can reproduce the entire end-to-end pipeline—from raw data synthesis and harmonization to AI model training, TreeSHAP attribution, decadal Monte Carlo ODE simulations (2025–2050), GIS GeoJSON export, and 600 DPI publication figure rendering.

```
+---------------------------------------------------------------------------------------------------------------+
|                                      REPRODUCIBILITY AT A GLANCE                                              |
+--------------------------+------------------------------------------------------------------------------------+
| Master Execution Command | python run_all.py                                                                  |
| Total Execution Time     | ~96 seconds (Standard CPU)                                                         |
| Pipeline Steps           | 17 sequential automated stages (All 17/17 passing with Exit Code 0)                |
| Random Seeds Enforced    | SEED = 42 (plus 5 evaluation seeds: 17, 42, 73, 108, 256)                          |
| Dependencies             | Listed in requirements.txt, 12_Reproducibility/environment.yml, and Dockerfile      |
| Data Provenance Flags    | 100.0% Digital_Twin_Simulated (N = 15,000, 30 stations, 36 columns, SEED = 42)     |
+--------------------------+------------------------------------------------------------------------------------+
```

---

## 2. Directory Structure of Reproducibility Assets

```text
12_Reproducibility/
├── README_reproducibility.md    # Master reproducibility manifest and badge certifications
├── data_sources.md              # Complete catalog of primary satellite and in-situ data sources
├── workflow_complete.md         # Detailed 13-stage mathematical and computational DAG workflow
├── replication_guide.md         # Step-by-step manual and automated replication guide for third parties
├── data_availability.md        # Formal FAIR data availability declaration for journal submission
├── requirements.txt             # Pinned pip dependency manifest
├── environment.yml              # Reproducible Conda virtual environment definition
└── workflow.md                  # High-level architecture workflow summary
```

---

## 3. Quick-Start Replication Commands

### Option A: Quick-Start with Standard Python Virtual Environment (`venv`)
```bash
# 1. Clone repository
git clone https://github.com/HrSly11/CoralTwin-DT.git
cd CoralTwin-DT

# 2. Initialize and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install pinned dependencies
pip install -r 12_Reproducibility/requirements.txt

# 4. Execute the master reproduction pipeline
python run_all.py
```

### Option B: Quick-Start with Conda Environment
```bash
# Create and activate conda environment
conda env create -f 12_Reproducibility/environment.yml
conda activate coraltwin-dt

# Run master reproduction
python run_all.py
```

---

## 4. Expected Output Artifacts & Verification Bounds

Upon successful completion of `python run_all.py`, the following core artifacts will be generated and validated:

| Output Artifact | Expected File Location | Expected Verification Criterion |
| :--- | :--- | :--- |
| **Harmonized Dataset** | `03_Data/final_dataset.csv` | Exact shape: $(15000, 36)$, 30 stations, 0 null values. |
| **Data Dictionary** | `03_Data/data_dictionary_final.csv` | 36 variables with ISO-19115 compliant metadata. |
| **AI Models Benchmark** | `results/model_benchmark_summary.csv` | Clean 10-feature XGBoost Acc $= 98.85\%$, $R^2 = 0.9336$, RMSE $= 4.044\%$. |
| **TreeSHAP Attributions** | `results/shap_global_importance.csv` | Clean 10-feature DHW importance $= 53.71\%$, PAR $= 11.35\%$, SSTA $= 9.28\%$. |
| **Decadal Projections** | `results/scenario_2050_summary.csv` | RK4 2050 mean coral cover: S1 $= 0.69\%$, S2 $= 18.55\%$, S3 $= 48.92\%$, S4 $= 55.20\%$. |
| **Restoration GeoJSON** | `08_GIS_and_Remote_Sensing/geospatial_outputs/priority_restoration_zones.geojson` | Valid RFC-7946 GeoJSON ($10/30 = 33.33\%$ Tier-1 stations at Eq. 7 $\text{SRPI} \ge 0.70$). |
| **Publication Figures** | `09_Results/figures/Figure1_*.png` through `Figure7_*.png` | 7 figures at 600 DPI resolution computed from CSV/JSON artifacts. |
| **Master Numbers JSON** | `results/manuscript_numbers.json` | Single source of truth with `script_source` and `file_source` traceability. |
