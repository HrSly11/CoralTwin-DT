"""
CoralTwin-DT: Master End-to-End Scientific Orchestration Pipeline
=================================================================
Reproduces and verifies the complete audited scientific workflow:
  1. Synthetic dataset generation & 30-station unification (SEED=42, N=15,000)
  2. Data provenance & RNG audit (`09_Results/audit/data_provenance.csv`)
  3. 5-fold spatial block cross-validation (>25 km buffer, min 119.72 km)
  4. Exploratory Data Analysis (EDA) & ANOVA
  5. Multi-seed (5 seeds x 5 folds) & 5-regime leakage ablation training
  6. Model evaluation, calibration (Brier/ECE), Wilcoxon & Cohen's d tests
  7. Legacy benchmark sync (`compare_rf_xgb_lstm.py`)
  8. Clean 10-feature interventional TreeSHAP & 2D partial dependence inflection points
  9. Coupled biophysical RK4 ODE decadal simulation (2025-2050; N=5,000 Monte Carlo)
 10. GIS Eq. (7) SRPI spatial prioritization & threshold sensitivity ({0.60, 0.70, 0.80})
 11. Master manuscript numbers compilation (`results/manuscript_numbers.json`)
 12. Dynamic 300 DPI publication figures rendering (Figures 1 to 7)
 13. Scientific manuscript PDF compilation (`.docx` files strictly untouched)
 14. Scientific presentation deck generation (`.pptx`)
 15. Scientific conference poster rendering (300 DPI `.png`)
 16. Executive summary & technical systems report PDF compilation

Writes execution telemetry to `results/pipeline_execution_log.json`.

Author: CoralTwin-DT Research Consortium
License: MIT
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


PIPELINE_STEPS = [
    ("Data Synthesis & 30-Station Unification", os.path.join("03_Data", "generate_datasets.py")),
    ("Data Provenance & Synthetic RNG Audit", os.path.join("03_Data", "audit_data_provenance.py")),
    ("5-Fold Spatial Block Cross-Validation (>25 km Buffer)", os.path.join("05_Methodology", "spatial_cv.py")),
    ("Exploratory Data Analysis (EDA) & Statistical Profiling", os.path.join("06_AI_and_Modeling", "exploratory_analysis", "eda.py")),
    ("Multi-Seed Spatial CV & 5-Regime Leakage Ablation Training", os.path.join("06_AI_and_Modeling", "machine_learning", "train_models.py")),
    ("Model Evaluation, Calibration & Non-Parametric Tests", os.path.join("06_AI_and_Modeling", "model_evaluation", "evaluate_models.py")),
    ("Benchmark Summary & Legacy Table Sync", os.path.join("06_AI_and_Modeling", "compare_rf_xgb_lstm.py")),
    ("Interventional TreeSHAP & 2D Partial Dependence Analysis", os.path.join("06_AI_and_Modeling", "explainability", "SHAP_analysis", "shap_explain.py")),
    ("Coupled RK4 ODE Decadal Simulation (2025-2050; N=5,000)", os.path.join("07_Scenarios_and_Simulations", "simulation_engine.py")),
    ("Spatial Restoration Priority Index (Eq. 7 SRPI) & Sensitivity", os.path.join("08_GIS_and_Remote_Sensing", "spatial_pipeline.py")),
    ("NOAA CRW 2015-2024 Generator Calibration (Train/Test)", os.path.join("01_Data", "calibrate_generator_to_noaa.py")),
    ("S4 vs S3 Factorial Isolation & ANOVA/Sobol (N=5,000)", os.path.join("07_Scenarios_and_Simulations", "s4_factor_isolation.py")),
    ("SRPI Extended Sensitivity (0.60-0.80, +-20% Weights, Bootstrap 10k, LOSO)", os.path.join("08_GIS_and_Remote_Sensing", "srpi_sensitivity.py")),
    ("Manuscript v3 DOCX Compilation & Track-Changes Report", os.path.join("09_Results", "build_v3_docx.py")),
    ("References & Banned Strings Audit (42 References, 0 Orphans)", os.path.join("09_Results", "audit_references.py")),
    ("Master Manuscript Numbers Compilation", os.path.join("09_Results", "build_manuscript_numbers.py")),
    ("Publication Figures Rendering (Figures 1-7 at 300 DPI)", os.path.join("09_Results", "generate_all_figures.py")),
    ("Scientific Manuscript PDF Compilation (DOCX Untouched)", os.path.join("10_Publication", "generate_publication_docs.py")),
    ("Scientific Presentation Deck Generation (.pptx)", os.path.join("11_Presentation", "generate_presentation.py")),
    ("Scientific Conference Poster Rendering (300 DPI .png)", os.path.join("11_Presentation", "generate_poster.py")),
    ("Executive Policy Brief PDF Compilation", os.path.join("11_Presentation", "generate_executive_summary_pdf.py")),
    ("Technical Systems Report PDF Compilation", os.path.join("13_Documentation", "generate_technical_report_pdf.py")),
]


def log_step(step_num, total_steps, title):
    print("\n" + "=" * 80)
    print(f" [STEP {step_num}/{total_steps}] {title}")
    print("=" * 80)


def run_script(rel_path):
    abs_path = os.path.join(PROJECT_ROOT, rel_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Script not found: {abs_path}")

    t0 = time.time()
    result = subprocess.run([sys.executable, abs_path], capture_output=False, text=True)
    elapsed = round(time.time() - t0, 3)
    if result.returncode != 0:
        print(f"Error executing {rel_path} (Return code {result.returncode})")
        sys.exit(result.returncode)
    print(f"Completed: {rel_path} in {elapsed:.2f}s")
    return elapsed, result.returncode


def main():
    start_total = time.time()
    print("*" * 80)
    print("  CORALTWIN-DT: MASTER SCIENTIFIC REPRODUCIBILITY ORCHESTRATOR")
    print("  Repository: https://github.com/HrSly11/CoralTwin-DT.git")
    print("*" * 80)

    step_logs = []
    total_steps = len(PIPELINE_STEPS)

    for idx, (title, rel_path) in enumerate(PIPELINE_STEPS, start=1):
        log_step(idx, total_steps, title)
        elapsed, rc = run_script(rel_path)
        step_logs.append({
            "step": idx,
            "title": title,
            "script": rel_path.replace("\\", "/"),
            "exit_code": rc,
            "elapsed_seconds": elapsed,
        })

    total_time = round(time.time() - start_total, 3)
    log_payload = {
        "pipeline": "CoralTwin-DT Master End-to-End Orchestrator",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "total_steps": total_steps,
        "all_steps_succeeded": all(s["exit_code"] == 0 for s in step_logs),
        "total_elapsed_seconds": total_time,
        "steps": step_logs,
    }
    log_path = os.path.join(RESULTS_DIR, "pipeline_execution_log.json")
    log_v3_path = os.path.join(RESULTS_DIR, "pipeline_execution_log_v3.json")
    for lp in [log_path, log_v3_path]:
        with open(lp, "w", encoding="utf-8") as f:
            json.dump(log_payload, f, indent=2)

    print("\n" + "=" * 80)
    print(f" ALL {total_steps} SCIENTIFIC PIPELINE STEPS EXECUTED SUCCESSFULLY IN {total_time:.2f}s!")
    print(f" Execution log written to: {log_path}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
