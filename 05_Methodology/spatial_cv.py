"""
CoralTwin-DT: 5-Fold Spatially Clustered & Biogeographically Stratified Cross-Validation
========================================================================================
Implements the 5-fold spatial block cross-validation scheme across the 30 global
benchmark stations (N = 15,000 observations, 6 stations = 3,000 observations per fold),
enforcing a strict 25 km Haversine spatial buffer (`Buffer_km = 25.0`) between
training and validation sets.

Addresses Audit Finding CRIT-02 (Unimplemented 25 km Spatial Buffer & Random KFold Leakage).

Outputs:
- `results/folds_assignment.csv`
- `09_Results/tables/folds_assignment.csv`
- `results/spatial_folds_diagram.png`
- `09_Results/figures/Fig_spatial_folds_diagram.png`
"""

import os
import sys
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_CSV = os.path.join(PROJECT_ROOT, "03_Data", "final_dataset.csv")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
TABLES_DIR = os.path.join(PROJECT_ROOT, "09_Results", "tables")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "09_Results", "figures")

for d in [RESULTS_DIR, TABLES_DIR, FIGURES_DIR]:
    os.makedirs(d, exist_ok=True)


# Canonical 5-fold spatially clustered and biogeographically stratified assignment
SPATIAL_FOLD_ASSIGNMENT = {
    # Fold 1
    "Mesoamerican_Fore_01": (1, "CLUST_01_Mesoamerican"),
    "Mesoamerican_Crest_02": (1, "CLUST_01_Mesoamerican"),
    "Mesoamerican_Back_03": (1, "CLUST_01_Mesoamerican"),
    "Mesoamerican_Lagoon_04": (1, "CLUST_01_Mesoamerican"),
    "GreatBarrier_Northern_13": (1, "CLUST_09_GBR_North"),
    "RedSea_Aqaba_23": (1, "CLUST_18_RedSea_Aqaba"),

    # Fold 2
    "Cozumel_South_07": (2, "CLUST_04_Cozumel"),
    "Cozumel_Shallow_08": (2, "CLUST_04_Cozumel"),
    "GreatBarrier_Central_14": (2, "CLUST_10_GBR_Central"),
    "GreatBarrier_Lagoon_15": (2, "CLUST_10_GBR_Central"),
    "RedSea_Shallow_24": (2, "CLUST_19_RedSea_Shallow"),
    "Seychelles_Mahe_26": (2, "CLUST_21_Seychelles"),

    # Fold 3
    "Roatan_North_09": (3, "CLUST_05_Roatan"),
    "Roatan_South_10": (3, "CLUST_05_Roatan"),
    "CoralTriangle_RajaAmpat_16": (3, "CLUST_11_RajaAmpat"),
    "CoralTriangle_Misool_17": (3, "CLUST_12_Misool"),
    "RedSea_Farasan_25": (3, "CLUST_20_RedSea_Farasan"),
    "Maldives_AriAtoll_27": (3, "CLUST_22_Maldives"),

    # Fold 4
    "Belize_Barrier_05": (4, "CLUST_02_Belize_Barrier"),
    "Belize_Atoll_06": (4, "CLUST_03_Belize_Atoll"),
    "CoralTriangle_Komodo_18": (4, "CLUST_13_Komodo"),
    "CoralTriangle_Sulawesi_19": (4, "CLUST_14_Sulawesi"),
    "Hawaii_Kaneohe_28": (4, "CLUST_23_Hawaii_Oahu"),
    "Hawaii_OahuFore_29": (4, "CLUST_23_Hawaii_Oahu"),

    # Fold 5
    "Florida_Keys_Uppers_11": (5, "CLUST_06_Florida_Uppers"),
    "Florida_Keys_Lowers_12": (5, "CLUST_07_Florida_Lowers"),
    "CoralTriangle_Bali_20": (5, "CLUST_15_Bali"),
    "Okinawa_Kerama_21": (5, "CLUST_16_Okinawa_Kerama"),
    "Okinawa_Ishigaki_22": (5, "CLUST_17_Okinawa_Ishigaki"),
    "Palau_RockIslands_30": (5, "CLUST_24_Palau"),
}


