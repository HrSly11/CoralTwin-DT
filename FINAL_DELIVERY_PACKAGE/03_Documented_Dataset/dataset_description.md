# Dataset Description: CoralTwin-DT Multi-Source Environmental & Benthic Repository

## 1. Overview & Data Provenance

The CoralTwin-DT repository integrates multi-source physical oceanographic observations, satellite remote sensing feeds, and benthic monitoring transects across pilot reef sectors located in the Caribbean (*Mesoamerican Barrier Reef System*) and Indo-Pacific (*Coral Triangle*).

```
+-------------------------------------------------------------------------------+
|                      MULTI-SOURCE DATA INGESTION MATRIX                       |
+-------------------------------------------------------------------------------+
| Source Feed             | Sensor / Mission       | Resolution   | Primary Var |
|-------------------------+------------------------+--------------+-------------|
| NOAA Coral Reef Watch   | AVHRR / VIIRS / MetOp  | 5 km / Daily | SST, DHW    |
| Copernicus Sentinel-2   | MSI Multispectral L2A  | 10 m / 5-day | Rrs, Kd(490)|
| Allen Coral Atlas       | PlanetScope / ML       | 3.7 m / Benth| Geomorphology|
| In-Situ Ocean Moorings  | SeaFET pH, CTD, PAR    | Point / Hour | pH, DO, PAR |
+-------------------------------------------------------------------------------+
```

---

## 2. Distinction: Real vs Synthetic Data

> [!IMPORTANT]
> **Data Integrity Statement:**
> - In-situ sensor baselines and satellite climatologies are calibrated against empirical NOAA Coral Reef Watch and GCRMN publications.
> - Forward projections (2025–2050) and fine-scale spatial grid interpolations are generated via the **computational digital twin prototype** (`03_Data/generate_datasets.py`) adhering to physical-chemical conservation laws.
> - All simulated data records are explicitly identified in metadata as: `"Resultado obtenido mediante prototipo computacional del gemelo digital"`.

---

## 3. Dataset Specifications

- **Total Harmonized Observations:** $N = 12,500$ spatio-temporal reef cell records.
- **Temporal Coverage:** 2015-01-01 to 2024-12-31 (Historical & Validation), with forward scenario projections spanning 2025–2050.
- **Spatial Resolution:** Standardized $500\text{m} \times 500\text{m}$ benthic grid cells.
- **Coordinate Reference System:** WGS 84 (EPSG:4326).
- **Target Categorical Variable:** `Bleaching_Risk` (`Low`, `Medium`, `High`).
- **Target Continuous Variable:** `Coral_Cover_Loss_Pct` ($\Delta C \in [0, 100]\%$).
