"""
CoralTwin-DT: GIS & Remote Sensing Spatial Prioritization Engine
================================================================
Computes the multi-criteria Spatial Restoration Priority Index (SRPI)
across all 30 benchmark reef stations (N = 15,000 observations) under both:
  1. Biophysical Formulation (Manuscript Section 2.7, Eq. 7):
     SRPI_Eq7 = 0.35 * ThermRefugia + 0.25 * RestoUrgency + 0.25 * BenthicRugosity + 0.15 * WaterQuality
     where:
       - ThermRefugia    = 1 - min(DHW_95th / 16.0, 1.0)
       - RestoUrgency    = clip(1 - CurrentCover / 50.0, 0.0, 1.0)
       - BenthicRugosity = clip((Structural_Rugosity - 1.0) / 2.0, 0.0, 1.0)
       - WaterQuality    = 1 - min(Kd490 / 0.25, 1.0), with Kd490 = 0.04 * Turbidity_NTU
  2. Relative Min-Max Normalization (Legacy Script Formulation):
     SRPI_MinMax = 0.35 * score_refugia + 0.25 * score_urgency + 0.25 * score_structure + 0.15 * score_water_quality

Also performs a sensitivity analysis across thresholds {0.60, 0.70, 0.80} and quantile tiering
at the 30-station level, 15,000-observation level, and legacy 25-station level.

Outputs:
- `08_GIS_and_Remote_Sensing/geospatial_outputs/spatial_restoration_priority_ranking.csv`
- `08_GIS_and_Remote_Sensing/geospatial_outputs/priority_restoration_zones.geojson`
- `08_GIS_and_Remote_Sensing/ArcGIS_WebMaps/reef_stations_priority.geojson`
- `09_Results/tables/Table3_spatial_restoration_priority.csv`
- `09_Results/tables/srpi_sensitivity.csv`
- `results/srpi_sensitivity.csv`

Author: CoralTwin-DT Research Consortium
License: MIT
"""

import os
import json
import numpy as np
import pandas as pd

SEED = 42
np.random.seed(SEED)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_PATH = os.path.join(PROJECT_ROOT, "03_Data", "final_dataset.csv")
LEGACY_TABLE3_PATH = os.path.join(PROJECT_ROOT, "legacy", "09_Results", "tables", "Table3_spatial_restoration_priority.csv")
OUT_GEO_DIR = os.path.join(BASE_DIR, "geospatial_outputs")
ARCGIS_DIR = os.path.join(BASE_DIR, "ArcGIS_WebMaps")
TABLES_DIR = os.path.join(PROJECT_ROOT, "09_Results", "tables")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

for d in [OUT_GEO_DIR, ARCGIS_DIR, TABLES_DIR, RESULTS_DIR]:
    os.makedirs(d, exist_ok=True)


