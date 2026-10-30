"""
CoralTwin-DT: Standalone Feature Ablation & Reverse Target Leakage Audit
=======================================================================
Direct reproduction script for Table 5 and Figure 3D in the manuscript.

Evaluates predictive performance across 5 feature regimes under 5-fold Spatial
Block Cross-Validation (25 km buffer) to audit target leakage and evaluate proxy degradation:

1. Regime 0 (16 features - Full Unconstrained / Leaked):
   - 10 clean environmental: Depth, SST, SST_Anomaly, DHW, pH, Salinity, DO, Omega, Turbidity, PAR
   - 2 auxiliary satellite: HotSpot_degC, Kd_490_m_inv
   - 4 post-target benthic: Shannon_Diversity_H, Structural_Rugosity, Live_Coral_Cover_Pct, Macroalgae_Cover_Pct
   Result: R² = 0.9994, RMSE = 0.395 % (Spurious target leakage via Shannon_Diversity_H).

2. Regime 0b (10 features - Legacy Leaked):
   - 8 environmental + 2 benthic (Structural_Rugosity, Live_Coral_Cover_Pct)
   Result: R² = 0.8305, RMSE = 6.460 %.

3. Regime 1 (10 features - Clean Canonical Emulation):
   - 10 clean environmental variables free of target leakage.
   Result: R² = 0.9336, RMSE = 4.044 % (Legitimate surrogate model benchmark).

4. Regime 2 (6 features - Ablated / No Direct Thermodynamic Forcings):
   - Depth, SST, SST_Anomaly, pH, Salinity, DO (excludes DHW, Omega, PAR, Turbidity).
   Result: R² = 0.8487, RMSE = 6.104 %.

5. Regime 3 (2 features - Strict Minimal Baseline):
   - Depth, Salinity only.
   Result: R² = -0.0269, RMSE = 15.901 % (Failure regime proving necessity of thermodynamic proxies).

Author: CoralTwin-DT Research Consortium
License: MIT
"""

import os
import sys
import argparse
import time
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    r2_score,
    mean_squared_error,
    mean_absolute_error,
)

# Setup paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "05_Methodology"))

from spatial_cv import get_spatial_cv_splits

DATA_PATH = os.path.join(PROJECT_ROOT, "03_Data", "final_dataset.csv")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# 5 Feature Regimes exactly as defined in Table 5
FEATURE_REGIMES = {
    "Regime_0_Leaked_16": {
        "display_name": "Con fuga (auditado)",
        "features": [
            "Depth_m", "SST_degC", "SST_Anomaly_degC", "HotSpot_degC", "DHW_degC_weeks",
            "pH_total", "Salinity_PSU", "Dissolved_Oxygen_mg_L", "Aragonite_Saturation_Omega",
            "Turbidity_NTU", "Kd_490_m_inv", "PAR_umol_m2_s",
            "Structural_Rugosity", "Live_Coral_Cover_Pct", "Macroalgae_Cover_Pct", "Shannon_Diversity_H"
        ],
        "description": "10 ambientales + 2 satelitales (HotSpot, Kd_490) + 4 bentonicas post-objetivo"
    },
    "Regime_0b_Legacy_Leaked_10": {
        "display_name": "Conjunto alternativo",
        "features": [
            "Depth_m", "SST_degC", "SST_Anomaly_degC", "DHW_degC_weeks",
            "pH_total", "Aragonite_Saturation_Omega", "Turbidity_NTU",
            "PAR_umol_m2_s", "Structural_Rugosity", "Live_Coral_Cover_Pct"
        ],
        "description": "Ambientales mas rugosidad y cobertura viva (en lugar de salinidad y oxigeno)"
    },
    "Regime_1_Clean_Emulation_10": {
        "display_name": "Canonico (Limpio)",
        "features": [
            "Depth_m", "SST_degC", "SST_Anomaly_degC", "DHW_degC_weeks",
            "pH_total", "Salinity_PSU", "Dissolved_Oxygen_mg_L",
            "Aragonite_Saturation_Omega", "Turbidity_NTU", "PAR_umol_m2_s"
        ],
        "description": "SST, anomalia SST, DHW, pH, salinidad, oxigeno disuelto, Omega, turbidez, PAR, profundidad"
    },
    "Regime_2_Ablated_No_Direct_Inputs_6": {
        "display_name": "Sin forzantes termicos",
        "features": [
            "Depth_m", "SST_degC", "SST_Anomaly_degC",
            "pH_total", "Salinity_PSU", "Dissolved_Oxygen_mg_L"
        ],
        "description": "Profundidad, SST, anomalia SST, pH, salinidad, oxigeno (sin DHW, Omega, PAR, turbidez)"
    },
    "Regime_3_Ablated_Strict_No_Proxies_2": {
        "display_name": "Linea base minima",
        "features": [
            "Depth_m", "Salinity_PSU"
        ],
        "description": "Profundidad y salinidad unicamente"
    }
}


