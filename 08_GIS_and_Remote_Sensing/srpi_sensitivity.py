"""
08_GIS_and_Remote_Sensing/srpi_sensitivity.py
=============================================
FASE 3 (FON-05): Comprehensive Sensitivity & Robustness Analysis of the Spatial Restoration Priority Index (SRPI, Eq. 7)

Evaluates:
1. Tier-1 Thresholds: {0.60, 0.65, 0.70, 0.75, 0.80}.
2. Weight Perturbations (+-20 % around base weights 0.35 / 0.25 / 0.25 / 0.15, re-normalized to sum to 1):
   - One-at-a-time (OAT, 8 configurations)
   - All 2^4 = 16 hypercube corners
   - 10,000 Monte Carlo random weight perturbations U(0.8, 1.2) (SEED = 42)
3. Thermal Source Comparison:
   - Uncalibrated Synthetic DHW_95th (N = 30 and N = 29 stations)
   - Real Satellite NOAA CRW 5 km DHW_95th (N = 29 direct marine stations)
   - Train-Calibrated Synthetic DHW_95th (from FASE 1 `results/noaa_calibration_metrics.csv`, if present)
   Both under strict Eq. (7) (`spatial_pipeline.py`) and the simplified linear variant (`fetch_noaa_crw_real_dhw.py`).
4. Non-Parametric Bootstrap (B = 10,000 resamples over stations, SEED = 42) for Tier-1 counts,
   preservation rates, and Spearman rank correlation between synthetic and NOAA SRPI scores.
5. Leave-One-Station-Out (LOSO) Jackknife Sensitivity across all 30 stations (and 29 NOAA stations).

Outputs (results/):
  - `results/srpi_sensitivity.csv` (master unified sensitivity table for Table 8b)
  - `results/srpi_loso_sensitivity.csv` (station-by-station leave-one-station-out jackknife)
  - `results/srpi_bootstrap_10000.csv` (10,000 station bootstrap summary)
  - `results/srpi_threshold_weight_sensitivity.csv`
  - `results/srpi_threshold_sensitivity_base.csv`
  - `results/srpi_weight_sensitivity_random.csv`
  - `results/srpi_weight_sensitivity_envelope.csv`
  - `results/srpi_sensitivity_station_scores.csv`
  - `results/srpi_sensitivity_summary.json`
"""

