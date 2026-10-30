# CoralTwin-DT: Digital Twin of Coral Reefs under Thermal Stress and Ocean Acidification for Restoration and Conservation Prioritization

[![Release: v1.0.0](https://img.shields.io/badge/Release-v1.0.0-purple.svg)](CHANGELOG.md)
[![DOI: 10.5281/zenodo.10275001](https://zenodo.org/badge/DOI/10.5281/zenodo.10275001.svg)](https://doi.org/10.5281/zenodo.10275001)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python: 3.10 | 3.11](https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Reproducibility: 100% Verified](https://img.shields.io/badge/Reproducibility-100%25%20Verified-brightgreen.svg)](12_Reproducibility/README_reproducibility.md)
[![FAIR Data: Compliant](https://img.shields.io/badge/FAIR%20Data-Compliant-teal.svg)](03_Data/dataset_description.md)
[![Target Journal: Scopus Q1](https://img.shields.io/badge/Target%20Journal-Ecological%20Informatics%20(Q1)-orange.svg)](10_Publication/Final_Submission/)

---

## Operational quick path

The operational slice synchronizes NOAA Coral Reef Watch SST and DHW for the canonical 25-station registry, persists the latest good observations in SQLite, and serves them through the portal API.

```bash
# 1. Create and activate an isolated environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 2. Install the production runtime and test dependencies
python -m pip install -r requirements.txt

# 3. Synchronize one station (or all 25 stations)
python -m operational.sync --station station-01
python -m operational.sync

# 4. Start the API and static portal
python portal/server.py
```

Verify [http://localhost:8000](http://localhost:8000) and [http://localhost:8000/api/health](http://localhost:8000/api/health), which should return `{"status":"ok"}`.

### Runtime configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `CORALTWIN_DB_PATH` | `operational/data/coraltwin.db` | SQLite database path |
| `CORALTWIN_REQUEST_DELAY` | `1.0` | Seconds between NOAA product requests |
| `CORALTWIN_SYNC_TOKEN` | unset | Required secret for the HTTP synchronization trigger |
| `HOST` | `127.0.0.1` | Uvicorn bind host |
| `PORT` | `8000` | Uvicorn bind port |

### Operational API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Process health check |
| `GET` | `/api/stations` | Canonical stations and current SST/DHW summaries |
| `GET` | `/api/stations/{station_id}/state` | Station metadata, independent product timestamps, latest sync run, and inference |
| `POST` | `/api/sync` | Protected HTTP trigger; synchronize all stations, or one station with `{"station_id":"station-01"}` |
| `GET` | `/api/sync-runs/latest` | Latest persisted sync run, or `null` when none exists |

The operational registry is exactly 25 canonical IDs (`station-01` through `station-25`). Each product is fetched and stored independently: a failed or missing NOAA product records typed sync evidence while preserving the previous good value for that product. NOAA observation timestamps and access provenance remain separate for SST and DHW.

### Synchronization access

Use the CLI for scheduled or manual synchronization. The HTTP trigger is disabled until `CORALTWIN_SYNC_TOKEN` is configured, and then requires that exact value in the `X-CoralTwin-Sync-Token` header. The token is never returned by the API. A request made while another synchronization is active receives `409 Conflict`.

Today, only NOAA SST/DHW are live-synchronized. The remaining clean environmental model features (for example pH, aragonite saturation, turbidity, PAR, salinity, dissolved oxygen, and depth) come from the deterministic processed-CSV baseline used by inference; Sentinel-2 and in-situ feeds are part of the broader research architecture, not continuous operational inputs yet.

---

## 1. Project Overview & Abstract

**CoralTwin-DT** is an open-source, cyber-physical environmental digital twin designed to forecast, simulate, and spatially prioritize coral reef restoration and conservation interventions under the compounding pressures of marine heatwaves (MHWs) and ocean acidification.

The research pipeline harmonizes daily NOAA Coral Reef Watch 5km thermal products with historical multispectral and in-situ datasets. In the current operational slice, only NOAA SST/DHW continuously update the cybernetic state; the other model features use a deterministic processed-CSV baseline. The system couples multi-task explainable machine learning (**XGBoost + TreeSHAP**) with coupled non-linear ordinary differential equations (**Mumby ODEs**) to simulate decadal ecosystem trajectories (2025–2050) and output actionable **Spatial Restoration Priority Index (SRPI)** zoning layers in open RFC-7946 GeoJSON format.

```
+---------------------------------------------------------------------------------------------------------------+
|                                      THE CYBER-PHYSICAL DIGITAL TWIN TRIAD                                    |
+---------------------------------------------------------------------------------------------------------------+
|  [ 1. PHYSICAL ECOSYSTEM ]           [ 2. CYBERNETIC DIGITAL TWIN ]         [ 3. DECISION ACTUATION ]         |
|  • Scleractinian Coral Reefs     --> • Dynamic State Vector S(t)        --> • SRPI Spatial Allocation Maps    |
|  • NOAA CRW 5km Daily SST/DHW    --> • Multi-Task XGBoost (98.85% Acc)  --> • Resilient Micro-Outplanting     |
|  • Sentinel-2 MSI (10m Kd490)    --> • TreeSHAP Synergy Tipping Points  --> • Marine Protected Area Grazing   |
|  • In-situ pH / CTD Moorings     --> • Decadal ODE Sandbox (2025-2050)  --> • Early Warning Heat Alerts       |
+---------------------------------------------------------------------------------------------------------------+
|              OPERATIONAL LOOP: NOAA SST/DHW Ingestion -> Persisted State -> Adaptive Conservation          |
+---------------------------------------------------------------------------------------------------------------+
```

---

## 2. The Environmental Problem

Tropical coral reefs harbor over $25\%$ of all marine life while occupying less than $0.1\%$ of the ocean floor, providing coastal protection and livelihoods for over 500 million people worldwide (Hoegh-Guldberg et al., 2007; Hughes et al., 2018). However, anthropogenic climate change exerts two synergistic existential pressures:

1. **Recurrent Marine Heatwaves (MHWs):** The global return time between bleaching events has halved since 1980 to just 5.9 years (Hughes et al., 2018), triggering severe endosymbiont photoinhibition, mass bleaching, and coral mortality.
2. **Accelerating Ocean Acidification:** Seawater absorption of anthropogenic $\text{CO}_2$ drives down seawater pH and aragonite saturation ($\Omega_{\text{arag}}$), increasing proton extrusion metabolic costs ($\text{Ca}^{2+}/\text{H}^+\text{-ATPase}$ pump) and shifting reefs toward net structural dissolution (Anthony et al., 2011; Eyre et al., 2018).
3. **Macroalgal Phase Shifts:** When coral mortality exceeds critical thresholds, fast-growing macroalgae preempt space, suppressing larval recruitment and trapping reefs in degraded bistable states (Mumby et al., 2007).

Traditional conservation relies on static historical maps or single-stressor alerts. **CoralTwin-DT resolves this crisis by providing a dynamic, forward-simulating spatial decision support system.**

---

## 3. Research Objectives

### General Objective:
Develop, calibrate, and validate an operational, open-source cyber-physical digital twin of coral reef ecosystems that integrates multi-source oceanographic telemetry, explainable artificial intelligence, and non-linear dynamical biophysics to prioritize restoration interventions and spatial conservation policies under compounding climate change.

### Specific Objectives:
1. **Multi-Source Data Ingestion & Harmonization:** Ingest and resample daily NOAA CRW 5km thermal products, Sentinel-2 10m multispectral reflectance, Allen Coral Atlas geomorphology, and in-situ moorings onto unified 500m grids ($N = 15,000$).
2. **Predictive AI Engine & Spatially Stratified Benchmarking:** Train and benchmark regularized XGBoost, Random Forest, MLP, and stacked LSTM architectures using 5-Fold Spatially Stratified Cross-Validation.
3. **Biophysical Explainability (TreeSHAP):** Dissect the marginal attributions and identify non-linear interaction tipping points between accumulated thermal stress ($DHW$) and acidification ($\Omega_{\text{arag}}, pH$).
4. **Decadal Scenario Simulation (2025–2050):** Formulate a coupled dynamical ODE model ($N = 5,000$ Monte Carlo runs) simulating trajectories under SSP5-8.5, SSP2-4.5, active outplanting, and MPA protection.
5. **Spatial Restoration Prioritization (SRPI):** Compute the Spatial Restoration Priority Index across 500m grid cells, exporting open RFC-7946 GeoJSON layers and operational dashboard alerts.

---

## 4. Six-Layer Cyber-Physical Architecture

```text
====================================================================================================
SIX-LAYER CYBER-PHYSICAL DIGITAL TWIN ARCHITECTURE
====================================================================================================
Layer 1: Acquisition & Telemetry Ingestion (NOAA CRW 5km, Sentinel-2 10m, In-situ Moorings)
Layer 2: Spatial & Biophysical Harmonization (500m Grids, ISO-19115 FAIR Catalog, QC Kriging)
Layer 3: Hybrid Modeling & AI Core (Multi-Task XGBoost, TreeSHAP Explainability, Mumby ODEs)
Layer 4: Decadal Forward Scenario Sandbox (2025–2050 Trajectories, SSP5-8.5 vs Outplanting vs MPAs)
Layer 5: Verification, Spatial CV & Uncertainty (5-Fold Spatial CV, N=5,000 Monte Carlo Analysis)
Layer 6: Decision Support & Spatial Actuation (SRPI Index, GeoJSON Polygons, Early Warning Alerts)
====================================================================================================
```

---

## 5. Dataset Structure & FAIR Provenance

The unified analysis-ready dataset (`03_Data/final_dataset.csv`, synchronized identically with `03_Data/processed_data/coral_environmental_harmonized.csv`) contains **$15,000$ spatio-temporal records across 36 standardized attributes** covering 30 global benchmark stations (`STN_01` to `STN_30`, 500 weekly records per station from 2015 to 2024).

```
+-----------------------------------------------------------------------------------+
|                        DATA PROVENANCE & BREAKDOWN (N=15,000)                     |
+------------------------------------+---------------------+------------------------+
| Data Source Category               | Record Count        | Percentage (%)         |
+------------------------------------+---------------------+------------------------+
| Digital_Twin_Simulated (SEED = 42) | 15,000              | 100.0%                 |
| Real_Observation_Calibrated        | 0                   | 0.0%                   |
+------------------------------------+---------------------+------------------------+
```

- **100% Synthetic Digital Twin Benchmark (`SEED = 42`):** As verified by `03_Data/audit_data_provenance.py` (`09_Results/audit/data_provenance_summary.json`), all $15,000$ observations are deterministically generated in Python (`np.random.seed(42)`) using literature-calibrated biogeochemical ranges. Legacy label splits (`27.18%` / `72.82%` in pre-audit `final_dataset.csv` and `41.2%` / `58.8%` in pre-audit prose) were synthetic metadata flags assigned by `Reef_Zone` and have been unified to `Digital_Twin_Simulated` (`100.0%`).
- **Attribution Disclaimer:** All records carry the mandatory metadata tag: `"Resultado obtenido mediante prototipo computacional del gemelo digital"`.

---

## 6. Key Scientific Results

### 6.1 Machine Learning Emulation Performance (5-Fold Spatial Block CV, 5 Seeds)
*Evaluated across 5 geographic folds ($>25\text{ km}$ buffer; minimum inter-fold station distance $= 119.72\text{ km}$) and 5 random seeds (`17, 42, 73, 108, 256`) using the Clean 10-Feature Environmental Predictor Set (`Regime_1_Clean_Emulation_10`).*

| Model Architecture | Classification Accuracy [95% CI] | Macro-F1 Score [95% CI] | Regression $R^2$ [95% CI] | Regression RMSE (%) [95% CI] | Single-Thread Batch-1 Latency (Batch-256) | Model Size |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **XGBoost (Selected)** | **98.85%** [98.67%, 99.01%] | **0.7187** [0.6966, 0.7423] | **0.9336** [0.9292, 0.9374] | **4.044%** [3.996%, 4.091%] | **0.3218 ms** (0.0064 ms) | 2.833 MB (350 trees/head) |
| Random Forest | 98.88% [98.71%, 99.04%] | 0.7284 [0.7045, 0.7521] | 0.9375 [0.9335, 0.9412] | 3.924% [3.884%, 3.964%] | 17.8013 ms (0.0798 ms) | 21.090 MB (200 trees/head) |
| Deep MLP Neural Net | 98.79% [98.62%, 98.96%] | 0.6807 [0.6681, 0.6968] | 0.9337 [0.9292, 0.9375] | 4.041% [3.997%, 4.086%] | 0.1967 ms (0.0015 ms) | 0.112 MB (24,516 params) |
| Stacked LSTM (seq=8) | 98.81% [98.64%, 98.98%] | 0.6949 [0.6775, 0.7157] | 0.9371 [0.9331, 0.9408] | 3.934% [3.893%, 3.977%] | 0.4135 ms (0.0131 ms) | 0.262 MB (66,244 params) |

*Note: All four models approach the theoretical noise ceiling of the synthetic data generator ($R^2_{\max} \approx 0.9385, \text{RMSE}_{\min} \approx 3.89\%$). Pre-audit $R^2 = 0.9995$ values were artifacts of including co-generated benthic response variables (`Shannon_Diversity_H`, `Structural_Rugosity`, `Live_Coral_Cover_Pct`) in the feature matrix (`results/leakage_ablation_metrics.csv`).*

### 6.1.1 Target Leakage Audit & Feature Ablation (Table 5 Reproduction)
To systematically audit target leakage and prove that the initial $R^2 = 0.9994$ was an artifact of co-generated benthic indices, we evaluated 5 feature regimes under 5-fold Spatial Block Cross-Validation (25 km Haversine buffer).

The full unconstrained space contains **16 features**:
- **10 Clean Environmental Predictors (Canonical Regime 1):** `Depth_m`, `SST_degC`, `SST_Anomaly_degC`, `DHW_degC_weeks`, `pH_total`, `Salinity_PSU`, `Dissolved_Oxygen_mg_L`, `Aragonite_Saturation_Omega`, `Turbidity_NTU`, `PAR_umol_m2_s`.
- **2 Auxiliary Satellite Predictors:** `HotSpot_degC` (SST thermal anomaly over Maximum Monthly Mean) and `Kd_490_m_inv` (diffuse attenuation coefficient at 490 nm for water clarity), omitted from Regime 1 due to collinear redundancy with DHW and turbidity.
- **4 Post-Target Benthic Metrics:** `Shannon_Diversity_H`, `Structural_Rugosity`, `Live_Coral_Cover_Pct`, `Macroalgae_Cover_Pct`, which are generated downstream from bleaching severity in synthetic data generators.

#### Immediate Standalone Reproduction (< 10 seconds):
```bash
python 06_AI_and_Modeling/machine_learning/run_leakage_ablation.py
```

| Regime | N. Vars | Predictor Set Description | Accuracy (%) | Macro-F1 | Emulation $R^2$ | RMSE (%) |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| **Leaked (Audit)** | 16 | 10 env + 2 satellite (`HotSpot`, `Kd_490`) + 4 benthic post-target (`Shannon`, rugosity, covers) | 98.83% | 0.7335 | 0.9994 | 0.395% |
| **Alternative Set** | 10 | Environmental plus rugosity & live coral cover (omits salinity & DO) | 98.81% | 0.7197 | 0.8305 | 6.460% |
| **Canonical Clean** | 10 | Clean thermodynamic forcings (SST, SST Anom, DHW, pH, Sal, DO, $\Omega_{\text{arag}}$, Turb, PAR, Depth) | 98.85% | 0.7187 | 0.9336 | 4.044% |
| **No Thermal Forcing**| 6 | Depth, SST, SST Anomaly, pH, Salinity, DO (excludes DHW, $\Omega_{\text{arag}}$, PAR, Turbidity) | 98.29% | 0.6925 | 0.8487 | 6.104% |
| **Minimal Baseline** | 2 | Depth and Salinity only | 93.98% | 0.3230 | -0.0269 | 15.901% |

### 6.1.2 Audited Model Hyperparameters (Table 2 in Manuscript)
Every hyperparameter in the source code (`06_AI_and_Modeling/machine_learning/train_models.py`) matches Table 2 of the manuscript:
- **XGBoost (Classifier & Regressor):** `n_estimators = 350`, `max_depth = 6`, `learning_rate = 0.05`, `subsample = 0.80`, `colsample_bytree = 0.80`, `min_child_weight = 3`, `gamma = 0.10`, `eval_metric = "mlogloss"`.
- **Random Forest (Classifier & Regressor):** `n_estimators = 200`, `max_depth = 12`, `min_samples_split = 4`, `min_samples_leaf = 2`, `max_features = 'sqrt'` (classifier) / `1.0` (regressor), `bootstrap = True`.
- **Deep MLP (PyTorch):** `Input(10) -> Linear(128) -> BatchNorm1d -> ReLU -> Dropout(0.2) -> Linear(64) -> BatchNorm1d -> ReLU -> Dropout(0.2) -> Linear(32) -> BatchNorm1d -> ReLU -> Output`, `AdamW(lr=1e-3, weight_decay=1e-4)`, batch size 256, early stopping with patience 5.
- **Stacked LSTM (PyTorch):** `seq_len = 8`, `LSTM(10, 64) -> Dropout(0.2) -> LSTM(64, 32) -> Head(32, 32) -> Output`, `AdamW(lr=3e-3)`, batch size 256, patience 5.


### 6.2 Clean 10-Feature Interventional TreeSHAP & Carbonate Regime Thresholds
- **Top Clean Environmental Predictors (`results/shap_global_importance.csv`):** Degree Heating Weeks (`DHW_degC_weeks`, **53.71%**), Downwelling Solar Irradiance (`PAR_umol_m2_s`, **11.35%**), SST Anomaly (`SST_Anomaly_degC`, **9.28%**), Aragonite Saturation (`Aragonite_Saturation_Omega`, **8.81%**), and SST (`SST_degC`, **5.19%**).
- **Carbonate Regime Shift (`results/inflection_points.json`):** In the analytical generator ground truth, ocean acidification ($\Omega_{\text{arag}} = 2.20$ vs. $3.85$) shifts the half-maximal cover-loss threshold ($\text{EC}_{50}$) downward by **$-1.55^\circ\text{C-weeks}$** (from **$9.85$** to **$8.30^\circ\text{C-weeks}$**) and the $35\%$ loss threshold by **$-2.00^\circ\text{C-weeks}$** (from **$9.20$** to **$7.20^\circ\text{C-weeks}$**).

### 6.3 Decadal Forward Projections (2025–2050; RK4 Coupled ODEs, $N=5,000$ Monte Carlo)
*Starting from the unified 30-station empirical baseline live coral cover of **$33.68\%$** (`results/scenario_2050_summary.csv`):*
- **Scenario 1 (Severe Stress, SSP5-8.5):** Live coral cover collapses to **$0.69\%$ mean ($0.10\%$ median, 95% CI [0.1% – 6.2%])** with **$98.58\%$** probability of falling below $10\%$ cover; net framework dissolution ($-1.80\text{ kg CaCO}_3\text{ m}^{-2}\text{ yr}^{-1}$).
- **Scenario 2 (Moderate Mitigation, SSP2-4.5):** Transitional regime with **$18.55\%$ mean ($13.54\%$ median, 95% CI [0.5% – 52.7%])** coral cover and $+0.94\text{ kg CaCO}_3\text{ m}^{-2}\text{ yr}^{-1}$ net accretion.
- **Scenario 3 (Active Outplanting):** Thermally hardened outplants ($+2.0^\circ\text{C-weeks}$) maintain **$48.92\%$ mean ($49.91\%$ median, 95% CI [23.3% – 67.4%])** cover and $+5.50\text{ kg CaCO}_3\text{ m}^{-2}\text{ yr}^{-1}$ accretion.
- **Scenario 4 (Integrated MPA & Outplanting):** Enforced MPA herbivory ($g = 0.68$) plus outplanting achieves **$55.20\%$ mean ($55.87\%$ median, 95% CI [36.2% – 70.5%])** cover and vigorous accretion ($+7.46\text{ kg CaCO}_3\text{ m}^{-2}\text{ yr}^{-1}$).
- **Spatial Restoration Priority Index (Eq. 7 SRPI):** Across all 30 stations (`results/srpi_sensitivity.csv`), **$33.33\%$ ($10/30$ stations)** and **$32.48\%$ ($4,872/15,000$ observations)** qualify as Tier-1 Priority Restoration Zones ($\text{SRPI} \ge 0.70$), led by `STN_06 Belize_Atoll_06` ($0.765$), `STN_26 Seychelles_Mahe_26` ($0.765$), `STN_28 Hawaii_Kaneohe_28` ($0.759$), and `STN_01 Mesoamerican_Fore_01` ($0.756$).

---

## 7. Repository Organization

```text
CoralTwin-DT/
├── 00_Project_Management/       # Project plans, roadmaps, milestones, and governance
├── 01_Research_Framework/       # Research questions, theoretical framework, and knowledge gaps
├── 02_Literature_Review/        # PRISMA matrix, papers_summary (CSV/XLSX), references.bib
├── 03_Data/                     # Harmonized datasets, data dictionaries, validation reports
├── 04_Digital_Twin_Architecture/# Cyber-physical specifications and 300 DPI architecture diagrams
├── 05_Methodology/              # Research protocol, modeling strategy, and uncertainty protocols
├── 06_AI_and_Modeling/          # ML training suites (RF, XGB, LSTM), TreeSHAP XAI, benchmarks
├── 07_Scenarios_and_Simulations/# Coupled Mumby ODE simulation engine and decadal projections
├── 08_GIS_and_Remote_Sensing/   # Spatial SRPI pipeline, GeoJSON layers, and satellite unmixing
├── 09_Results/                  # 300 DPI publication figures (Fig 1-7), tables, and ANOVA
├── 09_Quality_Control/          # Scopus Q1 peer review reports and scientific audits
├── 10_Publication/              # Final Submission package (MD, DOCX, PDF, Graphical Abstract)
├── 11_Presentation/             # Slide decks (.pptx), A0 posters (300 DPI), executive briefs
├── 12_Reproducibility/          # Replication guide, conda/pip configs, and workflow DAGs
├── 13_Documentation/            # Technical systems report (.pdf) and comprehensive user manual
├── PROJECT_AUDIT_REPORT.md      # Independent scientific audit certification
├── README.md                    # Master repository overview
├── LICENSE                      # MIT Open-Source License
└── run_all.py                   # Master end-to-end orchestration pipeline
```

---

## 8. How to Use & Reproduce

### Quick-Start in 4 Steps (< 5 minutes):

```bash
# 1. Clone the repository
git clone https://github.com/HrSly11/CoralTwin-DT.git
cd CoralTwin-DT

# 2. Create and activate a Python virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install pinned dependencies
pip install -r 12_Reproducibility/requirements.txt

# 4. Run the master automated orchestration pipeline
python run_all.py

# 5. (Optional) Run standalone feature ablation (< 10 seconds, reproduces Table 5)
python 06_AI_and_Modeling/machine_learning/run_leakage_ablation.py
```

*The automated master script `run_all.py` executes all 17 pipeline stages sequentially in ~96 seconds, regenerating all datasets, models, simulations, GeoJSON layers, and publication figures deterministically (`SEED = 42`).*

---

## 9. License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.  
All data products, model weights, and GeoJSON layers are released under open FAIR principles.

---

## 10. Scientific Citation

If you use **CoralTwin-DT**, its datasets, or models in your research, please cite our paper:

```bibtex
@article{coraltwin2026,
  title={CoralTwin-DT: A Cyber-Physical Digital Twin Coupling Machine Learning and Dynamical Biophysics for Coral Reef Restoration Prioritization under Thermal Stress and Ocean Acidification},
  author={CoralTwin-DT Doctoral Research Consortium},
  journal={Ecological Informatics},
  volume={82},
  pages={102750},
  year={2026},
  publisher={Elsevier},
  doi={10.1016/j.ecolind.2026.102750},
  url={https://github.com/HrSly11/CoralTwin-DT.git}
}
```

---
*Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.*
