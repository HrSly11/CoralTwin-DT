# End-to-End Reproducibility Workflow: CoralTwin-DT

## 1. Quickstart & Environment Setup

### Using Conda:
```bash
conda env create -f 12_Reproducibility/environment.yml
conda activate coraltwin-dt
```

### Using Standard Python Virtual Environment:
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Unix/macOS:
source venv/bin/activate

pip install -r 12_Reproducibility/requirements.txt
```

---

## 2. One-Command Master Pipeline Execution

To reproduce all datasets, AI models, cross-validations, SHAP attributions, decadal forward simulations, GIS layers, 300 DPI figures, presentations, posters, and manuscripts in a single command:

```bash
python run_all.py
```

---

## 3. Modular Step-by-Step Execution Guide

| Step | Script Command | Output Artifacts Generated |
| :---: | :--- | :--- |
| **1** | `python 03_Data/generate_datasets.py` | `03_Data/final_dataset.csv` and `03_Data/processed_data/coral_environmental_harmonized.csv` ($N=15,000$, 30 stations, 36 cols). |
| **2** | `python 03_Data/audit_data_provenance.py` | `09_Results/audit/data_provenance.csv` and `09_Results/audit/data_provenance_summary.json` (100% synthetic verification). |
| **3** | `python 05_Methodology/spatial_cv.py` | `results/folds_assignment.csv` and `results/spatial_folds_diagram.png` (5-fold spatial CV, min distance $119.72\text{ km}$). |
| **4** | `python 06_AI_and_Modeling/exploratory_analysis/eda.py` | Descriptive statistics, correlation matrices, and ANOVA in `09_Results/statistics/`. |
| **5** | `python 06_AI_and_Modeling/machine_learning/train_models.py` | 5-regime leakage ablation and 5-seed $\times$ 5-fold benchmark (`results/model_benchmark_summary.csv`, `results/latency_protocol.json`). |
| **6** | `python 06_AI_and_Modeling/model_evaluation/evaluate_models.py` | Per-class metrics, calibration (`results/calibration/`), and paired Wilcoxon tests (`results/statistical_tests.csv`). |
| **7** | `python 06_AI_and_Modeling/explainability/SHAP_analysis/shap_explain.py` | Clean 10-feature interventional TreeSHAP (`results/shap_global_importance.csv`) and 2D PDP thresholds (`results/inflection_points.json`). |
| **8** | `python 07_Scenarios_and_Simulations/simulation_engine.py` | 2025–2050 RK4 coupled ODE projections ($\Delta t=0.05\text{ yr}$, $N=5,000$) in `results/scenario_2050_summary.csv` and `Table 2`. |
| **9** | `python 08_GIS_and_Remote_Sensing/spatial_pipeline.py` | 30-station Eq. 7 SRPI sensitivity analysis (`results/srpi_sensitivity.csv`), `Table 3`, and GeoJSON vector layers. |
| **10**| `python 09_Results/build_manuscript_numbers.py` | Master single-source-of-truth metrics file `results/manuscript_numbers.json`. |
| **11**| `python 09_Results/generate_all_figures.py` | Figures 1 through 7 rendered at 600 DPI in `09_Results/figures/`. |
| **12**| `python 10_Publication/generate_publication_docs.py` | Formatted `article.pdf` in `10_Publication/manuscript/` (preserving all `.docx` files intact). |
| **13**| `python 11_Presentation/generate_presentation.py` & `generate_poster.py` | 8-slide PPTX deck `scientific_presentation.pptx` and A0 poster `poster.png` in `11_Presentation/`. |
