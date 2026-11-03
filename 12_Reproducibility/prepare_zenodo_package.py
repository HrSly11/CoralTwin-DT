"""
12_Reproducibility/prepare_zenodo_package.py
============================================
Implements Task 7a:
Bundles the artifacts required for official archiving on Zenodo:
1. Synthetic Benchmark Dataset (`03_Data/final_dataset.csv`, N=15,000, 30 stations, seed=42)
2. All Trained Models & Weights (`06_AI_and_Modeling/machine_learning/saved_models/`)
3. Geospatial GeoJSON Layers (`08_GIS_and_Remote_Sensing/geospatial_outputs/*.geojson`)
4. Zenodo Archival Documentation (`results/zenodo_package/README_ZENODO.md`)
5. Creates compressed archival bundle: `results/zenodo_package/CoralTwin-DT_Zenodo_Archive_v1.0.0.zip`
"""

import os
import zipfile
import shutil
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE_DIR = os.path.join(BASE_DIR, "results", "zenodo_package")
os.makedirs(PACKAGE_DIR, exist_ok=True)

DATA_SRC = os.path.join(BASE_DIR, "03_Data", "final_dataset.csv")
MODELS_SRC = os.path.join(BASE_DIR, "06_AI_and_Modeling", "machine_learning", "saved_models")
GEOJSON_SRC = os.path.join(BASE_DIR, "08_GIS_and_Remote_Sensing", "geospatial_outputs")
BENCHMARK_SRC = os.path.join(BASE_DIR, "results", "manuscript_numbers.json")

