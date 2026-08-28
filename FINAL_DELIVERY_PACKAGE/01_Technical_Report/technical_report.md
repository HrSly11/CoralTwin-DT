# CoralTwin-DT: Technical Architecture & Systems Engineering Report

## 1. System Engineering Specifications

CoralTwin-DT is engineered as a modular, containerizable cyber-physical digital twin. This technical report provides comprehensive engineering specifications for scientific software auditors.

```
+-------------------------------------------------------------------------------+
|                       CORALTWIN-DT PIPELINE ARCHITECTURE                      |
+-------------------------------------------------------------------------------+
| Raw Telemetry Ingestion -> ETL & Spatial Resampling (500m)                    |
|                         -> Multi-Task XGBoost & Mumby ODE Hybrid Engine       |
|                         -> 5-Fold Spatially Stratified Validation             |
|                         -> 2025-2050 Monte Carlo Scenario Projections         |
|                         -> Spatial Restoration Priority Index (SRPI) Mapping  |
|                         -> 300 DPI Visualization & FAIR Open Delivery         |
+-------------------------------------------------------------------------------+
```

---

## 2. Mathematical State Space & ODE Dynamics

The benthic state vector $\mathbf{S}(t) = [C(t), M(t), T(t)]^T$ represents the fractional substrate cover of live corals ($C$), macroalgae ($M$), and available grazing turf ($T = 1 - C - M$):

$$\frac{dC}{dt} = r C (1 - C - M) - \left(d_0 + \alpha \frac{DHW(t)^2}{1 + \beta \Omega_{\text{arag}}(t)}\right) C + \Phi_{\text{restoration}}$$

$$\frac{dM}{dt} = a M (1 - C - M) - \frac{g(H_{\text{MPA}}) M}{M + (1 - C - M)} + \gamma M C$$

Parameters calibrated via empirical optimization:
- $r = 0.10 \text{ yr}^{-1}$ (Coral intrinsic lateral growth rate)
- $d_0 = 0.02 \text{ yr}^{-1}$ (Background non-thermal baseline mortality)
- $\alpha = 0.0035$ (Thermal stress mortality multiplier)
- $\beta = 0.45$ (Aragonite chemical buffering coefficient)
- $a = 0.55 \text{ yr}^{-1}$ (Macroalgal colonization rate)
- $\gamma = 0.15 \text{ yr}^{-1}$ (Macroalgal overgrowth rate onto living tissue)
- $g(H_{\text{MPA}}) \in [0.20, 0.70] \text{ yr}^{-1}$ (Herbivorous grazing pressure)
- $\Phi_{\text{restoration}} \in [0.0, 0.035] \text{ yr}^{-1}$ (Active micro-fragmentation seeding rate)

---

## 3. Supervised Model Engineering & Validation

- **XGBoost Hyperparameters:** `n_estimators=250`, `max_depth=6`, `learning_rate=0.05`, `subsample=0.8`, `colsample_bytree=0.8`, `eval_metric="mlogloss"`.
- **Cross-Validation Scheme:** 5-Fold Spatially Stratified Cross-Validation by geographic station clusters ($25\text{ km}$ spatial separation buffer).
- **Explainability:** TreeSHAP exact game-theoretic Shapley values calculated on $N=2,500$ sample matrix.

*Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.*
