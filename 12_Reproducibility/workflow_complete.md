# Complete Computational Workflow & Pipeline Architecture: CoralTwin-DT

**Document Purpose:** Complete directed acyclic graph (DAG) and step-by-step mathematical description of all 13 computational pipeline stages.  
**Repository:** https://github.com/HrSly11/CoralTwin-DT.git  
**Master Orchestration Script:** `run_all.py`  

---

## 1. Directed Acyclic Graph (DAG) of Pipeline Execution

```
[ STAGE 1: Data Generation & Harmonization ]
  03_Data/generate_datasets.py -> 03_Data/build_final_dataset.py
                │
                ├───────────────────────────────────────────┐
                ▼                                           ▼
[ STAGE 2: Exploratory Data Analysis ]       [ STAGE 3: Machine Learning Training ]
  06_AI_and_Modeling/eda.py                    06_AI_and_Modeling/train_models.py
                │                                           │
                ├───────────────────────────────────────────┤
                ▼                                           ▼
[ STAGE 4: Model Evaluation Benchmarks ]     [ STAGE 5: Comparative AI Benchmark ]
  06_AI_and_Modeling/evaluate_models.py        06_AI_and_Modeling/compare_rf_xgb_lstm.py
                │                                           │
                └─────────────────────┬─────────────────────┘
                                      ▼
[ STAGE 6: TreeSHAP Game-Theoretic Explainability ]
  06_AI_and_Modeling/shap_explain.py
                                      │
                                      ▼
[ STAGE 7: Forward Decadal Dynamical Simulation (2025–2050) ]
  07_Scenarios_and_Simulations/simulation_engine.py
                                      │
                                      ▼
[ STAGE 8: GIS Spatial Prioritization & GeoJSON Generation ]
  08_GIS_and_Remote_Sensing/spatial_pipeline.py
                                      │
                                      ▼
[ STAGE 9: High-Resolution Publication Figure Rendering (300 DPI) ]
  09_Results/generate_all_figures.py
                                      │
                                      ▼
[ STAGE 10: Advanced Architecture & Closed-Loop Schematics ]
  04_Digital_Twin_Architecture/generate_digital_twin_diagram.py
                                      │
                                      ▼
[ STAGE 11: Scientific Presentation & Poster Generation ]
  11_Presentation/generate_presentation.py -> generate_poster.py
                                      │
                                      ▼
[ STAGE 12: Technical Reports & Executive Summary PDFs ]
  11_Presentation/generate_executive_summary_pdf.py -> 13_Documentation/generate_technical_report_pdf.py
                                      │
                                      ▼
[ STAGE 13: Final Scopus Q1 Manuscript & Graphical Abstract Compilation ]
  10_Publication/final_manuscript/build_final_manuscript_docs.py
```

---

## 2. Detailed Execution Matrix of the 13 Pipeline Stages

| Stage # | Pipeline Script | Primary Inputs | Primary Generated Outputs | Execution Time (approx) |
| :---: | :--- | :--- | :--- | :---: |
| **01** | `03_Data/generate_datasets.py` & `build_final_dataset.py` | Climatological MMM, NOAA CRW SST baselines | `03_Data/final_dataset.csv`, `data_dictionary_final.csv`, `dataset_validation_report.md` | ~8.5 s |
| **02** | `06_AI_and_Modeling/exploratory_analysis/eda.py` | `03_Data/final_dataset.csv` | `09_Results/statistics/descriptive_statistics.csv`, `pearson_correlation_matrix.csv` | ~4.2 s |
| **03** | `06_AI_and_Modeling/machine_learning/train_models.py` | Harmonized training splits | `saved_models/xgboost_classifier.json`, `random_forest.joblib`, `mlp_classifier.joblib` | ~16.8 s |
| **04** | `06_AI_and_Modeling/model_evaluation/evaluate_models.py` | Serialized AI models | `confusion_matrix_*.png`, `model_benchmark_metrics.csv`, `cross_validation_oof_predictions.csv` | ~6.5 s |
| **05** | `06_AI_and_Modeling/compare_rf_xgb_lstm.py` | Final dataset sequences | `06_AI_and_Modeling/model_comparison_report.md`, `model_comparison_charts.png` | ~24.5 s |
| **06** | `06_AI_and_Modeling/explainability/SHAP_analysis/shap_explain.py` | Serialized XGBoost model | `09_Results/statistics/global_feature_importance_shap.csv`, `shap_summary_plot.png` | ~11.2 s |
| **07** | `07_Scenarios_and_Simulations/simulation_engine.py` | Coupled Mumby ODE parameters | `monte_carlo_trajectories_2025_2050.csv`, `Table2_decadal_scenario_projections.csv` | ~7.8 s |
| **08** | `08_GIS_and_Remote_Sensing/spatial_pipeline.py` | 30 Station coordinates | `priority_restoration_zones.geojson`, `spatial_restoration_priority_ranking.csv` | ~3.4 s |
| **09** | `09_Results/generate_all_figures.py` | Statistics & scenario tables | `09_Results/figures/Figure1_*.png` through `Figure7_*.png` (300 DPI) | ~8.1 s |
| **10** | `04_Digital_Twin_Architecture/generate_digital_twin_diagram.py` | Architecture specifications | `04_Digital_Twin_Architecture/digital_twin_final_diagram.png` (300 DPI) | ~2.5 s |
| **11** | `11_Presentation/generate_presentation.py` & `generate_poster.py` | High-level synthesis | `scientific_presentation.pptx` (8 slides), `poster.png` (300 DPI A0) | ~4.8 s |
| **12** | `11_Presentation/generate_executive_summary_pdf.py` & `13_Documentation/generate_technical_report_pdf.py` | Executive & Technical texts | `executive_summary.pdf`, `technical_report.pdf` | ~3.2 s |
| **13** | `10_Publication/final_manuscript/build_final_manuscript_docs.py` & `generate_graphical_abstract.py` | Final manuscript markdown | `manuscript_q1.docx`, `manuscript_q1.pdf`, `graphical_abstract.png` | ~2.5 s |
| **TOTAL** | **Master Run (`python run_all.py`)** | **All Modules** | **Complete 100% Verified Scientific Digital Twin Repository** | **~104.0 s** |