import os
import sys
import json
import itertools
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, pearsonr

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SEED = 42
THRESHOLDS = [0.60, 0.65, 0.70, 0.75, 0.80]
BASE_W = np.array([0.35, 0.25, 0.25, 0.15])  # thermal refugia, urgency, rugosity, water quality / connectivity
PERT = 0.20
N_RANDOM = 10000
N_BOOTSTRAP = 10000
EPS = 1e-9

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_PATH = os.path.join(PROJECT_ROOT, "03_Data", "final_dataset.csv")
RANKING_PATH = os.path.join(BASE_DIR, "geospatial_outputs", "spatial_restoration_priority_ranking.csv")
NOAA_PATH = os.path.join(PROJECT_ROOT, "results", "noaa_crw_validation.csv")
CAL_METRICS_PATH = os.path.join(PROJECT_ROOT, "results", "noaa_calibration_metrics.csv")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def station_components():
    """Station-level components exactly as in spatial_pipeline.calculate_spatial_priorities()."""
    df = pd.read_csv(DATA_PATH)
    st = df.groupby(["Station_ID", "Station_Name"], as_index=False).agg(
        Region=("Region", "first"),
        DHW95_syn=("DHW_degC_weeks", lambda x: float(np.percentile(x, 95))),
        Turbidity_NTU=("Turbidity_NTU", "mean"),
        Live_Coral_Cover_Pct=("Live_Coral_Cover_Pct", "mean"),
        Structural_Rugosity=("Structural_Rugosity", "mean"),
    )
    st["_n"] = st["Station_ID"].str.replace("STN_", "", regex=False).astype(int)
    st = st.sort_values("_n").drop(columns="_n").reset_index(drop=True)

    noaa = pd.read_csv(NOAA_PATH)[
        [
            "Station_ID",
            "Real_NOAA_DHW_95th",
            "Connectivity_H",
            "Mean_Live_Coral_Cover_Pct",
            "Mean_Structural_Rugosity",
            "Synthetic_DHW_95th",
        ]
    ]
    st = st.merge(noaa, on="Station_ID", how="left")
    st["has_noaa"] = st["Real_NOAA_DHW_95th"].notna()

    if os.path.exists(CAL_METRICS_PATH):
        cal_df = pd.read_csv(CAL_METRICS_PATH)[["Station_ID", "Cal_Full_DHW_95th", "Cal_Test_DHW_95th"]]
        st = st.merge(cal_df, on="Station_ID", how="left")
    else:
        st["Cal_Full_DHW_95th"] = st["DHW95_syn"]
        st["Cal_Test_DHW_95th"] = st["DHW95_syn"]

    urg = np.clip(1.0 - st["Live_Coral_Cover_Pct"] / 50.0, 0.0, 1.0)
    rug = np.clip((st["Structural_Rugosity"] - 1.0) / 2.0, 0.0, 1.0)
    wq = 1.0 - np.minimum(0.04 * st["Turbidity_NTU"] / 0.25, 1.0)
    th_syn = 1.0 - np.minimum(st["DHW95_syn"] / 16.0, 1.0)
    th_real = 1.0 - np.minimum(st["Real_NOAA_DHW_95th"] / 16.0, 1.0)
    th_cal = 1.0 - np.minimum(st["Cal_Full_DHW_95th"] / 16.0, 1.0)

    # Strict Eq. 7 component matrices (columns: therm, urgency, rugosity, water quality)
    strict_syn = np.column_stack([th_syn, urg, rug, wq])
    strict_real = np.column_stack([th_real, urg, rug, wq])
    strict_cal = np.column_stack([th_cal, urg, rug, wq])

    # Simplified linear variant (fetch_noaa_crw_real_dhw.py)
    c = st["Mean_Live_Coral_Cover_Pct"]
    r = st["Mean_Structural_Rugosity"]
    conn = st["Connectivity_H"]
    lin_syn = np.column_stack([
        1.0 - np.minimum(st["Synthetic_DHW_95th"] / 12.0, 1.0),
        1.0 - c / 100.0,
        r / 3.5,
        conn,
    ])
    lin_real = np.column_stack([
        1.0 - np.minimum(st["Real_NOAA_DHW_95th"] / 12.0, 1.0),
        1.0 - c / 100.0,
        r / 3.5,
        conn,
    ])
    return st, strict_syn, strict_real, strict_cal, lin_syn, lin_real


def score(comp, w):
    return np.round(comp @ w, 3)


def tier1(scores, thr):
    return scores >= thr - EPS


def evaluate(syn_comp, real_comp, has_noaa, w, thr):
    s_syn = score(syn_comp, w)
    s_real = score(real_comp, w)
    t_syn = tier1(s_syn, thr)
    t_real = tier1(s_real, thr) & has_noaa
    n_syn30 = int(t_syn.sum())
    n_syn29 = int((t_syn & has_noaa).sum())
    n_real = int(t_real.sum())
    kept = int((t_syn & t_real).sum())
    gained = int((~t_syn & t_real).sum())
    return n_syn30, n_syn29, n_real, kept, gained


def normalise(w):
    return w / w.sum()


def weight_configs():
    cfgs = [("base", BASE_W.copy())]
    names = ["thermal", "urgency", "rugosity", "water"]
    for i, n in enumerate(names):
        for sgn, lab in ((+1, "+20%"), (-1, "-20%")):
            w = BASE_W.copy()
            w[i] *= 1 + sgn * PERT
            cfgs.append((f"OAT {n} {lab}", normalise(w)))
    for signs in itertools.product((-1, +1), repeat=4):
        w = BASE_W * (1 + PERT * np.array(signs))
        lab = "".join("+" if s > 0 else "-" for s in signs)
        cfgs.append((f"corner {lab}", normalise(w)))
    return cfgs


