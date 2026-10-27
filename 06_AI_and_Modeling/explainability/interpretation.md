# TreeSHAP Explainability & Partial Dependence Interpretation Report

**Project:** CoralTwin-DT (Synthetic Biophysical Digital Twin Benchmark)  
**Script Source:** [`06_AI_and_Modeling/explainability/SHAP_analysis/shap_explain.py`](file:///c:/Users/Harry/Documents/CICLO%208/ING%20SOFT%20II/CoralTwin-DT/06_AI_and_Modeling/explainability/SHAP_analysis/shap_explain.py)  
**Primary Artifacts:**
- [`results/shap_global_importance.csv`](file:///c:/Users/Harry/Documents/CICLO%208/ING%20SOFT%20II/CoralTwin-DT/results/shap_global_importance.csv)
- [`09_Results/audit/shap_leakage_comparison.csv`](file:///c:/Users/Harry/Documents/CICLO%208/ING%20SOFT%20II/CoralTwin-DT/09_Results/audit/shap_leakage_comparison.csv)
- [`results/partial_dependence_dhw_ph.csv`](file:///c:/Users/Harry/Documents/CICLO%208/ING%20SOFT%20II/CoralTwin-DT/results/partial_dependence_dhw_ph.csv)
- [`results/inflection_points.json`](file:///c:/Users/Harry/Documents/CICLO%208/ING%20SOFT%20II/CoralTwin-DT/results/inflection_points.json)

---

## 1. Methodological Scope & Emulator Disclaimer

All TreeSHAP attributions and two-dimensional partial dependence (PDP) curves reported here are computed using **interventional TreeSHAP** (`feature_perturbation="interventional"` with a 500-sample background distribution and $B = 200$ station-block bootstrap resamples) on out-of-fold models trained under **5-Fold Spatial Block Cross-Validation** ($>25\text{ km}$ inter-fold buffer; minimum inter-fold station distance $= 119.72\text{ km}$).

> [!IMPORTANT]
> Because the unified benchmark dataset (`03_Data/final_dataset.csv`, $N = 15,000$ rows across 30 stations) is 100.0% synthetic (`SEED = 42`), these TreeSHAP values and partial dependence thresholds quantify how the machine learning emulator recovers the coupled biophysical rules programmed in the data generator (`03_Data/build_final_dataset.py`). They do **not** constitute empirical discovery of new biological thresholds from wild field telemetry.

---

## 2. Clean 10-Feature Global TreeSHAP Attribution (`Regime_1_Clean_Emulation_10`)

When co-generated benthic state variables (`Shannon_Diversity_H`, `Structural_Rugosity`, `Live_Coral_Cover_Pct`, `Macroalgae_Cover_Pct`, `Turf_Algae_Cover_Pct`, `Colony_Density_m2`) are properly excluded from the predictor matrix, the 10 clean environmental predictors rank as follows (`results/shap_global_importance.csv`):

| Rank | Feature | Mean \|SHAP\| (% Cover Loss) | Normalized Importance (%) | 95% Station-Bootstrap CI (%) |
| :---: | :--- | :---: | :---: | :---: |
| 1 | `DHW_degC_weeks` | 3.8127 | **53.71%** | [51.37%, 55.98%] |
| 2 | `PAR_umol_m2_s` | 0.8057 | **11.35%** | [10.50%, 12.28%] |
| 3 | `SST_Anomaly_degC` | 0.6587 | **9.28%** | [8.99%, 9.59%] |
| 4 | `Aragonite_Saturation_Omega` | 0.6256 | **8.81%** | [8.23%, 9.45%] |
| 5 | `SST_degC` | 0.3684 | **5.19%** | [4.97%, 5.39%] |
| 6 | `Salinity_PSU` | 0.1887 | **2.66%** | [2.47%, 2.88%] |
| 7 | `Depth_m` | 0.1794 | **2.53%** | [2.32%, 2.74%] |
| 8 | `pH_total` | 0.1683 | **2.37%** | [2.19%, 2.57%] |
| 9 | `Dissolved_Oxygen_mg_L` | 0.1526 | **2.15%** | [1.99%, 2.33%] |
| 10 | `Turbidity_NTU` | 0.1387 | **1.95%** | [1.79%, 2.13%] |

---

## 3. Reverse Leakage Proof: Clean 10 vs. Leaked 13 vs. Leaked 16 (`09_Results/audit/shap_leakage_comparison.csv`)

A critical finding of the audit is why legacy scripts and pre-audit manuscript tables diverged on feature importance:

1. **16-Feature Leaked Regime (`compare_rf_xgb_lstm.py` legacy):** Included `Shannon_Diversity_H`, which was generated in `03_Data/build_final_dataset.py` (line 206) *after* `Bleaching_Severity_Pct` via the deterministic formula:
   $$\text{Shannon\_Diversity\_H} = \text{clip}\left(2.4 + 0.38 \cdot (\text{Rugosity} - 2.0) - 0.015 \cdot \text{Bleaching\_Severity\_Pct} + \epsilon_H,\; 0.5,\; 3.8\right)$$
   Because `Coral_Cover_Loss_Pct` is directly proportional to `Bleaching_Severity_Pct`, tree models inverted this equation, causing `Shannon_Diversity_H` to absorb **58.65%** of total TreeSHAP importance (`DHW_degC_weeks` dropped to **26.57%**).
2. **13-Feature Partially Leaked Regime (`train_models.py` legacy):** Excluded `Shannon_Diversity_H` but retained co-generated benthic state responses (`Structural_Rugosity` and `Live_Coral_Cover_Pct`), yielding `DHW_degC_weeks = 48.90%`, `Structural_Rugosity = 21.25%`, `Live_Coral_Cover_Pct = 7.72%`, `SST_degC = 7.03%`, and `Depth_m = 6.79%`.
3. **10-Feature Clean Regime (`Regime_1_Clean_Emulation_10`):** Retains only physical/chemical oceanographic forcing variables, restoring `DHW_degC_weeks` (**53.71%**), `PAR_umol_m2_s` (**11.35%**), `SST_Anomaly_degC` (**9.28%**), and `Aragonite_Saturation_Omega` (**8.81%**) as the primary drivers.

---

## 4. Two-Dimensional Partial Dependence & Carbonate Regime Thresholds (`results/inflection_points.json`)

Evaluating the continuous partial dependence surface across a 401-point `DHW_degC_weeks` grid ($[0.0, 20.0]^\circ\text{C-weeks}$, step $0.05^\circ\text{C-weeks}$) reveals two distinct mechanisms:

1. **Analytical Generator Ground Truth (`03_Data/build_final_dataset.py`):**
   - Under **Ambient Carbonate Conditions ($\Omega_{\text{arag}} = 3.85$)**:
     - Half-maximal loss threshold ($\text{EC}_{50}$) $= \mathbf{9.85^\circ\text{C-weeks}}$ (predicted loss $= 42.15\%$).
     - Max-slope inflection point ($\arg\max \partial\widehat{Y}/\partial\text{DHW}$) $= \mathbf{10.15^\circ\text{C-weeks}}$.
     - $35\%$ cover loss crossing $= \mathbf{9.20^\circ\text{C-weeks}}$.
   - Under **Acidified Conditions ($\Omega_{\text{arag}} = 2.20, pH = 7.80$)**:
     - Half-maximal loss threshold ($\text{EC}_{50}$) $= \mathbf{8.30^\circ\text{C-weeks}}$ (shift of **$-1.55^\circ\text{C-weeks}$**).
     - Max-slope inflection point $= \mathbf{8.60^\circ\text{C-weeks}}$ (shift of **$-1.55^\circ\text{C-weeks}$**).
     - $35\%$ cover loss crossing $= \mathbf{7.20^\circ\text{C-weeks}}$ (shift of **$-2.00^\circ\text{C-weeks}$**).
2. **Trained XGBoost Emulator Counterfactual PDP (`Regime_1_Clean_Emulation_10`):**
   - Because within the 2015–2024 historical dataset `DHW_degC_weeks` and `Aragonite_Saturation_Omega` vary additively in the stress index before the logistic transformation, the tree emulator learns an additive vertical shift ($+5.04\%$ baseline loss at $\text{DHW}=0$, shifting the $35\%$ loss threshold from $10.60$ to $10.35^\circ\text{C-weeks}$ in counterfactual space, and from $10.70$ to $7.50^\circ\text{C-weeks}$ across empirical low-pH subsets).
   - Notably, in `build_final_dataset.py` (lines 171–180), `pH_total` has **zero direct weight** once `Aragonite_Saturation_Omega` is fixed (`weight = 0.24` on $\Omega_{\text{arag}}$), explaining why `Aragonite_Saturation_Omega` (`8.81%`) carries $3.7\times$ the clean TreeSHAP attribution of `pH_total` (`2.37%`).
