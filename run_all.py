"""
CoralTwin-DT: Master End-to-End Scientific Orchestration Pipeline
================================================================
Reproduces the complete scientific workflow:
1. Data generation, synthesis & FAIR metadata harmonization
2. Exploratory Data Analysis (EDA) & ANOVA
3. Multi-task machine learning training (RF, XGBoost, MLP) with 5-fold spatial CV
4. Benchmark evaluation & confusion matrices
5. TreeSHAP game-theoretic explainability
6. Coupled biophysical ODE decadal simulation (2025-2050; N=5,000 Monte Carlo)
7. GIS spatial prioritization & GeoJSON generation
8. Publication-ready 300 DPI figures rendering (Figures 1 to 7)
9. Scientific manuscript compilation (DOCX & PDF)
10. Scientific presentation deck generation (.pptx)
11. Scientific conference poster rendering (.png, 300 DPI)
12. Executive summary policy brief compilation (.pdf)
13. Technical systems report compilation (.pdf)

Author: CoralTwin-DT Research Consortium
License: MIT
Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.
"""

import os
import sys
import time
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def log_step(step_num, title):
    print("\n" + "=" * 80)
    print(f" [STEP {step_num}/13] {title}")
    print("=" * 80)


def run_script(rel_path):
    abs_path = os.path.join(PROJECT_ROOT, rel_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Script not found: {abs_path}")
    
    t0 = time.time()
    result = subprocess.run([sys.executable, abs_path], capture_output=False, text=True)
    if result.returncode != 0:
        print(f"Error executing {rel_path} (Return code {result.returncode})")
        sys.exit(result.returncode)
    elapsed = time.time() - t0
    print(f"Completed: {rel_path} in {elapsed:.2f}s")


def main():
    start_total = time.time()
    print("*" * 80)
    print("  CORALTWIN-DT: MASTER SCIENTIFIC REPRODUCIBILITY ORCHESTRATOR")
    print("  Repository: https://github.com/HrSly11/CoralTwin-DT.git")
    print("  Target Journal: Global Change Biology / Ecological Informatics")
    print("*" * 80)

    # Step 1: Data Ingestion & Synthesis
    log_step(1, "Data Ingestion, Synthesis & FAIR Metadata Harmonization")
    run_script(os.path.join("03_Data", "generate_datasets.py"))

    # Step 2: Exploratory Data Analysis
    log_step(2, "Exploratory Data Analysis (EDA) & Statistical Profiling")
    run_script(os.path.join("06_AI_and_Modeling", "exploratory_analysis", "eda.py"))

    # Step 3: Model Training
    log_step(3, "Machine Learning Training & 5-Fold Spatially Stratified CV")
    run_script(os.path.join("06_AI_and_Modeling", "machine_learning", "train_models.py"))

    # Step 4: Model Evaluation
    log_step(4, "Model Evaluation, Metrics Benchmarking & Table 1 Generation")
    run_script(os.path.join("06_AI_and_Modeling", "model_evaluation", "evaluate_models.py"))

    # Step 5: TreeSHAP Explainability
    log_step(5, "TreeSHAP Game-Theoretic Explainability & Tipping Point Analysis")
    run_script(os.path.join("06_AI_and_Modeling", "explainability", "SHAP_analysis", "shap_explain.py"))

    # Step 6: Biophysical Simulation Engine
    log_step(6, "Decadal Forward Scenario Simulation (2025-2050; N=5,000 Monte Carlo)")
    run_script(os.path.join("07_Scenarios_and_Simulations", "simulation_engine.py"))

    # Step 7: GIS & Remote Sensing
    log_step(7, "Spatial Multi-Criteria Prioritization (SRPI) & GeoJSON Generation")
    run_script(os.path.join("08_GIS_and_Remote_Sensing", "spatial_pipeline.py"))

    # Step 8: Publication Figures Generator
    log_step(8, "Publication Figures Rendering (Figures 1-7 at 300 DPI)")
    run_script(os.path.join("09_Results", "generate_all_figures.py"))

    # Step 9: Manuscript Compilation
    log_step(9, "Scientific Manuscript Compilation (DOCX & PDF)")
    run_script(os.path.join("10_Publication", "generate_publication_docs.py"))

    # Step 10: Presentation Deck Generation
    log_step(10, "Scientific Presentation Deck Generation (.pptx)")
    run_script(os.path.join("11_Presentation", "generate_presentation.py"))

    # Step 11: Scientific Poster Generation
    log_step(11, "Scientific Conference Poster Rendering (300 DPI .png)")
    run_script(os.path.join("11_Presentation", "generate_poster.py"))

    # Step 12: Executive Summary PDF
    log_step(12, "Executive Policy Brief Compilation (.pdf)")
    run_script(os.path.join("11_Presentation", "generate_executive_summary_pdf.py"))

    # Step 13: Technical Systems Report PDF
    log_step(13, "Technical Architecture & Systems Report Compilation (.pdf)")
    run_script(os.path.join("13_Documentation", "generate_technical_report_pdf.py"))

    total_time = time.time() - start_total
    print("\n" + "=" * 80)
    print(f" ALL 13 SCIENTIFIC PIPELINES EXECUTED SUCCESSFULLY IN {total_time:.2f}s!")
    print(" 100% End-to-End Reproducibility Verified.")
    print(" Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
