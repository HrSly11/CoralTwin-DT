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
> - All $N = 15,000$ spatio-temporal records across the 30 global reef stations (`STN_01` to `STN_30`, 36 columns) are **100.0% synthetic (`Digital_Twin_Simulated`, `SEED = 42`)**, generated via `03_Data/build_final_dataset.py` using oceanographic and benthic bounds parameterized from NOAA Coral Reef Watch, Copernicus Sentinel-2, Allen Coral Atlas, and GCRMN literature.
> - Forward projections (2025–2050) are generated via the coupled RK4 ODE solver (`07_Scenarios_and_Simulations/simulation_engine.py`, $\Delta t = 0.05\text{ yr}$, $N = 5,000$ Monte Carlo runs).
> - All simulated data records are explicitly identified in metadata as: `"Resultado obtenido mediante prototipo computacional del gemelo digital"`.

---

## 3. Dataset Specifications

- **Total Harmonized Observations:** $N = 15,000$ weekly spatio-temporal records across 30 stations (`500` records/station, `36` attributes).
- **Temporal Coverage:** 2015-01-09 to 2024-06-21 (weekly sampling), with forward scenario projections spanning 2025–2050.
- **Spatial Coverage:** 30 reef stations (`STN_01`–`STN_30`) across 5 biogeographic provinces, partitioned into 5 spatial CV blocks with a minimum inter-fold station distance of $119.72\text{ km}$ ($115.33\text{ km}$ sample-level).
- **Coordinate Reference System:** WGS 84 (EPSG:4326).
- **Target Categorical Variables:** `Bleaching_Risk` (`Low`: $93.98\%$, `Medium`: $1.24\%$, `High`: $4.78\%$) and `Bleaching_Alert_Level` (`No_Stress`: $70.05\%$, `Watch`: $22.50\%$, `Warning`: $2.53\%$, `Alert_Level_1`: $0.14\%$, `Alert_Level_2`: $4.78\%$).
- **Target Continuous Variable:** `Coral_Cover_Loss_Pct` ($\Delta C \in [0, 100]\%$).
