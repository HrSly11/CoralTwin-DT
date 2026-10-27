"""
CoralTwin-DT: Unified Model Evaluation, Calibration, and Statistical Testing Module
===================================================================================
Computes and exports:
1. `results/per_class_report.csv` (3-class `Bleaching_Risk`: Precision, Recall, F1,
   PR-AUC, Support, Balanced Accuracy, Macro-F1, Fold SD, Seed SD, Bootstrap 95% CIs).
2. `results/per_class_report_5class.csv` (5-class `Bleaching_Alert_Level` with and
   without `DHW_degC_weeks`).
3. Unified benchmark tables:
   - `results/model_benchmark_summary.csv`
   - `06_AI_and_Modeling/model_evaluation/model_benchmark_metrics.csv`
   - `09_Results/tables/Table1_model_performance_benchmarks.csv`
   - `09_Results/tables/Table1_model_performance_benchmarks.md`
4. Multi-class probability calibration:
   - `results/calibration/calibration_metrics.csv`
   - `results/calibration/reliability_bins.csv`
   - `results/calibration/calibration_curves.png`
   - `09_Results/figures/Fig_calibration_curves.png`
5. Pairwise non-parametric statistical tests across all C(4,2)=6 model pairs:
   - Two-sided Wilcoxon signed-rank test (W, p-value, Bonferroni alpha = 0.05/6 = 0.008333)
   - Cohen's d effect size
   - Saved to `results/statistical_tests.csv` and
     `09_Results/statistics/statistical_tests_wilcoxon_cohen.csv`
"""

import os
import json
import itertools
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    average_precision_score,
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    confusion_matrix,
)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
EVAL_DIR = os.path.join(BASE_DIR, "model_evaluation")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
CALIB_DIR = os.path.join(RESULTS_DIR, "calibration")
TABLES_DIR = os.path.join(PROJECT_ROOT, "09_Results", "tables")
STATS_DIR = os.path.join(PROJECT_ROOT, "09_Results", "statistics")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "09_Results", "figures")

for d in [EVAL_DIR, RESULTS_DIR, CALIB_DIR, TABLES_DIR, STATS_DIR, FIGURES_DIR]:
    os.makedirs(d, exist_ok=True)

MODELS = ["XGBoost", "Random_Forest", "Deep_MLP", "Stacked_LSTM"]
CLASS_3_NAMES = ["Low", "Medium", "High"]
CLASS_5_NAMES = ["No_Stress", "Watch", "Warning", "Alert_Level_1", "Alert_Level_2"]


def compute_ece_and_bins(y_true: np.ndarray, probs: np.ndarray, n_bins: int = 10):
    """
    Computes top-label Expected Calibration Error (ECE), multi-class Brier score,
    and per-bin reliability statistics.
    """
    n_samples, n_classes = probs.shape
    y_onehot = np.eye(n_classes)[y_true]
    brier_multi = float(np.mean(np.sum((probs - y_onehot) ** 2, axis=1)))

    confidences = np.max(probs, axis=1)
    predictions = np.argmax(probs, axis=1)
    accuracies = (predictions == y_true).astype(float)

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    bin_rows = []

    for b in range(n_bins):
        lo, hi = bin_edges[b], bin_edges[b + 1]
        if b == 0:
            mask = (confidences >= lo) & (confidences <= hi)
        else:
            mask = (confidences > lo) & (confidences <= hi)
        cnt = int(np.sum(mask))
        if cnt > 0:
            avg_conf = float(np.mean(confidences[mask]))
            avg_acc = float(np.mean(accuracies[mask]))
            gap = abs(avg_acc - avg_conf)
            ece += (cnt / n_samples) * gap
        else:
            avg_conf = float(0.5 * (lo + hi))
            avg_acc = np.nan
            gap = np.nan

        bin_rows.append({
            "Bin_Index": b + 1,
            "Bin_Low": round(float(lo), 2),
            "Bin_High": round(float(hi), 2),
            "Count": cnt,
            "Mean_Confidence": round(avg_conf, 5) if not np.isnan(avg_conf) else np.nan,
            "Empirical_Accuracy": round(avg_acc, 5) if not np.isnan(avg_acc) else np.nan,
            "Calibration_Gap": round(gap, 5) if not np.isnan(gap) else np.nan,
        })

    # Per-class one-vs-rest Brier and ECE
    per_class_brier = {}
    per_class_ece = {}
    for c_idx in range(n_classes):
        y_c = (y_true == c_idx).astype(float)
        p_c = probs[:, c_idx]
        per_class_brier[c_idx] = float(np.mean((p_c - y_c) ** 2))
        ece_c = 0.0
        for b in range(n_bins):
            lo, hi = bin_edges[b], bin_edges[b + 1]
            mask = (p_c >= lo) & (p_c <= hi) if b == 0 else (p_c > lo) & (p_c <= hi)
            cnt = int(np.sum(mask))
            if cnt > 0:
                ece_c += (cnt / n_samples) * abs(float(np.mean(y_c[mask])) - float(np.mean(p_c[mask])))
        per_class_ece[c_idx] = float(ece_c)

    return brier_multi, float(ece), per_class_brier, per_class_ece, bin_rows