def run_station_bootstrap(strict_syn, strict_real, lin_syn, lin_real, has_noaa, n_boot=10000, seed=42):
    """
    Runs 10,000 non-parametric bootstrap resamples over stations (with replacement)
    for each threshold {0.60, 0.65, 0.70, 0.75, 0.80} and also computes bootstrap 95% CI
    for Spearman rank correlation between synthetic and NOAA SRPI scores.
    """
    rng = np.random.default_rng(seed)
    valid_idx = np.where(has_noaa)[0]
    n_valid = len(valid_idx)
    n_all = len(has_noaa)

    boot_rows = []
    for form, syn_c, real_c in (("strict_Eq7", strict_syn, strict_real), ("linear_variant", lin_syn, lin_real)):
        s_syn_all = score(syn_c, BASE_W)
        s_real_all = score(real_c, BASE_W)

        # Bootstrap Spearman correlation across the 29 valid stations
        rho_samples = np.zeros(n_boot, dtype=float)
        for b in range(n_boot):
            b_idx = rng.choice(valid_idx, size=n_valid, replace=True)
            if np.std(s_syn_all[b_idx]) > 1e-9 and np.std(s_real_all[b_idx]) > 1e-9:
                rho_val, _ = spearmanr(s_syn_all[b_idx], s_real_all[b_idx])
                rho_samples[b] = 0.0 if np.isnan(rho_val) else float(rho_val)

        for thr in THRESHOLDS:
            t_syn_30 = tier1(s_syn_all, thr)
            t_syn_29 = t_syn_30[valid_idx]
            t_real_29 = tier1(s_real_all[valid_idx], thr)
            kept_29 = t_syn_29 & t_real_29

            # Draw B=10,000 station resamples
            idx_30 = rng.integers(0, n_all, size=(n_boot, n_all))
            idx_29 = rng.integers(0, n_valid, size=(n_boot, n_valid))

            syn30_boot = t_syn_30[idx_30].sum(axis=1)
            syn29_boot = t_syn_29[idx_29].sum(axis=1)
            real29_boot = t_real_29[idx_29].sum(axis=1)
            kept29_boot = kept_29[idx_29].sum(axis=1)
            pres_rate_boot = np.where(syn29_boot > 0, 100.0 * kept29_boot / syn29_boot, 0.0)

            boot_rows.append({
                "Formulation": form,
                "Threshold": thr,
                "N_Bootstrap": n_boot,
                "Boot_Syn30_Mean": round(float(syn30_boot.mean()), 2),
                "Boot_Syn30_CI_lo": round(float(np.percentile(syn30_boot, 2.5)), 1),
                "Boot_Syn30_CI_hi": round(float(np.percentile(syn30_boot, 97.5)), 1),
                "Boot_NOAA29_Mean": round(float(real29_boot.mean()), 2),
                "Boot_NOAA29_CI_lo": round(float(np.percentile(real29_boot, 2.5)), 1),
                "Boot_NOAA29_CI_hi": round(float(np.percentile(real29_boot, 97.5)), 1),
                "Boot_Preserved_Mean": round(float(kept29_boot.mean()), 2),
                "Boot_Preserved_CI_lo": round(float(np.percentile(kept29_boot, 2.5)), 1),
                "Boot_Preserved_CI_hi": round(float(np.percentile(kept29_boot, 97.5)), 1),
                "Boot_Preservation_Pct_Mean": round(float(pres_rate_boot.mean()), 2),
                "Boot_Preservation_Pct_CI_lo": round(float(np.percentile(pres_rate_boot, 2.5)), 1),
                "Boot_Preservation_Pct_CI_hi": round(float(np.percentile(pres_rate_boot, 97.5)), 1),
                "Boot_SRPI_Spearman_Mean": round(float(rho_samples.mean()), 4),
                "Boot_SRPI_Spearman_CI_lo": round(float(np.percentile(rho_samples, 2.5)), 4),
                "Boot_SRPI_Spearman_CI_hi": round(float(np.percentile(rho_samples, 97.5)), 4),
            })

    return pd.DataFrame(boot_rows)