README_CONTENT = """# CoralTwin-DT: Open Research Archive for Zenodo

**Digital Twin Prototyping & Ecological Emulation for Global Coral Reef Systems**
**Repository:** `https://github.com/HrSly11/CoralTwin-DT`  
**License:** MIT License  
**Release Version:** v1.0.0 (Reproducible Scientific Audit Release)  

---

## 1. Description & Archival Scope
This archive contains the complete computational assets required to independently replicate, verify, and inspect the machine learning models, spatial cross-validation, and scenario projections of the **CoralTwin-DT** project:

1. **Synthetic Multi-Stressor Benchmark Dataset (`final_dataset.csv`):**
   - Observations: $N = 15,000$ weekly records spanning 2015-01-01 to 2024-12-30.
   - Spatial Extent: 30 globally distributed reef station complexes ($500$ observations per station).
   - Dimensionality: 36 environmental, oceanographic, carbonate, and ecological columns.
   - Provenance: 100.0% computationally simulated via biophysical coupling equations with literature-derived empirical bounds.
   - Generator Random Number Seed: `SEED = 42` (`numpy.random`).

2. **Pretrained Model Weights & Serialization Assets (`saved_models/`):**
   - `xgboost_classifier.joblib` & `xgboost_regressor.joblib`: Canonical 10-feature gradient-boosted trees.
   - `random_forest_classifier.joblib` & `random_forest_regressor.joblib`: 200-estimator ensemble trees.
   - `deep_mlp_classifier.pt` & `deep_mlp_regressor.pt`: PyTorch 4-layer MLP with BatchNorm and Dropout.
   - `stacked_lstm_classifier.pt` & `stacked_lstm_regressor.pt`: PyTorch 2-layer stacked LSTM (`seq_len = 8`).
   - `feature_scaler.joblib`, `label_encoder.joblib`, `preprocessing_contract.json`.

3. **Geospatial GeoJSON Layers (`geospatial_outputs/`):**
   - `reefs_restoration_priority_zones.geojson`: 30-station global coordinates with Eq. 7 SRPI index and priority tiers.
   - `coral_triangle_aoi.geojson`, `great_barrier_reef_aoi.geojson`, `mesoamerican_reef_aoi.geojson`.

4. **Master Numerical Registry (`manuscript_numbers.json`):**
   - Complete machine-readable JSON containing every single numerical figure cited in the manuscript with exact file and script provenance.

5. **Reviewer Sensitivity & S4 Factor Isolation Suite:**
   - `07_Scenarios_and_Simulations/s4_factor_isolation.py`: Coupled ODE factor isolation (DHW, grazing g, restoration Phi, Omega).
   - `08_GIS_and_Remote_Sensing/srpi_sensitivity_analysis.py`: Multi-criteria SRPI threshold and weight sensitivity (5 thresholds, +-20% weights, 10,000 Monte Carlo draws).
   - Associated analytical results: `results/s4_factor_isolation_*.csv`, `results/srpi_*sensitivity*.csv`.

---

## 2. Experimental Random Seeds
- **Data Generator Seed:** `42`
- **Spatial Block Cross-Validation Evaluation Seeds:** `[17, 42, 73, 108, 256]` (5-fold spatial CV, 25 outer executions)
- **Train/Test Spatial Buffer:** $\ge 25\text{ km}$ minimum geographical separation (actual minimum inter-fold distance $= 119.72\text{ km}$; 0 buffer violations).

---

## 3. Step-by-Step Instructions for Obtaining Your Official Zenodo DOI

To obtain the real, permanent Digital Object Identifier (DOI) for *Ecocycles*:

### Option A: Automatic GitHub-Zenodo Integration (Recommended)
1. Navigate to **Zenodo** (`https://zenodo.org`) and log in using your GitHub account (`HrSly11`).
2. Go to **Settings > GitHub** (`https://zenodo.org/account/settings/github/`).
3. Locate the repository `HrSly11/CoralTwin-DT` in the list and flip the toggle switch to **ON (Enabled)**.
4. Return to GitHub, go to `https://github.com/HrSly11/CoralTwin-DT/releases/new`.
5. Create a new release tag: `v1.0.0` (Title: `CoralTwin-DT v1.0.0: Certified Reproducible Release`).
6. Click **Publish Release**.
7. Zenodo will immediately detect the release, archive the exact repository snapshot, and mint your real DOI (e.g., `10.5281/zenodo.XXXXXXX`).

### Option B: Manual Upload via Zenodo Web Portal
1. Navigate to `https://zenodo.org/deposit/new`.
2. Under **Files**, drag and drop the provided archive: `CoralTwin-DT_Zenodo_Archive_v1.0.0.zip`.
3. Under **Basic Information**:
   - **Upload type:** Dataset (or Software).
   - **Publication date:** 2026-10-27 (or current submission date).
   - **Title:** `CoralTwin-DT: Cyber-Physical Architecture & Machine Learning Emulation for Global Coral Reef Conservation`.
   - **Authors:** List authors matching the manuscript.
   - **Description:** Copy the summary from Section 1 above.
   - **License:** Open Access -> Creative Commons Attribution 4.0 International (or MIT).
4. Click **Reserve DOI** in the upper right. Zenodo will issue your guaranteed DOI string before publishing.
5. Paste this real DOI into Section 5 and Table 2 of the manuscript.
6. Click **Save** and then **Publish**.

---

## 4. Software Environment & Execution
```bash
# Clone and enter workspace
git clone https://github.com/HrSly11/CoralTwin-DT.git
cd CoralTwin-DT

# Using Docker (Identical pinned environment)
docker build -t coraltwin-dt:v1 .
docker run --rm coraltwin-dt:v1

# Or locally with Python 3.11:
pip install -r requirements.txt
python run_all.py
```
"""


