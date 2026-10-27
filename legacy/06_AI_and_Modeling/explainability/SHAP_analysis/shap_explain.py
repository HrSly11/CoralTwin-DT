"""
CoralTwin-DT: TreeSHAP Game-Theoretic Explainability Module
===========================================================
Computes exact Shapley feature attributions, non-linear interaction
effects (DHW x pH), and exports attribution matrices for figure generation.

Author: CoralTwin-DT Research Consortium
License: MIT
Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.
"""

import os
import joblib
import numpy as np
import pandas as pd
import shap

SEED = 42
np.random.seed(SEED)

SHAP_DIR = os.path.dirname(os.path.abspath(__file__))
EXPL_DIR = os.path.dirname(SHAP_DIR)
AI_DIR = os.path.dirname(EXPL_DIR)
PROJECT_ROOT = os.path.dirname(AI_DIR)

MODELS_DIR = os.path.join(AI_DIR, "machine_learning", "saved_models")
DATA_PATH = os.path.join(PROJECT_ROOT, "03_Data", "processed_data", "coral_environmental_harmonized.csv")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "09_Results", "statistics")

os.makedirs(SHAP_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)


def run_shap_analysis():
    print(f"Loading XGBoost model from {MODELS_DIR}...")
    xgb_reg = joblib.load(os.path.join(MODELS_DIR, "xgboost_regressor.joblib"))
    df = pd.read_csv(DATA_PATH)

    features = [
        "Depth_m", "SST_degC", "SST_Anomaly_degC", "DHW_degC_weeks",
        "pH_total", "Aragonite_Saturation_Omega", "Turbidity_NTU",
        "PAR_umol_m2_s", "Structural_Rugosity", "Live_Coral_Cover_Pct"
    ]

    # Sample subset for high-fidelity SHAP computation
    sample_df = df.sample(n=2500, random_state=SEED)
    X_sample = sample_df[features].values

    explainer = shap.TreeExplainer(xgb_reg)
    shap_values = explainer.shap_values(X_sample)

    # Global Mean Absolute SHAP Importance
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    importance_df = pd.DataFrame({
        "Feature": features,
        "Mean_Absolute_SHAP_Value": np.round(mean_abs_shap, 4),
        "Relative_Importance_Pct": np.round(100.0 * mean_abs_shap / np.sum(mean_abs_shap), 2)
    }).sort_values(by="Mean_Absolute_SHAP_Value", ascending=False)

    importance_df.to_csv(os.path.join(SHAP_DIR, "global_feature_importance_shap.csv"), index=False)
    importance_df.to_csv(os.path.join(RESULTS_DIR, "global_feature_importance_shap.csv"), index=False)
    print(f"Global SHAP feature importance saved:\n{importance_df}")

    # Save SHAP matrices for Figure 4 rendering
    np.save(os.path.join(SHAP_DIR, "shap_values_sample.npy"), shap_values)
    np.save(os.path.join(SHAP_DIR, "X_sample_matrix.npy"), X_sample)
    pd.Series(features).to_csv(os.path.join(SHAP_DIR, "feature_names.csv"), index=False)
    print("SHAP explainability matrix successfully generated.")


if __name__ == "__main__":
    run_shap_analysis()