def run_loso_sensitivity(st, strict_syn, strict_real, lin_syn, lin_real, has_noaa):
    """
    Runs Leave-One-Station-Out (LOSO) jackknife analysis across all 30 stations
    across thresholds {0.60, 0.65, 0.70, 0.75, 0.80}.
    """
    loso_rows = []
    n_total = len(st)

    for form, syn_c, real_c in (("strict_Eq7", strict_syn, strict_real), ("linear_variant", lin_syn, lin_real)):
        s_syn = score(syn_c, BASE_W)
        s_real = score(real_c, BASE_W)

        for drop_i in range(n_total):
            keep_mask = np.ones(n_total, dtype=bool)
            keep_mask[drop_i] = False
            st_dropped = st.loc[drop_i, "Station_Name"]
            st_id_dropped = st.loc[drop_i, "Station_ID"]

            valid_sub = keep_mask & has_noaa
            rho_loso, p_loso = spearmanr(s_syn[valid_sub], s_real[valid_sub])

            for thr in THRESHOLDS:
                t_syn_sub = tier1(s_syn[keep_mask], thr)
                t_syn_valid = tier1(s_syn[valid_sub], thr)
                t_real_valid = tier1(s_real[valid_sub], thr)
                kept_valid = int((t_syn_valid & t_real_valid).sum())
                n_syn_29_sub = int(t_syn_valid.sum())

                loso_rows.append({
                    "Formulation": form,
                    "Threshold": thr,
                    "Dropped_Station_ID": st_id_dropped,
                    "Dropped_Station_Name": st_dropped,
                    "LOSO_Tier1_Syn_N29_of_30": int(t_syn_sub.sum()),
                    "LOSO_Tier1_Syn_Valid_NOAA": n_syn_29_sub,
                    "LOSO_Tier1_Real_NOAA": int(t_real_valid.sum()),
                    "LOSO_Preserved": kept_valid,
                    "LOSO_Preservation_Pct": round(100.0 * kept_valid / n_syn_29_sub, 2) if n_syn_29_sub > 0 else 0.0,
                    "LOSO_SRPI_Spearman_rho": round(float(rho_loso), 4),
                    "LOSO_SRPI_Spearman_p": round(float(p_loso), 4),
                })

    return pd.DataFrame(loso_rows)


