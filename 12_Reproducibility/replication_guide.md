# Third-Party Replication Guide: CoralTwin-DT

**Document Purpose:** Practical, step-by-step replication and validation protocol for peer reviewers, independent researchers, and marine conservation practitioners.  
**Repository:** https://github.com/HrSly11/CoralTwin-DT.git  
**Estimated Time to Complete Full Replication:** ~5 minutes (setup + execution)  

---

## 1. System & Hardware Requirements

```
+-------------------------------------------------------------------------------+
|                        SYSTEM & HARDWARE SPECIFICATIONS                       |
+---------------------+-------------------------+-------------------------------+
| Component           | Minimum Requirement     | Recommended Specification     |
+---------------------+-------------------------+-------------------------------+
| Operating System    | Windows 10/11, Linux    | Ubuntu 22.04 LTS or Win 11    |
|                     | (Ubuntu 20.04+), macOS  |                               |
| Python Version      | Python 3.10.x – 3.11.x  | Python 3.11.x                 |
| CPU                 | Dual-Core Intel/AMD     | Quad-Core (e.g. i5/i7/Ryzen)  |
| Memory (RAM)        | 4 GB RAM                | 8 GB RAM                      |
| Storage             | 1.5 GB Free Disk Space  | 3 GB Free Disk Space (NVMe)   |
| GPU                 | Not Required (CPU only) | Optional (NVIDIA CUDA)        |
+---------------------+-------------------------+-------------------------------+
```

---

## 2. Step-by-Step Replication Protocol

### Step 1: Clone the Official Repository
```bash
git clone https://github.com/HrSly11/CoralTwin-DT.git
cd CoralTwin-DT
```

### Step 2: Environment Provisioning

#### Option A: Using Conda (Recommended for Cross-Platform Isolation)
```bash
conda env create -f 12_Reproducibility/environment.yml
conda activate coraltwin-dt
```

#### Option B: Using Standard Python Virtual Environment (`venv`)
```bash
# Create environment
python -m venv venv

# Activate environment
# On Windows PowerShell:
.\venv\Scripts\activate
# On Linux / macOS:
source venv/bin/activate

# Upgrade pip and install pinned dependencies
pip install --upgrade pip
pip install -r 12_Reproducibility/requirements.txt
```

---

### Step 3: Master Automated Pipeline Execution
To execute all 13 pipeline stages automatically in sequence, run:
```bash
python run_all.py
```

### Expected Terminal Output:
```text
======================================================================
CoralTwin-DT: Master Reproduction Pipeline
======================================================================
[1/13] Generating synthetic datasets... [OK] (8.5s)
[2/13] Running exploratory data analysis... [OK] (4.2s)
[3/13] Training AI models (XGBoost, RF, MLP)... [OK] (16.8s)
[4/13] Evaluating models & computing cross-validation metrics... [OK] (6.5s)
[5/13] Benchmarking AI architectures (RF vs XGB vs LSTM)... [OK] (24.5s)
[6/13] Running TreeSHAP game-theoretic explainability... [OK] (11.2s)
[7/13] Simulating decadal forward scenarios (2025-2050)... [OK] (7.8s)
[8/13] Executing GIS spatial restoration priority pipeline... [OK] (3.4s)
[9/13] Rendering publication-quality 300 DPI figures... [OK] (8.1s)
[10/13] Generating advanced digital twin architecture diagrams... [OK] (2.5s)
[11/13] Generating scientific presentation & poster... [OK] (4.8s)
[12/13] Compiling executive summary and technical report PDFs... [OK] (3.2s)
[13/13] Building Scopus Q1 manuscript docs (DOCX/PDF)... [OK] (2.5s)
======================================================================
All 13/13 pipelines executed successfully in 104.0s.
Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.
======================================================================
```

---

## 3. Metric Validation & Tolerance Bounds

When validating the replication output, ensure that computed metrics fall within the established statistical tolerance bounds:

| Metric / Parameter | File to Inspect | Expected Target | Permissible Tolerance |
| :--- | :--- | :---: | :---: |
| **XGBoost Accuracy** | `06_AI_and_Modeling/model_comparison_report.md` | $98.85\%$ | $\pm 0.50\%$ |
| **XGBoost Regression $R^2$** | `06_AI_and_Modeling/model_comparison_report.md` | $0.9995$ | $\pm 0.005$ |
| **XGBoost Regression RMSE** | `06_AI_and_Modeling/model_comparison_report.md` | $0.346\%$ | $\pm 0.05\%$ |
| **TreeSHAP Top Feature** | `09_Results/statistics/global_feature_importance_shap.csv` | $DHW$ ($47.0\%$) | Rank #1 feature |
| **2050 Unmitigated Cover** | `09_Results/tables/Table2_decadal_scenario_projections.csv` | $4.8\%$ | $[2.0\% - 8.5\%]$ |
| **2050 Restored Cover** | `09_Results/tables/Table2_decadal_scenario_projections.csv` | $46.2\%$ | $[40.0\% - 53.0\%]$ |
| **SRPI Top Station** | `08_GIS_and_Remote_Sensing/geospatial_outputs/spatial_restoration_priority_ranking.csv` | `Mesoamerican_Fore_01` | Rank #1 ($\text{SRPI} \approx 0.78$) |

---

## 4. Troubleshooting & Common Issues

```
+---------------------------------------------------------------------------------------------------------------+
|                                      TROUBLESHOOTING GUIDE                                                    |
+------------------------------------+--------------------------------------------------------------------------+
| Issue Encountered                  | Resolution Strategy                                                      |
+------------------------------------+--------------------------------------------------------------------------+
| Matplotlib Headless Backend Error  | The scripts explicitly set `matplotlib.use('Agg')` for headless servers. |
|                                    | If running on an exotic Linux server without X11, ensure no DISPLAY is set|
|                                    | or use `export MPLBACKEND=Agg`.                                          |
|                                    |                                                                          |
| TensorFlow oneDNN Warnings         | Harmless optimization info. To silence, set:                            |
|                                    | `export TF_ENABLE_ONEDNN_OPTS=0` or `export TF_CPP_MIN_LOG_LEVEL=3`.    |
|                                    |                                                                          |
| fpdf2 Font / Character Encoding    | Scripts automatically sanitize non-ASCII characters using latin-1 escape.|
|                                    | Ensure `fpdf2 >= 2.8.0` is installed.                                    |
|                                    |                                                                          |
| Python-PPTX Missing Library        | Install via `pip install python-pptx>=1.0.0`.                           |
+------------------------------------+--------------------------------------------------------------------------+
```

---

## 5. Contact for Replication Support

For questions, bug reports, or assistance replicating CoralTwin-DT:
- **GitHub Issues:** https://github.com/HrSly11/CoralTwin-DT/issues
- **Lead Developer:** CoralTwin-DT Doctoral Research Consortium