# Canonical station nominal coordinates (matches 03_Data/build_final_dataset.py)
STATION_NOMINAL_COORDS = {
    "Mesoamerican_Fore_01": ("STN_01", 18.250, -87.800),
    "Mesoamerican_Crest_02": ("STN_02", 18.280, -87.820),
    "Mesoamerican_Back_03": ("STN_03", 18.310, -87.850),
    "Mesoamerican_Lagoon_04": ("STN_04", 18.350, -87.880),
    "Belize_Barrier_05": ("STN_05", 17.150, -87.900),
    "Belize_Atoll_06": ("STN_06", 17.200, -87.550),
    "Cozumel_South_07": ("STN_07", 20.300, -87.020),
    "Cozumel_Shallow_08": ("STN_08", 20.350, -86.980),
    "Roatan_North_09": ("STN_09", 16.380, -86.500),
    "Roatan_South_10": ("STN_10", 16.320, -86.550),
    "Florida_Keys_Uppers_11": ("STN_11", 25.020, -80.400),
    "Florida_Keys_Lowers_12": ("STN_12", 24.550, -81.450),
    "GreatBarrier_Northern_13": ("STN_13", -14.500, 145.450),
    "GreatBarrier_Central_14": ("STN_14", -18.250, 147.200),
    "GreatBarrier_Lagoon_15": ("STN_15", -18.300, 147.150),
    "CoralTriangle_RajaAmpat_16": ("STN_16", -0.550, 130.500),
    "CoralTriangle_Misool_17": ("STN_17", -1.950, 130.150),
    "CoralTriangle_Komodo_18": ("STN_18", -8.600, 119.550),
    "CoralTriangle_Sulawesi_19": ("STN_19", 1.650, 124.750),
    "CoralTriangle_Bali_20": ("STN_20", -8.120, 115.650),
    "Okinawa_Kerama_21": ("STN_21", 26.200, 127.350),
    "Okinawa_Ishigaki_22": ("STN_22", 24.350, 124.150),
    "RedSea_Aqaba_23": ("STN_23", 29.450, 34.950),
    "RedSea_Shallow_24": ("STN_24", 27.200, 33.850),
    "RedSea_Farasan_25": ("STN_25", 16.700, 41.950),
    "Seychelles_Mahe_26": ("STN_26", -4.680, 55.450),
    "Maldives_AriAtoll_27": ("STN_27", 3.850, 72.850),
    "Hawaii_Kaneohe_28": ("STN_28", 21.450, -157.800),
    "Hawaii_OahuFore_29": ("STN_29", 21.300, -157.700),
    "Palau_RockIslands_30": ("STN_30", 7.300, 134.450),
}


def haversine_km(lat1, lon1, lat2, lon2):
    """Computes great-circle Haversine distance in kilometers between WGS84 coordinates."""
    R = 6371.0088
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    return 2.0 * R * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def apply_25km_buffer(df, train_idx, test_idx, buffer_km=25.0):
    """
    Enforces a spatial exclusion buffer of `buffer_km` (default 25.0 km) around all
    validation/test coordinates (`Latitude`, `Longitude`), removing any training sample
    located within `buffer_km` of any test sample.

    Returns:
        filtered_train_idx (np.ndarray), n_removed (int), min_train_test_dist_km (float)
    """
    train_idx = np.asarray(train_idx)
    test_idx = np.asarray(test_idx)

    train_lats = df.iloc[train_idx]["Latitude"].values[:, None]
    train_lons = df.iloc[train_idx]["Longitude"].values[:, None]
    test_lats = df.iloc[test_idx]["Latitude"].values[None, :]
    test_lons = df.iloc[test_idx]["Longitude"].values[None, :]

    dist_matrix = haversine_km(train_lats, train_lons, test_lats, test_lons)
    min_dists_per_train = dist_matrix.min(axis=1)
    keep_mask = min_dists_per_train >= buffer_km
    filtered_train_idx = train_idx[keep_mask]
    n_removed = int((~keep_mask).sum())
    min_dist_after = float(min_dists_per_train[keep_mask].min()) if keep_mask.any() else 0.0
    return filtered_train_idx, n_removed, min_dist_after


def get_spatial_cv_splits(df, buffer_km=25.0):
    """
    Yields `(fold_id, train_idx, test_idx)` across the 5 spatially clustered folds,
    verifying and enforcing the 25 km Haversine buffer on every split.
    """
    fold_series = df["Station_Name"].map(lambda s: SPATIAL_FOLD_ASSIGNMENT[s][0])
    splits = []
    for fold_id in range(1, 6):
        test_mask = (fold_series == fold_id).values
        train_mask = ~test_mask
        raw_train_idx = np.where(train_mask)[0]
        test_idx = np.where(test_mask)[0]
        clean_train_idx, n_removed, min_dist = apply_25km_buffer(
            df, raw_train_idx, test_idx, buffer_km=buffer_km
        )
        splits.append((fold_id, clean_train_idx, test_idx, n_removed, min_dist))
    return splits