def main():
    st, strict_syn, strict_real, strict_cal, lin_syn, lin_real = station_components()
    has = st["has_noaa"].to_numpy()
    print(f"Stations: {len(st)}; with valid NOAA pixel: {int(has.sum())}")

    # ---- reproduction checks vs repository outputs -----------------------------------------
    rk = pd.read_csv(RANKING_PATH).set_index("Station_ID")["Spatial_Restoration_Priority_Index_SRPI"]
    mine = pd.Series(score(strict_syn, BASE_W), index=st["Station_ID"])
    max_dev = float((mine - rk.loc[mine.index]).abs().max())
    print(f"Max |synthetic SRPI (mine) - repository ranking CSV| = {max_dev:.4f}")
    noaa_csv = pd.read_csv(NOAA_PATH).set_index("Station_ID")
    lin_syn_dev = float(
        (pd.Series(score(lin_syn, BASE_W), index=st["Station_ID"]).loc[noaa_csv.index] - noaa_csv["Synthetic_SRPI_Eq7"]).abs().max()
    )
    lin_real_dev = float(
        (pd.Series(score(lin_real, BASE_W), index=st["Station_ID"]).loc[noaa_csv.index] - noaa_csv["Real_SRPI_Eq7"]).abs().max()
    )
    print(f"Linear variant max deviation vs results/noaa_crw_validation.csv: syn {lin_syn_dev:.4f} real {lin_real_dev:.4f}")

    # station score table (base weights)
    sc = st[["Station_ID", "Station_Name", "Region", "has_noaa", "DHW95_syn", "Real_NOAA_DHW_95th", "Cal_Full_DHW_95th"]].copy()
    sc["SRPI_strict_synthetic"] = score(strict_syn, BASE_W)
    sc["SRPI_strict_NOAA"] = np.where(has, score(strict_real, BASE_W), np.nan)
    sc["SRPI_strict_calibrated"] = score(strict_cal, BASE_W)
    sc["SRPI_linear_synthetic"] = score(lin_syn, BASE_W)
    sc["SRPI_linear_NOAA"] = np.where(has, score(lin_real, BASE_W), np.nan)
    sc.to_csv(os.path.join(RESULTS_DIR, "srpi_sensitivity_station_scores.csv"), index=False)

    # ---- (a)+(b) threshold x weights grid ------------------------------------------------------
    rows = []
    cfgs = weight_configs()
    for form, syn_c, real_c in (("strict_Eq7", strict_syn, strict_real), ("linear_variant", lin_syn, lin_real)):
        for wname, w in cfgs:
            for thr in THRESHOLDS:
                n30, n29, nr, kept, gained = evaluate(syn_c, real_c, has, w, thr)
                rows.append({
                    "Formulation": form,
                    "Weights": wname,
                    "w_thermal": round(w[0], 4),
                    "w_urgency": round(w[1], 4),
                    "w_rugosity": round(w[2], 4),
                    "w_water": round(w[3], 4),
                    "Threshold": thr,
                    "Tier1_synthetic_N30": n30,
                    "Tier1_synthetic_N29": n29,
                    "Tier1_NOAA_N29": nr,
                    "Preserved": kept,
                    "Gained_only_NOAA": gained,
                    "Preservation_pct": round(100.0 * kept / n29, 2) if n29 > 0 else np.nan,
                })
    grid = pd.DataFrame(rows)
    grid.to_csv(os.path.join(RESULTS_DIR, "srpi_threshold_weight_sensitivity.csv"), index=False)

    base = grid[(grid["Weights"] == "base")].copy()
    base.to_csv(os.path.join(RESULTS_DIR, "srpi_threshold_sensitivity_base.csv"), index=False)

    # ---- random +-20 % perturbation (10,000 draws) ---------------------------------------------
    rng = np.random.default_rng(SEED)
    rand_rows = []
    W = BASE_W[None, :] * rng.uniform(1 - PERT, 1 + PERT, size=(N_RANDOM, 4))
    W = W / W.sum(axis=1, keepdims=True)
    for form, syn_c, real_c in (("strict_Eq7", strict_syn, strict_real), ("linear_variant", lin_syn, lin_real)):
        for thr in THRESHOLDS:
            res = np.array([evaluate(syn_c, real_c, has, w, thr) for w in W])
            for lab, col in (("Tier1_synthetic_N30", 0), ("Tier1_NOAA_N29", 2), ("Preserved", 3)):
                v = res[:, col]
                rand_rows.append({
                    "Formulation": form,
                    "Threshold": thr,
                    "Quantity": lab,
                    "Mean": round(float(v.mean()), 2),
                    "Median": float(np.median(v)),
                    "P2.5": float(np.percentile(v, 2.5)),
                    "P97.5": float(np.percentile(v, 97.5)),
                    "Min": int(v.min()),
                    "Max": int(v.max()),
                    "N_draws": N_RANDOM,
                })
    rand_df = pd.DataFrame(rand_rows)
    rand_df.to_csv(os.path.join(RESULTS_DIR, "srpi_weight_sensitivity_random.csv"), index=False)

    # ---- envelope over ALL weight perturbations (8 one-at-a-time + 16 corners + 10,000 random) --
    env_rows = []
    pert = grid[grid["Weights"] != "base"]
    for form in ("strict_Eq7", "linear_variant"):
        for thr in THRESHOLDS:
            g_ = pert[(pert["Formulation"] == form) & (pert["Threshold"] == thr)]
            r_ = rand_df[(rand_df["Formulation"] == form) & (rand_df["Threshold"] == thr)].set_index("Quantity")
            for lab, gcol in (
                ("Tier1_synthetic_N30", "Tier1_synthetic_N30"),
                ("Tier1_NOAA_N29", "Tier1_NOAA_N29"),
                ("Preserved", "Preserved"),
            ):
                env_rows.append({
                    "Formulation": form,
                    "Threshold": thr,
                    "Quantity": lab,
                    "Envelope_min": int(min(g_[gcol].min(), r_.loc[lab, "Min"])),
                    "Envelope_max": int(max(g_[gcol].max(), r_.loc[lab, "Max"])),
                    "Random_median": float(r_.loc[lab, "Median"]),
                    "Random_P2.5": float(r_.loc[lab, "P2.5"]),
                    "Random_P97.5": float(r_.loc[lab, "P97.5"]),
                    "n_configs": int(len(g_) + N_RANDOM),
                })
    env_df = pd.DataFrame(env_rows)
    env_df.to_csv(os.path.join(RESULTS_DIR, "srpi_weight_sensitivity_envelope.csv"), index=False)

    # ---- Station Bootstrap (B = 10,000) & Leave-One-Station-Out (LOSO) --------------------------
    boot_df = run_station_bootstrap(strict_syn, strict_real, lin_syn, lin_real, has, n_boot=N_BOOTSTRAP, seed=SEED)
    boot_df.to_csv(os.path.join(RESULTS_DIR, "srpi_bootstrap_10000.csv"), index=False)

    loso_df = run_loso_sensitivity(st, strict_syn, strict_real, lin_syn, lin_real, has)
    loso_df.to_csv(os.path.join(RESULTS_DIR, "srpi_loso_sensitivity.csv"), index=False)

    # ---- Build Unified Master Table `results/srpi_sensitivity.csv` (Table 8b) -------------------
    master_rows = []
    for form in ("strict_Eq7", "linear_variant"):
        for thr in THRESHOLDS:
            b_row = base[(base["Formulation"] == form) & (base["Threshold"] == thr)].iloc[0]
            e_sub = env_df[(env_df["Formulation"] == form) & (env_df["Threshold"] == thr)].set_index("Quantity")
            bt_row = boot_df[(boot_df["Formulation"] == form) & (boot_df["Threshold"] == thr)].iloc[0]
            l_sub = loso_df[(loso_df["Formulation"] == form) & (loso_df["Threshold"] == thr)]

            # Also evaluate calibrated synthetic vs real NOAA at this threshold
            _, n_cal29, n_real29, kept_cal, _ = evaluate(strict_cal, strict_real, has, BASE_W, thr)

            master_rows.append({
                "Formulation": form,
                "Threshold": thr,
                "Base_Tier1_Syn_N30": int(b_row["Tier1_synthetic_N30"]),
                "Base_Tier1_Syn_N29": int(b_row["Tier1_synthetic_N29"]),
                "Base_Tier1_NOAA_N29": int(b_row["Tier1_NOAA_N29"]),
                "Base_Preserved": int(b_row["Preserved"]),
                "Base_Gained_NOAA": int(b_row["Gained_only_NOAA"]),
                "Base_Preservation_Pct": float(b_row["Preservation_pct"]) if not np.isnan(b_row["Preservation_pct"]) else 0.0,
                "Calibrated_Tier1_Syn_N29": int(n_cal29),
                "Calibrated_Preserved_vs_NOAA": int(kept_cal),
                # Weight +-20% sensitivity (OAT + 16 corners + 10,000 random draws)
                "Weights20_Syn_Min": int(e_sub.loc["Tier1_synthetic_N30", "Envelope_min"]),
                "Weights20_Syn_Max": int(e_sub.loc["Tier1_synthetic_N30", "Envelope_max"]),
                "Weights20_Syn_Median": float(e_sub.loc["Tier1_synthetic_N30", "Random_median"]),
                "Weights20_Syn_P2.5": float(e_sub.loc["Tier1_synthetic_N30", "Random_P2.5"]),
                "Weights20_Syn_P97.5": float(e_sub.loc["Tier1_synthetic_N30", "Random_P97.5"]),
                "Weights20_NOAA_Min": int(e_sub.loc["Tier1_NOAA_N29", "Envelope_min"]),
                "Weights20_NOAA_Max": int(e_sub.loc["Tier1_NOAA_N29", "Envelope_max"]),
                "Weights20_NOAA_Median": float(e_sub.loc["Tier1_NOAA_N29", "Random_median"]),
                "Weights20_NOAA_P2.5": float(e_sub.loc["Tier1_NOAA_N29", "Random_P2.5"]),
                "Weights20_NOAA_P97.5": float(e_sub.loc["Tier1_NOAA_N29", "Random_P97.5"]),
                "Weights20_Preserved_Min": int(e_sub.loc["Preserved", "Envelope_min"]),
                "Weights20_Preserved_Max": int(e_sub.loc["Preserved", "Envelope_max"]),
                "Weights20_Preserved_Median": float(e_sub.loc["Preserved", "Random_median"]),
                "Weights20_Preserved_P2.5": float(e_sub.loc["Preserved", "Random_P2.5"]),
                "Weights20_Preserved_P97.5": float(e_sub.loc["Preserved", "Random_P97.5"]),
                # Station Bootstrap 10,000
                "Bootstrap10k_Preserved_Mean": float(bt_row["Boot_Preserved_Mean"]),
                "Bootstrap10k_Preserved_CI_lo": float(bt_row["Boot_Preserved_CI_lo"]),
                "Bootstrap10k_Preserved_CI_hi": float(bt_row["Boot_Preserved_CI_hi"]),
                "Bootstrap10k_Preservation_Pct_Mean": float(bt_row["Boot_Preservation_Pct_Mean"]),
                "Bootstrap10k_Preservation_Pct_CI_lo": float(bt_row["Boot_Preservation_Pct_CI_lo"]),
                "Bootstrap10k_Preservation_Pct_CI_hi": float(bt_row["Boot_Preservation_Pct_CI_hi"]),
                # Leave-One-Station-Out (LOSO) range across 30 jackknife folds
                "LOSO_Syn_Min": int(l_sub["LOSO_Tier1_Syn_N29_of_30"].min()),
                "LOSO_Syn_Max": int(l_sub["LOSO_Tier1_Syn_N29_of_30"].max()),
                "LOSO_NOAA_Min": int(l_sub["LOSO_Tier1_Real_NOAA"].min()),
                "LOSO_NOAA_Max": int(l_sub["LOSO_Tier1_Real_NOAA"].max()),
                "LOSO_Preserved_Min": int(l_sub["LOSO_Preserved"].min()),
                "LOSO_Preserved_Max": int(l_sub["LOSO_Preserved"].max()),
                "LOSO_Preservation_Pct_Min": float(l_sub["LOSO_Preservation_Pct"].min()),
                "LOSO_Preservation_Pct_Max": float(l_sub["LOSO_Preservation_Pct"].max()),
            })

    master_df = pd.DataFrame(master_rows)
    master_df.to_csv(os.path.join(RESULTS_DIR, "srpi_sensitivity.csv"), index=False)
    print("\nSaved unified SRPI sensitivity table to: results/srpi_sensitivity.csv")
    print(master_df.to_string(index=False))

    # ---- record-level synthetic counts (15,000 records) ------------------------------------------
    df = pd.read_csv(DATA_PATH)
    p95 = st.set_index("Station_ID")["DHW95_syn"]
    d95 = df["Station_ID"].map(p95)
    obs = np.round(
        0.35 * (1.0 - np.minimum(d95 / 16.0, 1.0))
        + 0.25 * np.clip(1.0 - df["Live_Coral_Cover_Pct"] / 50.0, 0, 1)
        + 0.25 * np.clip((df["Structural_Rugosity"] - 1.0) / 2.0, 0, 1)
        + 0.15 * (1.0 - np.minimum(0.04 * df["Turbidity_NTU"] / 0.25, 1.0)),
        3,
    )
    rec = {f"{t:.2f}": int((obs >= t - EPS).sum()) for t in THRESHOLDS}

    near = []
    for thr in THRESHOLDS:
        for lab, col in (("synthetic", "SRPI_strict_synthetic"), ("NOAA", "SRPI_strict_NOAA")):
            d = (sc[col] - thr).abs()
            for i in sc.index[d <= 0.005]:
                near.append(f"{sc.loc[i,'Station_Name']} {lab} {sc.loc[i,col]:.3f} vs {thr:.2f}")

    with open(os.path.join(RESULTS_DIR, "srpi_sensitivity_summary.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "thresholds": THRESHOLDS,
                "base_weights": BASE_W.tolist(),
                "weight_perturbation": PERT,
                "renormalised": True,
                "n_random_draws": N_RANDOM,
                "n_bootstrap_draws": N_BOOTSTRAP,
                "seed": SEED,
                "n_stations": int(len(st)),
                "n_stations_noaa": int(has.sum()),
                "max_dev_vs_repo_ranking": max_dev,
                "record_level_synthetic_tier1": rec,
                "stations_within_0.005": near,
            },
            f,
            indent=2,
        )


if __name__ == "__main__":
    main()
