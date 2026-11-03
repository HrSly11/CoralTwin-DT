"""
CoralTwin-DT: SRPI sensitivity analysis (reviewer-requested, manuscript Sections 3.3 and 3.4)
==============================================================================================
Recomputes the Spatial Restoration Priority Index (Eq. 7, Section 2.7) while varying

  (a) the Tier-1 threshold: {0.60, 0.65, 0.70, 0.75, 0.80}
  (b) the four weights 0.35 / 0.25 / 0.25 / 0.15, perturbed by +-20 % (each weight multiplied by
      0.8 or 1.2, then the weight vector is re-normalised to sum to 1 so that thresholds keep their
      meaning). Three designs: one-at-a-time (8 configs), all 2^4 = 16 sign corners, and 10,000
      random draws with every weight multiplied by U(0.8, 1.2) (seed 42).

For every (threshold, weights) pair it reports how many stations are Tier 1 with the synthetic
dataset (N = 30 and N = 29 stations with valid NOAA pixel), how many with real NOAA CRW 95th
percentile DHW (N = 29), and how many synthetic Tier-1 stations are preserved.

Formulation used for the main analysis = strict Eq. 7 exactly as in
08_GIS_and_Remote_Sensing/spatial_pipeline.py; the NOAA variant only swaps DHW_95th (thermal
refugia) for the NOAA CRW value stored in results/noaa_crw_validation.csv; the other three
components are unchanged. The simplified "linear" variant of 03_Data/fetch_noaa_crw_real_dhw.py is
also analysed as a secondary robustness check.

Scores are rounded to 3 decimals before applying ">= threshold", as the repository does.

Outputs (results/): srpi_threshold_weight_sensitivity.csv, srpi_threshold_sensitivity_base.csv,
srpi_weight_sensitivity_random.csv, srpi_sensitivity_station_scores.csv, srpi_sensitivity_summary.json
"""

import os
import json
import itertools

import numpy as np
import pandas as pd

SEED = 42
THRESHOLDS = [0.60, 0.65, 0.70, 0.75, 0.80]
BASE_W = np.array([0.35, 0.25, 0.25, 0.15])  # thermal refugia, urgency, rugosity, water quality / connectivity
PERT = 0.20
N_RANDOM = 10000
EPS = 1e-9

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_PATH = os.path.join(PROJECT_ROOT, "03_Data", "final_dataset.csv")
RANKING_PATH = os.path.join(BASE_DIR, "geospatial_outputs", "spatial_restoration_priority_ranking.csv")
NOAA_PATH = os.path.join(PROJECT_ROOT, "results", "noaa_crw_validation.csv")
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

    noaa = pd.read_csv(NOAA_PATH)[["Station_ID", "Real_NOAA_DHW_95th", "Connectivity_H",
                                   "Mean_Live_Coral_Cover_Pct", "Mean_Structural_Rugosity",
                                   "Synthetic_DHW_95th"]]
    st = st.merge(noaa, on="Station_ID", how="left")
    st["has_noaa"] = st["Real_NOAA_DHW_95th"].notna()

    urg = np.clip(1.0 - st["Live_Coral_Cover_Pct"] / 50.0, 0.0, 1.0)
    rug = np.clip((st["Structural_Rugosity"] - 1.0) / 2.0, 0.0, 1.0)
    wq = 1.0 - np.minimum(0.04 * st["Turbidity_NTU"] / 0.25, 1.0)
    th_syn = 1.0 - np.minimum(st["DHW95_syn"] / 16.0, 1.0)
    th_real = 1.0 - np.minimum(st["Real_NOAA_DHW_95th"] / 16.0, 1.0)

    # Strict Eq. 7 component matrices (columns: therm, urgency, rugosity, water quality)
    strict_syn = np.column_stack([th_syn, urg, rug, wq])
    strict_real = np.column_stack([th_real, urg, rug, wq])

    # Simplified linear variant (fetch_noaa_crw_real_dhw.py)
    c = st["Mean_Live_Coral_Cover_Pct"]
    r = st["Mean_Structural_Rugosity"]
    conn = st["Connectivity_H"]
    lin_syn = np.column_stack([1.0 - np.minimum(st["Synthetic_DHW_95th"] / 12.0, 1.0),
                               1.0 - c / 100.0, r / 3.5, conn])
    lin_real = np.column_stack([1.0 - np.minimum(st["Real_NOAA_DHW_95th"] / 12.0, 1.0),
                                1.0 - c / 100.0, r / 3.5, conn])
    return st, strict_syn, strict_real, lin_syn, lin_real


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


