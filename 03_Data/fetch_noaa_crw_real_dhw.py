"""
03_Data/fetch_noaa_crw_real_dhw.py
==================================
Fetches real public NOAA Coral Reef Watch (CRW) 5 km daily Degree Heating Week (DHW)
time-series (2015-2024) via NOAA OceanWatch ERDDAP for the coordinates of the 30 stations.
Computes:
1. Real DHW_95th percentile per station.
2. Spearman correlation between real and synthetic DHW_95th across the 30 stations.
3. Recalculated Spatial Restoration Priority Index (SRPI, Eq. 7) using real thermal refugia,
   evaluating how many of the 10 Tier-1 stations are preserved.
"""

import os
import sys
import json
import time
import urllib.request
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, pearsonr

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "03_Data"))

from build_final_dataset import generate_extended_stations

RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

DATA_PATH = os.path.join(BASE_DIR, "03_Data", "final_dataset.csv")


def fetch_noaa_crw_for_station(lat: float, lon: float, station_name: str, max_retries: int = 3):
    """
    Queries NOAA OceanWatch ERDDAP for CRW 5km weekly DHW from 2015-01-01 to 2024-12-31.
    ERDDAP Grid:
    latitude: -89.975 to 89.975 (step 0.05)
    longitude: 0.025 to 359.975 (step 0.05)
    """
    # Align to ERDDAP 0.05 grid
    lat_grid = round(round((lat - 0.025) / 0.05) * 0.05 + 0.025, 3)
    lon_360 = (lon + 360.0) % 360.0
    lon_grid = round(round((lon_360 - 0.025) / 0.05) * 0.05 + 0.025, 3)

    # Stride of 7 days across 10 years (~522 weekly records)
    url = (
        f"https://oceanwatch.pifsc.noaa.gov/erddap/griddap/CRW_dhw_v1_0.csv?"
        f"degree_heating_week[(2015-01-01T12:00:00Z):7:(2024-12-31T12:00:00Z)]"
        f"[({lat_grid}):1:({lat_grid})][({lon_grid}):1:({lon_grid})]"
    )

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CoralTwin-DT Scientific Audit/1.0"})
            with urllib.request.urlopen(req, timeout=25) as response:
                content = response.read().decode("utf-8")
                lines = content.strip().splitlines()
                if len(lines) < 3:
                    raise ValueError("Empty or malformed ERDDAP response")

                # Parse CSV (skip header line 1: column names, line 2: units)
                records = []
                for line in lines[2:]:
                    parts = line.split(",")
                    if len(parts) >= 4:
                        t_str, lat_val, lon_val, dhw_str = parts[0], parts[1], parts[2], parts[3]
                        try:
                            dhw_val = float(dhw_str)
                            records.append(dhw_val)
                        except ValueError:
                            continue
                return np.array(records, dtype=float)
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Failed to fetch NOAA data for {station_name} ({lat}, {lon}) after {max_retries} attempts: {e}")
                return None
            time.sleep(2.0 * (attempt + 1))


