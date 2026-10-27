# CoralTwin-DT: Open Research Archive for Zenodo

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

---

## 2. Experimental Random Seeds
- **Data Generator Seed:** `42`
- **Spatial Block Cross-Validation Evaluation Seeds:** `[17, 42, 73, 108, 256]` (5-fold spatial CV, 25 outer executions)
- **Train/Test Spatial Buffer:** $\ge 25	ext{ km}$ minimum geographical separation (actual minimum inter-fold distance $= 119.72	ext{ km}$; 0 buffer violations).

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
