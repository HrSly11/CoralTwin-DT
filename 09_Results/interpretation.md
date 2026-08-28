# Ecological & Oceanographic Results Interpretation: CoralTwin-DT

## 1. Biophysical Model Interpretation & Non-Linear Thresholds

The empirical and simulated results from CoralTwin-DT demonstrate that coral reef degradation under climate change is governed by critical non-linear tipping points rather than smooth linear decay.

```
+-------------------------------------------------------------------------------+
|                       KEY ECOLOGICAL FINDINGS SUMMARY                         |
+-------------------------------------------------------------------------------+
| 1. Compound Thermal-Acidification Tipping Point:                              |
|    When DHW >= 8.0 °C-weeks and pH <= 7.85 (Omega_arag <= 2.8), coral         |
|    mortality accelerates non-linearly, exceeding 65% within 8 weeks.          |
| 2. Machine Learning Predictive Superiority:                                   |
|    XGBoost achieved Macro-F1 = 0.958 and R2 = 0.934 under 5-fold spatial     |
|    cross-validation, vastly outperforming linear baselines (F1 = 0.782).      |
| 3. Intervention Synergies (2025-2050):                                        |
|    Neither active outplanting nor passive MPA protection alone averts         |
|    macroalgal dominance under SSP5-8.5. Only hybrid intervention maintains    |
|    >45% live coral cover and net-positive framework accretion.                |
| 4. Spatial Micro-Refugia Prioritization:                                      |
|    Top Tier-1 priority zones (SRPI >= 0.70) cluster in well-flushed           |
|    fore-reef sites with high structural rugosity and moderate natural shading.|
+-------------------------------------------------------------------------------+
```

---

## 2. Quantitative Benchmark Validation

As documented in `Table 1` (`09_Results/tables/Table1_model_performance_benchmarks.md`), TreeSHAP feature attribution reveals that **Degree Heating Weeks (DHW)** accounts for $38.4\%$ of predictive model variance, followed by **Aragonite Saturation State ($\Omega_{\text{arag}}$)** at $21.2\%$, **Surface Seawater pH** at $14.8\%$, and **Benthic Structural Rugosity** at $11.5\%$.

---

## 3. Decadal Scenario Implications (2025–2050)

*Resultado obtenido mediante prototipo computacional del gemelo digital.*

- **Under SSP5-8.5 (Scenario 1):** Live coral cover collapses to $4.8\%$ [2.1% – 8.3%] by 2050, accompanied by complete carbonate dissolution ($-1.82\text{ kg CaCO}_3\text{ m}^{-2}\text{ yr}^{-1}$).
- **Under Integrated MPA & Active Restoration (Scenario 4):** Live coral cover recovers to $46.2\%$ [40.1% – 52.8%], with net calcification flourishing at $+6.80\text{ kg CaCO}_3\text{ m}^{-2}\text{ yr}^{-1}$.
