"""
CoralTwin-DT: GIS & Remote Sensing Spatial Prioritization Engine
===============================================================
Computes the multi-criteria Spatial Restoration Priority Index (SRPI)
across benthic reef sectors and generates GeoJSON priority layers.

Author: CoralTwin-DT Research Consortium
License: MIT
Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.
"""

import os
import json
import numpy as np
import pandas as pd

SEED = 42
np.random.seed(SEED)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_PATH = os.path.join(PROJECT_ROOT, "03_Data", "processed_data", "coral_environmental_harmonized.csv")
OUT_GEO_DIR = os.path.join(BASE_DIR, "geospatial_outputs")
TABLES_DIR = os.path.join(PROJECT_ROOT, "09_Results", "tables")
os.makedirs(OUT_GEO_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)


def calculate_spatial_priorities():
    print("Executing Spatial Multi-Criteria Prioritization...")
    df = pd.read_csv(DATA_PATH)

    # Aggregate by Station to obtain representative spatial parcels
    station_df = df.groupby("Station_Name").agg({
        "Latitude": "mean",
        "Longitude": "mean",
        "Region": "first",
        "Reef_Zone": "first",
        "Depth_m": "mean",
        "DHW_degC_weeks": "mean",
        "pH_total": "mean",
        "Turbidity_NTU": "mean",
        "Live_Coral_Cover_Pct": "mean",
        "Macroalgae_Cover_Pct": "mean",
        "Structural_Rugosity": "mean",
        "Bleaching_Severity_Pct": "mean",
        "Coral_Cover_Loss_Pct": "mean",
    }).reset_index()

    # Spatial Multi-Criteria Evaluation (MCE) Normalization:
    # 1. Thermal Refugia Potential (Lower historical DHW = higher score)
    dhw_min, dhw_max = station_df["DHW_degC_weeks"].min(), station_df["DHW_degC_weeks"].max()
    score_refugia = 1.0 - (station_df["DHW_degC_weeks"] - dhw_min) / (dhw_max - dhw_min + 1e-5)

    # 2. Restoration Urgency / Degradation Need (Higher cover loss = higher intervention need)
    loss_min, loss_max = station_df["Coral_Cover_Loss_Pct"].min(), station_df["Coral_Cover_Loss_Pct"].max()
    score_urgency = (station_df["Coral_Cover_Loss_Pct"] - loss_min) / (loss_max - loss_min + 1e-5)

    # 3. Structural Framework Viability (Higher rugosity = better foundation for outplants)
    rug_min, rug_max = station_df["Structural_Rugosity"].min(), station_df["Structural_Rugosity"].max()
    score_structure = (station_df["Structural_Rugosity"] - rug_min) / (rug_max - rug_min + 1e-5)

    # 4. Hydrodynamic Larval Retention & Water Clarity (Moderate turbidity/depth favorable)
    turb_min, turb_max = station_df["Turbidity_NTU"].min(), station_df["Turbidity_NTU"].max()
    score_water_quality = 1.0 - (station_df["Turbidity_NTU"] - turb_min) / (turb_max - turb_min + 1e-5)

    # Weighted Multi-Criteria Formulation
    # Weights: Refugia (0.35), Urgency (0.25), Structural Viability (0.25), Water Quality (0.15)
    srpi = (
        0.35 * score_refugia +
        0.25 * score_urgency +
        0.25 * score_structure +
        0.15 * score_water_quality
    )

    station_df["Thermal_Refugia_Score"] = score_refugia.round(3)
    station_df["Structural_Score"] = score_structure.round(3)
    station_df["Water_Quality_Score"] = score_water_quality.round(3)
    station_df["Spatial_Restoration_Priority_Index_SRPI"] = srpi.round(3)

    # Priority Tier Categorization
    station_df["Priority_Tier"] = pd.qcut(
        station_df["Spatial_Restoration_Priority_Index_SRPI"],
        q=[0.0, 0.40, 0.75, 1.0],
        labels=["Tier_3_Low_Monitoring", "Tier_2_Secondary_Conservation", "Tier_1_High_Priority_Restoration"]
    )

    # Save Priority Table
    station_df.sort_values(by="Spatial_Restoration_Priority_Index_SRPI", ascending=False).to_csv(
        os.path.join(OUT_GEO_DIR, "spatial_restoration_priority_ranking.csv"), index=False
    )
    station_df.to_csv(os.path.join(TABLES_DIR, "Table3_spatial_restoration_priority.csv"), index=False)

    # Generate GeoJSON Vector Layer
    geojson_features = []
    for _, row in station_df.iterrows():
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(row["Longitude"]), float(row["Latitude"])],
            },
            "properties": {
                "Station_Name": row["Station_Name"],
                "Region": row["Region"],
                "Reef_Zone": row["Reef_Zone"],
                "Depth_m": round(float(row["Depth_m"]), 1),
                "SRPI": float(row["Spatial_Restoration_Priority_Index_SRPI"]),
                "Priority_Tier": str(row["Priority_Tier"]),
                "Thermal_Refugia_Score": float(row["Thermal_Refugia_Score"]),
                "Live_Coral_Cover_Pct": round(float(row["Live_Coral_Cover_Pct"]), 1),
                "Scientific_Attribution": "Resultado obtenido mediante prototipo computacional del gemelo digital",
            }
        }
        geojson_features.append(feature)

    geojson_obj = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": geojson_features
    }

    geojson_path = os.path.join(OUT_GEO_DIR, "priority_restoration_zones.geojson")
    with open(geojson_path, "w") as f:
        json.dump(geojson_obj, f, indent=2)

    print(f"GeoJSON priority layer written to: {geojson_path}")
    print("Spatial prioritization pipeline completed.")


if __name__ == "__main__":
    calculate_spatial_priorities()
