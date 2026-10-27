"""
CoralTwin-DT: Comparative AI Benchmarking (XGBoost vs Random Forest vs Deep MLP vs Stacked LSTM)
================================================================================================
Unified comparative benchmark report and chart generator aligned with the
5-Fold Spatial Block Cross-Validation (>25 km Haversine buffer, 5 random seeds)
on the clean 10-feature environmental predictor set (Regime 1, N=15,000).

Addresses Audit Findings CRIT-02, CRIT-04, FON-01, and FON-02.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
EVAL_DIR = os.path.join(BASE_DIR, "model_evaluation")
REPORT_PATH = os.path.join(BASE_DIR, "model_comparison_report.md")
CHART_PATH = os.path.join(BASE_DIR, "model_comparison_charts.png")


def generate_charts(df_bench: pd.DataFrame, df_oof: pd.DataFrame):
    plt.rcParams.update({"font.family": "sans-serif", "font.size": 10})
    fig, axes = plt.subplots(2, 2, figsize=(14, 10.5), dpi=300, facecolor="#f8fafc")

    models = df_bench["Model_Architecture"].values
    x = np.arange(len(models))
    w = 0.28

    # Panel A: Accuracy, Macro-F1, and R2
    ax_a = axes[0, 0]
    ax_a.bar(x - w, df_bench["Classification_Accuracy"] * 100, w, label="Accuracy (%)", color="#2b6cb0", edgecolor="black")
    ax_a.bar(x, df_bench["Macro_F1_Score"] * 100, w, label="Macro-F1 (%)", color="#805ad5", edgecolor="black")
    ax_a.bar(x + w, df_bench["Regression_R2"] * 100, w, label="Regression R² (%)", color="#2f855a", edgecolor="black")
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(models, fontweight="bold")
    ax_a.set_ylim(55, 104)
    ax_a.set_ylabel("Score (%)")
    ax_a.set_title("A. Spatial-CV Emulation Skill (Clean 10-Feature Set, N=15,000)", fontweight="bold")
    ax_a.legend(loc="lower right")
    ax_a.grid(True, axis="y", linestyle=":", alpha=0.6)

    # Panel B: Regression Error (RMSE & MAE) vs Irreducible Noise Floor
    ax_b = axes[0, 1]
    ax_b.bar(x - w / 2, df_bench["Regression_RMSE"], w, yerr=df_bench["RMSE_Fold_SD"], capsize=4, label="RMSE (% ± Fold SD)", color="#e53e3e", edgecolor="black")
    ax_b.bar(x + w / 2, df_bench["Regression_MAE"], w, yerr=df_bench["MAE_Fold_SD"], capsize=4, label="MAE (% ± Fold SD)", color="#dd6b20", edgecolor="black")
    ax_b.axhline(3.89, color="#1a202c", linestyle="--", lw=1.4, label="Theoretical Irreducible Noise Floor (~3.89%)")
    ax_b.set_xticks(x)
    ax_b.set_xticklabels(models, fontweight="bold")
    ax_b.set_ylabel("Error (% Coral Cover Loss)")
    ax_b.set_title("B. Out-of-Fold Regression Error vs. Stochastic Noise Floor", fontweight="bold")
    ax_b.legend(loc="upper left", fontsize=8.5)
    ax_b.grid(True, axis="y", linestyle=":", alpha=0.6)

    # Panel C: Single-Thread Latency vs Model Size
    ax_c = axes[1, 0]
    colors = ["#1b9e77", "#d95f02", "#7570b3", "#e7298a"]
    ax_c.scatter(df_bench["Model_Size_MB"], df_bench["Latency_Batch256_ms"], s=240, c=colors, edgecolors="black", lw=1.5)
    for idx, row in df_bench.iterrows():
        ax_c.annotate(
            f"{row['Model_Architecture']}\n({row['Latency_Batch256_ms']:.4f} ms)",
            (row["Model_Size_MB"], row["Latency_Batch256_ms"]),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=8.5,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9),
        )
    ax_c.set_xscale("log")
    ax_c.set_yscale("log")
    ax_c.set_xlabel("Serialized Model Size (MB, log scale)")
    ax_c.set_ylabel("Single-Thread Latency at Batch=256 (ms/sample, log scale)")
    ax_c.set_title("C. Computational Footprint vs. Single-Thread Inference Latency", fontweight="bold")
    ax_c.grid(True, linestyle=":", alpha=0.6)

    # Panel D: XGBoost Out-of-Fold Predicted vs Observed
    ax_d = axes[1, 1]
    rng = np.random.default_rng(42)
    sub_idx = rng.choice(len(df_oof), 2000, replace=False)
    y_true = df_oof["True_Loss_Pct"].values[sub_idx]
    y_pred = df_oof["XGB_Loss_Pred"].values[sub_idx]
    ax_d.scatter(y_true, y_pred, color="#2f855a", alpha=0.45, s=16, label="XGBoost OOF Predictions (n=2,000 sample)")
    ax_d.plot([0, 96], [0, 96], color="#c53030", linestyle="--", lw=1.5, label="1:1 Ideal Line")
    ax_d.set_xlabel("Simulated Ground-Truth Coral Cover Loss (%)")
    ax_d.set_ylabel("Out-of-Fold Predicted Loss (%)")
    ax_d.set_title("D. Leakage-Free XGBoost Out-of-Fold Parity Plot", fontweight="bold")
    ax_d.legend(loc="upper left", fontsize=8.5)
    ax_d.grid(True, linestyle=":", alpha=0.6)

    plt.suptitle(
        "CoralTwin-DT: Unified 5-Fold Spatial Block CV Benchmark (Clean 10-Feature Emulation, N=15,000)",
        fontsize=12.5,
        fontweight="bold",
        y=0.99,
    )
    plt.tight_layout()
    fig.savefig(CHART_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Comparison charts saved to: {CHART_PATH}")


def write_comparison_report(df_bench: pd.DataFrame, df_ablation: pd.DataFrame):
    lines = [
        "# Unified Machine Learning & Deep Learning Benchmark Report",
        "",
        "**Dataset:** `03_Data/final_dataset.csv` ($N = 15,000$ synthetic observations across 30 stations; 100.0% simulated)",
        "**Validation Protocol:** 5-Fold Spatially Clustered & Biogeographically Stratified Cross-Validation (`>25 km` Haversine buffer, min out-of-fold distance `119.72 km`) across 5 random seeds (`17, 42, 73, 108, 256`)",
        "**Canonical Predictor Set (`Regime_1_Clean_Emulation_10`):** `Depth_m`, `SST_degC`, `SST_Anomaly_degC`, `DHW_degC_weeks`, `pH_total`, `Salinity_PSU`, `Dissolved_Oxygen_mg_L`, `Aragonite_Saturation_Omega`, `Turbidity_NTU`, `PAR_umol_m2_s` (all post-target benthic variables excluded)",
        "",
        "---",
        "",
        "## 1. Canonical 4-Model Spatial-CV Benchmark Summary (`Regime_1_Clean_Emulation_10`)",
        "",
        df_bench.to_markdown(index=False),
        "",
        "---",
        "",
        "## 2. Reverse Target Leakage & Feature Ablation Summary (`Task B Part 2`)",
        "",
        df_ablation.to_markdown(index=False),
        "",
    ]
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Comparison report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    bench_csv = os.path.join(RESULTS_DIR, "model_benchmark_summary.csv")
    oof_csv = os.path.join(EVAL_DIR, "cross_validation_oof_predictions.csv")
    ablation_csv = os.path.join(RESULTS_DIR, "leakage_ablation_metrics.csv")

    df_bench = pd.read_csv(bench_csv)
    df_oof = pd.read_csv(oof_csv)
    df_ablation = pd.read_csv(ablation_csv)

    generate_charts(df_bench, df_oof)
    write_comparison_report(df_bench, df_ablation)