def main():
    st, strict_syn, strict_real, lin_syn, lin_real = station_components()
    has = st["has_noaa"].to_numpy()
    print(f"Stations: {len(st)}; with valid NOAA pixel: {int(has.sum())}")

    # ---- reproduction checks vs repository outputs -----------------------------------------
    rk = pd.read_csv(RANKING_PATH).set_index("Station_ID")["Spatial_Restoration_Priority_Index_SRPI"]
    mine = pd.Series(score(strict_syn, BASE_W), index=st["Station_ID"])
    max_dev = float((mine - rk.loc[mine.index]).abs().max())
    print(f"Max |synthetic SRPI (mine) - repository ranking CSV| = {max_dev:.4f}")
    noaa_csv = pd.read_csv(NOAA_PATH).set_index("Station_ID")
    lin_syn_dev = float((pd.Series(score(lin_syn, BASE_W), index=st["Station_ID"]).loc[noaa_csv.index]
                         - noaa_csv["Synthetic_SRPI_Eq7"]).abs().max())
    lin_real_dev = float((pd.Series(score(lin_real, BASE_W), index=st["Station_ID"]).loc[noaa_csv.index]
                          - noaa_csv["Real_SRPI_Eq7"]).abs().max())
    print(f"Linear variant max deviation vs results/noaa_crw_validation.csv: syn {lin_syn_dev:.4f} real {lin_real_dev:.4f}")

    # station score table (base weights)
    sc = st[["Station_ID", "Station_Name", "Region", "has_noaa", "DHW95_syn", "Real_NOAA_DHW_95th"]].copy()
    sc["SRPI_strict_synthetic"] = score(strict_syn, BASE_W)
    sc["SRPI_strict_NOAA"] = np.where(has, score(strict_real, BASE_W), np.nan)
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
                    "Formulation": form, "Weights": wname,
                    "w_thermal": round(w[0], 4), "w_urgency": round(w[1], 4),
                    "w_rugosity": round(w[2], 4), "w_water": round(w[3], 4),
                    "Threshold": thr,
                    "Tier1_synthetic_N30": n30, "Tier1_synthetic_N29": n29,
                    "Tier1_NOAA_N29": nr, "Preserved": kept, "Gained_only_NOAA": gained,
                    "Preservation_pct": round(100.0 * kept / n29, 2) if n29 > 0 else np.nan,
                })
    grid = pd.DataFrame(rows)
    grid.to_csv(os.path.join(RESULTS_DIR, "srpi_threshold_weight_sensitivity.csv"), index=False)

    base = grid[(grid["Weights"] == "base")]
    base.to_csv(os.path.join(RESULTS_DIR, "srpi_threshold_sensitivity_base.csv"), index=False)
    print("\nBASE WEIGHTS")
    print(base.drop(columns=["Weights", "w_thermal", "w_urgency", "w_rugosity", "w_water"]).to_string(index=False))

    corners = grid[grid["Weights"].str.startswith("corner") | (grid["Weights"] == "base")]
    oat = grid[grid["Weights"].str.startswith("OAT") | (grid["Weights"] == "base")]
    print("\nRANGE over 16 sign corners (+base) per formulation/threshold")
    agg = corners.groupby(["Formulation", "Threshold"]).agg(
        syn_min=("Tier1_synthetic_N30", "min"), syn_max=("Tier1_synthetic_N30", "max"),
        noaa_min=("Tier1_NOAA_N29", "min"), noaa_max=("Tier1_NOAA_N29", "max"),
        kept_min=("Preserved", "min"), kept_max=("Preserved", "max")).reset_index()
    print(agg.to_string(index=False))
    print("\nRANGE over one-at-a-time perturbations (+base)")
    agg2 = oat.groupby(["Formulation", "Threshold"]).agg(
        syn_min=("Tier1_synthetic_N30", "min"), syn_max=("Tier1_synthetic_N30", "max"),
        noaa_min=("Tier1_NOAA_N29", "min"), noaa_max=("Tier1_NOAA_N29", "max"),
        kept_min=("Preserved", "min"), kept_max=("Preserved", "max")).reset_index()
    print(agg2.to_string(index=False))

    # ---- random +-20 % perturbation ------------------------------------------------------------
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
                    "Formulation": form, "Threshold": thr, "Quantity": lab,
                    "Mean": round(float(v.mean()), 2), "Median": float(np.median(v)),
                    "P2.5": float(np.percentile(v, 2.5)), "P97.5": float(np.percentile(v, 97.5)),
                    "Min": int(v.min()), "Max": int(v.max()), "N_draws": N_RANDOM,
                })
    rand_df = pd.DataFrame(rand_rows)
    rand_df.to_csv(os.path.join(RESULTS_DIR, "srpi_weight_sensitivity_random.csv"), index=False)

    # ---- envelope over ALL weight perturbations (8 one-at-a-time + 16 corners + random draws) ---
    env_rows = []
    pert = grid[grid["Weights"] != "base"]
    for form in ("strict_Eq7", "linear_variant"):
        for thr in THRESHOLDS:
            g_ = pert[(pert["Formulation"] == form) & (pert["Threshold"] == thr)]
            r_ = rand_df[(rand_df["Formulation"] == form) & (rand_df["Threshold"] == thr)].set_index("Quantity")
            for lab, gcol in (("Tier1_synthetic_N30", "Tier1_synthetic_N30"),
                              ("Tier1_NOAA_N29", "Tier1_NOAA_N29"), ("Preserved", "Preserved")):
                env_rows.append({
                    "Formulation": form, "Threshold": thr, "Quantity": lab,
                    "Envelope_min": int(min(g_[gcol].min(), r_.loc[lab, "Min"])),
                    "Envelope_max": int(max(g_[gcol].max(), r_.loc[lab, "Max"])),
                    "Random_median": float(r_.loc[lab, "Median"]),
                    "Random_P2.5": float(r_.loc[lab, "P2.5"]), "Random_P97.5": float(r_.loc[lab, "P97.5"]),
                    "n_configs": int(len(g_) + N_RANDOM),
                })
    env_df = pd.DataFrame(env_rows)
    env_df.to_csv(os.path.join(RESULTS_DIR, "srpi_weight_sensitivity_envelope.csv"), index=False)
    print("\nENVELOPE over all weight perturbations (strict Eq.7)")
    print(env_df[env_df["Formulation"] == "strict_Eq7"].to_string(index=False))

    # in how many perturbed configs does NOAA identify at least as many Tier-1 stations as the synthetic data?
    bad = pert[(pert["Formulation"] == "strict_Eq7") & (pert["Tier1_NOAA_N29"] >= pert["Tier1_synthetic_N29"])
               & (pert["Tier1_synthetic_N29"] > 0)]
    print(f"\nDeterministic weight configs (strict) where NOAA Tier-1 count >= synthetic count (synthetic>0): {len(bad)}")
    print("\nRANDOM weights (strict Eq.7)")
    print(rand_df[rand_df["Formulation"] == "strict_Eq7"].to_string(index=False))

    # ---- record-level synthetic counts (15,000 records) ------------------------------------------
    df = pd.read_csv(DATA_PATH)
    p95 = st.set_index("Station_ID")["DHW95_syn"]
    d95 = df["Station_ID"].map(p95)
    obs = np.round(0.35 * (1.0 - np.minimum(d95 / 16.0, 1.0))
                   + 0.25 * np.clip(1.0 - df["Live_Coral_Cover_Pct"] / 50.0, 0, 1)
                   + 0.25 * np.clip((df["Structural_Rugosity"] - 1.0) / 2.0, 0, 1)
                   + 0.15 * (1.0 - np.minimum(0.04 * df["Turbidity_NTU"] / 0.25, 1.0)), 3)
    rec = {f"{t:.2f}": int((obs >= t - EPS).sum()) for t in THRESHOLDS}
    print("\nRecord-level synthetic Tier-1 counts (N=15,000):", rec)

    # margin of stations to thresholds (how close stations are to a cut)
    near = []
    for thr in THRESHOLDS:
        for lab, col in (("synthetic", "SRPI_strict_synthetic"), ("NOAA", "SRPI_strict_NOAA")):
            d = (sc[col] - thr).abs()
            for i in sc.index[d <= 0.005]:
                near.append(f"{sc.loc[i,'Station_Name']} {lab} {sc.loc[i,col]:.3f} vs {thr:.2f}")
    print("\nStations within 0.005 of a threshold:", near)

    with open(os.path.join(RESULTS_DIR, "srpi_sensitivity_summary.json"), "w", encoding="utf-8") as f:
        json.dump({
            "thresholds": THRESHOLDS, "base_weights": BASE_W.tolist(), "weight_perturbation": PERT,
            "renormalised": True, "n_random_draws": N_RANDOM, "seed": SEED,
            "n_stations": int(len(st)), "n_stations_noaa": int(has.sum()),
            "max_dev_vs_repo_ranking": max_dev,
            "record_level_synthetic_tier1": rec, "stations_within_0.005": near,
        }, f, indent=2)


if __name__ == "__main__":
    main()
