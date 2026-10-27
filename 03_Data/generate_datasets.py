"""
CoralTwin-DT: Data Ingestion, Synthesis, and Harmonization Engine
================================================================
Unified entrypoint that delegates harmonized dataset generation to
`build_final_dataset.py` so both `03_Data/final_dataset.csv` and
`03_Data/processed_data/coral_environmental_harmonized.csv` contain the exact
same 30-station, N=15,000 synthetic benchmark dataset (100.0% simulated).

Author: CoralTwin-DT Research Consortium
License: MIT
Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.
"""

import os
import math
import numpy as np
import pandas as pd

from build_final_dataset import (
    SEED,
    FINAL_DATA_CSV,
    HARMONIZED_DATA_CSV,
    generate_extended_stations,
    build_final_dataset,
    generate_final_data_dictionary,
)

np.random.seed(SEED)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
RAW_DIR = os.path.join(BASE_DIR, "raw_data")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed_data")
SYNTHETIC_DIR = os.path.join(BASE_DIR, "synthetic_dataset")
METADATA_DIR = os.path.join(BASE_DIR, "metadata")
LIT_DIR = os.path.join(PROJECT_ROOT, "02_Literature_Review")

for d in [
    os.path.join(RAW_DIR, "NOAA"),
    os.path.join(RAW_DIR, "Sentinel2"),
    os.path.join(RAW_DIR, "Allen_Coral_Atlas"),
    os.path.join(RAW_DIR, "Oceanographic_Data"),
    PROCESSED_DIR,
    SYNTHETIC_DIR,
    METADATA_DIR,
    LIT_DIR,
]:
    os.makedirs(d, exist_ok=True)


def generate_pilot_stations():
    """Returns the unified 30-station benchmark configuration."""
    return generate_extended_stations()


def build_harmonized_dataset(n_samples=15000):
    """
    Delegates to `build_final_dataset(n_total=15000)` so that all downstream
    pipelines operate on the unified 30-station, N=15,000 dataset.
    """
    return build_final_dataset(n_total=n_samples)


def generate_raw_source_feeds(df_master):
    """Saves synthetic raw provider partitions from the unified 15,000-row dataset."""
    np.random.seed(SEED)
    # 1. NOAA CRW 5km feed
    noaa_cols = [
        "Record_ID", "Date", "Station_ID", "Station_Name", "Latitude", "Longitude",
        "SST_degC", "SST_Anomaly_degC", "DHW_degC_weeks", "Data_Source_Type", "Scientific_Attribution"
    ]
    df_master[noaa_cols].to_csv(os.path.join(RAW_DIR, "NOAA", "noaa_crw_5km_pilot.csv"), index=False)

    # 2. Sentinel-2 L2A optical reflectance feed
    s2_df = df_master[
        ["Record_ID", "Date", "Station_ID", "Station_Name", "Latitude", "Longitude", "Turbidity_NTU", "Kd_490_m_inv", "PAR_umol_m2_s"]
    ].copy()
    s2_df["B2_Blue_Reflectance"] = (0.045 + np.random.uniform(-0.005, 0.005, len(s2_df))).round(4)
    s2_df["B3_Green_Reflectance"] = (0.062 + np.random.uniform(-0.008, 0.008, len(s2_df))).round(4)
    s2_df["B4_Red_Reflectance"] = (0.021 + np.random.uniform(-0.004, 0.004, len(s2_df))).round(4)
    s2_df["B8_NIR_Reflectance"] = (0.003 + np.random.uniform(-0.001, 0.001, len(s2_df))).round(4)
    s2_df["Data_Source_Type"] = "Digital_Twin_Simulated"
    s2_df["Scientific_Attribution"] = "Resultado obtenido mediante prototipo computacional del gemelo digital"
    s2_df.to_csv(os.path.join(RAW_DIR, "Sentinel2", "sentinel2_l2a_reflectance.csv"), index=False)

    # 3. Allen Coral Atlas Benthic feed
    aca_cols = [
        "Record_ID", "Station_ID", "Station_Name", "Latitude", "Longitude", "Reef_Zone",
        "Depth_m", "Structural_Rugosity", "Live_Coral_Cover_Pct", "Macroalgae_Cover_Pct",
        "Data_Source_Type", "Scientific_Attribution"
    ]
    df_master[aca_cols].to_csv(os.path.join(RAW_DIR, "Allen_Coral_Atlas", "allen_coral_atlas_benthic.csv"), index=False)

    # 4. In-Situ Mooring sensors feed
    moor_cols = [
        "Record_ID", "Date", "Station_ID", "Station_Name", "Depth_m", "pH_total",
        "Aragonite_Saturation_Omega", "Shannon_Diversity_H", "Bleaching_Severity_Pct",
        "Data_Source_Type", "Scientific_Attribution"
    ]
    df_master[moor_cols].to_csv(os.path.join(RAW_DIR, "Oceanographic_Data", "in_situ_mooring_sensors.csv"), index=False)


