# Data & Model Availability Statement: CoralTwin-DT

## 1. FAIR Data Principles Compliance

CoralTwin-DT adheres strictly to the **FAIR Data Principles** (Findable, Accessible, Interoperable, Reusable):

- **Findable:** Datasets are assigned unique identifiers and documented using ISO 19115 / Dublin Core compliant metadata schemas in `03_Data/metadata/data_dictionary.csv`.
- **Accessible:** All data feeds, processed CSVs, and GeoJSON priority layers are stored without paywalls or proprietary formats in the public repository: https://github.com/HrSly11/CoralTwin-DT.git.
- **Interoperable:** Spatial layers use standard WGS 84 (EPSG:4326) coordinate reference systems and standard GeoJSON / netCDF4 / CSV formats.
- **Reusable:** Released under the permissive open-source **MIT License**, permitting unrestricted academic, governmental, and commercial reuse with scientific attribution.

---

## 2. Model & Weight Checkpoints

Trained machine learning models (XGBoost, Random Forest, Multi-Layer Perceptrons, Feature Scalers, Label Encoders) are stored in `06_AI_and_Modeling/machine_learning/saved_models/` as serialized `joblib` artifacts, enabling instant out-of-the-box inference on new oceanographic telemetry streams.

---

## 3. Scientific Attribution & Integrity

All forward-projected or synthetically calibrated outputs in this repository are certified with the standard reproducibility label:  
`"Resultado obtenido mediante prototipo computacional del gemelo digital"`.
