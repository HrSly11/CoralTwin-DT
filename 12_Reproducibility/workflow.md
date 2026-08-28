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
| **1** | `python 03_Data/generate_datasets.py` | `03_Data/processed_data/coral_environmental_harmonized.csv` (N=12,500), raw feeds, and PRISMA literature matrix. |
| **2** | `python 06_AI_and_Modeling/exploratory_analysis/eda.py` | Descriptive statistics, skewness, correlation matrices, and ANOVA in `09_Results/statistics/`. |
| **3** | `python 06_AI_and_Modeling/machine_learning/train_models.py` | Saved models (XGBoost, RF, MLP) and 5-fold cross-validation out-of-fold predictions. |
| **4** | `python 06_AI_and_Modeling/model_evaluation/evaluate_models.py` | Benchmark metrics, confusion matrices, and `Table 1` in `09_Results/tables/`. |
| **5** | `python 06_AI_and_Modeling/explainability/SHAP_analysis/shap_explain.py` | TreeSHAP feature importance rankings, interaction terms, and attribution matrices. |
| **6** | `python 07_Scenarios_and_Simulations/simulation_engine.py` | 2025–2050 Monte Carlo ODE projections (N=5,000) and `Table 2` in `09_Results/tables/`. |
| **7** | `python 08_GIS_and_Remote_Sensing/spatial_pipeline.py` | Spatial Restoration Priority Index (SRPI), `Table 3`, and GeoJSON vector layer. |
| **8** | `python 09_Results/generate_all_figures.py` | Figures 1 through 7 rendered at 300 DPI in `09_Results/figures/`. |
| **9** | `python 10_Publication/generate_publication_docs.py` | Formatted `article.docx` and `article.pdf` in `10_Publication/manuscript/`. |
| **10**| `python 11_Presentation/generate_presentation.py` | 8-slide PPTX deck `scientific_presentation.pptx` in `11_Presentation/`. |
| **11**| `python 11_Presentation/generate_poster.py` | 300 DPI scientific poster `poster.png` in `11_Presentation/`. |
| **12**| `python 11_Presentation/generate_executive_summary_pdf.py` | Executive policy brief `executive_summary.pdf` in `11_Presentation/`. |
