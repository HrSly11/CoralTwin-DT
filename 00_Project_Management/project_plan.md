# CoralTwin-DT: Project Management Plan

## 1. Executive Summary & Project Identification

- **Project Title:** Digital twin of coral reefs under thermal stress and ocean acidification for restoration and conservation prioritization (CoralTwin-DT)
- **Principal Investigator (PI):** Marine Ecology & Computational Oceanography Research Consortium
- **Target Publication Outlets:** *Global Change Biology* (Q1), *Ecological Informatics* (Q1), *Environmental Research Letters* (Q1)
- **Repository URL:** https://github.com/HrSly11/CoralTwin-DT.git
- **Primary Domain:** Marine Systems Ecology, Physical Oceanography, Ecological Digital Twins, Applied Machine Learning, Spatial Conservation Prioritization.

---

## 2. Consortium Work Packages (WPs) & Multidisciplinary Roles

```
+-------------------------------------------------------------------------------+
|                             STEERING COMMITTEE                               |
|          Lead Principal Investigator - Doctoral Advisory Board                |
+-------------------------------------------------------------------------------+
         |                       |                       |
         v                       v                       v
+------------------+    +------------------+    +------------------+
|      WP 1:       |    |      WP 2:       |    |      WP 3:       |
| Oceanography &   |    | Digital Twin     |    | Artificial       |
| Remote Sensing   |    | Architecture &   |    | Intelligence &   |
| (NOAA/Sentinel)  |    | Biophysics (6L)  |    | Predictive ML    |
+------------------+    +------------------+    +------------------+
         |                       |                       |
         +-----------------------+-----------------------+
                                 |
                                 v
+-------------------------------------------------------------------------------+
|      WP 4: Scenario Simulation & Spatial Optimization (Restoration/MPAs)      |
+-------------------------------------------------------------------------------+
                                 |
                                 v
+-------------------------------------------------------------------------------+
|      WP 5: Publication, Scientific Dissemination & Open-Science FAIR Repo     |
+-------------------------------------------------------------------------------+
```

### Multidisciplinary Role Allocation

1. **Lead Marine Ecology Researcher:** Formulates ecological state equations, coral-algal symbiosis breakdown models, calcification kinetics, and restoration mortality thresholds.
2. **Climate & Physical Oceanographer:** Models Degree Heating Weeks (DHW), sea surface temperature (SST) anomaly dynamics, carbonate chemistry equilibria ($pH$, $\Omega_{\text{arag}}$), and marine heatwave (MHW) recurrence.
3. **Digital Twin Systems Architect:** Designs the 6-layer digital twin framework, high-throughput ETL pipelines, cyber-physical coupling, and real-time/historical synchronization.
4. **Data Scientist & AI Specialist:** Implements supervised classifiers/regressors (Random Forest, XGBoost, Deep MLP, LSTM/Transformers), hyperparameter optimization, and TreeSHAP explainability.
5. **GIS & Remote Sensing Specialist:** Manages Sentinel-2 multispectral processing, Allen Coral Atlas habitat layers, benthic bathymetry integration, and Spatial Restoration Priority Index (SRPI) raster generation.
6. **Scientific Publishing & Q1 Lead:** Authors manuscript adhering to strict journal formatting (*Global Change Biology*), structural consistency, and reproducibility audits.
7. **Scientific Visualization Designer:** Crafts high-resolution (300+ DPI) figures, vector schematics, GIS thematic cartography, and interactive dashboard layouts.
8. **Scientific Repository & FAIR Data Curator:** Ensures compliance with FAIR data principles (Findable, Accessible, Interoperable, Reusable), Docker/Conda environment freezing, and reproducible execution pipelines.

---

## 3. Work Breakdown Structure (WBS)

- **WP 1: Data Ingestion & Harmonization (Months 1–3)**
  - Task 1.1: Ingest NOAA Coral Reef Watch (CRW) 5km Daily Global Satellite Coral Bleaching Heat Stress Products.
  - Task 1.2: Ingest Copernicus Sentinel-2 Level-2A surface reflectance and derive bottom-reflectance/turbidity indices.
  - Task 1.3: Harmonize Allen Coral Atlas benthic classification and Global Coral Reef Monitoring Network (GCRMN) benthic survey baselines.
  - Task 1.4: Formulate physical-chemical synthetic generator for controlled boundary condition experiments.

- **WP 2: Six-Layer Digital Twin Engineering (Months 3–6)**
  - Task 2.1: Layer 1 (Data Acquisition) & Layer 2 (ETL & Spatial-Temporal Normalization).
  - Task 2.2: Layer 3 (Coupled Biophysical-AI Hybrid Engine).
  - Task 2.3: Layer 4 (Forward Scenario Simulation: SSP2-4.5, SSP5-8.5, Active Restoration, MPAs).
  - Task 2.4: Layer 5 (Cross-Validation, Backtesting, Monte Carlo Uncertainty).
  - Task 2.5: Layer 6 (Visualization, Thematic Cartography, Decision Support Dashboard).

- **WP 3: Machine Learning & Predictive Modeling (Months 5–8)**
  - Task 3.1: Supervised predictive modeling of Bleaching Risk ($Low, Medium, High$) and Live Coral Cover decline ($\Delta C$).
  - Task 3.2: 5-Fold Spatio-Temporal Cross Validation to eliminate spatial autocorrelation artifacts.
  - Task 3.3: Global and local explainability via TreeSHAP (SHAP beeswarm, feature interaction values).

- **WP 4: Scenario Simulation & Restoration Optimization (Months 8–10)**
  - Task 4.1: Calibrate dynamical system differential equations for coral-macroalgal competition.
  - Task 4.2: Simulate 2025–2050 trajectories across 4 IPCC climate pathways and active outplanting interventions.
  - Task 4.3: Calculate Spatial Restoration Priority Index (SRPI) across pilot reef grid cells.

- **WP 5: Manuscript Finalization, Peer Review & Release (Months 10–12)**
  - Task 5.1: Write full research article and supplementary materials.
  - Task 5.2: Render vector/raster publication figures (Fig 1 to Fig 7).
  - Task 5.3: Verify 100% end-to-end code execution via `run_all.py`.

---

## 4. Risk Assessment and Mitigation Matrix

| Identified Risk | Severity | Probability | Mitigation Strategy |
| :--- | :---: | :---: | :--- |
| **Spatial autocorrelation in ML training** | High | High | Implement spatial-block cross-validation and spatial buffer splitting. |
| **Gaps in in-situ historical pH data** | Medium | High | Reconstruct carbonate equilibrium using satellite SST, salinity, and CMIP6 biogeochemical reanalysis. |
| **Computational bottle-neck in Monte Carlo runs** | Medium | Medium | Vectorize differential equation solvers using NumPy and parallelize via multiprocessing. |
| **Lack of reproducibility across platforms** | High | Low | Lock dependency versions in `requirements.txt`, `environment.yml`, and build unified runner `run_all.py`. |