def calculate_spatial_priorities():
    print("Executing Spatial Multi-Criteria Prioritization across 30 stations (N=15,000)...")
    df = pd.read_csv(DATA_PATH)

    # Aggregate by Station_ID & Station_Name to obtain representative spatial parcels (N = 30 stations)
    station_df = df.groupby(["Station_ID", "Station_Name"], as_index=False).agg(
        Latitude=("Latitude", "mean"),
        Longitude=("Longitude", "mean"),
        Region=("Region", "first"),
        Reef_Zone=("Reef_Zone", "first"),
        Depth_m=("Depth_m", "mean"),
        DHW_degC_weeks=("DHW_degC_weeks", "mean"),
        DHW_95th_degC_weeks=("DHW_degC_weeks", lambda x: float(np.percentile(x, 95))),
        pH_total=("pH_total", "mean"),
        Turbidity_NTU=("Turbidity_NTU", "mean"),
        Live_Coral_Cover_Pct=("Live_Coral_Cover_Pct", "mean"),
        Macroalgae_Cover_Pct=("Macroalgae_Cover_Pct", "mean"),
        Structural_Rugosity=("Structural_Rugosity", "mean"),
        Bleaching_Severity_Pct=("Bleaching_Severity_Pct", "mean"),
        Coral_Cover_Loss_Pct=("Coral_Cover_Loss_Pct", "mean"),
    )

    # Sort by numeric station index (STN_01 .. STN_30)
    station_df["_stn_num"] = station_df["Station_ID"].str.replace("STN_", "", regex=False).astype(int)
    station_df = station_df.sort_values("_stn_num").drop(columns=["_stn_num"]).reset_index(drop=True)

    # -------------------------------------------------------------------------
    # 1. Biophysical Formulation (Manuscript Eq. 7)
    # -------------------------------------------------------------------------
    therm_refugia_eq7 = 1.0 - np.minimum(station_df["DHW_95th_degC_weeks"] / 16.0, 1.0)
    resto_urgency_eq7 = np.clip(1.0 - (station_df["Live_Coral_Cover_Pct"] / 50.0), 0.0, 1.0)
    benthic_rugosity_eq7 = np.clip((station_df["Structural_Rugosity"] - 1.0) / 2.0, 0.0, 1.0)
    kd490_est = 0.04 * station_df["Turbidity_NTU"]
    water_quality_eq7 = 1.0 - np.minimum(kd490_est / 0.25, 1.0)

    srpi_eq7 = (
        0.35 * therm_refugia_eq7
        + 0.25 * resto_urgency_eq7
        + 0.25 * benthic_rugosity_eq7
        + 0.15 * water_quality_eq7
    )

    # -------------------------------------------------------------------------
    # 2. Relative Min-Max Normalization (Legacy Script Formulation on 30 Stations)
    # -------------------------------------------------------------------------
    dhw_min, dhw_max = station_df["DHW_degC_weeks"].min(), station_df["DHW_degC_weeks"].max()
    score_refugia_mm = 1.0 - (station_df["DHW_degC_weeks"] - dhw_min) / (dhw_max - dhw_min + 1e-5)

    loss_min, loss_max = station_df["Coral_Cover_Loss_Pct"].min(), station_df["Coral_Cover_Loss_Pct"].max()
    score_urgency_mm = (station_df["Coral_Cover_Loss_Pct"] - loss_min) / (loss_max - loss_min + 1e-5)

    rug_min, rug_max = station_df["Structural_Rugosity"].min(), station_df["Structural_Rugosity"].max()
    score_structure_mm = (station_df["Structural_Rugosity"] - rug_min) / (rug_max - rug_min + 1e-5)

    turb_min, turb_max = station_df["Turbidity_NTU"].min(), station_df["Turbidity_NTU"].max()
    score_wq_mm = 1.0 - (station_df["Turbidity_NTU"] - turb_min) / (turb_max - turb_min + 1e-5)

    srpi_minmax = (
        0.35 * score_refugia_mm
        + 0.25 * score_urgency_mm
        + 0.25 * score_structure_mm
        + 0.15 * score_wq_mm
    )

    station_df["Thermal_Refugia_Score"] = therm_refugia_eq7.round(3)
    station_df["Restoration_Urgency_Score"] = resto_urgency_eq7.round(3)
    station_df["Structural_Score"] = benthic_rugosity_eq7.round(3)
    station_df["Water_Quality_Score"] = water_quality_eq7.round(3)
    station_df["Spatial_Restoration_Priority_Index_SRPI"] = srpi_eq7.round(3)
    station_df["SRPI_MinMax_Legacy"] = srpi_minmax.round(3)

    # Priority Tier Categorization under explicit Eq. 7 threshold (>= 0.70 Tier 1, 0.60-0.70 Tier 2, < 0.60 Tier 3)
    def assign_tier(val):
        if val >= 0.70:
            return "Tier_1_High_Priority_Restoration"
        elif val >= 0.60:
            return "Tier_2_Secondary_Conservation"
        return "Tier_3_Low_Monitoring"

    station_df["Priority_Tier"] = station_df["Spatial_Restoration_Priority_Index_SRPI"].apply(assign_tier)
    station_df["Priority_Tier_Quantile_Legacy"] = pd.qcut(
        station_df["SRPI_MinMax_Legacy"],
        q=[0.0, 0.40, 0.75, 1.0],
        labels=["Tier_3_Low_Monitoring", "Tier_2_Secondary_Conservation", "Tier_1_High_Priority_Restoration"],
    )

    # Save Priority Tables
    ranking_df = station_df.sort_values(by="Spatial_Restoration_Priority_Index_SRPI", ascending=False).reset_index(drop=True)
    ranking_df.to_csv(os.path.join(OUT_GEO_DIR, "spatial_restoration_priority_ranking.csv"), index=False)
    station_df.to_csv(os.path.join(TABLES_DIR, "Table3_spatial_restoration_priority.csv"), index=False)

    # -------------------------------------------------------------------------
    # 3. Sensitivity Analysis across thresholds {0.60, 0.70, 0.80} and formulations
    # -------------------------------------------------------------------------
    dhw_p95_map = station_df.set_index("Station_ID")["DHW_95th_degC_weeks"].to_dict()
    obs_dhw_p95 = df["Station_ID"].map(dhw_p95_map)
    obs_srpi_eq7 = (
        0.35 * (1.0 - np.minimum(obs_dhw_p95 / 16.0, 1.0))
        + 0.25 * np.clip(1.0 - (df["Live_Coral_Cover_Pct"] / 50.0), 0.0, 1.0)
        + 0.25 * np.clip((df["Structural_Rugosity"] - 1.0) / 2.0, 0.0, 1.0)
        + 0.15 * (1.0 - np.minimum((0.04 * df["Turbidity_NTU"]) / 0.25, 1.0))
    ).round(3)

    sensitivity_rows = []
    for thr in [0.60, 0.70, 0.80]:
        c_eq7_st = int((station_df["Spatial_Restoration_Priority_Index_SRPI"] >= thr).sum())
        c_eq7_obs = int((obs_srpi_eq7 >= thr).sum())
        c_mm_st = int((station_df["SRPI_MinMax_Legacy"] >= thr).sum())

        sensitivity_rows.append({
            "Formulation": "Biophysical_Eq7_30_Stations",
            "Unit_of_Analysis": "Station (N=30)",
            "Total_Units": 30,
            "Threshold_Method": f"Fixed_Threshold_SRPI_ge_{thr:.2f}",
            "Threshold_Value": thr,
            "Tier_1_Count": c_eq7_st,
            "Tier_1_Pct": round(c_eq7_st / 30.0 * 100.0, 2),
            "SRPI_Min": round(float(station_df["Spatial_Restoration_Priority_Index_SRPI"].min()), 3),
            "SRPI_Mean": round(float(station_df["Spatial_Restoration_Priority_Index_SRPI"].mean()), 3),
            "SRPI_Max": round(float(station_df["Spatial_Restoration_Priority_Index_SRPI"].max()), 3),
        })
        sensitivity_rows.append({
            "Formulation": "Biophysical_Eq7_15000_Observations",
            "Unit_of_Analysis": "Observation_Grid_Record (N=15000)",
            "Total_Units": len(df),
            "Threshold_Method": f"Fixed_Threshold_SRPI_ge_{thr:.2f}",
            "Threshold_Value": thr,
            "Tier_1_Count": c_eq7_obs,
            "Tier_1_Pct": round(c_eq7_obs / float(len(df)) * 100.0, 2),
            "SRPI_Min": round(float(obs_srpi_eq7.min()), 3),
            "SRPI_Mean": round(float(obs_srpi_eq7.mean()), 3),
            "SRPI_Max": round(float(obs_srpi_eq7.max()), 3),
        })
        sensitivity_rows.append({
            "Formulation": "Relative_MinMax_30_Stations",
            "Unit_of_Analysis": "Station (N=30)",
            "Total_Units": 30,
            "Threshold_Method": f"Fixed_Threshold_SRPI_ge_{thr:.2f}",
            "Threshold_Value": thr,
            "Tier_1_Count": c_mm_st,
            "Tier_1_Pct": round(c_mm_st / 30.0 * 100.0, 2),
            "SRPI_Min": round(float(station_df["SRPI_MinMax_Legacy"].min()), 3),
            "SRPI_Mean": round(float(station_df["SRPI_MinMax_Legacy"].mean()), 3),
            "SRPI_Max": round(float(station_df["SRPI_MinMax_Legacy"].max()), 3),
        })

    # Add quantile top-25% rows (30 stations and legacy 25 stations)
    q75_30_cnt = int((station_df["Priority_Tier_Quantile_Legacy"] == "Tier_1_High_Priority_Restoration").sum())
    sensitivity_rows.append({
        "Formulation": "Relative_MinMax_30_Stations",
        "Unit_of_Analysis": "Station (N=30)",
        "Total_Units": 30,
        "Threshold_Method": "Quantile_qcut_Top25Pct",
        "Threshold_Value": round(float(np.quantile(station_df["SRPI_MinMax_Legacy"], 0.75)), 3),
        "Tier_1_Count": q75_30_cnt,
        "Tier_1_Pct": round(q75_30_cnt / 30.0 * 100.0, 2),
        "SRPI_Min": round(float(station_df["SRPI_MinMax_Legacy"].min()), 3),
        "SRPI_Mean": round(float(station_df["SRPI_MinMax_Legacy"].mean()), 3),
        "SRPI_Max": round(float(station_df["SRPI_MinMax_Legacy"].max()), 3),
    })

    if os.path.exists(LEGACY_TABLE3_PATH):
        leg_df = pd.read_csv(LEGACY_TABLE3_PATH)
        for thr in [0.60, 0.70, 0.80]:
            c_leg = int((leg_df["Spatial_Restoration_Priority_Index_SRPI"] >= thr).sum())
            sensitivity_rows.append({
                "Formulation": "Relative_MinMax_Legacy_25_Stations",
                "Unit_of_Analysis": "Station_Legacy (N=25)",
                "Total_Units": len(leg_df),
                "Threshold_Method": f"Fixed_Threshold_SRPI_ge_{thr:.2f}",
                "Threshold_Value": thr,
                "Tier_1_Count": c_leg,
                "Tier_1_Pct": round(c_leg / float(len(leg_df)) * 100.0, 2),
                "SRPI_Min": round(float(leg_df["Spatial_Restoration_Priority_Index_SRPI"].min()), 3),
                "SRPI_Mean": round(float(leg_df["Spatial_Restoration_Priority_Index_SRPI"].mean()), 3),
                "SRPI_Max": round(float(leg_df["Spatial_Restoration_Priority_Index_SRPI"].max()), 3),
            })
        c_leg_q = int((leg_df["Priority_Tier"] == "Tier_1_High_Priority_Restoration").sum())
        sensitivity_rows.append({
            "Formulation": "Relative_MinMax_Legacy_25_Stations",
            "Unit_of_Analysis": "Station_Legacy (N=25)",
            "Total_Units": len(leg_df),
            "Threshold_Method": "Quantile_qcut_Top25Pct",
            "Threshold_Value": round(float(np.quantile(leg_df["Spatial_Restoration_Priority_Index_SRPI"], 0.75)), 3),
            "Tier_1_Count": c_leg_q,
            "Tier_1_Pct": round(c_leg_q / float(len(leg_df)) * 100.0, 2),
            "SRPI_Min": round(float(leg_df["Spatial_Restoration_Priority_Index_SRPI"].min()), 3),
            "SRPI_Mean": round(float(leg_df["Spatial_Restoration_Priority_Index_SRPI"].mean()), 3),
            "SRPI_Max": round(float(leg_df["Spatial_Restoration_Priority_Index_SRPI"].max()), 3),
        })

    sens_df = pd.DataFrame(sensitivity_rows)
    sens_df.to_csv(os.path.join(RESULTS_DIR, "srpi_sensitivity.csv"), index=False)
    sens_df.to_csv(os.path.join(TABLES_DIR, "srpi_sensitivity.csv"), index=False)

    # -------------------------------------------------------------------------
    # 4. Generate GeoJSON Vector Layers (30 stations)
    # -------------------------------------------------------------------------
    geojson_features = []
    for _, row in station_df.iterrows():
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [round(float(row["Longitude"]), 4), round(float(row["Latitude"]), 4)],
            },
            "properties": {
                "Station_ID": str(row["Station_ID"]),
                "Station_Name": str(row["Station_Name"]),
                "Region": str(row["Region"]),
                "Reef_Zone": str(row["Reef_Zone"]),
                "Depth_m": round(float(row["Depth_m"]), 1),
                "SRPI": float(row["Spatial_Restoration_Priority_Index_SRPI"]),
                "SRPI_MinMax_Legacy": float(row["SRPI_MinMax_Legacy"]),
                "Priority_Tier": str(row["Priority_Tier"]),
                "Priority_Tier_Quantile_Legacy": str(row["Priority_Tier_Quantile_Legacy"]),
                "Thermal_Refugia_Score": float(row["Thermal_Refugia_Score"]),
                "Restoration_Urgency_Score": float(row["Restoration_Urgency_Score"]),
                "Structural_Score": float(row["Structural_Score"]),
                "Water_Quality_Score": float(row["Water_Quality_Score"]),
                "Live_Coral_Cover_Pct": round(float(row["Live_Coral_Cover_Pct"]), 2),
                "DHW_95th_degC_weeks": round(float(row["DHW_95th_degC_weeks"]), 2),
                "Scientific_Attribution": "Resultado obtenido mediante prototipo computacional del gemelo digital",
            },
        }
        geojson_features.append(feature)

    geojson_obj = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": geojson_features,
    }

    for gpath in [
        os.path.join(OUT_GEO_DIR, "priority_restoration_zones.geojson"),
        os.path.join(ARCGIS_DIR, "reef_stations_priority.geojson"),
    ]:
        with open(gpath, "w", encoding="utf-8") as f:
            json.dump(geojson_obj, f, indent=2)
        print(f"GeoJSON priority layer written to: {gpath}")

    print("Spatial prioritization pipeline completed:")
    print(sens_df[sens_df["Threshold_Value"] == 0.70][["Formulation", "Unit_of_Analysis", "Tier_1_Count", "Tier_1_Pct", "SRPI_Max"]])
    return station_df, sens_df


if __name__ == "__main__":
    calculate_spatial_priorities()
