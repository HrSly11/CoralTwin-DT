# Research Protocol: CoralTwin-DT

## 1. Experimental Design & Computational Setup

The research protocol follows a formal 5-stage doctoral investigation workflow:

```
[ Stage 1: Data Ingestion & FAIR Standardization ]
                     |
                     v
[ Stage 2: Feature Engineering & Spatiotemporal Harmonization ]
                     |
                     v
[ Stage 3: Supervised Machine Learning & Biophysical Coupling ]
                     |
                     v
[ Stage 4: 2025-2050 Scenario Simulation & Uncertainty Quantification ]
                     |
                     v
[ Stage 5: Multi-Criteria Spatial Optimization & Scientific Dissemination ]
```

---

## 2. Quantitative Quality Control Protocol

1. **Replication & Determinism:** All pseudorandom processes (data synthesis, train/test splitting, bootstrapping) use a fixed master seed `SEED = 42`.
2. **Spatial Stratification:** Evaluation sets are split into spatial clusters with a minimum buffer distance of $25\text{ km}$ to avoid leakage across neighboring reef cells.
3. **Data Provenance:** Every transformation from raw netCDF/GeoTIFF inputs to tabular training tensors is logged with SHA-256 hashes and timestamped metadata.
4. **Attribution Requirement:** Every simulated or forward-projected metric is explicitly flagged as `"Resultado obtenido mediante prototipo computacional del gemelo digital"`.