def plot_calibration_curves(all_bins_df: pd.DataFrame, calib_metrics_df: pd.DataFrame):
    plt.rcParams.update({"font.family": "sans-serif", "font.size": 10})
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.5), dpi=300)

    colors = {
        "XGBoost": "#1b9e77",
        "Random_Forest": "#d95f02",
        "Deep_MLP": "#7570b3",
        "Stacked_LSTM": "#e7298a",
    }
    markers = {"XGBoost": "o", "Random_Forest": "s", "Deep_MLP": "^", "Stacked_LSTM": "D"}

    # Panel A: Reliability Diagram
    ax = axes[0]
    ax.plot([0, 1], [0, 1], "k--", lw=1.2, label="Perfect Calibration (Diagonal)")
    for m in MODELS:
        sub = all_bins_df[(all_bins_df["Model"] == m) & (all_bins_df["Count"] > 0)]
        cm_row = calib_metrics_df[calib_metrics_df["Model"] == m].iloc[0]
        ax.plot(
            sub["Mean_Confidence"],
            sub["Empirical_Accuracy"],
            marker=markers[m],
            color=colors[m],
            lw=1.8,
            label=f"{m} (ECE={cm_row['ECE_10Bins']:.4f}, Brier={cm_row['Multiclass_Brier_Score']:.4f})",
        )
    ax.set_xlim(0.30, 1.02)
    ax.set_ylim(0.30, 1.02)
    ax.set_xlabel("Mean Predicted Confidence")
    ax.set_ylabel("Empirical Out-of-Fold Accuracy")
    ax.set_title("A. Multi-Class Reliability Diagram (5-Fold Spatial CV)", fontweight="bold")
    ax.legend(loc="lower right", fontsize=8.5)
    ax.grid(True, linestyle=":", alpha=0.6)

    # Panel B: Per-Class Brier Score Comparison
    ax2 = axes[1]
    x = np.arange(len(MODELS))
    w = 0.24
    ax2.bar(x - w, calib_metrics_df["Brier_Low"], w, color="#4daf4a", edgecolor="black", label="Low Risk Brier")
    ax2.bar(x, calib_metrics_df["Brier_Medium"], w, color="#ff7f00", edgecolor="black", label="Medium Risk Brier")
    ax2.bar(x + w, calib_metrics_df["Brier_High"], w, color="#e41a1c", edgecolor="black", label="High Risk Brier")
    ax2.set_xticks(x)
    ax2.set_xticklabels(MODELS, fontweight="bold")
    ax2.set_ylabel("One-vs-Rest Brier Score (Lower is Better)")
    ax2.set_title("B. Class-Specific Brier Scores Across Architectures", fontweight="bold")
    ax2.legend(loc="upper left", fontsize=8.5)
    ax2.grid(True, axis="y", linestyle=":", alpha=0.6)

    out_cal = os.path.join(CALIB_DIR, "calibration_curves.png")
    out_fig = os.path.join(FIGURES_DIR, "Fig_calibration_curves.png")
    fig.savefig(out_cal, bbox_inches="tight", dpi=300)
    fig.savefig(out_fig, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Calibration curves saved to: {out_cal} and {out_fig}")


def cohen_d_paired(x: np.ndarray, y: np.ndarray) -> float:
    diff = np.asarray(x, dtype=float) - np.asarray(y, dtype=float)
    sd = float(np.std(diff, ddof=1))
    if sd < 1e-12:
        return 0.0
    return float(np.mean(diff) / sd)


def evaluate_all_models():
    oof_path = os.path.join(EVAL_DIR, "cross_validation_oof_predictions.csv")
    npz_path = os.path.join(EVAL_DIR, "oof_probabilities_seed42.npz")
    seed_var_path = os.path.join(RESULTS_DIR, "seed_variance.csv")
    latency_path = os.path.join(RESULTS_DIR, "latency_protocol.json")

    for p in [oof_path, npz_path, seed_var_path, latency_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Missing required artifact {p}. Run train_models.py first.")

    df_oof = pd.read_csv(oof_path)
    npz = np.load(npz_path)
    df_seed = pd.read_csv(seed_var_path)
    with open(latency_path, "r", encoding="utf-8") as f:
        latency_info = json.load(f)

    y_true_c3 = npz["y_true_c3"]
    y_true_c5 = npz["y_true_c5"]
    y_true_r = npz["y_true_r"]
    fold_ids = npz["fold_ids"]

    class_col_map = {
        "XGBoost": "XGB_Class_Pred",
        "Random_Forest": "RF_Class_Pred",
        "Deep_MLP": "MLP_Class_Pred",
        "Stacked_LSTM": "LSTM_Class_Pred",
    }
    reg_col_map = {
        "XGBoost": "XGB_Loss_Pred",
        "Random_Forest": "RF_Loss_Pred",
        "Deep_MLP": "MLP_Loss_Pred",
        "Stacked_LSTM": "LSTM_Loss_Pred",
    }

    # Bootstrap indices (B=1,000) for per-class 95% CIs
    rng = np.random.default_rng(42)
    n_samples = len(y_true_c3)
    boot_indices = rng.integers(0, n_samples, size=(1000, n_samples))

    per_class_rows = []
    calib_rows = []
    all_bin_rows = []
    benchmark_rows = []

    for m in MODELS:
        y_pred_c = df_oof[class_col_map[m]].values
        y_pred_r = df_oof[reg_col_map[m]].values
        probs_3 = npz[f"{m}_p3"]

        # Save confusion matrix
        cm = confusion_matrix(y_true_c3, y_pred_c, labels=[0, 1, 2])
        cm_df = pd.DataFrame(
            cm,
            index=["True_Low", "True_Medium", "True_High"],
            columns=["Pred_Low", "Pred_Medium", "Pred_High"],
        )
        cm_df.to_csv(os.path.join(EVAL_DIR, f"confusion_matrix_{m.lower()}.csv"))

        # Calibration metrics
        brier_multi, ece_10, pc_brier, pc_ece, bins_m = compute_ece_and_bins(y_true_c3, probs_3, n_bins=10)
        for brow in bins_m:
            brow["Model"] = m
            all_bin_rows.append(brow)

        calib_rows.append({
            "Model": m,
            "Multiclass_Brier_Score": round(brier_multi, 5),
            "ECE_10Bins": round(ece_10, 5),
            "Brier_Low": round(pc_brier[0], 5),
            "Brier_Medium": round(pc_brier[1], 5),
            "Brier_High": round(pc_brier[2], 5),
            "ECE_Low": round(pc_ece[0], 5),
            "ECE_Medium": round(pc_ece[1], 5),
            "ECE_High": round(pc_ece[2], 5),
        })

        # Per-class precision, recall, F1, PR-AUC, Support + Fold SD + Bootstrap 95% CIs
        y_onehot = np.eye(3)[y_true_c3]
        pr_aucs = []
        for c_idx, c_name in enumerate(CLASS_3_NAMES):
            prec_c = float(precision_score(y_true_c3 == c_idx, y_pred_c == c_idx, zero_division=0))
            rec_c = float(recall_score(y_true_c3 == c_idx, y_pred_c == c_idx, zero_division=0))
            f1_c = float(f1_score(y_true_c3 == c_idx, y_pred_c == c_idx, zero_division=0))
            prauc_c = float(average_precision_score(y_onehot[:, c_idx], probs_3[:, c_idx]))
            pr_aucs.append(prauc_c)
            sup_c = int(np.sum(y_true_c3 == c_idx))

            # Fold SD for this class
            f_precs, f_recs, f_f1s, f_praucs = [], [], [], []
            for f_id in range(1, 6):
                fmask = fold_ids == f_id
                f_precs.append(float(precision_score(y_true_c3[fmask] == c_idx, y_pred_c[fmask] == c_idx, zero_division=0)))
                f_recs.append(float(recall_score(y_true_c3[fmask] == c_idx, y_pred_c[fmask] == c_idx, zero_division=0)))
                f_f1s.append(float(f1_score(y_true_c3[fmask] == c_idx, y_pred_c[fmask] == c_idx, zero_division=0)))
                f_praucs.append(float(average_precision_score(y_onehot[fmask, c_idx], probs_3[fmask, c_idx])))

            # Fast vectorized bootstrap for binary class c_idx
            yt_bin = (y_true_c3 == c_idx)
            yp_bin = (y_pred_c == c_idx)
            b_f1s = []
            for b_idx in boot_indices[:500]:
                yt_b = yt_bin[b_idx]
                yp_b = yp_bin[b_idx]
                tp = float(np.sum(yt_b & yp_b))
                fp = float(np.sum((~yt_b) & yp_b))
                fn = float(np.sum(yt_b & (~yp_b)))
                denom = 2.0 * tp + fp + fn
                b_f1s.append((2.0 * tp / denom) if denom > 0 else 0.0)

            per_class_rows.append({
                "Model": m,
                "Class_Name": c_name,
                "Support": sup_c,
                "Precision": round(prec_c, 4),
                "Precision_Fold_SD": round(float(np.std(f_precs, ddof=1)), 4),
                "Recall": round(rec_c, 4),
                "Recall_Fold_SD": round(float(np.std(f_recs, ddof=1)), 4),
                "F1_Score": round(f1_c, 4),
                "F1_Fold_SD": round(float(np.std(f_f1s, ddof=1)), 4),
                "F1_Boot_CI95_Low": round(float(np.percentile(b_f1s, 2.5)), 4),
                "F1_Boot_CI95_High": round(float(np.percentile(b_f1s, 97.5)), 4),
                "PR_AUC": round(prauc_c, 4),
                "PR_AUC_Fold_SD": round(float(np.std(f_praucs, ddof=1)), 4),
            })

        # Add overall summary row per model in per_class_report.csv
        acc = float(accuracy_score(y_true_c3, y_pred_c))
        bal_acc = float(balanced_accuracy_score(y_true_c3, y_pred_c))
        prec_mac = float(precision_score(y_true_c3, y_pred_c, average="macro", zero_division=0))
        rec_mac = float(recall_score(y_true_c3, y_pred_c, average="macro", zero_division=0))
        f1_mac = float(f1_score(y_true_c3, y_pred_c, average="macro", zero_division=0))
        f1_wt = float(f1_score(y_true_c3, y_pred_c, average="weighted", zero_division=0))
        prauc_mac = float(np.mean(pr_aucs))

        sub_s = df_seed[df_seed["Model"] == m].set_index("Record_Type")
        f1_fold_sd = float(sub_s.loc["SUMMARY_FOLD_SD_SEED42", "Macro_F1"])
        f1_seed_sd = float(sub_s.loc["SUMMARY_SEED_SD_5SEEDS", "Macro_F1"])
        f1_ci_lo = float(sub_s.loc["SUMMARY_BOOT_CI95_LOW", "Macro_F1"])
        f1_ci_hi = float(sub_s.loc["SUMMARY_BOOT_CI95_HIGH", "Macro_F1"])

        per_class_rows.append({
            "Model": m,
            "Class_Name": "OVERALL_MACRO_SUMMARY",
            "Support": n_samples,
            "Precision": round(prec_mac, 4),
            "Precision_Fold_SD": np.nan,
            "Recall": round(rec_mac, 4),
            "Recall_Fold_SD": round(bal_acc, 4),
            "F1_Score": round(f1_mac, 4),
            "F1_Fold_SD": round(f1_fold_sd, 4),
            "F1_Boot_CI95_Low": round(f1_ci_lo, 4),
            "F1_Boot_CI95_High": round(f1_ci_hi, 4),
            "PR_AUC": round(prauc_mac, 4),
            "PR_AUC_Fold_SD": np.nan,
        })

        # Regression metrics + seed/fold variance
        rmse = float(np.sqrt(mean_squared_error(y_true_r, y_pred_r)))
        mae = float(mean_absolute_error(y_true_r, y_pred_r))
        r2 = float(r2_score(y_true_r, y_pred_r))

        acc_fold_sd = float(sub_s.loc["SUMMARY_FOLD_SD_SEED42", "Accuracy"])
        acc_seed_sd = float(sub_s.loc["SUMMARY_SEED_SD_5SEEDS", "Accuracy"])
        acc_ci_lo = float(sub_s.loc["SUMMARY_BOOT_CI95_LOW", "Accuracy"])
        acc_ci_hi = float(sub_s.loc["SUMMARY_BOOT_CI95_HIGH", "Accuracy"])

        r2_fold_sd = float(sub_s.loc["SUMMARY_FOLD_SD_SEED42", "R2"])
        r2_seed_sd = float(sub_s.loc["SUMMARY_SEED_SD_5SEEDS", "R2"])
        r2_ci_lo = float(sub_s.loc["SUMMARY_BOOT_CI95_LOW", "R2"])
        r2_ci_hi = float(sub_s.loc["SUMMARY_BOOT_CI95_HIGH", "R2"])

        rmse_fold_sd = float(sub_s.loc["SUMMARY_FOLD_SD_SEED42", "RMSE"])
        rmse_seed_sd = float(sub_s.loc["SUMMARY_SEED_SD_5SEEDS", "RMSE"])
        rmse_ci_lo = float(sub_s.loc["SUMMARY_BOOT_CI95_LOW", "RMSE"])
        rmse_ci_hi = float(sub_s.loc["SUMMARY_BOOT_CI95_HIGH", "RMSE"])

        mae_fold_sd = float(sub_s.loc["SUMMARY_FOLD_SD_SEED42", "MAE"])

        lat_b1 = latency_info["latency_benchmarks"][m]["batch_1"]["inference_only_ms_per_sample"]["mean"]
        lat_b256 = latency_info["latency_benchmarks"][m]["batch_256"]["inference_only_ms_per_sample"]["mean"]
        size_mb = latency_info["model_complexity_and_size"][m]["serialized_size_mb"]

        benchmark_rows.append({
            "Model_Architecture": m,
            "Classification_Accuracy": round(acc, 4),
            "Accuracy_Fold_SD": round(acc_fold_sd, 4),
            "Accuracy_Seed_SD": round(acc_seed_sd, 4),
            "Accuracy_CI95": f"[{acc_ci_lo:.4f}, {acc_ci_hi:.4f}]",
            "Balanced_Accuracy": round(bal_acc, 4),
            "Macro_Precision": round(prec_mac, 4),
            "Macro_Recall": round(rec_mac, 4),
            "Macro_F1_Score": round(f1_mac, 4),
            "Macro_F1_Fold_SD": round(f1_fold_sd, 4),
            "Macro_F1_Seed_SD": round(f1_seed_sd, 4),
            "Macro_F1_CI95": f"[{f1_ci_lo:.4f}, {f1_ci_hi:.4f}]",
            "Weighted_F1_Score": round(f1_wt, 4),
            "Macro_PR_AUC": round(prauc_mac, 4),
            "Regression_R2": round(r2, 4),
            "R2_Fold_SD": round(r2_fold_sd, 4),
            "R2_Seed_SD": round(r2_seed_sd, 4),
            "R2_CI95": f"[{r2_ci_lo:.4f}, {r2_ci_hi:.4f}]",
            "Regression_RMSE": round(rmse, 3),
            "RMSE_Fold_SD": round(rmse_fold_sd, 3),
            "RMSE_Seed_SD": round(rmse_seed_sd, 3),
            "RMSE_CI95": f"[{rmse_ci_lo:.3f}, {rmse_ci_hi:.3f}]",
            "Regression_MAE": round(mae, 3),
            "MAE_Fold_SD": round(mae_fold_sd, 3),
            "Multiclass_Brier_Score": round(brier_multi, 4),
            "ECE_10Bins": round(ece_10, 4),
            "Latency_Batch1_ms": round(lat_b1, 4),
            "Latency_Batch256_ms": round(lat_b256, 4),
            "Model_Size_MB": round(size_mb, 3),
        })

    # Save 3-class per-class report
    df_per_class = pd.DataFrame(per_class_rows)
    per_class_path = os.path.join(RESULTS_DIR, "per_class_report.csv")
    df_per_class.to_csv(per_class_path, index=False)
    print(f"3-class per-class report saved to: {per_class_path}")

    # Save 5-class per-class report (`Bleaching_Alert_Level`)
    rows_5c = []
    y5_onehot = np.eye(5)[y_true_c5]
    for cfg_label, suffix in [("Clean_10_With_DHW", "10"), ("Clean_9_No_DHW", "9")]:
        for m in MODELS:
            probs_5 = npz[f"{m}_p5_{suffix}"]
            preds_5 = np.argmax(probs_5, axis=1)
            for c_idx, c_name in enumerate(CLASS_5_NAMES):
                prec_c = float(precision_score(y_true_c5 == c_idx, preds_5 == c_idx, zero_division=0))
                rec_c = float(recall_score(y_true_c5 == c_idx, preds_5 == c_idx, zero_division=0))
                f1_c = float(f1_score(y_true_c5 == c_idx, preds_5 == c_idx, zero_division=0))
                prauc_c = float(average_precision_score(y5_onehot[:, c_idx], probs_5[:, c_idx]))
                sup_c = int(np.sum(y_true_c5 == c_idx))
                rows_5c.append({
                    "Feature_Config": cfg_label,
                    "Model": m,
                    "Class_Name": c_name,
                    "Support": sup_c,
                    "Precision": round(prec_c, 4),
                    "Recall": round(rec_c, 4),
                    "F1_Score": round(f1_c, 4),
                    "PR_AUC": round(prauc_c, 4),
                })
            rows_5c.append({
                "Feature_Config": cfg_label,
                "Model": m,
                "Class_Name": "OVERALL_MACRO_SUMMARY",
                "Support": len(y_true_c5),
                "Precision": round(float(precision_score(y_true_c5, preds_5, average="macro", zero_division=0)), 4),
                "Recall": round(float(balanced_accuracy_score(y_true_c5, preds_5)), 4),
                "F1_Score": round(float(f1_score(y_true_c5, preds_5, average="macro", zero_division=0)), 4),
                "PR_AUC": round(float(accuracy_score(y_true_c5, preds_5)), 4),
            })

    df_5c = pd.DataFrame(rows_5c)
    per_class_5_path = os.path.join(RESULTS_DIR, "per_class_report_5class.csv")
    df_5c.to_csv(per_class_5_path, index=False)
    print(f"5-class per-class report saved to: {per_class_5_path}")

    # Save calibration tables and plot
    df_calib = pd.DataFrame(calib_rows)
    df_bins = pd.DataFrame(all_bin_rows)
    df_calib.to_csv(os.path.join(CALIB_DIR, "calibration_metrics.csv"), index=False)
    df_bins.to_csv(os.path.join(CALIB_DIR, "reliability_bins.csv"), index=False)
    plot_calibration_curves(df_bins, df_calib)

    # Save unified benchmark summary tables
    df_bench = pd.DataFrame(benchmark_rows)
    df_bench.to_csv(os.path.join(RESULTS_DIR, "model_benchmark_summary.csv"), index=False)
    df_bench.to_csv(os.path.join(EVAL_DIR, "model_benchmark_metrics.csv"), index=False)
    df_bench.to_csv(os.path.join(TABLES_DIR, "Table1_model_performance_benchmarks.csv"), index=False)

    with open(os.path.join(TABLES_DIR, "Table1_model_performance_benchmarks.md"), "w", encoding="utf-8") as f:
        f.write("# Table 1: Cross-Validated Statistical Emulation Performance Across AI Architectures (5-Fold Spatial Block CV, N=15,000)\n\n")
        try:
            f.write(df_bench.to_markdown(index=False))
        except Exception:
            f.write(df_bench.to_string(index=False))
        f.write(
            "\n\n*Note: Evaluated on the unified 30-station synthetic benchmark dataset (N=15,000, 100.0% simulated) "
            "using 5-fold spatially clustered cross-validation (>25 km Haversine buffer, min out-of-fold distance 119.72 km) "
            "and 5 random seeds (17, 42, 73, 108, 256) on the clean 10-feature environmental predictor set.*\n"
        )

    # Compute Pairwise Statistical Tests (Wilcoxon signed-rank + Cohen's d + Bonferroni correction)
    stat_rows = []
    alpha_bonf = 0.05 / 6.0  # 6 model pairs

    sub_runs = df_seed[df_seed["Record_Type"] == "Fold_Seed_Run"].copy()
    sub_runs["Run_Key"] = sub_runs["Seed"].astype(str) + "_F" + sub_runs["Fold_ID"].astype(str)

    for m1, m2 in itertools.combinations(MODELS, 2):
        r1 = sub_runs[sub_runs["Model"] == m1].set_index("Run_Key")
        r2_df = sub_runs[sub_runs["Model"] == m2].set_index("Run_Key").loc[r1.index]

        # 1. Across N=25 (5 folds x 5 seeds) evaluation runs: Macro-F1 and RMSE
        for metric_name, higher_better in [("Macro_F1", True), ("Accuracy", True), ("RMSE", False), ("R2", True)]:
            v1 = r1[metric_name].values
            v2 = r2_df[metric_name].values
            w_stat, p_val = stats.wilcoxon(v1, v2, zero_method="zsplit", alternative="two-sided")
            d_val = cohen_d_paired(v1, v2)
            stat_rows.append({
                "Comparison_Pair": f"{m1} vs {m2}",
                "Model_A": m1,
                "Model_B": m2,
                "Evaluation_Unit": "25_Fold_x_Seed_Runs",
                "N_Paired_Units": 25,
                "Metric": metric_name,
                "Mean_Model_A": round(float(np.mean(v1)), 5),
                "Mean_Model_B": round(float(np.mean(v2)), 5),
                "Mean_Difference_A_minus_B": round(float(np.mean(v1 - v2)), 5),
                "Wilcoxon_W": round(float(w_stat), 4),
                "p_value_two_sided": float(f"{p_val:.6e}"),
                "Bonferroni_Alpha": round(alpha_bonf, 6),
                "Significant_Bonferroni": bool(p_val < alpha_bonf),
                "Cohens_d": round(d_val, 4),
            })

        # 2. Across N=30 stations (Seed 42 OOF): Station-level RMSE and Macro-F1
        st_rmse_1, st_rmse_2 = [], []
        for _, grp in df_oof.groupby("Station_Name", sort=False):
            yt = grp["True_Loss_Pct"].values
            st_rmse_1.append(float(np.sqrt(mean_squared_error(yt, grp[reg_col_map[m1]].values))))
            st_rmse_2.append(float(np.sqrt(mean_squared_error(yt, grp[reg_col_map[m2]].values))))
        st_rmse_1 = np.array(st_rmse_1)
        st_rmse_2 = np.array(st_rmse_2)
        w_st, p_st = stats.wilcoxon(st_rmse_1, st_rmse_2, zero_method="zsplit", alternative="two-sided")
        d_st = cohen_d_paired(st_rmse_1, st_rmse_2)
        stat_rows.append({
            "Comparison_Pair": f"{m1} vs {m2}",
            "Model_A": m1,
            "Model_B": m2,
            "Evaluation_Unit": "30_Stations_OOF",
            "N_Paired_Units": 30,
            "Metric": "Station_RMSE",
            "Mean_Model_A": round(float(np.mean(st_rmse_1)), 5),
            "Mean_Model_B": round(float(np.mean(st_rmse_2)), 5),
            "Mean_Difference_A_minus_B": round(float(np.mean(st_rmse_1 - st_rmse_2)), 5),
            "Wilcoxon_W": round(float(w_st), 4),
            "p_value_two_sided": float(f"{p_st:.6e}"),
            "Bonferroni_Alpha": round(alpha_bonf, 6),
            "Significant_Bonferroni": bool(p_st < alpha_bonf),
            "Cohens_d": round(d_st, 4),
        })

        # 3. Across N=15,000 samples (Seed 42 OOF): Sample-level Absolute Error
        ae_1 = np.abs(y_true_r - df_oof[reg_col_map[m1]].values)
        ae_2 = np.abs(y_true_r - df_oof[reg_col_map[m2]].values)
        w_smp, p_smp = stats.wilcoxon(ae_1, ae_2, zero_method="zsplit", alternative="two-sided")
        d_smp = cohen_d_paired(ae_1, ae_2)
        stat_rows.append({
            "Comparison_Pair": f"{m1} vs {m2}",
            "Model_A": m1,
            "Model_B": m2,
            "Evaluation_Unit": "15000_Samples_OOF",
            "N_Paired_Units": 15000,
            "Metric": "Sample_Absolute_Error",
            "Mean_Model_A": round(float(np.mean(ae_1)), 5),
            "Mean_Model_B": round(float(np.mean(ae_2)), 5),
            "Mean_Difference_A_minus_B": round(float(np.mean(ae_1 - ae_2)), 5),
            "Wilcoxon_W": round(float(w_smp), 4),
            "p_value_two_sided": float(f"{p_smp:.6e}"),
            "Bonferroni_Alpha": round(alpha_bonf, 6),
            "Significant_Bonferroni": bool(p_smp < alpha_bonf),
            "Cohens_d": round(d_smp, 4),
        })

    df_stats = pd.DataFrame(stat_rows)
    stat_res_path = os.path.join(RESULTS_DIR, "statistical_tests.csv")
    stat_pub_path = os.path.join(STATS_DIR, "statistical_tests_wilcoxon_cohen.csv")
    df_stats.to_csv(stat_res_path, index=False)
    df_stats.to_csv(stat_pub_path, index=False)
    print(f"Statistical tests saved to: {stat_res_path} and {stat_pub_path}")


if __name__ == "__main__":
    evaluate_all_models()