def generate_future_scenarios_dataset():
    """Generates forward time series (2025-2050) across 4 experimental management scenarios."""
    np.random.seed(SEED)
    years = np.arange(2025, 2051)
    scenarios = [
        "Scenario_1_Severe_Thermal_Stress_SSP585",
        "Scenario_2_Moderate_Mitigation_SSP245",
        "Scenario_3_Active_Coral_Restoration",
        "Scenario_4_MPA_Integrated_Protection",
    ]

    rows = []
    for sc in scenarios:
        cover = 32.0
        macroalgae = 22.0
        shannon = 2.85

        for yr in years:
            t = yr - 2025
            if sc == "Scenario_1_Severe_Thermal_Stress_SSP585":
                dhw_mean = 9.5 + 0.35 * t
                ph = 8.04 - 0.012 * t
                omega = 3.65 - 0.055 * t
                mortality = 0.045 * (dhw_mean / 4.0)**1.5
                growth = 0.02 * max(omega / 3.0, 0.2)
                grazing = 0.25
                resto_seed = 0.0
            elif sc == "Scenario_2_Moderate_Mitigation_SSP245":
                dhw_mean = 5.2 + 0.12 * t
                ph = 8.04 - 0.0045 * t
                omega = 3.65 - 0.022 * t
                mortality = 0.028 * (dhw_mean / 4.0)
                growth = 0.06 * max(omega / 3.0, 0.5)
                grazing = 0.35
                resto_seed = 0.0
            elif sc == "Scenario_3_Active_Coral_Restoration":
                dhw_mean = 7.0 + 0.20 * t
                ph = 8.04 - 0.007 * t
                omega = 3.65 - 0.035 * t
                mortality = 0.022 * max(dhw_mean - 2.5, 0.5) / 4.0
                growth = 0.08 * max(omega / 3.0, 0.6)
                grazing = 0.40
                resto_seed = 2.8
            else:
                dhw_mean = 6.5 + 0.18 * t
                ph = 8.04 - 0.006 * t
                omega = 3.65 - 0.030 * t
                mortality = 0.020 * max(dhw_mean - 2.0, 0.5) / 4.0
                growth = 0.09 * max(omega / 3.0, 0.7)
                grazing = 0.68
                resto_seed = 1.8

            unoccupied = max(100.0 - cover - macroalgae, 0.0)
            d_cover = (growth * cover * (unoccupied / 100.0) - mortality * cover + resto_seed)
            d_macro = (0.35 * macroalgae * (unoccupied / 100.0) - grazing * macroalgae * 0.4)

            cover = float(np.clip(cover + d_cover + np.random.normal(0, 0.6), 1.5, 80.0))
            macroalgae = float(np.clip(macroalgae + d_macro + np.random.normal(0, 0.8), 2.0, 85.0))
            shannon = float(np.clip(shannon + (0.02 if sc in ["Scenario_3_Active_Coral_Restoration", "Scenario_4_MPA_Integrated_Protection"] else -0.04) * (cover / 30.0), 0.4, 3.6))

            calcification_net = 12.5 * ((omega - 1.0) / 2.8)**1.2 * math.exp(-0.08 * dhw_mean) - (2.5 if macroalgae > 40 else 1.2)

            rows.append({
                "Year": int(yr),
                "Scenario_ID": sc,
                "Projected_DHW_degC_weeks": round(dhw_mean, 2),
                "Projected_pH": round(ph, 3),
                "Projected_Aragonite_Omega": round(omega, 2),
                "Live_Coral_Cover_Pct": round(cover, 2),
                "Macroalgae_Cover_Pct": round(macroalgae, 2),
                "Shannon_Diversity_H": round(shannon, 2),
                "Net_Calcification_kg_CaCO3_m2_yr": round(calcification_net, 2),
                "Data_Source_Type": "Digital_Twin_Simulated",
                "Scientific_Attribution": "Resultado obtenido mediante prototipo computacional del gemelo digital",
            })

    df_future = pd.DataFrame(rows)
    df_future.to_csv(os.path.join(SYNTHETIC_DIR, "synthetic_climate_scenarios_2025_2050.csv"), index=False)
    return df_future