def build_folds_assignment_table(df):
    """
    Builds the station-level spatial CV assignment table (`results/folds_assignment.csv`
    and `09_Results/tables/folds_assignment.csv`) with exact pairwise Haversine distances.
    """
    station_names = list(STATION_NOMINAL_COORDS.keys())
    rows = []

    for st_name in station_names:
        st_id, nom_lat, nom_lon = STATION_NOMINAL_COORDS[st_name]
        fold_id, cluster_id = SPATIAL_FOLD_ASSIGNMENT[st_name]
        sub = df[df["Station_Name"] == st_name]

        region = sub["Region"].iloc[0]
        zone = sub["Reef_Zone"].iloc[0]

        # Compute nearest neighbor overall and nearest out-of-fold (training) station
        min_overall_dist = float("inf")
        nearest_overall_st = ""
        min_train_dist = float("inf")
        nearest_train_st = ""

        for other_name in station_names:
            if other_name == st_name:
                continue
            _, o_lat, o_lon = STATION_NOMINAL_COORDS[other_name]
            other_fold, _ = SPATIAL_FOLD_ASSIGNMENT[other_name]
            d_km = float(haversine_km(nom_lat, nom_lon, o_lat, o_lon))

            if d_km < min_overall_dist:
                min_overall_dist = d_km
                nearest_overall_st = other_name

            if other_fold != fold_id and d_km < min_train_dist:
                min_train_dist = d_km
                nearest_train_st = other_name

        risk_vc = sub["Bleaching_Risk"].value_counts()
        alert_vc = sub["Bleaching_Alert_Level"].value_counts()

        rows.append({
            "Station_ID": st_id,
            "Station_Name": st_name,
            "Region": region,
            "Reef_Zone": zone,
            "Latitude": nom_lat,
            "Longitude": nom_lon,
            "Spatial_Cluster_ID": cluster_id,
            "Fold_ID": fold_id,
            "N_Observations": len(sub),
            "N_Grid_Cells": 80,
            "Nearest_Station_Overall": nearest_overall_st,
            "Nearest_Dist_Overall_km": round(min_overall_dist, 2),
            "Nearest_Train_Station_In_CV": nearest_train_st,
            "Min_Train_Test_Dist_km": round(min_train_dist, 2),
            "Buffer_25km_Compliant": bool(min_train_dist >= 25.0),
            "Low_Count": int(risk_vc.get("Low", 0)),
            "Medium_Count": int(risk_vc.get("Medium", 0)),
            "High_Count": int(risk_vc.get("High", 0)),
            "No_Stress_Count": int(alert_vc.get("No_Stress", 0)),
            "Watch_Count": int(alert_vc.get("Watch", 0)),
            "Warning_Count": int(alert_vc.get("Warning", 0)),
            "Alert_Level_1_Count": int(alert_vc.get("Alert_Level_1", 0)),
            "Alert_Level_2_Count": int(alert_vc.get("Alert_Level_2", 0)),
            "Mean_Coral_Cover_Loss_Pct": round(float(sub["Coral_Cover_Loss_Pct"].mean()), 2),
        })

    df_folds = pd.DataFrame(rows)
    res_csv = os.path.join(RESULTS_DIR, "folds_assignment.csv")
    tab_csv = os.path.join(TABLES_DIR, "folds_assignment.csv")
    df_folds.to_csv(res_csv, index=False)
    df_folds.to_csv(tab_csv, index=False)
    print(f"Folds assignment written to: {res_csv} and {tab_csv}")
    return df_folds


