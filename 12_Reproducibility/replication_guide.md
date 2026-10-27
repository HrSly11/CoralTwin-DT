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
To execute all 17 pipeline stages automatically in sequence, run:
```bash
python run_all.py
```

### Expected Terminal Output:
```text
======================================================================
CoralTwin-DT: Master Reproduction Pipeline
======================================================================
[1/17] Generating unified 30-station synthetic datasets (N=15,000)... [OK]
[2/17] Auditing row-level data provenance... [OK]
[3/17] Building 5-fold spatial block cross-validation splits (>25 km buffer)... [OK]
[4/17] Running exploratory data analysis... [OK]
[5/17] Training AI models (XGBoost, RF, Deep MLP, Stacked LSTM) across 5 seeds x 5 folds... [OK]
[6/17] Evaluating models, calibration, & paired Wilcoxon statistical tests... [OK]
[7/17] Synchronizing multi-architecture benchmark report... [OK]
[8/17] Running clean 10-feature interventional TreeSHAP & 2D PDP inflection analysis... [OK]
[9/17] Simulating decadal RK4 coupled ODE scenarios (2025-2050, N=5,000 MC)... [OK]
[10/17] Executing 30-station Eq. 7 SRPI spatial priority & sensitivity pipeline... [OK]
[11/17] Compiling master manuscript numbers JSON (results/manuscript_numbers.json)... [OK]
[12/17] Rendering publication-quality 600 DPI figures from computed artifacts... [OK]
[13/17] Generating digital twin architecture diagrams... [OK]
[14/17] Generating scientific presentation & poster... [OK]
[15/17] Compiling executive summary and technical report PDFs... [OK]
[16/17] Building manuscript PDF (preserving all .docx files untouched)... [OK]
[17/17] Running automated biophysical unit tests... [OK]
======================================================================
All 17/17 pipelines executed successfully in ~96.0s.
Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.
======================================================================
```

---

## 3. Metric Validation & Tolerance Bounds

When validating the replication output, ensure that computed metrics match the audited values in `results/manuscript_numbers.json`:

| Metric / Parameter | File to Inspect | Expected Target | Permissible Tolerance |
| :--- | :--- | :---: | :---: |
| **XGBoost Accuracy (Clean 10)** | `results/model_benchmark_summary.csv` | $98.85\%$ | $[98.67\% - 99.01\%]$ |
| **XGBoost Regression $R^2$ (Clean 10)** | `results/model_benchmark_summary.csv` | $0.9336$ | $[0.9292 - 0.9374]$ |
| **XGBoost Regression RMSE (Clean 10)** | `results/model_benchmark_summary.csv` | $4.044\%$ | $[3.996\% - 4.091\%]$ |
| **TreeSHAP Top Feature (Clean 10)** | `results/shap_global_importance.csv` | `DHW_degC_weeks` ($53.71\%$) | $[51.37\% - 55.98\%]$ |
| **2050 Unmitigated Cover (S1 RK4)** | `results/scenario_2050_summary.csv` | $0.69\%$ mean ($0.10\%$ med) | $[0.1\% - 6.2\%]$ |
| **2050 Integrated Cover (S4 RK4)** | `results/scenario_2050_summary.csv` | $55.20\%$ mean ($55.87\%$ med) | $[36.2\% - 70.5\%]$ |
| **Eq. 7 SRPI Tier-1 Stations** | `results/srpi_sensitivity.csv` | $10/30$ ($33.33\%$, top `STN_06` $= 0.765$) | Exact match |

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
