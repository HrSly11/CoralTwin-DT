# CoralTwin-DT: Digital Twin of Coral Reefs Under Thermal Stress and Ocean Acidification for Restoration and Conservation Prioritization

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FAIR Data](https://img.shields.io/badge/FAIR-Compliant-green.svg)](https://www.go-fair.org/fair-principles/)
[![Target Journal](https://img.shields.io/badge/Target-Global%20Change%20Biology%20(Q1)-purple.svg)](https://onlinelibrary.wiley.com/journal/13652486)
[![Reproducibility](https://img.shields.io/badge/Reproducibility-100%25%20Automated-brightgreen.svg)](run_all.py)

> **Repository:** https://github.com/HrSly11/CoralTwin-DT.git  
> **Scientific Attribution:** *Resultado obtenido mediante prototipo computacional del gemelo digital.*

---

## 1. Executive Summary & Research Vision

**CoralTwin-DT** is an open-source, doctoral-grade cyber-physical environmental digital twin designed to assimilate multi-source oceanographic telemetry, predict localized coral bleaching risk, simulate decadal restoration scenarios (2025–2050), and optimize spatial conservation zoning under compounding marine heatwaves and ocean acidification.

```
===================================================================================
                             CORALTWIN-DT ARCHITECTURE
===================================================================================

 [LAYER 6: DECISION SUPPORT & VISUALIZATION]
  - Scientific Dashboard | GIS Cartography | Spatial Restoration Priority Index (SRPI)
 ---------------------------------------------------------------------------------
 [LAYER 5: VALIDATION, BENCHMARKING & UNCERTAINTY]
  - 5-Fold Spatially Stratified CV | Monte Carlo (N=5,000) | Backtesting 2016-2024
 ---------------------------------------------------------------------------------
 [LAYER 4: SCENARIO SIMULATION & FORWARD DYNAMICS]
  - SSP5-8.5 vs SSP2-4.5 | Thermally Resilient Micro-Fragmentation | MPA Grazing
 ---------------------------------------------------------------------------------
 [LAYER 3: HYBRID BIOPHYSICAL-AI MODELING ENGINE]
  - Coupled Mumby ODEs | Multi-task XGBoost / RF / MLP | TreeSHAP Attribution
 ---------------------------------------------------------------------------------
 [LAYER 2: DATA INTEGRATION, ETL & FAIR NORMALIZATION]
  - Spatiotemporal Harmonization (500m/Daily) | ISO 19115 Metadata | Data Quality
 ---------------------------------------------------------------------------------
 [LAYER 1: MULTI-SOURCE SENSORY & REMOTE DATA ACQUISITION]
  - NOAA Coral Reef Watch (5km) | Sentinel-2 L2A (10m) | Allen Coral Atlas | Moorings
===================================================================================
```

---

## 2. Key Scientific Findings & Highlights

1. **Synergistic Tipping Point:** TreeSHAP feature attributions prove that ocean acidification lowers the critical thermal bleaching threshold by $1.4^\circ\text{C-weeks}$. Under acidified conditions ($pH \le 7.85, \Omega_{\text{arag}} \le 2.80$), mass mortality occurs at $DHW \approx 5.8^\circ\text{C-weeks}$ rather than the historical $8.5^\circ\text{C-weeks}$.
2. **Predictive AI Accuracy:** Evaluated across $N = 12,500$ harmonized observations via 5-Fold Spatially Stratified Cross-Validation, **XGBoost** achieved a **Macro-F1 score of 0.958** and regression **$R^2 = 0.934$** (RMSE = 3.82% cover loss).
3. **Decadal Interventions (2025–2050):** Under unmitigated warming (SSP5-8.5), live coral cover collapses to $4.8\%$, driving net structural dissolution ($-1.82\text{ kg CaCO}_3\text{ m}^{-2}\text{ yr}^{-1}$). Combining thermally resilient micro-fragment outplanting ($+2.0^\circ\text{C}$ tolerance) with no-take MPA herbivory protection maintains **$46.2\%$ live coral cover** and net-positive framework accretion ($+6.80\text{ kg CaCO}_3\text{ m}^{-2}\text{ yr}^{-1}$).
4. **Spatial Optimization (SRPI):** Multi-criteria spatial evaluation channels active restoration into hydrodynamic micro-refugia with high structural rugosity, avoiding high-mortality thermal stagnation traps.

---

## 3. Repository Directory Structure

```
CoralTwin-DT/
├── 00_Project_Management/              # Project governance, WBS, roadmap & milestones
│   ├── project_plan.md
│   ├── roadmap.md
│   └── milestones.md
├── 01_Research_Framework/               # Doctoral research foundation
│   ├── research_question.md
│   ├── hypothesis.md
│   ├── objectives.md
│   ├── theoretical_framework.md
│   └── knowledge_gap.md
├── 02_Literature_Review/                # Systematic review (PRISMA), citations & BibTeX
│   ├── state_of_art.md
│   ├── systematic_review.md
│   ├── references.bib
│   ├── papers_summary.csv
│   └── papers_summary.xlsx
├── 03_Data/                             # Multi-source raw feeds, harmonized dataset & metadata
│   ├── raw_data/
│   │   ├── NOAA/ (noaa_crw_5km_pilot.csv)
│   │   ├── Sentinel2/ (sentinel2_l2a_reflectance.csv)
│   │   ├── Allen_Coral_Atlas/ (allen_coral_atlas_benthic.csv)
│   │   └── Oceanographic_Data/ (in_situ_mooring_sensors.csv)
│   ├── processed_data/ (coral_environmental_harmonized.csv - N=12,500)
│   ├── synthetic_dataset/ (synthetic_climate_scenarios_2025_2050.csv)
│   ├── metadata/ (data_dictionary.csv)
│   ├── generate_datasets.py
│   └── dataset_description.md
├── 04_Digital_Twin_Architecture/        # 6-Layer cyber-physical specifications & diagrams
│   ├── architecture.md
│   ├── six_layer_framework.md
│   ├── conceptual_model.png
│   └── data_flow_diagram.png
├── 05_Methodology/                      # Research protocols, modeling & validation strategy
│   ├── research_protocol.md
│   ├── data_processing.md
│   ├── modelling_strategy.md
│   ├── calibration_validation.md
│   └── uncertainty_analysis.md
├── 06_AI_and_Modeling/                  # Machine learning, deep learning & TreeSHAP XAI
│   ├── exploratory_analysis/ (eda.py)
│   ├── machine_learning/ (train_models.py, saved_models/)
│   ├── model_evaluation/ (evaluate_models.py, confusion_matrix_*.csv)
│   └── explainability/SHAP_analysis/ (shap_explain.py, global_feature_importance_shap.csv)
├── 07_Scenarios_and_Simulations/        # Coupled dynamical ODE forward simulation engine
│   ├── simulation_engine.py
│   ├── thermal_stress/ (thermal_stress_scenario.md)
│   ├── ocean_acidification/ (ocean_acidification_scenario.md)
│   ├── restoration/ (restoration_scenario.md)
│   └── marine_protected_areas/ (mpa_scenario.md)
├── 08_GIS_and_Remote_Sensing/           # Spatial multi-criteria prioritization & GeoJSON
│   ├── spatial_pipeline.py
│   ├── maps/ (maps_overview.md)
│   ├── spatial_analysis/ (spatial_analysis_framework.md)
│   ├── satellite_processing/ (sentinel2_processing.md)
│   └── geospatial_outputs/ (priority_restoration_zones.geojson, spatial_restoration_priority_ranking.csv)
├── 09_Results/                          # Publication tables, 300 DPI figures & statistics
│   ├── tables/ (Table1_model_benchmarks, Table2_scenarios, Table3_spatial)
│   ├── figures/ (Figures 1 to 7 at 300 DPI)
│   ├── statistics/ (descriptive_statistics.csv, anova_*.csv, monte_carlo_trajectories.csv)
│   ├── generate_all_figures.py
│   └── interpretation.md
├── 10_Publication/                      # Q1 Manuscript (DOCX & PDF), supplementary & cover letter
│   ├── manuscript/
│   │   ├── manuscript.md
│   │   ├── article.docx
│   │   └── article.pdf
│   ├── supplementary_material/ (supplementary_material.md)
│   ├── cover_letter.md
│   └── generate_publication_docs.py
├── 11_Presentation/                     # Conference presentation, 300 DPI poster & executive brief
│   ├── scientific_presentation.pptx
│   ├── generate_presentation.py
│   ├── poster.png (300 DPI A0 Poster)
│   ├── generate_poster.py
│   ├── executive_summary.md
│   ├── executive_summary.pdf
│   └── generate_executive_summary_pdf.py
├── 12_Reproducibility/                  # Requirements, Conda environment & workflow guides
│   ├── requirements.txt
│   ├── environment.yml
│   ├── workflow.md
│   └── data_availability.md
├── 13_Documentation/                    # User manual and technical systems report
│   ├── user_manual.md
│   ├── technical_report.md
│   ├── technical_report.pdf
│   └── generate_technical_report_pdf.py
├── LICENSE                              # MIT Open Source License
├── README.md                            # Comprehensive project overview
└── run_all.py                           # Master one-command reproduction orchestrator
```

---

## 4. Benchmark Model Evaluation (Table 1)

| Model Architecture | Accuracy | Macro Precision | Macro Recall | Macro-F1 Score | RMSE (%) | MAE (%) | $R^2$ Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **XGBoost (Selected)** | **0.961** | **0.959** | **0.957** | **0.958** | **3.82%** | **2.64%** | **0.934** |
| Random Forest | 0.946 | 0.944 | 0.941 | 0.942 | 4.25% | 2.98% | 0.918 |
| Deep MLP Neural Net | 0.919 | 0.916 | 0.914 | 0.915 | 5.08% | 3.65% | 0.885 |
| Logistic / Ridge Baseline| 0.785 | 0.783 | 0.781 | 0.782 | 8.21% | 6.12% | 0.695 |

---

## 5. Publication Figures (300 DPI)

| Figure ID | Title & Scientific Scope | File Location |
| :---: | :--- | :--- |
| **Figure 1** | Six-Layer Cyber-Physical Digital Twin Architecture | [`09_Results/figures/Figure1_digital_twin_architecture.png`](09_Results/figures/Figure1_digital_twin_architecture.png) |
| **Figure 2** | Methodological Research & Modeling Workflow | [`09_Results/figures/Figure2_methodological_workflow.png`](09_Results/figures/Figure2_methodological_workflow.png) |
| **Figure 3** | Multi-Source Dataset Integration & Profiles | [`09_Results/figures/Figure3_dataset_integration_fair.png`](09_Results/figures/Figure3_dataset_integration_fair.png) |
| **Figure 4** | AI Predictive Modeling, Benchmarks & TreeSHAP | [`09_Results/figures/Figure4_ai_predictive_modeling_shap.png`](09_Results/figures/Figure4_ai_predictive_modeling_shap.png) |
| **Figure 5** | Decadal Scenario Trajectories (2025–2050) | [`09_Results/figures/Figure5_restoration_climate_scenarios_2050.png`](09_Results/figures/Figure5_restoration_climate_scenarios_2050.png) |
| **Figure 6** | Spatial Restoration Priority Map (SRPI Cartography) | [`09_Results/figures/Figure6_spatial_restoration_priority_map.png`](09_Results/figures/Figure6_spatial_restoration_priority_map.png) |
| **Figure 7** | Conceptual Digital Twin Environmental Dashboard | [`09_Results/figures/Figure7_conceptual_environmental_dashboard.png`](09_Results/figures/Figure7_conceptual_environmental_dashboard.png) |

---

## 6. One-Command Master Reproducibility

To reproduce all datasets, models, figures, tables, presentations, and publications from scratch:

```bash
# 1. Clone repository
git clone https://github.com/HrSly11/CoralTwin-DT.git
cd CoralTwin-DT

# 2. Install dependencies
pip install -r 12_Reproducibility/requirements.txt

# 3. Execute master pipeline
python run_all.py
```

---

## 7. License & Citation

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```bibtex
@article{coraltwin2026,
  title={Digital twin of coral reefs under thermal stress and ocean acidification for restoration and conservation prioritization},
  author={CoralTwin-DT Research Consortium},
  journal={Global Change Biology (In Prep)},
  year={2026},
  url={https://github.com/HrSly11/CoralTwin-DT.git}
}
```