def main():
    print("=" * 70)
    print("TASK 7a: Preparing Zenodo Archival Package")
    print("=" * 70)

    # 1. Write README_ZENODO.md
    readme_path = os.path.join(PACKAGE_DIR, "README_ZENODO.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(README_CONTENT.strip() + "\n")
    print(f"Created: {readme_path}")

    # 2. Build ZIP package
    zip_path = os.path.join(PACKAGE_DIR, "CoralTwin-DT_Zenodo_Archive_v1.0.0.zip")
    print(f"Building archival zip bundle: {zip_path}...")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add README
        zf.write(readme_path, arcname="README_ZENODO.md")

        # Add Dataset
        if os.path.exists(DATA_SRC):
            zf.write(DATA_SRC, arcname="data/final_dataset.csv")
            print("  + Added data/final_dataset.csv")

        # Add master numbers
        if os.path.exists(BENCHMARK_SRC):
            zf.write(BENCHMARK_SRC, arcname="results/manuscript_numbers.json")
            print("  + Added results/manuscript_numbers.json")

        # Add models
        if os.path.exists(MODELS_SRC):
            for fname in os.listdir(MODELS_SRC):
                fpath = os.path.join(MODELS_SRC, fname)
                if os.path.isfile(fpath):
                    zf.write(fpath, arcname=f"saved_models/{fname}")
            print(f"  + Added saved_models/ ({len(os.listdir(MODELS_SRC))} files)")

        # Add geojson layers
        if os.path.exists(GEOJSON_SRC):
            for fname in os.listdir(GEOJSON_SRC):
                fpath = os.path.join(GEOJSON_SRC, fname)
                if os.path.isfile(fpath) and fname.endswith(".geojson"):
                    zf.write(fpath, arcname=f"geospatial_outputs/{fname}")
            print("  + Added geospatial_outputs/ (*.geojson)")

        # Add reviewer analysis scripts and outputs (v1.0.1 + v2.0.0 closure suite)
        extra_files = [
            ("01_Data/calibrate_generator_to_noaa.py", "01_Data/calibrate_generator_to_noaa.py"),
            ("03_Data/calibrate_generator_to_noaa.py", "03_Data/calibrate_generator_to_noaa.py"),
            ("03_Data/final_dataset_noaa_calibrated.csv", "data/final_dataset_noaa_calibrated.csv"),
            ("07_Scenarios_and_Simulations/s4_factor_isolation.py", "07_Scenarios_and_Simulations/s4_factor_isolation.py"),
            ("08_GIS_and_Remote_Sensing/srpi_sensitivity.py", "08_GIS_and_Remote_Sensing/srpi_sensitivity.py"),
            ("08_GIS_and_Remote_Sensing/srpi_sensitivity_analysis.py", "08_GIS_and_Remote_Sensing/srpi_sensitivity_analysis.py"),
            ("09_Results/audit_references.py", "09_Results/audit_references.py"),
            ("09_Results/build_manuscript_numbers.py", "09_Results/build_manuscript_numbers.py"),
            ("09_Results/build_v3_docx.py", "09_Results/build_v3_docx.py"),
            ("figures/fig_noaa_calibration_v3.png", "figures/fig_noaa_calibration_v3.png"),
            ("references_audit.csv", "references_audit.csv"),
            ("Grupo28B_RodriguezSandoval_HarrySly_v3.docx", "Grupo28B_RodriguezSandoval_HarrySly_v3.docx"),
            ("Grupo28B_RodriguezSandoval_HarrySly_v3_trackchanges_report.md", "Grupo28B_RodriguezSandoval_HarrySly_v3_trackchanges_report.md"),
            ("response_to_reviewer_v3.md", "response_to_reviewer_v3.md"),
            ("Dockerfile", "Dockerfile"),
            ("verify_release.sh", "verify_release.sh"),
            ("SHA256SUMS", "SHA256SUMS"),
        ]
        for rel_src, arc_dst in extra_files:
            f_src = os.path.join(BASE_DIR, *rel_src.split("/"))
            if os.path.exists(f_src):
                zf.write(f_src, arcname=arc_dst)
                print(f"  + Added {arc_dst}")

        results_dir = os.path.join(BASE_DIR, "results")
        if os.path.exists(results_dir):
            prefixes = (
                "s4_factor_isolation",
                "srpi_",
                "noaa_",
                "references_audit",
                "pipeline_execution_log",
            )
            for fname in sorted(os.listdir(results_dir)):
                if fname.startswith(prefixes):
                    fpath = os.path.join(results_dir, fname)
                    if os.path.isfile(fpath):
                        zf.write(fpath, arcname=f"results/{fname}")
                        print(f"  + Added results/{fname}")

    zip_size_mb = os.path.getsize(zip_path) / (1024.0 * 1024.0)
    print(f"\nZenodo archival package ready: {zip_path} ({zip_size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
