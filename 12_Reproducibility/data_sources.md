# Primary Data Sources & Provenance Catalog: CoralTwin-DT

**Document Purpose:** Complete catalog of all empirical remote sensing, in-situ oceanographic, and benthic habitat data sources integrated into CoralTwin-DT.  
**Repository:** https://github.com/HrSly11/CoralTwin-DT.git  
**Licensing & Terms:** Open Data for Non-Commercial Research & Conservation (CC-BY 4.0 / Public Domain)  

---

## 1. Primary Empirical Data Sources Catalog

```
+-------------------------------------------------------------------------------------------------------------------------------+
|                                            PRIMARY DATA SOURCES SPECIFICATIONS                                                |
+----------------------+--------------------+---------------------+------------------+-----------------------+------------------+
| Data Source Name     | Operating Agency   | Spatial Resolution  | Temporal Cadence | Key Variables         | Access URL / API |
+----------------------+--------------------+---------------------+------------------+-----------------------+------------------+
| NOAA CRW Daily 5km   | NOAA NESDIS / CRW  | 5 km (0.05° grid)   | Daily            | SST, SSTA, HotSpot,   | ERDDAP / OPeNDAP |
| Satellite Products   | (United States)    |                     | (1985–Present)   | DHW (°C-weeks), MMM   | coralreefwatch.noaa.gov|
+----------------------+--------------------+---------------------+------------------+-----------------------+------------------+
| Copernicus Sentinel-2| European Space     | 10 m / 20 m         | 5 days           | Surface Reflectance   | Copernicus Data  |
| MSI Level-2A BOA     | Agency (ESA)       |                     | (2015–Present)   | Rrs(490), Rrs(560),   | Space Ecosystem  |
|                      |                    |                     |                  | Kd(490), Turbidity    | dataspace.copernicus.eu|
+----------------------+--------------------+---------------------+------------------+-----------------------+------------------+
| Allen Coral Atlas    | Vulcan / Arizona   | ~5 m                | Static Baseline  | Geomorphic Zones,     | allencoralatlas.org|
| Benthic Habitats     | State University   |                     | (2020 Update)    | Benthic Substrate     | Download Hub / WMS|
+----------------------+--------------------+---------------------+------------------+-----------------------+------------------+
| Global Coral Reef    | GCRMN / ICRI       | In-situ Transects   | Annual / Sporadic| Live Coral Cover %,   | gcrmn.net /      |
| Monitoring Network   | (International)    | (Fixed Stations)    | (1980–Present)   | Macroalgae %, Rugosity| Data Portal      |
+----------------------+--------------------+---------------------+------------------+-----------------------+------------------+
| In-Situ Biogeochem.  | NOAA Ocean Acid. / | Mooring Point Data  | Hourly           | pH (Total Scale), CTD | nodc.noaa.gov /  |
| Moorings & CTD       | Integrated Ocean   | (Global Buoys)      | (2010–Present)   | Salinity (PSU), DO    | NCEI Ocean Acid. |
+----------------------+--------------------+---------------------+------------------+-----------------------+------------------+
```

---

## 2. API Endpoints & Automated Download Access Points

### 2.1 NOAA Coral Reef Watch 5km Daily Global Satellite Ingestion (ERDDAP)
- **Protocol:** RESTful ERDDAP CSV/NetCDF Query
- **Base URL:** `https://coralreefwatch.noaa.gov/erddap/griddap/`
- **Dataset ID:** `noaacrw_5km_dhw_v3_1`
- **Sample Query Structure:**
  ```text
  https://coralreefwatch.noaa.gov/erddap/griddap/noaacrw_5km_dhw_v3_1.csv?CRW_DHW[(2024-01-01T12:00:00Z):1:(2024-12-31T12:00:00Z)][(18.0):1:(25.5)][(-88.5):1:(-80.0)]
  ```

### 2.2 Copernicus Sentinel-2 MSI Multi-Spectral Ingestion (OpenSearch API)
- **Protocol:** STAC / OData API via Copernicus Data Space Ecosystem
- **Base URL:** `https://catalogue.dataspace.copernicus.eu/stac/search`
- **Product Class:** `SENTINEL-2_MSI_Level-2A` (Bottom-Of-Atmosphere Reflectance)
- **Spectral Bands Used:** Band 2 (Blue, 490 nm), Band 3 (Green, 560 nm), Band 4 (Red, 665 nm), Band 8 (NIR, 842 nm).

### 2.3 Allen Coral Atlas Habitat Polygons
- **Protocol:** WFS / GeoJSON Export
- **Base URL:** `https://allencoralatlas.org/geoserver/wfs`
- **Typology:** Geomorphic Zoning (Fore Reef, Reef Crest, Back Reef, Lagoon) and Benthic Cover (Coral/Algae, Seagrass, Sand, Rubble).

---

## 3. Data Integration, Harmonization & Provenance Policy

```
[ RAW HETEROGENEOUS FEEDS ]
  ├─ NOAA CRW 5km NetCDF (SST, DHW)
  ├─ Sentinel-2 10m GeoTIFF (Rrs bands)
  ├─ Allen Coral Atlas Shapefile (Geomorphology)
  └─ In-Situ Mooring CSVs (pH, Salinity, DO)
               │
               ▼ (Bilinear Interpolation & Coordinate Reprojection to WGS84 EPSG:4326)
[ UNIFIED 500M BENTHIC TENSOR ]
  └─ 03_Data/final_dataset.csv (N = 15,000 records, 34 ISO-19115 attributes)
```

- **Real Observation Calibrated Records (41.2%):** Directly sampled and calibrated from historical NOAA CRW, GCRMN, and Sentinel-2 overpasses across 30 global reef stations (2015–2021).
- **Digital Twin Simulated Records (58.8%):** Numerically extrapolated using the coupled biophysical model to provide dense daily spatial time-series, non-linear stress tipping responses, and forward decadal scenario stress tests.
- **Scientific Attribution:** Certified under `"Resultado obtenido mediante prototipo computacional del gemelo digital"`.
