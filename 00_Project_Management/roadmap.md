# CoralTwin-DT: Development & Research Roadmap

```
2025-Q1                  2025-Q2                  2025-Q3                  2025-Q4
 [Phase 1: Ingestion]  -> [Phase 2: Modeling]  -> [Phase 3: Simulation] -> [Phase 4: Synthesis]
  - Ingest NOAA CRW        - Train RF, XGB, MLP     - 2025-2050 Scenarios    - Q1 Manuscript
  - Process Sentinel-2     - Spatio-temporal CV     - MCE Spatial Resto      - 300 DPI Figures
  - FAIR Data Struct       - SHAP Analysis          - Dashboard Prototypes   - FAIR Release
```

---

## 1. Multi-Horizon Strategic Roadmap

### Near-Term (Months 1–4): Foundation & Harmonization
- [x] Establish ISO 19115 and FAIR metadata standards for multi-source marine datasets.
- [x] Standardize NOAA CRW 5km operational metrics ($SST$, $SSTA$, $DHW$, $Bleaching Alert Area$).
- [x] Couple satellite-derived turbidity ($K_d(490)$) with in-situ benthic surveys.
- [x] Develop biophysical synthetic generator adhering to carbonate equilibrium thermodynamics.

### Medium-Term (Months 5–8): AI Modeling & Cyber-Physical Integration
- [x] Build multi-task machine learning architecture predicting both continuous coral mortality and categorical bleaching severity (`Low`, `Medium`, `High`).
- [x] Implement rigorous spatial block cross-validation (5-fold) to prevent spatial over-optimism.
- [x] Extract TreeSHAP interaction metrics revealing non-linear tipping points between $DHW \ge 8^\circ\text{C-weeks}$ and $pH \le 7.85$.
- [x] Formulate dynamical ordinary differential equation (ODE) solver for coral-macroalgae phase shifts.

### Long-Term (Months 9–12): Forward Projection, Spatial Optimization & Global Dissemination
- [x] Forward-simulate 4 climate/management scenarios to 2050 (SSP5-8.5 unmitigated, SSP2-4.5 moderate, Active Micro-fragment Outplanting, Marine Protected Area herbivory protection).
- [x] Generate raster/vector maps of the Spatial Restoration Priority Index (SRPI).
- [x] Finalize Q1 scientific manuscript for submission to *Global Change Biology*.
- [x] Package reproducible digital twin repository with automated execution orchestrator `run_all.py`.

---

## 2. Technology & Architecture Stack

| Domain | Selected Framework / Library | Rationale |
| :--- | :--- | :--- |
| **Numerical Biophysics** | `numpy`, `scipy` (ODE integrators) | High-performance ODE and matrix computation for coral dynamical models. |
| **Data Engineering & FAIR** | `pandas`, `openpyxl`, `pyarrow` | Efficient handling of multi-decade spatial-temporal tabular datasets. |
| **Machine Learning** | `scikit-learn`, `xgboost`, `keras`/`MLP` | SOTA gradient boosting and deep learning with rock-solid reproducibility. |
| **Explainable AI (XAI)** | `shap` (TreeSHAP) | Game-theoretic feature attribution and non-linear threshold discovery. |
| **Geospatial & Remote Sensing** | `geopandas`, `shapely`, GeoJSON | Benthic spatial geometry and multi-criteria spatial zoning. |
| **Scientific Visualization** | `matplotlib`, `seaborn`, `plotly` | Publication-ready 300+ DPI vector/raster figures conforming to journal guidelines. |
| **Dissemination & Deliverables**| `python-docx`, `python-pptx`, `reportlab` | Automated generation of Word manuscripts, PowerPoint slides, and PDF briefs. |
