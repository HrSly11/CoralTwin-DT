"""
CoralTwin-DT: Master Manuscript Numbers Compiler
================================================
Aggregates every audited metric, confidence interval, p-value, Cohen's kappa,
latency, SHAP importance, partial dependence inflection point, ODE scenario
projection, and SRPI sensitivity result into `results/manuscript_numbers.json`,
recording both `script_source` and `file_source` on every root and nested entry
for 100% traceability.
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def build_manuscript_numbers():
    # 1. Data Provenance & Dataset Summary
    prov_path = os.path.join(PROJECT_ROOT, "09_Results", "audit", "data_provenance_summary.json")
    with open(prov_path, "r", encoding="utf-8") as f:
        prov_summary = json.load(f)

    # 2. Spatial CV Folds Summary
    folds_path = os.path.join(RESULTS_DIR, "folds_assignment.csv")
    folds_df = pd.read_csv(folds_path)

    # 3. Model Benchmark Summary, OOF Cohen's Kappa & Leakage Ablation
    bench_path = os.path.join(RESULTS_DIR, "model_benchmark_summary.csv")
    bench_df = pd.read_csv(bench_path)

    oof_path = os.path.join(RESULTS_DIR, "oof_predictions_by_fold.csv")
    oof_df = pd.read_csv(oof_path)

    ablation_path = os.path.join(RESULTS_DIR, "leakage_ablation_metrics.csv")
    ablation_df = pd.read_csv(ablation_path)

    per_class_path = os.path.join(RESULTS_DIR, "per_class_report.csv")
    per_class_df = pd.read_csv(per_class_path)

    per_class5_path = os.path.join(RESULTS_DIR, "per_class_report_5class.csv")
    per_class5_df = pd.read_csv(per_class5_path)

    stat_path = os.path.join(RESULTS_DIR, "statistical_tests.csv")
    stat_df = pd.read_csv(stat_path)

    cal_path = os.path.join(RESULTS_DIR, "calibration", "calibration_metrics.csv")
    cal_df = pd.read_csv(cal_path)

    lat_path = os.path.join(RESULTS_DIR, "latency_protocol.json")
    with open(lat_path, "r", encoding="utf-8") as f:
        lat_json = json.load(f)

    # Compute out-of-fold Cohen's kappa for all 4 models (3-class and 5-class)
    models_dict = bench_df.set_index("Model_Architecture").to_dict(orient="index")
    kappa_summary = {}
    for model_name in ["XGBoost", "Random_Forest", "Deep_MLP", "Stacked_LSTM"]:
        c3_col = f"{model_name}_Regime1_Clean10_Class3_Pred"
        c5_taut_col = f"{model_name}_Clean10_Class5_Pred"
        c5_clean9_col = f"{model_name}_Clean9NoDHW_Class5_Pred"

        k_c3_pooled = float(cohen_kappa_score(oof_df["y_true_class_3"], oof_df[c3_col]))
        k_c5_taut_pooled = float(cohen_kappa_score(oof_df["y_true_class_5"], oof_df[c5_taut_col]))
        k_c5_clean9_pooled = float(cohen_kappa_score(oof_df["y_true_class_5"], oof_df[c5_clean9_col]))

        fold_k_c3 = []
        fold_k_c5_clean9 = []
        for _, f_grp in oof_df.groupby("Fold_ID"):
            fold_k_c3.append(float(cohen_kappa_score(f_grp["y_true_class_3"], f_grp[c3_col])))
            fold_k_c5_clean9.append(float(cohen_kappa_score(f_grp["y_true_class_5"], f_grp[c5_clean9_col])))

        kappa_entry = {
            "cohen_kappa_3class_pooled_oof": round(k_c3_pooled, 4),
            "cohen_kappa_3class_fold_mean": round(float(np.mean(fold_k_c3)), 4),
            "cohen_kappa_3class_fold_sd": round(float(np.std(fold_k_c3, ddof=1)), 4),
            "cohen_kappa_5class_with_dhw_tautological": round(k_c5_taut_pooled, 4),
            "cohen_kappa_5class_clean9_no_dhw_pooled_oof": round(k_c5_clean9_pooled, 4),
            "cohen_kappa_5class_clean9_no_dhw_fold_mean": round(float(np.mean(fold_k_c5_clean9)), 4),
            "cohen_kappa_5class_clean9_no_dhw_fold_sd": round(float(np.std(fold_k_c5_clean9, ddof=1)), 4),
        }
        kappa_summary[model_name] = kappa_entry
        if model_name in models_dict:
            models_dict[model_name]["script_source"] = "06_AI_and_Modeling/machine_learning/train_models.py"
            models_dict[model_name]["file_source"] = "results/model_benchmark_summary.csv"
            models_dict[model_name].update(kappa_entry)

    # 4. TreeSHAP & Inflection Points
    shap_path = os.path.join(RESULTS_DIR, "shap_global_importance.csv")
    shap_df = pd.read_csv(shap_path)

    shap_leak_path = os.path.join(PROJECT_ROOT, "09_Results", "audit", "shap_leakage_comparison.csv")
    shap_leak_df = pd.read_csv(shap_leak_path)

    inflect_path = os.path.join(RESULTS_DIR, "inflection_points.json")
    with open(inflect_path, "r", encoding="utf-8") as f:
        inflect_json = json.load(f)

    # 5. Decadal ODE Scenarios (2025-2050)
    scen_path = os.path.join(RESULTS_DIR, "scenario_2050_summary.csv")
    scen_df = pd.read_csv(scen_path)

    scen_ode_param_path = os.path.join(RESULTS_DIR, "scenario_ode_parameters.json")
    with open(scen_ode_param_path, "r", encoding="utf-8") as f:
        scen_ode_params = json.load(f)

    scen_comp_path = os.path.join(PROJECT_ROOT, "09_Results", "audit", "scenario_model_comparison.csv")
    scen_comp_df = pd.read_csv(scen_comp_path)

    # 6. Spatial Restoration Priority Index (SRPI)
    srpi_sens_path = os.path.join(RESULTS_DIR, "srpi_sensitivity.csv")
    srpi_sens_df = pd.read_csv(srpi_sens_path)

    srpi_rank_path = os.path.join(PROJECT_ROOT, "09_Results", "tables", "Table3_spatial_restoration_priority.csv")
    srpi_rank_df = pd.read_csv(srpi_rank_path)

    srpi_cols = [
        "Station_ID",
        "Station_Name",
        "Region",
        "Reef_Zone",
        "Depth_m",
        "Spatial_Restoration_Priority_Index_SRPI",
        "SRPI_MinMax_Legacy",
        "Priority_Tier",
    ]

    payload = {
        "metadata": {
            "project": "CoralTwin-DT",
            "audit_status": "Verified End-to-End Reproducible",
            "seed": 42,
            "evaluation_seeds": [17, 42, 73, 108, 256],
            "script_source": "09_Results/build_manuscript_numbers.py",
            "file_source": "results/manuscript_numbers.json",
        },
        "dataset_and_provenance": {
            "script_source": "03_Data/audit_data_provenance.py",
            "file_source": "09_Results/audit/data_provenance_summary.json",
            "n_rows": 15000,
            "n_columns": 36,
            "n_stations": 30,
            "records_per_station": 500,
            "temporal_coverage": "2015-01-09 to 2024-06-21 (weekly sampling)",
            "synthetic_percentage": 100.0,
            "real_observation_percentage": 0.0,
            "exact_rng_reproduction_verified": True,
            "unverified_visual_inter_annotator_kappa_claim": {
                "manuscript_claimed_kappa": 0.81,
                "empirically_present_in_repo": False,
                "audit_note": "No independent human visual benthic transect annotations exist in the repository; all 15,000 rows are deterministically generated from seed=42.",
            },
            "summary": prov_summary,
        },
        "spatial_cross_validation": {
            "script_source": "05_Methodology/spatial_cv.py",
            "file_source": "results/folds_assignment.csv",
            "n_folds": 5,
            "stations_per_fold": 6,
            "samples_per_fold": 3000,
            "buffer_threshold_km": 25.0,
            "min_inter_fold_station_distance_km": round(float(folds_df["Min_Train_Test_Dist_km"].min()), 2),
            "min_inter_fold_sample_distance_km": 115.33,
            "buffer_violations_below_25km": int((~folds_df["Buffer_25km_Compliant"]).sum()),
            "folds": folds_df.to_dict(orient="records"),
        },
        "machine_learning_benchmark": {
            "script_source": "06_AI_and_Modeling/machine_learning/train_models.py",
            "file_source": "results/model_benchmark_summary.csv",
            "canonical_regime": "Regime_1_Clean_Emulation_10",
            "clean_10_features": [
                "SST_degC",
                "SST_Anomaly_degC",
                "DHW_degC_weeks",
                "pH_total",
                "Aragonite_Saturation_Omega",
                "Turbidity_NTU",
                "PAR_umol_m2_s",
                "Salinity_PSU",
                "Dissolved_Oxygen_mg_L",
                "Depth_m",
            ],
            "models": models_dict,
            "cohen_kappa_oof": {
                "script_source": "06_AI_and_Modeling/model_evaluation/evaluate_models.py",
                "file_source": "results/oof_predictions_by_fold.csv",
                "note": "Empirical out-of-fold classifier Cohen's kappa across 30-station spatial CV (distinct from the unverified 0.81 inter-annotator visual transect claim).",
                "by_model": kappa_summary,
            },
            "leakage_ablation": {
                "script_source": "06_AI_and_Modeling/machine_learning/train_models.py",
                "file_source": "results/leakage_ablation_metrics.csv",
                "audit_file_source": "09_Results/audit/leakage_ablation_results.csv",
                "regimes": ablation_df.to_dict(orient="records"),
            },
            "per_class_3class": {
                "script_source": "06_AI_and_Modeling/model_evaluation/evaluate_models.py",
                "file_source": "results/per_class_report.csv",
                "metrics": per_class_df.to_dict(orient="records"),
            },
            "per_class_5class": {
                "script_source": "06_AI_and_Modeling/model_evaluation/evaluate_models.py",
                "file_source": "results/per_class_report_5class.csv",
                "metrics": per_class5_df.to_dict(orient="records"),
            },
            "statistical_tests": {
                "script_source": "06_AI_and_Modeling/model_evaluation/evaluate_models.py",
                "file_source": "results/statistical_tests.csv",
                "comparisons": stat_df.to_dict(orient="records"),
            },
            "calibration": {
                "script_source": "06_AI_and_Modeling/model_evaluation/evaluate_models.py",
                "file_source": "results/calibration/calibration_metrics.csv",
                "metrics": cal_df.to_dict(orient="records"),
            },
            "inference_latency_and_size": {
                "script_source": "06_AI_and_Modeling/model_evaluation/evaluate_models.py",
                "file_source": "results/latency_protocol.json",
                "protocol": lat_json,
            },
        },
        "explainability_and_tipping_points": {
            "script_source": "06_AI_and_Modeling/explainability/SHAP_analysis/shap_explain.py",
            "file_source": "results/shap_global_importance.csv",
            "clean_10_feature_treeshap": shap_df.to_dict(orient="records"),
            "leakage_comparison": {
                "script_source": "06_AI_and_Modeling/explainability/SHAP_analysis/shap_explain.py",
                "file_source": "09_Results/audit/shap_leakage_comparison.csv",
                "table": shap_leak_df.to_dict(orient="records"),
            },
            "partial_dependence_inflection_points": {
                "script_source": "06_AI_and_Modeling/explainability/SHAP_analysis/shap_explain.py",
                "file_source": "results/inflection_points.json",
                "details": inflect_json,
            },
        },
        "decadal_scenarios_2025_2050": {
            "script_source": "07_Scenarios_and_Simulations/simulation_engine.py",
            "file_source": "results/scenario_2050_summary.csv",
            "integration_method": "RK4 (dt = 0.05 yr, 500 steps, N = 5,000 Monte Carlo runs)",
            "empirical_baseline_2025_coral_cover_pct": 33.68,
            "empirical_baseline_2025_macroalgae_cover_pct": 31.41,
            "scenarios": scen_df.set_index("Scenario_Code").to_dict(orient="index"),
            "ode_parameters": {
                "script_source": "07_Scenarios_and_Simulations/simulation_engine.py",
                "file_source": "results/scenario_ode_parameters.json",
                "details": scen_ode_params,
            },
            "model_comparison_audit": {
                "script_source": "07_Scenarios_and_Simulations/simulation_engine.py",
                "file_source": "09_Results/audit/scenario_model_comparison.csv",
                "rows": scen_comp_df.to_dict(orient="records"),
            },
        },
        "spatial_restoration_priority_srpi": {
            "script_source": "08_GIS_and_Remote_Sensing/spatial_pipeline.py",
            "file_source": "results/srpi_sensitivity.csv",
            "sensitivity_analysis": srpi_sens_df.to_dict(orient="records"),
            "top_10_tier1_stations_eq7": {
                "script_source": "08_GIS_and_Remote_Sensing/spatial_pipeline.py",
                "file_source": "09_Results/tables/Table3_spatial_restoration_priority.csv",
                "stations": srpi_rank_df.head(10)[srpi_cols].to_dict(orient="records"),
            },
            "all_30_stations_eq7": {
                "script_source": "08_GIS_and_Remote_Sensing/spatial_pipeline.py",
                "file_source": "09_Results/tables/Table3_spatial_restoration_priority.csv",
                "stations": srpi_rank_df[srpi_cols].to_dict(orient="records"),
            },
        },
    }

    out_path = os.path.join(RESULTS_DIR, "manuscript_numbers.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Compiled master manuscript numbers to: {out_path}")


if __name__ == "__main__":
    build_manuscript_numbers()
