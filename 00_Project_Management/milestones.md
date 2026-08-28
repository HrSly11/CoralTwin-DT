# CoralTwin-DT: Scientific Milestones & Verification Criteria

## Key Research Milestones (M1 – M6)

| Milestone ID | Target Phase | Description & Key Deliverables | Verification & Success Criteria | Status |
| :--- | :--- | :--- | :--- | :---: |
| **M1: Ingestion & FAIR Data** | Months 1–2 | Multimodal dataset harmonized (NOAA CRW, Sentinel-2, Allen Coral Atlas). Data dictionary and synthetic biophysical generator complete. | Data validation passes without nulls. Schema adheres to ISO 19115. Physical equations reproduce known thermodynamics ($CO_2-pH-\Omega_{\text{arag}}$). | **ACHIEVED** |
| **M2: 6-Layer DT Architecture** | Months 3–4 | Formal design of Six-Layer Cyber-Physical Digital Twin Architecture documented with conceptual diagrams and data flow specifications. | Complete separation of Acquisition, Integration, Modeling, Simulation, Validation, and Visualization layers. | **ACHIEVED** |
| **M3: Machine Learning Engine** | Months 5–6 | Training, optimization, and spatial cross-validation of Random Forest, XGBoost, and Deep Neural Networks for bleaching prediction. | Multi-class Bleaching Risk Macro-F1 $> 0.90$, Regression $R^2 > 0.85$ on unseen spatial test blocks. | **ACHIEVED** |
| **M4: XAI & Biophysical Discovery** | Months 7–8 | TreeSHAP explainability pipeline quantifying global feature importance and interaction terms (DHW $\times$ pH). | SHAP summary, beeswarm, and partial dependence plots rendered at 300 DPI with ecological consistency. | **ACHIEVED** |
| **M5: Forward Simulation & MCE** | Months 9–10 | Coupled ODE simulation of 4 IPCC/restoration scenarios (2025–2050) and Spatial Restoration Priority Index (SRPI) mapping. | Convergence of dynamical trajectory models; spatial priority geo-layers generated with zero topology errors. | **ACHIEVED** |
| **M6: Manuscript & Dissemination** | Months 11–12 | Full Q1 research paper, 7 publication figures, supplementary materials, PPTX slide deck, scientific poster, and master runner `run_all.py`. | 100% automated reproduction verification across all scripts. Manuscript conforms to *Global Change Biology* author guidelines. | **ACHIEVED** |

---

## Reproducibility Gates

1. **Gate A (Data Integrity):** Deterministic random seeds (`SEED = 42`) across all data generation and cross-validation splits.
2. **Gate B (Model Convergence):** Training loss convergence verified across all ML and deep neural architectures without overfitting.
3. **Gate C (Scientific Attribution):** Clear metadata flagging all forward projections with `"Resultado obtenido mediante prototipo computacional del gemelo digital"`.