def generate_literature_summary_files():
    """Creates papers_summary.xlsx and summary.csv for PRISMA literature matrix."""
    papers = [
        {"Authors": "Hoegh-Guldberg et al.", "Year": 2007, "Journal": "Science", "Title": "Coral reefs under rapid climate change and ocean acidification", "Citations": 6420, "Theme": "Biogeochemical & Acidification", "Key_Finding": "Synergistic threshold of 450ppm CO2 and +2C leads to widespread carbonate dissolution."},
        {"Authors": "Hughes et al.", "Year": 2018, "Journal": "Science", "Title": "Spatial and temporal patterns of mass bleaching of corals in the Anthropocene", "Citations": 2180, "Theme": "Thermal Stress & Climatology", "Key_Finding": "Recurrence interval between mass bleaching events has halved since 1980 to 5.9 years."},
        {"Authors": "Anthony et al.", "Year": 2011, "Journal": "Global Change Biology", "Title": "Ocean acidification and warming will lower coral reef resilience", "Citations": 890, "Theme": "Resilience Modeling", "Key_Finding": "Compounded acidification reduces critical thermal bleaching threshold by 1.0-1.5C."},
        {"Authors": "Mumby et al.", "Year": 2007, "Journal": "Nature", "Title": "Thresholds and the resilience of Caribbean coral reefs", "Citations": 1450, "Theme": "Ecological Dynamics", "Key_Finding": "Hysteresis and bistability between coral and macroalgal states mediated by herbivory grazing."},
        {"Authors": "Liu et al.", "Year": 2014, "Journal": "Remote Sensing", "Title": "NOAA Coral Reef Watch 50 km and 5 km satellite coral bleaching monitoring products", "Citations": 680, "Theme": "Remote Sensing & CRW", "Key_Finding": "Operational 5km satellite products enhance localized alert accuracy for coral heat stress."},
        {"Authors": "Lyons et al.", "Year": 2020, "Journal": "Ecological Indicators", "Title": "Mapping the world's coral reefs using high-resolution satellite imagery and machine learning", "Citations": 340, "Theme": "Machine Learning GIS", "Key_Finding": "Global Random Forest benthic classification achieves 78% overall accuracy on PlanetScope data."},
        {"Authors": "Rasheed et al.", "Year": 2020, "Journal": "IEEE Access", "Title": "Digital twin: Values, challenges and enablers from a modeling perspective", "Citations": 1250, "Theme": "Digital Twin Architecture", "Key_Finding": "Formalizes 6-layer cyber-physical data assimilation and hybrid physics-AI workflows."},
        {"Authors": "Beyer et al.", "Year": 2018, "Journal": "Conservation Letters", "Title": "Risk-sensitive planning for conserving coral reefs under rapid climate change", "Citations": 290, "Theme": "Spatial Conservation", "Key_Finding": "Identifies 50 priority reef bioclimatic biocapsules for climate change portfolio conservation."},
        {"Authors": "Voolstra et al.", "Year": 2021, "Journal": "Nature Protocols", "Title": "Standardized short-term acute thermal stress assays for rapidly assessing coral heat tolerance", "Citations": 210, "Theme": "Experimental Restoration", "Key_Finding": "CBASS protocol allows rapid phenotypic identification of thermally resilient super-corals."},
        {"Authors": "CoralTwin-DT Consortium", "Year": 2026, "Journal": "Global Change Biology (In Prep)", "Title": "Digital twin of coral reefs under thermal stress and ocean acidification for restoration prioritization", "Citations": 0, "Theme": "Integrated Cyber-Physical Twin", "Key_Finding": "Coupled 6-layer architecture with statistical emulation and TreeSHAP enables decadal spatial restoration optimization."}
    ]
    df_lit = pd.DataFrame(papers)
    csv_path = os.path.join(LIT_DIR, "papers_summary.csv")
    xlsx_path = os.path.join(LIT_DIR, "papers_summary.xlsx")
    df_lit.to_csv(csv_path, index=False)

    try:
        df_lit.to_excel(xlsx_path, index=False, engine="openpyxl")
    except Exception as e:
        print(f"Excel export notice: {e}")


if __name__ == "__main__":
    print("Generating unified 30-station harmonized dataset (N=15,000)...")
    df_harmonized = build_harmonized_dataset(n_samples=15000)

    df_harmonized.to_csv(FINAL_DATA_CSV, index=False)
    df_harmonized.to_csv(HARMONIZED_DATA_CSV, index=False)
    print(f"Unified dataset written to both {FINAL_DATA_CSV} and {HARMONIZED_DATA_CSV} ({len(df_harmonized)} records)")

    generate_final_data_dictionary()

    print("Extracting multi-source synthetic raw feeds...")
    generate_raw_source_feeds(df_harmonized)

    print("Simulating 2025-2050 forward climate scenarios...")
    df_future = generate_future_scenarios_dataset()
    print(f"Future climate scenarios written ({len(df_future)} records)")

    print("Generating PRISMA systematic literature matrices...")
    generate_literature_summary_files()

    print("Data synthesis and harmonization completed successfully.")
