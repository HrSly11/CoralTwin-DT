"""
06_AI_and_Modeling/explainability/SHAP_analysis/compute_within_support_thresholds.py
===================================================================================
Implements Task 4:
1. Computes the exact empirical ranges and counts of pH_total and Aragonite_Saturation_Omega
   in `03_Data/final_dataset.csv`.
2. Computes the Partial Dependence (PD) response curves of XGBoost across DHW in [0, 20]
   under conditions strictly WITHIN the empirical support:
   - High Omega: 90th percentile = 3.90 (pH = 8.12)
   - Low Omega:  10th percentile = 3.16 (pH = 8.03)
3. Computes the Analytical Generator ground truth expectation under those exact same Omega values.
4. Calculates exact EC50, maximum derivative, and 35% cover loss crossing thresholds for both.
5. Saves the updated dataset to `results/partial_dependence_within_support.csv` and
   `results/inflection_points_within_support.json`.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d
import xgboost as xgb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_PATH = os.path.join(BASE_DIR, "03_Data", "final_dataset.csv")
MODELS_DIR = os.path.join(BASE_DIR, "06_AI_and_Modeling", "machine_learning", "saved_models")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

CLEAN_10_FEATURES = [
    "Depth_m", "SST_degC", "SST_Anomaly_degC", "DHW_degC_weeks",
    "pH_total", "Salinity_PSU", "Dissolved_Oxygen_mg_L",
    "Aragonite_Saturation_Omega", "Turbidity_NTU", "PAR_umol_m2_s",
]


def extract_thresholds(dhw_grid, y_curve):
    y_arr = np.asarray(y_curve, dtype=float)
    y_smooth = gaussian_filter1d(y_arr, sigma=8)
    dy = np.gradient(y_smooth, dhw_grid)
    max_slope_idx = int(np.argmax(dy))
    inflection_dhw = float(dhw_grid[max_slope_idx])
    inflection_loss = float(y_arr[max_slope_idx])

    y_min, y_max = float(y_arr[0]), float(y_arr[-1])
    half_target = y_min + 0.50 * (y_max - y_min)
    ec50_step_idx = int(np.argmin(np.abs(y_arr - half_target)))
    ec50_smooth_idx = int(np.argmin(np.abs(y_smooth - half_target)))

    c20_idx = np.where(y_smooth >= 20.0)[0]
    dhw_20_smooth = float(dhw_grid[c20_idx[0]]) if len(c20_idx) > 0 else float("nan")
    c35_idx = np.where(y_smooth >= 35.0)[0]
    dhw_35_smooth = float(dhw_grid[c35_idx[0]]) if len(c35_idx) > 0 else float("nan")

    return {
        "smoothed_max_derivative_dhw_degC_weeks": round(inflection_dhw, 2),
        "predicted_loss_at_max_derivative_pct": round(inflection_loss, 2),
        "max_slope_pct_per_dhw": round(float(dy[max_slope_idx]), 3),
        "ec50_half_maximal_dhw_degC_weeks": round(float(dhw_grid[ec50_smooth_idx]), 2),
        "ec50_step_raw_dhw_degC_weeks": round(float(dhw_grid[ec50_step_idx]), 2),
        "ec50_predicted_loss_pct": round(float(y_smooth[ec50_smooth_idx]), 2),
        "dhw_crossing_20pct_loss_degC_weeks": round(dhw_20_smooth, 2),
        "dhw_crossing_35pct_loss_degC_weeks": round(dhw_35_smooth, 2),
        "loss_at_dhw_0_pct": round(y_min, 2),
        "loss_at_dhw_8_pct": round(float(y_arr[int(8.0 / 0.05)]), 2),
        "loss_at_dhw_20_pct": round(y_max, 2),
    }


def main():
    print("=" * 70)
    print("TASK 4: Partial Dependence Analysis WITHIN Data Support")
    print("=" * 70)

    df = pd.read_csv(DATA_PATH)
    omega = df["Aragonite_Saturation_Omega"]
    ph = df["pH_total"]

    # 1. Distribution summary
    omega_stats = {
        "min": float(omega.min()),
        "max": float(omega.max()),
        "mean": round(float(omega.mean()), 4),
        "std": round(float(omega.std()), 4),
        "p05": round(float(np.percentile(omega, 5)), 2),
        "p10": round(float(np.percentile(omega, 10)), 2),
        "p25": round(float(np.percentile(omega, 25)), 2),
        "median": round(float(np.percentile(omega, 50)), 2),
        "p75": round(float(np.percentile(omega, 75)), 2),
        "p90": round(float(np.percentile(omega, 90)), 2),
        "p95": round(float(np.percentile(omega, 95)), 2),
        "count_le_2_40": int((omega <= 2.40).sum()),
        "count_le_2_60": int((omega <= 2.60).sum()),
        "count_le_2_80": int((omega <= 2.80).sum()),
        "count_le_3_00": int((omega <= 3.00).sum()),
        "count_le_p10_3_16": int((omega <= 3.16).sum()),
        "count_ge_p90_3_90": int((omega >= 3.90).sum()),
    }

    ph_stats = {
        "min": float(ph.min()),
        "max": float(ph.max()),
        "mean": round(float(ph.mean()), 4),
        "std": round(float(ph.std()), 4),
        "p05": round(float(np.percentile(ph, 5)), 3),
        "p10": round(float(np.percentile(ph, 10)), 3),
        "median": round(float(np.percentile(ph, 50)), 3),
        "p90": round(float(np.percentile(ph, 90)), 3),
        "p95": round(float(np.percentile(ph, 95)), 3),
    }

    print("Omega Support:", omega_stats)
    print("pH Support:", ph_stats)

    # Load canonical XGBoost regressor
    xgb_reg_path = os.path.join(MODELS_DIR, "xgboost_regressor.joblib")
    print(f"Loading canonical XGBoost regressor from: {xgb_reg_path}")
    xgb_reg = joblib.load(xgb_reg_path)

    # Draw evaluation dataset (2,500 samples stratified)
    eval_sample = df.sample(n=3000, random_state=42)
    X_base = eval_sample[CLEAN_10_FEATURES].copy().values

    dhw_idx = CLEAN_10_FEATURES.index("DHW_degC_weeks")
    ph_idx = CLEAN_10_FEATURES.index("pH_total")
    omega_idx = CLEAN_10_FEATURES.index("Aragonite_Saturation_Omega")

    dhw_grid = np.round(np.arange(0.0, 20.05, 0.05), 2)

    # Within-support high vs low regimes
    omega_high = 3.90  # 90th percentile
    ph_high = 8.12
    omega_low = 3.16   # 10th percentile
    ph_low = 8.03

    X_hi = X_base.copy()
    X_hi[:, omega_idx] = omega_high
    X_hi[:, ph_idx] = ph_high

    X_lo = X_base.copy()
    X_lo[:, omega_idx] = omega_low
    X_lo[:, ph_idx] = ph_low

    pd_xgb_hi, pd_xgb_lo = [], []
    ana_hi, ana_lo = [], []

    mean_par = float(eval_sample["PAR_umol_m2_s"].mean())
    mean_turb = float(eval_sample["Turbidity_NTU"].mean())
    light_pen = max(mean_par - 1100.0, 0.0) / 1000.0
    turb_buf = min(mean_turb / 6.0, 0.25)

    for d_val in dhw_grid:
        X_hi[:, dhw_idx] = d_val
        X_lo[:, dhw_idx] = d_val

        pd_xgb_hi.append(float(np.mean(xgb_reg.predict(X_hi))))
        pd_xgb_lo.append(float(np.mean(xgb_reg.predict(X_lo))))

        # Analytical generator formula
        for om_val, t_list in [(omega_high, ana_hi), (omega_low, ana_lo)]:
            acid_pen = max(3.8 - om_val, 0.0) / 1.4
            bsi = max(0.60 * (d_val / 8.0) ** 1.8 + 0.24 * acid_pen + 0.16 * light_pen - 0.10 * turb_buf, 0.0)
            sev = 100.0 / (1.0 + np.exp(-3.4 * (bsi - 0.88)))
            t_list.append(0.80 * sev)

    # Threshold extraction
    t_xgb_hi = extract_thresholds(dhw_grid, pd_xgb_hi)
    t_xgb_lo = extract_thresholds(dhw_grid, pd_xgb_lo)
    t_ana_hi = extract_thresholds(dhw_grid, ana_hi)
    t_ana_lo = extract_thresholds(dhw_grid, ana_lo)

    # Compute shifts (Low Omega minus High Omega)
    xgb_shifts = {
        "delta_ec50_dhw_degC_weeks": round(t_xgb_lo["ec50_half_maximal_dhw_degC_weeks"] - t_xgb_hi["ec50_half_maximal_dhw_degC_weeks"], 2),
        "delta_crossing_35pct_dhw_degC_weeks": round(t_xgb_lo["dhw_crossing_35pct_loss_degC_weeks"] - t_xgb_hi["dhw_crossing_35pct_loss_degC_weeks"], 2),
        "delta_crossing_20pct_dhw_degC_weeks": round(t_xgb_lo["dhw_crossing_20pct_loss_degC_weeks"] - t_xgb_hi["dhw_crossing_20pct_loss_degC_weeks"], 2),
        "delta_inflection_dhw_degC_weeks": round(t_xgb_lo["smoothed_max_derivative_dhw_degC_weeks"] - t_xgb_hi["smoothed_max_derivative_dhw_degC_weeks"], 2),
    }

    ana_shifts = {
        "delta_ec50_dhw_degC_weeks": round(t_ana_lo["ec50_half_maximal_dhw_degC_weeks"] - t_ana_hi["ec50_half_maximal_dhw_degC_weeks"], 2),
        "delta_crossing_35pct_dhw_degC_weeks": round(t_ana_lo["dhw_crossing_35pct_loss_degC_weeks"] - t_ana_hi["dhw_crossing_35pct_loss_degC_weeks"], 2),
        "delta_crossing_20pct_dhw_degC_weeks": round(t_ana_lo["dhw_crossing_20pct_loss_degC_weeks"] - t_ana_hi["dhw_crossing_20pct_loss_degC_weeks"], 2),
        "delta_inflection_dhw_degC_weeks": round(t_ana_lo["smoothed_max_derivative_dhw_degC_weeks"] - t_ana_hi["smoothed_max_derivative_dhw_degC_weeks"], 2),
    }

    out_csv_df = pd.DataFrame({
        "DHW_degC_weeks": dhw_grid,
        "PD_XGBoost_HighOmega_390": np.round(pd_xgb_hi, 4),
        "PD_XGBoost_LowOmega_316": np.round(pd_xgb_lo, 4),
        "Analytical_HighOmega_390": np.round(ana_hi, 4),
        "Analytical_LowOmega_316": np.round(ana_lo, 4),
    })
    csv_path = os.path.join(RESULTS_DIR, "partial_dependence_within_support.csv")
    out_csv_df.to_csv(csv_path, index=False)

    full_results = {
        "scientific_disclaimer": "Partial dependence thresholds evaluated strictly within the empirical data support (10th to 90th percentiles of Omega); reflects learned response surface of the surrogate model.",
        "empirical_support_statistics": {
            "aragonite_saturation_omega": omega_stats,
            "ph_total": ph_stats,
        },
        "within_support_definitions": {
            "high_omega_p90": {"omega": omega_high, "ph": ph_high, "empirical_records_ge_390": omega_stats["count_ge_p90_3_90"]},
            "low_omega_p10": {"omega": omega_low, "ph": ph_low, "empirical_records_le_316": omega_stats["count_le_p10_3_16"]},
        },
        "xgboost_within_support": {
            "high_omega_390": t_xgb_hi,
            "low_omega_316": t_xgb_lo,
            "threshold_shift_low_minus_high": xgb_shifts,
        },
        "analytical_generator_within_support": {
            "high_omega_390": t_ana_hi,
            "low_omega_316": t_ana_lo,
            "threshold_shift_low_minus_high": ana_shifts,
        },
    }

    json_path = os.path.join(RESULTS_DIR, "inflection_points_within_support.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_results, f, indent=2)

    print("\nWithin-Support Results Summary:")
    print("XGBoost High Omega (3.90) EC50:", t_xgb_hi["ec50_half_maximal_dhw_degC_weeks"], "35% loss crossing:", t_xgb_hi["dhw_crossing_35pct_loss_degC_weeks"])
    print("XGBoost Low  Omega (3.16) EC50:", t_xgb_lo["ec50_half_maximal_dhw_degC_weeks"], "35% loss crossing:", t_xgb_lo["dhw_crossing_35pct_loss_degC_weeks"])
    print("XGBoost Delta (Low - High):", xgb_shifts)
    print("Analytical High Omega (3.90) EC50:", t_ana_hi["ec50_half_maximal_dhw_degC_weeks"], "35% loss crossing:", t_ana_hi["dhw_crossing_35pct_loss_degC_weeks"])
    print("Analytical Low  Omega (3.16) EC50:", t_ana_lo["ec50_half_maximal_dhw_degC_weeks"], "35% loss crossing:", t_ana_lo["dhw_crossing_35pct_loss_degC_weeks"])
    print("Analytical Delta (Low - High):", ana_shifts)


if __name__ == "__main__":
    main()
