"""
CoralTwin-DT: Exploratory Data Analysis (EDA) Module
===================================================
Analyzes multi-stressor distributions, biophysical correlations,
and spatial variance across coral reef sectors.

Author: CoralTwin-DT Research Consortium
License: MIT
Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.
"""

import os
import numpy as np
import pandas as pd
from scipy import stats

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_PATH = os.path.join(PROJECT_ROOT, "03_Data", "processed_data", "coral_environmental_harmonized.csv")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "09_Results", "statistics")
os.makedirs(RESULTS_DIR, exist_ok=True)


def run_exploratory_analysis():
    print(f"Loading harmonized dataset from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded dataset: {df.shape[0]} records, {df.shape[1]} variables.")

    numeric_cols = [
        "Depth_m", "SST_degC", "SST_Anomaly_degC", "DHW_degC_weeks",
        "pH_total", "Aragonite_Saturation_Omega", "Turbidity_NTU",
        "PAR_umol_m2_s", "Live_Coral_Cover_Pct", "Macroalgae_Cover_Pct",
        "Structural_Rugosity", "Shannon_Diversity_H", "Bleaching_Severity_Pct",
        "Coral_Cover_Loss_Pct"
    ]

    # Descriptive Statistics
    desc_df = df[numeric_cols].describe().T
    desc_df["skewness"] = df[numeric_cols].skew()
    desc_df["kurtosis"] = df[numeric_cols].kurtosis()
    desc_path = os.path.join(RESULTS_DIR, "descriptive_statistics.csv")
    desc_df.round(3).to_csv(desc_path)
    print(f"Descriptive statistics saved to: {desc_path}")

    # Pearson and Spearman Correlation Matrices
    pearson_corr = df[numeric_cols].corr(method="pearson")
    spearman_corr = df[numeric_cols].corr(method="spearman")
    pearson_corr.round(3).to_csv(os.path.join(RESULTS_DIR, "pearson_correlation_matrix.csv"))
    spearman_corr.round(3).to_csv(os.path.join(RESULTS_DIR, "spearman_correlation_matrix.csv"))
    print("Correlation matrices saved.")

    # One-Way ANOVA across Reef Zones and Regions for Bleaching Severity
    f_val_zone, p_val_zone = stats.f_oneway(
        *[group["Bleaching_Severity_Pct"].values for _, group in df.groupby("Reef_Zone")]
    )
    f_val_reg, p_val_reg = stats.f_oneway(
        *[group["Bleaching_Severity_Pct"].values for _, group in df.groupby("Region")]
    )

    anova_df = pd.DataFrame([
        {"Factor": "Reef_Zone (Geomorphic)", "F_Statistic": round(f_val_zone, 3), "p_Value": float(p_val_zone), "Significance": "***" if p_val_zone < 0.001 else "ns"},
        {"Factor": "Region (Biogeographic)", "F_Statistic": round(f_val_reg, 3), "p_Value": float(p_val_reg), "Significance": "***" if p_val_reg < 0.001 else "ns"},
    ])
    anova_path = os.path.join(RESULTS_DIR, "anova_bleaching_by_zone_region.csv")
    anova_df.to_csv(anova_path, index=False)
    print(f"ANOVA results saved to: {anova_path}")

    # Risk class distribution
    risk_counts = df["Bleaching_Risk"].value_counts(normalize=True).reset_index()
    risk_counts.columns = ["Bleaching_Risk_Class", "Proportion"]
    risk_counts.to_csv(os.path.join(RESULTS_DIR, "bleaching_risk_distribution.csv"), index=False)
    print("EDA completed successfully.")


if __name__ == "__main__":
    run_exploratory_analysis()