def run_ablation(model_name: str = "xgboost", seed: int = 42, save_csv: bool = True):
    print("=" * 80)
    print("CoralTwin-DT: Reverse Target Leakage & Feature Ablation Reproduction")
    print(f"Model: {model_name.upper()} | Primary Seed: {seed} | Spatial CV: 5-Fold Block (25 km)")
    print("=" * 80)

    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    splits = get_spatial_cv_splits(df)

    y_c3 = df["Bleaching_Risk"].map({"Low": 0, "Medium": 1, "High": 2}).values
    y_r = df["Coral_Cover_Loss_Pct"].values.astype(np.float32)

    results = []

    for reg_key, reg_info in FEATURE_REGIMES.items():
        feats = reg_info["features"]
        n_feats = len(feats)
        X = df[feats].values.astype(np.float32)

        oof_pred_c = np.zeros(len(df), dtype=int)
        oof_pred_r = np.zeros(len(df), dtype=np.float32)

        t0 = time.time()
        for fold_id, tr_idx, te_idx, _, _ in splits:
            X_tr, X_te = X[tr_idx], X[te_idx]
            yc_tr, yc_te = y_c3[tr_idx], y_c3[te_idx]
            yr_tr, yr_te = y_r[tr_idx], y_r[te_idx]

            if model_name.lower() == "xgboost":
                clf = xgb.XGBClassifier(
                    n_estimators=350, max_depth=6, learning_rate=0.05,
                    subsample=0.80, colsample_bytree=0.80, min_child_weight=3,
                    gamma=0.1, random_state=seed, eval_metric="mlogloss", n_jobs=4
                )
                reg = xgb.XGBRegressor(
                    n_estimators=350, max_depth=6, learning_rate=0.05,
                    subsample=0.80, colsample_bytree=0.80, min_child_weight=3,
                    gamma=0.1, random_state=seed, n_jobs=4
                )
            elif model_name.lower() in ["random_forest", "rf"]:
                clf = RandomForestClassifier(
                    n_estimators=200, max_depth=12, min_samples_split=4, min_samples_leaf=2,
                    random_state=seed, n_jobs=4
                )
                reg = RandomForestRegressor(
                    n_estimators=200, max_depth=12, min_samples_split=4, min_samples_leaf=2,
                    random_state=seed, n_jobs=4
                )
            else:
                raise ValueError(f"Unsupported model: {model_name}")

            clf.fit(X_tr, yc_tr)
            reg.fit(X_tr, yr_tr)

            oof_pred_c[te_idx] = clf.predict(X_te)
            oof_pred_r[te_idx] = reg.predict(X_te)

        elapsed = time.time() - t0

        acc = float(accuracy_score(y_c3, oof_pred_c)) * 100.0
        bal_acc = float(balanced_accuracy_score(y_c3, oof_pred_c)) * 100.0
        f1_mac = float(f1_score(y_c3, oof_pred_c, average="macro", zero_division=0))
        r2 = float(r2_score(y_r, oof_pred_r))
        rmse = float(np.sqrt(mean_squared_error(y_r, oof_pred_r)))
        mae = float(mean_absolute_error(y_r, oof_pred_r))

        results.append({
            "regime_key": reg_key,
            "display_name": reg_info["display_name"],
            "n_vars": n_feats,
            "description": reg_info["description"],
            "features_list": ";".join(feats),
            "model": model_name,
            "accuracy_pct": acc,
            "balanced_acc_pct": bal_acc,
            "macro_f1": f1_mac,
            "r2": r2,
            "rmse_pct": rmse,
            "mae_pct": mae,
            "elapsed_sec": elapsed
        })
        print(f"[{reg_key}] {n_feats:2d} vars -> Acc: {acc:6.2f}% | F1: {f1_mac:.4f} | R2: {r2:7.4f} | RMSE: {rmse:6.3f}% ({elapsed:4.1f}s)")

    # Print Table 5 Reproduction
    print("\n" + "=" * 92)
    print("TABLA 5 DEL MANUSCRITO: EVALUACION DE FUGA DE OBJETIVO Y ABLACION DE VARIABLES")
    print("=" * 92)
    print(f"{'Regimen de Entrada':<25} | {'N. Vars':<7} | {'Exactitud (%)':<13} | {'Macro-F1':<8} | {'R2 Emulacion':<12} | {'RMSE (%)':<8}")
    print("-" * 92)
    for r in results:
        print(f"{r['display_name']:<25} | {r['n_vars']:<7} | {r['accuracy_pct']:13.2f} | {r['macro_f1']:8.4f} | {r['r2']:12.4f} | {r['rmse_pct']:8.3f}")
    print("=" * 92)

    if save_csv:
        out_csv = os.path.join(RESULTS_DIR, "standalone_ablation_reproduction.csv")
        pd.DataFrame(results).to_csv(out_csv, index=False)
        print(f"\nReproduction metrics saved to: {out_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CoralTwin-DT Feature Ablation & Leakage Reproduction")
    parser.add_argument("--model", type=str, default="xgboost", choices=["xgboost", "rf", "random_forest"],
                        help="Model architecture to run (default: xgboost)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    args = parser.parse_args()

    run_ablation(model_name=args.model, seed=args.seed)
