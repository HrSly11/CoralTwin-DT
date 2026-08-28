# Changelog: CoralTwin-DT

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-08-27

### Added
- **Six-Layer Cyber-Physical Digital Twin Architecture:**
  - Layer 1 (Acquisition): Automated data ingestion from NOAA CRW (5km), Sentinel-2 MSI (10m), and in-situ oceanographic moorings (pH, Salinity, DO).
  - Layer 2 (Harmonization): Spatial infilling onto standardized $500\text{m} \times 500\text{m}$ benthic grids ($N = 15,000$ records across 30 global reef stations) with ISO-19115 compliant metadata.
  - Layer 3 (Hybrid Modeling): Multi-task AI prediction suite featuring regularized XGBoost, Random Forest, Deep MLP, and stacked Bidirectional LSTM networks.
  - Layer 4 (Decadal Forward Sandbox): Non-linear dynamical ordinary differential equation (ODE) solver simulating coral-macroalgae space competition (Mumby-Hastings-Edwards model) through 2050 ($N = 5,000$ Monte Carlo stochastic iterations).
  - Layer 5 (Verification & Uncertainty): 5-Fold Spatially Stratified Cross-Validation with a 25 km geographic buffer to eliminate spatial autocorrelation inflation.
  - Layer 6 (Decision Support & Actuation): Multi-criteria Spatial Restoration Priority Index (SRPI) exporting open RFC-7946 GeoJSON spatial zoning layers (`priority_restoration_zones.geojson`).
- **Biophysical Explainability (TreeSHAP):**
  - Polynomial-time exact Shapley value feature attribution revealing that ocean acidification ($pH \le 7.85$) drops the critical thermal mortality tipping point from $8.5$ to $5.8^\circ\text{C-weeks}$.
- **Comprehensive Scientific Publication Package:**
  - Full research article formatted for *Ecological Informatics* (Elsevier, Scopus Q1) / *Environmental Research Letters* (IOP, Scopus Q1) in Markdown, editable DOCX, and publication PDF formats.
  - High-resolution Graphical Abstract (16:9, 300 DPI) and 5 Research Highlights.
  - Formal Cover Letter to the Editor-in-Chief and Supplementary Material document (DOCX and PDF).
- **Conference Presentation & Documentation:**
  - 8-slide widescreen scientific presentation deck (`scientific_presentation.pptx`) and A0 conference poster (`poster.png`, 300 DPI).
  - Executive summary policy brief (`executive_summary.pdf`) and comprehensive technical systems report (`technical_report.pdf`).
- **Master Automated Orchestration Pipeline:**
  - `run_all.py` executing all 13 pipeline stages deterministically (`SEED = 42`) in ~104 seconds.
- **Reproducibility & Open Science Suite:**
  - `12_Reproducibility/` manifest with Conda `environment.yml`, pinned `requirements.txt`, step-by-step replication guide, and data sources catalog.

### Changed
- Refactored `03_Data/final_dataset.csv` to 15,000 records across 34 variables with clear provenance flags (41.2% real calibrated vs 58.8% digital twin simulated).
- Standardized data dictionary to `03_Data/data_dictionary_final.csv`.
- Updated master `README.md` with official scientific research badges, citations, and replication instructions.

### Fixed
- Modernized `fpdf2` cell positioning parameters to eliminate console deprecation warnings.
- Fixed learning rate schedules and gradient bounds to ensure mathematical convergence across all neural networks.

---
*Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.*
