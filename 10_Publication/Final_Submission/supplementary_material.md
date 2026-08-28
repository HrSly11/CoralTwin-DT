# Supplementary Material: CoralTwin-DT

**Document Title:** Supplementary Methods, Tables, and Numerical Formulations for CoralTwin-DT  
**Target Journal:** *Ecological Informatics* (Elsevier, Q1)  
**Manuscript Title:** CoralTwin-DT: A Cyber-Physical Digital Twin Coupling Machine Learning and Dynamical Biophysics for Coral Reef Restoration Prioritization under Thermal Stress and Ocean Acidification  
**Authors:** CoralTwin-DT Doctoral Research Consortium  
**Repository:** https://github.com/HrSly11/CoralTwin-DT.git  
**Scientific Attribution:** *Resultado obtenido mediante prototipo computacional del gemelo digital.*

---

## Supplementary Methods

### Supplementary Method S1: Carbonate Chemistry & Aragonite Saturation ($\Omega_{\text{arag}}$)
The stoichiometric aragonite saturation state ($\Omega_{\text{arag}}$) is calculated using Dickson & Millero (1987) carbonate equilibrium equations:

$$\Omega_{\text{arag}} = \frac{[\text{Ca}^{2+}]_{\text{sw}} \cdot [\text{CO}_3^{2-}]_{\text{sw}}}{K'_{\text{sp}}(\text{arag})}$$

where $[\text{Ca}^{2+}]_{\text{sw}} = 0.01028 \cdot \frac{S}{35.0}\text{ mol/kg}$, and $K'_{\text{sp}}(\text{arag})$ is computed as a function of temperature ($T$ in Kelvin), practical salinity ($S$), and hydrostatic pressure ($P$ in dbar):

$$\ln K'_{\text{sp}}(\text{arag}) = -171.945 - 0.077993 \cdot T + \frac{2903.293}{T} + 71.595 \cdot \log_{10} T + \left(-0.068393 + \frac{0.0017276}{T} + 88.46 \cdot \frac{S^{0.5}}{T}\right) \cdot S^{0.5}$$

---

### Supplementary Method S2: Optical Water Column Diffuse Attenuation ($K_d(490)$)
Surface downwelling irradiance attenuation at 490 nm is derived from Sentinel-2 MSI Bottom-Of-Atmosphere reflectance ($R_{rs}$):

$$K_d(490) = 0.0166 + 0.052 \cdot \left(\frac{R_{rs}(490)}{R_{rs}(560)}\right)^{-1.24} + 0.008 \cdot \text{Turbidity}_{\text{NTU}}$$

Daily downwelling photosynthetically active radiation ($PAR$) reaching the benthic substrate at depth $z$ (meters) is modeled via the Lambert-Beer formulation:

$$PAR(z, t) = PAR_0(t) \cdot (1 - \rho_{\text{surface}}) \cdot \exp\left(-K_d(490) \cdot z\right)$$

---

### Supplementary Method S3: Coupled Dynamical ODE Formulation & Parameter Definitions
The non-linear space-preemption dynamics between live coral cover ($C$), fleshy macroalgae ($M$), and algal turf substrate ($T = 1 - C - M$) follow:

$$\frac{dC}{dt} = r \cdot C \cdot (1 - C - M) - d(DHW, \Omega_{\text{arag}}) \cdot C + \Phi_{\text{restoration}}$$

$$\frac{dM}{dt} = a \cdot M \cdot (1 - C - M) - \frac{g(H_{\text{MPA}}) \cdot M}{M + (1 - C - M)} + \gamma \cdot M \cdot C$$

where:
- $r = 0.45\text{ yr}^{-1}$: Coral intrinsic lateral growth rate.
- $a = 0.65\text{ yr}^{-1}$: Macroalgae colonization rate onto bare turf substrate.
- $\gamma = 0.22\text{ yr}^{-1}$: Direct overgrowth rate of coral by macroalgae.
- $g(H_{\text{MPA}}) \in [0.15, 0.70]\text{ yr}^{-1}$: Herbivorous grazing capacity mediated by MPA enforcement ($g = 0.25$ unprotected; $g = 0.68$ enforced).
- $\Phi_{\text{restoration}} = 0.028\text{ yr}^{-1}$: Active micro-fragment outplanting rate in Tier-1 zones.
- $d(DHW, \Omega_{\text{arag}}) = d_0 + \alpha \frac{DHW(t)^2}{1 + \beta \Omega_{\text{arag}}(t)}$: Compound thermal-acidification mortality function ($d_0 = 0.035, \alpha = 0.0028, \beta = 0.45$).

---

## Supplementary Tables

### Supplementary Table S1: Global Benchmark Reef Monitoring Stations Metadata

| Station ID | Station Name | Province | Latitude | Longitude | Reef Zone | Depth (m) | Climatological MMM (°C) | Dominant Genus |
| :---: | :--- | :--- | :---: | :---: | :--- | :---: | :---: | :--- |
| **ST-01** | `Mesoamerican_Fore_01` | Caribbean | 18.250 | -87.800 | Fore Reef | 12.5 | 29.20 | *Acropora* |
| **ST-02** | `Mesoamerican_Crest_02`| Caribbean | 18.280 | -87.820 | Reef Crest | 4.2 | 29.20 | *Porites* |
| **ST-03** | `Mesoamerican_Back_03` | Caribbean | 18.310 | -87.850 | Back Reef | 6.8 | 29.20 | *Orbicella* |
| **ST-04** | `Mesoamerican_Lagoon_04`| Caribbean | 18.350 | -87.880 | Lagoon | 2.5 | 29.20 | *Porites* |
| **ST-05** | `Belize_Barrier_05` | Caribbean | 17.150 | -87.900 | Fore Reef | 15.0 | 29.15 | *Orbicella* |
| **ST-06** | `Belize_Atoll_06` | Caribbean | 17.200 | -87.550 | Reef Crest | 5.0 | 29.15 | *Acropora* |
| **ST-07** | `Cozumel_South_07` | Caribbean | 20.300 | -87.020 | Fore Reef | 18.2 | 29.30 | *Montastraea* |
| **ST-08** | `Cozumel_Shallow_08` | Caribbean | 20.350 | -86.980 | Lagoon | 3.1 | 29.30 | *Porites* |
| **ST-09** | `Roatan_North_09` | Caribbean | 16.380 | -86.500 | Fore Reef | 14.0 | 29.25 | *Acropora* |
| **ST-10** | `Roatan_South_10` | Caribbean | 16.320 | -86.550 | Back Reef | 8.0 | 29.25 | *Agaricia* |
| **ST-11** | `Florida_Keys_Uppers_11`| Caribbean | 25.020 | -80.400 | Fore Reef | 9.5 | 29.80 | *Acropora* |
| **ST-12** | `Florida_Keys_Lowers_12`| Caribbean | 24.550 | -81.450 | Reef Crest | 4.5 | 29.80 | *Orbicella* |
| **ST-13** | `GreatBarrier_Northern_13`| Indo-Pacific | -14.500 | 145.450 | Fore Reef | 11.0 | 29.80 | *Acropora* |
| **ST-14** | `GreatBarrier_Central_14`| Indo-Pacific | -18.250 | 147.200 | Fore Reef | 13.5 | 29.60 | *Pocillopora* |
| **ST-15** | `GreatBarrier_Lagoon_15`| Indo-Pacific | -18.300 | 147.150 | Lagoon | 3.8 | 29.60 | *Porites* |
| **ST-16** | `CoralTriangle_RajaAmpat_16`| Indo-Pacific | -0.550 | 130.500 | Fore Reef | 10.5 | 29.80 | *Acropora* |
| **ST-17** | `CoralTriangle_Misool_17`| Indo-Pacific | -1.950 | 130.150 | Reef Crest | 5.2 | 29.80 | *Pocillopora* |
| **ST-18** | `CoralTriangle_Komodo_18`| Indo-Pacific | -8.600 | 119.550 | Fore Reef | 16.0 | 29.50 | *Porites* |
| **ST-19** | `CoralTriangle_Sulawesi_19`| Indo-Pacific | 1.650 | 124.750 | Fore Reef | 12.0 | 29.70 | *Acropora* |
| **ST-20** | `CoralTriangle_Bali_20` | Indo-Pacific | -8.120 | 115.650 | Reef Crest | 6.5 | 29.40 | *Pocillopora* |
| **ST-21** | `Okinawa_Kerama_21` | Indo-Pacific | 26.200 | 127.350 | Fore Reef | 14.5 | 28.90 | *Acropora* |
| **ST-22** | `Okinawa_Ishigaki_22` | Indo-Pacific | 24.350 | 124.150 | Lagoon | 3.2 | 29.10 | *Porites* |
| **ST-23** | `RedSea_Aqaba_23` | Red Sea | 29.450 | 34.950 | Fore Reef | 15.5 | 28.50 | *Stylophora* |
| **ST-24** | `RedSea_Shallow_24` | Red Sea | 27.200 | 33.850 | Reef Crest | 4.0 | 28.50 | *Porites* |
| **ST-25** | `RedSea_Farasan_25` | Red Sea | 16.700 | 41.950 | Fore Reef | 12.0 | 30.20 | *Acropora* |
| **ST-26** | `Seychelles_Mahe_26` | Indian Ocean | -4.680 | 55.450 | Fore Reef | 10.8 | 29.50 | *Pocillopora* |
| **ST-27** | `Maldives_AriAtoll_27` | Indian Ocean | 3.850 | 72.850 | Reef Crest | 5.5 | 29.60 | *Acropora* |
| **ST-28** | `Hawaii_Kaneohe_28` | Pacific | 21.450 | -157.800 | Lagoon | 3.5 | 27.50 | *Porites* |
| **ST-29** | `Hawaii_OahuFore_29` | Pacific | 21.300 | -157.700 | Fore Reef | 11.2 | 27.50 | *Montipora* |
| **ST-30** | `Palau_RockIslands_30` | Pacific | 7.300 | 134.450 | Lagoon | 4.8 | 29.80 | *Porites* |

---

### Supplementary Table S2: Complete Machine Learning Hyperparameter Grid

```
+-----------------------------------------------------------------------------------------------+
|                             AI MODEL HYPERPARAMETER SPECIFICATIONS                            |
+---------------------+-------------------------+-----------------------------------------------+
| Model Architecture  | Hyperparameter Name     | Optimal Tuned Value                           |
+---------------------+-------------------------+-----------------------------------------------+
| XGBoost             | n_estimators            | 200 trees                                     |
|                     | max_depth               | 6 levels                                      |
|                     | learning_rate (eta)     | 0.06                                          |
|                     | subsample ratio         | 0.80                                          |
|                     | colsample_bytree        | 0.80                                          |
|                     | gamma (min split loss)  | 0.10                                          |
|                     | reg_lambda (L2 penalty) | 1.50                                          |
|                     | eval_metric             | mlogloss (Classification) / rmse (Regression) |
+---------------------+-------------------------+-----------------------------------------------+
| Random Forest       | n_estimators            | 200 trees                                     |
|                     | max_depth               | 12 levels                                     |
|                     | min_samples_split       | 5 samples                                     |
|                     | min_samples_leaf        | 2 samples                                     |
|                     | criterion               | gini (Classification) / squared_error (Reg.)  |
+---------------------+-------------------------+-----------------------------------------------+
| Stacked LSTM        | Sequence window (L)     | 6 time steps (rolling lookback)               |
|                     | Layer 1 Units           | 64 (Return Sequences = True)                  |
|                     | Layer 2 Units           | 32 (Return Sequences = False)                 |
|                     | Dropout rate            | 0.20 + Batch Normalization                    |
|                     | Optimizer               | Adam (lr = 0.003, beta_1 = 0.9, beta_2 = 0.999)|
|                     | Batch size / Epochs     | 64 samples / 25 epochs (Early Stopping pat=5) |
+---------------------+-------------------------+-----------------------------------------------+
```

---

## Supplementary Figures & Code

All source code, simulation routines, and high-resolution figures are distributed in the repository under open licenses:
- **Master Replication Pipeline:** `run_all.py`
- **Biophysical ODE Simulation Engine:** `07_Scenarios_and_Simulations/simulation_engine.py`
- **Spatial Prioritization GeoJSON:** `08_GIS_and_Remote_Sensing/geospatial_outputs/priority_restoration_zones.geojson`
- **TreeSHAP Explainability:** `06_AI_and_Modeling/explainability/SHAP_analysis/shap_explain.py`
