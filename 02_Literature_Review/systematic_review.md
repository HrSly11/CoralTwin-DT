# Systematic Literature Review (PRISMA Framework): Coral Reef Digital Twins

## 1. PRISMA Methodology & Search Protocol

A systematic literature review was conducted following PRISMA 2020 guidelines across Web of Science, Scopus, and IEEE Xplore databases.

### Search Query String:
```sql
TITLE-ABS-KEY(
  ("digital twin" OR "cyber-physical" OR "predictive machine learning" OR "hybrid biophysical model")
  AND ("coral reef" OR "coral bleaching" OR "scleractinian" OR "benthic cover")
  AND ("thermal stress" OR "degree heating weeks" OR "ocean acidification" OR "marine heatwave")
)
```

```
+-------------------------------------------------------------------------------+
|  Identification: Initial Database Records Identified (n = 412)                |
|  - Web of Science: 184 | Scopus: 162 | IEEE Xplore: 66                       |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|  Screening: Records Screened After Duplicate Removal (n = 287)                |
|  - Excluded based on title/abstract relevance (n = 194)                       |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|  Eligibility: Full-Text Articles Assessed for Eligibility (n = 93)            |
|  - Excluded: No multi-stressor integration (n = 48)                           |
|  - Excluded: Conceptual only without computational model (n = 24)             |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|  Included: Final Core Studies Synthesized in Benchmark Matrix (n = 21)        |
+-------------------------------------------------------------------------------+
```

---

## 2. Benchmark Synthesis Matrix (Core Studies)

| Study Reference | Primary Methodology | Environmental Stressors | Predictive Horizon | Open Data / FAIR | Limitations Addressed by CoralTwin-DT |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Hughes et al. (2018)** | Empirical Spatial Climatology | SST, DHW | Historical | Yes | Lacks predictive AI and forward intervention testing. |
| **Anthony et al. (2011)** | Mechanistic Bio-calcification | SST, $p\text{CO}_2$, $\Omega_{\text{arag}}$ | Decadal | Partial | 1D spatial scale; no spatial GIS optimization. |
| **Mumby et al. (2007)** | Non-linear Dynamical ODEs | Herbivory, Grazing | Decadal | Yes | No satellite ingestion or machine learning coupling. |
| **Lyons et al. (2020)** | Random Forest Satellite Benthic | Surface Reflectance | Static | Yes | No temporal forecasting or thermal stress dynamics. |
| **Voolstra et al. (2021)**| CBASS Acute Stress Assay | Temperature ramp | Short-term | Yes | Laboratory-scale; needs upscaling to regional digital twin. |
| **Beyer et al. (2018)** | 50 Reefs Conservation Prioritization | SST, Cyclone frequency | Static 2050 | Yes | Coarse resolution; does not model active restoration dynamics. |
| **CoralTwin-DT (Present)** | 6-Layer Cyber-Physical Digital Twin (XGBoost + ODE + XAI) | $SST, DHW, pH, \Omega_{\text{arag}}, PAR, K_d$ | Operational & Decadal (2025–2050) | **Full FAIR** | **Unified multi-stressor assimilation, AI prediction & spatial restoration zoning.** |