def plot_spatial_folds_diagram(df_folds):
    """
    Generates `results/spatial_folds_diagram.png` and
    `09_Results/figures/Fig_spatial_folds_diagram.png`.
    """
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
    })

    fig = plt.figure(figsize=(15, 8.5), dpi=300)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.25, 1.0], hspace=0.35, wspace=0.25)

    # Panel A: Global Spatial Distribution of the 30 Stations Color-Coded by Fold (1-5)
    ax_map = fig.add_subplot(gs[0, :])
    fold_colors = {
        1: "#1f77b4",
        2: "#ff7f0e",
        3: "#2ca02c",
        4: "#d62728",
        5: "#9467bd",
    }
    fold_markers = {1: "o", 2: "s", 3: "^", 4: "D", 5: "P"}

    ax_map.set_facecolor("#eef6fa")
    ax_map.axhline(0, color="#888888", linestyle="--", linewidth=0.7, alpha=0.6)
    ax_map.axhline(23.436, color="#cccccc", linestyle=":", linewidth=0.7)
    ax_map.axhline(-23.436, color="#cccccc", linestyle=":", linewidth=0.7)

    for fold_id in range(1, 6):
        sub = df_folds[df_folds["Fold_ID"] == fold_id]
        min_d = sub["Min_Train_Test_Dist_km"].min()
        ax_map.scatter(
            sub["Longitude"],
            sub["Latitude"],
            c=fold_colors[fold_id],
            marker=fold_markers[fold_id],
            s=95,
            edgecolors="black",
            linewidths=0.8,
            label=f"Fold {fold_id} (6 stns, N=3,000 | min buffer={min_d:.1f} km)",
            zorder=4,
        )

    # Annotate key reef complexes
    annotations = [
        ("Mesoamerican (Fold 1)\nBelize (Fold 4), Cozumel (Fold 2),\nRoatan (Fold 3)", -87.8, 18.0, (-145, -12)),
        ("Florida Keys (Fold 5)", -80.9, 24.8, (-125, 27)),
        ("Hawaii Oahu (Fold 4)", -157.75, 21.4, (-172, 8)),
        ("Red Sea (Folds 1, 2, 3)", 36.5, 24.0, (2, 26)),
        ("Indian Ocean\n(Folds 2, 3)", 64.0, -0.5, (42, -16)),
        ("Coral Triangle & Palau\n(Folds 3, 4, 5)", 126.0, -2.0, (88, -22)),
        ("Great Barrier Reef\n(Folds 1, 2)", 146.5, -16.8, (132, -31)),
        ("Okinawa (Fold 5)", 125.7, 25.3, (105, 28)),
    ]
    for text, x, y, xyt in annotations:
        ax_map.annotate(
            text,
            xy=(x, y),
            xytext=xyt,
            fontsize=8,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#bbbbbb", alpha=0.9),
            arrowprops=dict(arrowstyle="->", color="#444444", lw=0.8),
            zorder=5,
        )

    ax_map.set_xlim(-180, 180)
    ax_map.set_ylim(-36, 36)
    ax_map.set_xlabel("Longitude (°E)")
    ax_map.set_ylabel("Latitude (°N)")
    ax_map.set_title(
        "A. Global 5-Fold Spatial Block Cross-Validation Across 30 Stations (N = 15,000 | Strict >25 km Buffer Enforced)"
    )
    ax_map.legend(loc="lower left", ncol=3, fontsize=8.5, framealpha=0.95)
    ax_map.grid(True, linestyle=":", alpha=0.5)

    # Panel B: Minimum Out-of-Fold Haversine Distance vs. Closest Overall Neighbor per Fold
    ax_dist = fig.add_subplot(gs[1, 0])
    folds = np.arange(1, 6)
    min_overall_by_fold = [df_folds[df_folds["Fold_ID"] == f]["Nearest_Dist_Overall_km"].min() for f in folds]
    min_cv_by_fold = [df_folds[df_folds["Fold_ID"] == f]["Min_Train_Test_Dist_km"].min() for f in folds]

    width = 0.36
    bars1 = ax_dist.bar(
        folds - width / 2,
        min_overall_by_fold,
        width,
        color="#d95f02",
        edgecolor="black",
        label="Nearest Station Overall (Violates 25 km under Random KFold)",
    )
    bars2 = ax_dist.bar(
        folds + width / 2,
        min_cv_by_fold,
        width,
        color="#1b9e77",
        edgecolor="black",
        label="Nearest Train Station in Spatial Block CV (Compliant)",
    )
    ax_dist.axhline(25.0, color="#d62728", linestyle="--", linewidth=1.5, label="25 km Spatial Buffer Threshold")
    ax_dist.set_yscale("log")
    ax_dist.set_ylim(1.5, 2000.0)
    ax_dist.set_xticks(folds)
    ax_dist.set_xticklabels([f"Fold {f}" for f in folds])
    ax_dist.set_ylabel("Minimum Haversine Distance (km, log scale)")
    ax_dist.set_title("B. Minimum Train-to-Test Distance vs. 25 km Buffer")
    ax_dist.grid(True, axis="y", linestyle=":", alpha=0.5)
    ax_dist.legend(loc="upper left", fontsize=7.8)

    for b in bars1:
        h = b.get_height()
        ax_dist.text(b.get_x() + b.get_width() / 2, h * 1.12, f"{h:.1f}", ha="center", va="bottom", fontsize=7.5)
    for b in bars2:
        h = b.get_height()
        ax_dist.text(b.get_x() + b.get_width() / 2, h * 1.12, f"{h:.1f}", ha="center", va="bottom", fontsize=7.5, fontweight="bold")

    # Panel C: Target Class & Sample Distribution Across Folds
    ax_cls = fig.add_subplot(gs[1, 1])
    low_counts = [df_folds[df_folds["Fold_ID"] == f]["Low_Count"].sum() for f in folds]
    med_counts = [df_folds[df_folds["Fold_ID"] == f]["Medium_Count"].sum() for f in folds]
    high_counts = [df_folds[df_folds["Fold_ID"] == f]["High_Count"].sum() for f in folds]

    ax_cls.bar(folds, low_counts, width=0.55, color="#4daf4a", edgecolor="black", label="Low Risk")
    ax_cls.bar(folds, med_counts, width=0.55, bottom=low_counts, color="#ff7f00", edgecolor="black", label="Medium Risk")
    ax_cls.bar(
        folds,
        high_counts,
        width=0.55,
        bottom=np.array(low_counts) + np.array(med_counts),
        color="#e41a1c",
        edgecolor="black",
        label="High Risk",
    )

    for idx, f in enumerate(folds):
        ax_cls.text(
            f,
            2650,
            f"Low: {low_counts[idx]}\nMed: {med_counts[idx]}\nHigh: {high_counts[idx]}",
            ha="center",
            va="top",
            fontsize=7.5,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.85),
        )

    ax_cls.set_xticks(folds)
    ax_cls.set_xticklabels([f"Fold {f}\n(N=3,000)" for f in folds])
    ax_cls.set_ylim(0, 3300)
    ax_cls.set_ylabel("Number of Observations per Fold")
    ax_cls.set_title("C. Stratified Target Class Balance Across Spatial Folds")
    ax_cls.legend(loc="upper right", ncol=3, fontsize=8)
    ax_cls.grid(True, axis="y", linestyle=":", alpha=0.5)

    out_res = os.path.join(RESULTS_DIR, "spatial_folds_diagram.png")
    out_fig = os.path.join(FIGURES_DIR, "Fig_spatial_folds_diagram.png")
    fig.savefig(out_res, bbox_inches="tight", dpi=300)
    fig.savefig(out_fig, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Spatial folds diagram saved to: {out_res} and {out_fig}")


if __name__ == "__main__":
    print("Loading unified 30-station dataset for Spatial CV verification...")
    df_all = pd.read_csv(DATA_CSV)
    df_folds = build_folds_assignment_table(df_all)

    n_under_25_overall = int((df_folds["Nearest_Dist_Overall_km"] < 25.0).sum())
    min_overall = float(df_folds["Nearest_Dist_Overall_km"].min())
    min_cv_station = float(df_folds["Min_Train_Test_Dist_km"].min())
    n_violations_cv = int((~df_folds["Buffer_25km_Compliant"]).sum())

    print(
        f"Station-level Haversine summary: {n_under_25_overall}/30 stations have a neighbor <25 km "
        f"(min overall = {min_overall:.2f} km)."
    )
    print(
        f"Spatial Block CV station-level summary: min train-to-test station distance = {min_cv_station:.2f} km "
        f"(>25 km violations = {n_violations_cv})."
    )

    print("Verifying sample-level 25 km Haversine buffer across all 5 folds (N=15,000)...")
    splits = get_spatial_cv_splits(df_all, buffer_km=25.0)
    for fold_id, train_idx, test_idx, n_removed, min_sample_dist in splits:
        print(
            f"  Fold {fold_id}: n_train={len(train_idx)}, n_test={len(test_idx)}, "
            f"n_removed_by_25km_buffer={n_removed}, min_sample_train_test_dist={min_sample_dist:.2f} km"
        )

    plot_spatial_folds_diagram(df_folds)
