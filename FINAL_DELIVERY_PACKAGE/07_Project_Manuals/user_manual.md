# CoralTwin-DT: Operational User Manual & System Guide

## 1. System Requirements & Architecture Overview

CoralTwin-DT is an integrated computational environment for marine ecosystem modeling, real-time telemetry assimilation, and forward restoration prioritization.

```
System Requirements:
- Python: 3.10+ (Recommended: 3.11)
- Memory (RAM): >= 8 GB
- Disk Space: ~ 500 MB (Dataset + Serialized Models + Figures)
- Supported OS: Windows 10/11, Linux (Ubuntu 20.04+), macOS (12+)
```

---

## 2. Step-by-Step Operational Instructions

### 2.1 Ingesting New Satellite / Sensor Feeds
To assimilate new oceanographic data:
1. Place raw NOAA CRW netCDF or CSV daily feeds into `03_Data/raw_data/NOAA/`.
2. Place Sentinel-2 multispectral reflectance files into `03_Data/raw_data/Sentinel2/`.
3. Execute the data harmonization pipeline:
   ```bash
   python 03_Data/generate_datasets.py
   ```

### 2.2 Running Predictive Bleaching Inference
To evaluate bleaching risk across a newly updated dataset:
```python
import joblib
import pandas as pd

# Load serialized XGBoost production classifier and scaler
model = joblib.load("06_AI_and_Modeling/machine_learning/saved_models/xgboost_classifier.joblib")
scaler = joblib.load("06_AI_and_Modeling/machine_learning/saved_models/feature_scaler.joblib")
le = joblib.load("06_AI_and_Modeling/machine_learning/saved_models/label_encoder.joblib")

# Example input tensor: [Depth, SST, SSTA, DHW, pH, Omega, Turbidity, PAR, Rugosity, Cover]
sample_features = [[12.5, 30.2, 1.8, 9.4, 7.82, 2.65, 1.4, 1650, 2.2, 28.5]]
pred_class_idx = model.predict(sample_features)[0]
risk_label = le.inverse_transform([pred_class_idx])[0]
print(f"Predicted Bleaching Risk Category: {risk_label}") # Outputs: 'High'
```

### 2.3 Simulating Forward Restoration Scenarios
To simulate custom outplanting density or MPA protection levels:
```bash
python 07_Scenarios_and_Simulations/simulation_engine.py
```
Outputs are written to `09_Results/tables/Table2_decadal_scenario_projections.csv` and `09_Results/statistics/monte_carlo_trajectories_2025_2050.csv`.

### 2.4 Generating Spatial Cartography & GeoJSON Layers
To compute the Spatial Restoration Priority Index (SRPI) for GIS mapping:
```bash
python 08_GIS_and_Remote_Sensing/spatial_pipeline.py
```
Open `08_GIS_and_Remote_Sensing/geospatial_outputs/priority_restoration_zones.geojson` directly in QGIS or ArcGIS.
