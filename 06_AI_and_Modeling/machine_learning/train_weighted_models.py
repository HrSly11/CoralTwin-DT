"""
06_AI_and_Modeling/machine_learning/train_weighted_models.py
============================================================
Implements Task 5:
Trains XGBoost and Random Forest with class weighting (class_weight='balanced'
and sample_weight=compute_sample_weight('balanced', y_tr)) under the identical
5-fold spatial block cross-validation (25 km buffer) across all 5 seeds (17, 42, 73, 108, 256).

Computes and compares against the unweighted canonical baseline:
- Overall Accuracy
- Balanced Accuracy
- Macro-F1
- Per-class Recall (Low, Medium, High)
- Per-class PR-AUC (Low, Medium, High)
- 1,000-iteration bootstrap 95% confidence intervals.
Outputs:
- `results/class_weighting_comparison_table6.csv`
- `results/class_weighting_summary.json`
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    precision_recall_curve,
    auc,
)
import xgboost as xgb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "05_Methodology"))

from spatial_cv import get_spatial_cv_splits

DATA_PATH = os.path.join(PROJECT_ROOT, "03_Data", "final_dataset.csv")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

SEEDS = [17, 42, 73, 108, 256]
PRIMARY_SEED = 42

CLEAN_10_FEATURES = [
    "Depth_m", "SST_degC", "SST_Anomaly_degC", "DHW_degC_weeks",
    "pH_total", "Salinity_PSU", "Dissolved_Oxygen_mg_L",
    "Aragonite_Saturation_Omega", "Turbidity_NTU", "PAR_umol_m2_s",
]


def bootstrap_ci(metric_fn, y_true, y_pred, n_boot: int = 1000, seed: int = 42):
    rng = np.random.default_rng(seed)
    n = len(y_true)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        v = metric_fn(y_true[idx], y_pred[idx])
        vals.append(v)
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def compute_pr_auc_per_class(y_true, probs):
    n_classes = probs.shape[1]
    pr_aucs = []
    for c in range(n_classes):
        y_bin = (y_true == c).astype(int)
        if y_bin.sum() == 0:
            pr_aucs.append(0.0)
            continue
        p, r, _ = precision_recall_curve(y_bin, probs[:, c])
        pr_aucs.append(float(auc(r, p)))
    return pr_aucs


def main():
    print("=" * 70)
    print("TASK 5: Retraining XGBoost & Random Forest with Class Weighting")
    print("=" * 70)

    df = pd.read_csv(DATA_PATH)
    splits = get_spatial_cv_splits(df)

    X_raw = df[CLEAN_10_FEATURES].values.astype(np.float32)
    label_map = {"Low": 0, "Medium": 1, "High": 2}
    class_names = ["Low", "Medium", "High"]
    y_true = df["Bleaching_Risk"].map(label_map).values
    n_samples = len(df)

    models_config = ["XGBoost", "Random_Forest"]

    # Store multi-seed OOF predictions for unweighted vs weighted
    # {model: {"unweighted": {seed: (preds, probs)}, "weighted": {seed: (preds, probs)}}}
    oof_results = {m: {"unweighted": {}, "weighted": {}} for m in models_config}

    for seed in SEEDS:
        print(f"\n--- Running Seed {seed} ---")
        for fold_id, train_idx, test_idx, _, _ in splits:
            X_tr, X_te = X_raw[train_idx], X_raw[test_idx]
            y_tr, y_te = y_true[train_idx], y_true[test_idx]

            # 1. XGBoost Unweighted
            xgb_unw = xgb.XGBClassifier(
                n_estimators=350, max_depth=6, learning_rate=0.05,
                subsample=0.80, colsample_bytree=0.80, min_child_weight=3, gamma=0.1,
                random_state=seed, eval_metric="mlogloss", n_jobs=4,
            )
            xgb_unw.fit(X_tr, y_tr)
            if seed not in oof_results["XGBoost"]["unweighted"]:
                oof_results["XGBoost"]["unweighted"][seed] = (np.zeros(n_samples, dtype=int), np.zeros((n_samples, 3), dtype=np.float32))
            oof_results["XGBoost"]["unweighted"][seed][0][test_idx] = xgb_unw.predict(X_te)
            oof_results["XGBoost"]["unweighted"][seed][1][test_idx] = xgb_unw.predict_proba(X_te)

            # 2. XGBoost Weighted (using compute_sample_weight('balanced', y_tr))
            sample_weights = compute_sample_weight("balanced", y_tr)
            xgb_w = xgb.XGBClassifier(
                n_estimators=350, max_depth=6, learning_rate=0.05,
                subsample=0.80, colsample_bytree=0.80, min_child_weight=3, gamma=0.1,
                random_state=seed, eval_metric="mlogloss", n_jobs=4,
            )
            xgb_w.fit(X_tr, y_tr, sample_weight=sample_weights)
            if seed not in oof_results["XGBoost"]["weighted"]:
                oof_results["XGBoost"]["weighted"][seed] = (np.zeros(n_samples, dtype=int), np.zeros((n_samples, 3), dtype=np.float32))
            oof_results["XGBoost"]["weighted"][seed][0][test_idx] = xgb_w.predict(X_te)
            oof_results["XGBoost"]["weighted"][seed][1][test_idx] = xgb_w.predict_proba(X_te)

            # 3. Random Forest Unweighted
            rf_unw = RandomForestClassifier(
                n_estimators=200, max_depth=12, min_samples_split=4, min_samples_leaf=2,
                random_state=seed, n_jobs=4,
            )
            rf_unw.fit(X_tr, y_tr)
            if seed not in oof_results["Random_Forest"]["unweighted"]:
                oof_results["Random_Forest"]["unweighted"][seed] = (np.zeros(n_samples, dtype=int), np.zeros((n_samples, 3), dtype=np.float32))
            oof_results["Random_Forest"]["unweighted"][seed][0][test_idx] = rf_unw.predict(X_te)
            oof_results["Random_Forest"]["unweighted"][seed][1][test_idx] = rf_unw.predict_proba(X_te)

            # 4. Random Forest Weighted (class_weight='balanced')
            rf_w = RandomForestClassifier(
                n_estimators=200, max_depth=12, min_samples_split=4, min_samples_leaf=2,
                class_weight="balanced", random_state=seed, n_jobs=4,
            )
            rf_w.fit(X_tr, y_tr)
            if seed not in oof_results["Random_Forest"]["weighted"]:
                oof_results["Random_Forest"]["weighted"][seed] = (np.zeros(n_samples, dtype=int), np.zeros((n_samples, 3), dtype=np.float32))
            oof_results["Random_Forest"]["weighted"][seed][0][test_idx] = rf_w.predict(X_te)
            oof_results["Random_Forest"]["weighted"][seed][1][test_idx] = rf_w.predict_proba(X_te)

    # Compute comprehensive performance comparison table across the 5 seeds
    table_rows = []

    for m in models_config:
        for mode in ["unweighted", "weighted"]:
            seed_accs = []
            seed_bal_accs = []
            seed_f1s = []
            seed_rec_low = []
            seed_rec_med = []
            seed_rec_high = []
            seed_prauc_low = []
            seed_prauc_med = []
            seed_prauc_high = []

            for seed in SEEDS:
                preds, probs = oof_results[m][mode][seed]
                seed_accs.append(accuracy_score(y_true, preds))
                seed_bal_accs.append(balanced_accuracy_score(y_true, preds))
                seed_f1s.append(f1_score(y_true, preds, average="macro", zero_division=0))

                recs = recall_score(y_true, preds, average=None, zero_division=0)
                seed_rec_low.append(recs[0])
                seed_rec_med.append(recs[1])
                seed_rec_high.append(recs[2])

                praucs = compute_pr_auc_per_class(y_true, probs)
                seed_prauc_low.append(praucs[0])
                seed_prauc_med.append(praucs[1])
                seed_prauc_high.append(praucs[2])

            # Primary seed (42) predictions for bootstrap CIs
            prim_preds, prim_probs = oof_results[m][mode][PRIMARY_SEED]

            acc_ci = bootstrap_ci(accuracy_score, y_true, prim_preds)
            bal_ci = bootstrap_ci(balanced_accuracy_score, y_true, prim_preds)
            f1_ci = bootstrap_ci(lambda yt, yp: f1_score(yt, yp, average="macro", zero_division=0), y_true, prim_preds)
            rec_med_ci = bootstrap_ci(lambda yt, yp: recall_score(yt, yp, average=None, zero_division=0)[1], y_true, prim_preds)

            table_rows.append({
                "Model": m,
                "Weighting_Mode": "Ponderado (Balanced)" if mode == "weighted" else "Sin ponderar (Canónico)",
                "Overall_Accuracy": round(float(np.mean(seed_accs)) * 100.0, 2),
                "Overall_Accuracy_CI95": f"[{acc_ci[0]*100:.2f}%, {acc_ci[1]*100:.2f}%]",
                "Balanced_Accuracy": round(float(np.mean(seed_bal_accs)) * 100.0, 2),
                "Balanced_Accuracy_CI95": f"[{bal_ci[0]*100:.2f}%, {bal_ci[1]*100:.2f}%]",
                "Macro_F1": round(float(np.mean(seed_f1s)), 4),
                "Macro_F1_CI95": f"[{f1_ci[0]:.4f}, {f1_ci[1]:.4f}]",
                "Recall_Low": round(float(np.mean(seed_rec_low)) * 100.0, 2),
                "Recall_Medium": round(float(np.mean(seed_rec_med)) * 100.0, 2),
                "Recall_Medium_CI95": f"[{rec_med_ci[0]*100:.2f}%, {rec_med_ci[1]*100:.2f}%]",
                "Recall_High": round(float(np.mean(seed_rec_high)) * 100.0, 2),
                "PR_AUC_Low": round(float(np.mean(seed_prauc_low)), 4),
                "PR_AUC_Medium": round(float(np.mean(seed_prauc_med)), 4),
                "PR_AUC_High": round(float(np.mean(seed_prauc_high)), 4),
            })

    df_table = pd.DataFrame(table_rows)
    out_csv = os.path.join(RESULTS_DIR, "class_weighting_comparison_table6.csv")
    df_table.to_csv(out_csv, index=False)
    print(f"\nTable 6 (Class Weighting Comparison) saved to: {out_csv}")
    print(df_table.to_string())

    # Build summary dictionary for manuscript_numbers.json
    summary_dict = {
        "description": "Comparison of unweighted canonical models vs. class-weighted models (addressing severe minority class imbalance in Medium risk)",
        "protocol": "5-Fold Spatial Block CV (25 km buffer) x 5 Seeds (17, 42, 73, 108, 256)",
        "script_source": "06_AI_and_Modeling/machine_learning/train_weighted_models.py",
        "file_source": "results/class_weighting_comparison_table6.csv",
        "table_rows": table_rows,
    }
    with open(os.path.join(RESULTS_DIR, "class_weighting_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=2)

    print("\nTask 5 execution complete.")


if __name__ == "__main__":
    main()
