# CoralTwin-DT: Digital Twin Architecture Specification

## 1. Architectural Philosophy & Systems Engineering

CoralTwin-DT implements a six-layer cyber-physical digital twin architecture designed for environmental resilience, real-time telemetry assimilation, and forward ecological forecasting.

```
===================================================================================
                             CORALTWIN-DT ARCHITECTURE
===================================================================================

 [LAYER 6: DECISION SUPPORT & VISUALIZATION]
  - Scientific Dashboard | GIS Cartography | Restoration Priority Index (SRPI)
 ---------------------------------------------------------------------------------
 [LAYER 5: VALIDATION, BENCHMARKING & UNCERTAINTY]
  - 5-Fold Spatio-Temporal CV | Monte Carlo (N=10,000) | Backtesting 2015-2024
 ---------------------------------------------------------------------------------
 [LAYER 4: SCENARIO SIMULATION & FORWARD DYNAMICS]
  - SSP5-8.5 vs SSP2-4.5 | Thermal-Resistant Outplanting | MPA Herbivory Enforcement
 ---------------------------------------------------------------------------------
 [LAYER 3: HYBRID BIOPHYSICAL-AI MODELING ENGINE]
  - Coupled Mumby ODEs | Multi-task XGBoost / RF / MLP | TreeSHAP Attribution
 ---------------------------------------------------------------------------------
 [LAYER 2: DATA INTEGRATION, ETL & FAIR NORMALIZATION]
  - Spatiotemporal Harmonization (500m/Daily) | ISO 19115 Metadata | Data Quality
 ---------------------------------------------------------------------------------
 [LAYER 1: MULTI-SOURCE SENSORY & REMOTE DATA ACQUISITION]
  - NOAA Coral Reef Watch (5km) | Sentinel-2 L2A (10m) | Allen Coral Atlas | GCRMN
===================================================================================
```

---

## 2. Component Coupling & Data Flow

1. **Ingestion Pipeline:** Reads netCDF4/GeoTIFF raster tiles and in-situ benthic surveys.
2. **Feature Engineering Engine:** Extracts 84-day rolling heat accumulation ($DHW$), chemical saturation state ($\Omega_{\text{arag}}$), and optical attenuation proxies ($K_d$).
3. **Inference Pipeline:** Evaluates current Bleaching Risk class (`Low`, `Medium`, `High`) and continuous mortality rate ($\Delta C$).
4. **Dynamical Simulation Core:** Propagates benthic state variables ($C, M, T$) over 25-year projection horizons (2025–2050) under parameterized climate forcing.
5. **Spatial Allocation Engine:** Computes the Spatial Restoration Priority Index (SRPI) across candidate reef parcels.
