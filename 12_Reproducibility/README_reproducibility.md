# Scientific Reproducibility & Open Science Manifest: CoralTwin-DT

**Repository:** https://github.com/HrSly11/CoralTwin-DT.git  
**Standard Compliance:** FAIR Principles (Findable, Accessible, Interoperable, Reusable)  
**Certification Standard:** Nature / Elsevier Reproducibility Guidelines  
**Master Execution Script:** `python run_all.py` (Complete execution time: ~104 seconds)  
**Scientific Attribution:** *Resultado obtenido mediante prototipo computacional del gemelo digital.*

---

## 1. Reproducibility Overview

**CoralTwin-DT** is built from the ground up to achieve **100% deterministic, push-button computational reproducibility**. Any independent researcher with Python 3.10+ or an active Conda environment can reproduce the entire end-to-end pipeline—from raw data synthesis and harmonization to AI model training, TreeSHAP attribution, decadal Monte Carlo ODE simulations (2025–2050), GIS GeoJSON export, and 300 DPI publication figure rendering.

```
+---------------------------------------------------------------------------------------------------------------+
|                                      REPRODUCIBILITY AT A GLANCE                                              |
+--------------------------+------------------------------------------------------------------------------------+
| Master Execution Command | python run_all.py                                                                  |
| Total Execution Time     | 104 seconds (Standard 4-core laptop CPU)                                           |
| Pipeline Steps           | 13 sequential automated stages (All 13/13 passing with Exit Code 0)                |
| Random Seeds Enforced    | SEED = 42 (NumPy, Scikit-Learn, XGBoost, TensorFlow)                               |
| Dependencies             | Listed in requirements.txt and environment.yml                                      |
| Data Provenance Flags    | Real_Observation_Calibrated (41.2%) vs Digital_Twin_Simulated (58.8%)              |
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
| **Harmonized Dataset** | `03_Data/final_dataset.csv` | Exact shape: $(15000, 34)$, 0 null values. |
| **Data Dictionary** | `03_Data/data_dictionary_final.csv` | 34 variables with ISO-19115 compliant metadata. |
| **AI Models Benchmark** | `06_AI_and_Modeling/machine_learning/saved_models/` | Serialized `.json` and `.joblib` files ($>98\%$ accuracy). |
| **TreeSHAP Attributions** | `09_Results/statistics/global_feature_importance_shap.csv` | DHW importance $\approx 47\%$, Rugosity $\approx 20\%$. |
| **Decadal Projections** | `09_Results/statistics/monte_carlo_trajectories_2025_2050.csv` | Scenario 1 cover $\approx 4.8\%$, Scenario 4 cover $\approx 46.2\%$. |
| **Restoration GeoJSON** | `08_GIS_and_Remote_Sensing/geospatial_outputs/priority_restoration_zones.geojson` | Valid RFC-7946 GeoJSON FeatureCollection. |
| **Publication Figures** | `09_Results/figures/Figure1_*.png` through `Figure7_*.png` | 7 figures at 300 DPI resolution. |
| **Q1 Manuscript** | `10_Publication/final_manuscript/manuscript_q1.pdf` | Formatted multi-page publication document. |