def main():
    print("=" * 70)
    print("TASK 6: Real NOAA Coral Reef Watch 5km DHW Validation")
    print("=" * 70)

    stations = generate_extended_stations()
    df_synth = pd.read_csv(DATA_PATH)

    cache_path = os.path.join(RESULTS_DIR, "noaa_crw_real_dhw_timeseries.csv")
    rows_dhw = []

    # Offsets for coastal pixels that fall on land in the 5km NOAA grid
    coastal_offsets = {
        "Mesoamerican_Back_03": (0.0, 0.05),
        "Mesoamerican_Lagoon_04": (0.0, -0.05),
        "Cozumel_Shallow_08": (0.0, -0.05),
        "CoralTriangle_Misool_17": (0.05, 0.05),
    }

    print(f"Fetching real NOAA CRW 5km weekly DHW for {len(stations)} stations...")
    station_real_dhws = {}

    for i, st in enumerate(stations):
        st_id = st["id"]
        st_name = st["name"]
        lat = st["lat"]
        lon = st["lon"]

        # Apply offshore offset if station is land-masked
        if st_name in coastal_offsets:
            d_lat, d_lon = coastal_offsets[st_name]
            lat += d_lat
            lon += d_lon

        print(f"[{i+1:02d}/30] Fetching {st_name} (lat={lat:.3f}, lon={lon:.3f})...", end=" ")
        t0 = time.time()
        dhw_series = fetch_noaa_crw_for_station(lat, lon, st_name)
        elapsed = time.time() - t0

        if dhw_series is not None and len(dhw_series) > 0 and not np.all(np.isnan(dhw_series)):
            valid_vals = dhw_series[~np.isnan(dhw_series)]
            if len(valid_vals) > 0:
                p95_real = float(np.percentile(valid_vals, 95))
                max_real = float(np.max(valid_vals))
                mean_real = float(np.mean(valid_vals))
                print(f"OK ({len(valid_vals)} valid obs in {elapsed:.2f}s) -> 95th: {p95_real:.2f}, Max: {max_real:.2f}")
                station_real_dhws[st_name] = {
                    "Station_ID": st_id,
                    "Station_Name": st_name,
                    "Region": st["region"],
                    "Reef_Zone": st["zone"],
                    "Latitude": st["lat"],
                    "Longitude": st["lon"],
                    "N_Real_Observations": len(valid_vals),
                    "Real_DHW_Mean": round(mean_real, 3),
                    "Real_DHW_95th": round(p95_real, 3),
                    "Real_DHW_Max": round(max_real, 3),
                }
            else:
                print("FAILED (all NaNs).")
        else:
            print("FAILED.")

    if len(station_real_dhws) < 25:
        print("Network access failed or could not retrieve sufficient NOAA data. Marking as no ejecutable.")
        summary_fail = {
            "status": "no ejecutable",
            "reason": "Could not connect to NOAA OceanWatch ERDDAP service or retrieve sufficient stations.",
        }
        with open(os.path.join(RESULTS_DIR, "noaa_crw_validation_summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary_fail, f, indent=2)
        return

    # Compute synthetic station-level metrics from final_dataset.csv
    synth_metrics = {}
    for st_name, group in df_synth.groupby("Station_Name"):
        dhw_syn = group["DHW_degC_weeks"].values
        synth_metrics[st_name] = {
            "Synthetic_DHW_Mean": round(float(np.mean(dhw_syn)), 3),
            "Synthetic_DHW_95th": round(float(np.percentile(dhw_syn, 95)), 3),
            "Synthetic_DHW_Max": round(float(np.max(dhw_syn)), 3),
            "Mean_Live_Coral_Cover_Pct": round(float(group["Live_Coral_Cover_Pct"].mean()), 2),
            "Mean_Structural_Rugosity": round(float(group["Structural_Rugosity"].mean()), 2),
        }

    # Merge real and synthetic metrics
    comparison_rows = []
    real_p95_list = []
    syn_p95_list = []

    # Nominal connectivity index per region (from spatial_pipeline.py)
    connectivity_map = {
        "Caribbean": 0.72,
        "Indo-Pacific": 0.85,
        "Red Sea": 0.65,
        "Indian Ocean": 0.60,
        "Pacific": 0.78,
    }

    for st in stations:
        st_name = st["name"]
        if st_name not in station_real_dhws:
            continue
        r = station_real_dhws[st_name]
        s = synth_metrics[st_name]

        # Calculate SRPI under synthetic vs real DHW_95th
        # Eq. 7: SRPI = 0.35 * (1 - V_therm) + 0.25 * (1 - C_curr/100) + 0.25 * (R / 3.5) + 0.15 * H
        c_curr = s["Mean_Live_Coral_Cover_Pct"]
        rugosity = s["Mean_Structural_Rugosity"]
        conn = connectivity_map.get(st["region"], 0.70)

        # Synthetic SRPI
        v_therm_syn = min(s["Synthetic_DHW_95th"] / 12.0, 1.0)
        srpi_synth = (
            0.35 * (1.0 - v_therm_syn)
            + 0.25 * (1.0 - c_curr / 100.0)
            + 0.25 * (rugosity / 3.5)
            + 0.15 * conn
        )

        # Real SRPI
        v_therm_real = min(r["Real_DHW_95th"] / 12.0, 1.0)
        srpi_real = (
            0.35 * (1.0 - v_therm_real)
            + 0.25 * (1.0 - c_curr / 100.0)
            + 0.25 * (rugosity / 3.5)
            + 0.15 * conn
        )

        real_p95_list.append(r["Real_DHW_95th"])
        syn_p95_list.append(s["Synthetic_DHW_95th"])

        comparison_rows.append({
            "Station_ID": r["Station_ID"],
            "Station_Name": st_name,
            "Region": r["Region"],
            "Reef_Zone": r["Reef_Zone"],
            "Latitude": r["Latitude"],
            "Longitude": r["Longitude"],
            "Real_NOAA_DHW_Mean": r["Real_DHW_Mean"],
            "Real_NOAA_DHW_95th": r["Real_DHW_95th"],
            "Real_NOAA_DHW_Max": r["Real_DHW_Max"],
            "Synthetic_DHW_Mean": s["Synthetic_DHW_Mean"],
            "Synthetic_DHW_95th": s["Synthetic_DHW_95th"],
            "Synthetic_DHW_Max": s["Synthetic_DHW_Max"],
            "DHW_95th_Difference_Real_minus_Syn": round(r["Real_DHW_95th"] - s["Synthetic_DHW_95th"], 3),
            "Mean_Live_Coral_Cover_Pct": c_curr,
            "Mean_Structural_Rugosity": rugosity,
            "Connectivity_H": conn,
            "Synthetic_SRPI_Eq7": round(srpi_synth, 3),
            "Real_SRPI_Eq7": round(srpi_real, 3),
            "Synthetic_Tier_1": bool(srpi_synth >= 0.70),
            "Real_Tier_1": bool(srpi_real >= 0.70),
            "Maintains_Tier_1": bool((srpi_synth >= 0.70) and (srpi_real >= 0.70)),
        })

    df_comp = pd.DataFrame(comparison_rows)
    comp_csv_path = os.path.join(RESULTS_DIR, "noaa_crw_validation.csv")
    df_comp.to_csv(comp_csv_path, index=False)
    print(f"\nStation-by-station validation saved to: {comp_csv_path}")

    # Statistical correlation strictly on stations with valid marine pixel coverage
    valid_df = df_comp.dropna(subset=["Real_NOAA_DHW_95th", "Synthetic_DHW_95th"])
    spearman_rho, spearman_p = spearmanr(valid_df["Real_NOAA_DHW_95th"], valid_df["Synthetic_DHW_95th"])
    pearson_r, pearson_p = pearsonr(valid_df["Real_NOAA_DHW_95th"], valid_df["Synthetic_DHW_95th"])

    real_valid_p95 = valid_df["Real_NOAA_DHW_95th"].tolist()
    syn_valid_p95 = valid_df["Synthetic_DHW_95th"].tolist()

    # SRPI Tier-1 counts
    synth_tier1_count = int(df_comp["Synthetic_Tier_1"].sum())
    real_tier1_count = int(df_comp["Real_Tier_1"].sum())
    maintained_tier1_count = int(df_comp["Maintains_Tier_1"].sum())

    maintained_stations = df_comp[df_comp["Maintains_Tier_1"]]["Station_Name"].tolist()
    dropped_stations = df_comp[df_comp["Synthetic_Tier_1"] & (~df_comp["Real_Tier_1"])]["Station_Name"].tolist()
    added_stations = df_comp[(~df_comp["Synthetic_Tier_1"]) & df_comp["Real_Tier_1"]]["Station_Name"].tolist()

    summary = {
        "status": "completado_con_datos_reales",
        "data_source": "NOAA Coral Reef Watch (CRW) Operational Daily Global 5km Satellite Bleaching Heat Stress (CRW_dhw_v1_0)",
        "erddap_endpoint": "https://oceanwatch.pifsc.noaa.gov/erddap/griddap/CRW_dhw_v1_0",
        "temporal_coverage": "2015-01-01 to 2024-12-31 (weekly sample, stride=7)",
        "n_stations_evaluated": len(df_comp),
        "spearman_correlation_dhw_95th": {
            "rho": round(float(spearman_rho), 4),
            "p_value": float(spearman_p),
            "significant_at_005": bool(spearman_p < 0.05),
        },
        "pearson_correlation_dhw_95th": {
            "r": round(float(pearson_r), 4),
            "p_value": float(pearson_p),
        },
        "dhw_95th_summary": {
            "n_valid_stations": len(valid_df),
            "real_noaa_mean_across_stations": round(float(np.mean(real_valid_p95)), 3),
            "real_noaa_min": round(float(np.min(real_valid_p95)), 3),
            "real_noaa_max": round(float(np.max(real_valid_p95)), 3),
            "synthetic_mean_across_stations": round(float(np.mean(syn_valid_p95)), 3),
            "synthetic_min": round(float(np.min(syn_valid_p95)), 3),
            "synthetic_max": round(float(np.max(syn_valid_p95)), 3),
        },
        "srpi_tier1_preservation": {
            "synthetic_tier1_threshold": 0.70,
            "synthetic_tier1_count": synth_tier1_count,
            "real_noaa_tier1_count": real_tier1_count,
            "maintained_tier1_count": maintained_tier1_count,
            "preservation_rate_pct": round(100.0 * maintained_tier1_count / max(synth_tier1_count, 1), 2),
            "maintained_stations": maintained_stations,
            "dropped_from_tier1": dropped_stations,
            "newly_qualifying_tier1": added_stations,
        },
    }

    summary_path = os.path.join(RESULTS_DIR, "noaa_crw_validation_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 70)
    print("NOAA VALIDATION RESULTS SUMMARY:")
    print(f"Spearman Rho (DHW_95th): {spearman_rho:.4f} (p = {spearman_p:.4e})")
    print(f"Pearson r   (DHW_95th): {pearson_r:.4f} (p = {pearson_p:.4e})")
    print(f"Synthetic Tier-1 Stations (SRPI >= 0.70): {synth_tier1_count}/30")
    print(f"Real NOAA Tier-1 Stations (SRPI >= 0.70): {real_tier1_count}/30")
    print(f"Maintained in Tier-1: {maintained_tier1_count}/{synth_tier1_count} ({summary['srpi_tier1_preservation']['preservation_rate_pct']}%)")
    print(f"Maintained Stations: {maintained_stations}")
    print("=" * 70)


if __name__ == "__main__":
    main()
