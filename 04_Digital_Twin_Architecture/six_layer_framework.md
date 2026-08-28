# The Six-Layer Cyber-Physical Framework: CoralTwin-DT

## Detailed Specification of Architectural Layers

### CAPA 1: ADQUISICIÓN DE DATOS (Data Acquisition Layer)
- **Satellite Multi-Spectral Feeds:**
  - *Copernicus Sentinel-2 MSI (Level-2A):* Bands B2 (Blue, 490 nm), B3 (Green, 560 nm), B4 (Red, 665 nm), and B8 (NIR, 842 nm) at 10m spatial resolution. Used to derive water clarity, benthic albedo, and shallow turbidity indices ($K_d$).
  - *NOAA Coral Reef Watch (CRW) Operational 5km Daily v3.1:* Sea Surface Temperature ($SST$), SST Anomaly ($SSTA$), Coral Bleaching HotSpots, Degree Heating Weeks ($DHW$), and Bleaching Alert Areas ($BAA$).
- **Benthic Ecological & Geomorphic Databases:**
  - *Allen Coral Atlas:* Global benthic habitat classification (Coral/Algae, Sand, Rubble, Seagrass, Microalgal Mats) and geomorphic zones (Fore Reef, Reef Crest, Back Reef, Lagoon).
  - *Global Coral Reef Monitoring Network (GCRMN):* Long-term in-situ transect data of live coral cover ($LCC\%$), macroalgae cover ($MAC\%$), and structural rugosity ($R$).
- **In-Situ Physical & Oceanographic Sensors:**
  - High-frequency moorings measuring seawater $pH_{\text{total}}$, dissolved oxygen ($DO$), photosynthetically active radiation ($PAR$), and flow velocity ($U$).

---

### CAPA 2: INTEGRACIÓN DE DATOS (Data Integration & Harmonization Layer)
- **ETL & Spatial Normalization Pipeline:**
  - Bilinear interpolation and nearest-neighbor resampling to a unified spatial grid ($500\text{m} \times 500\text{m}$).
  - Temporal aggregation to daily and weekly rolling climatological time steps.
- **Data Quality & Imputation:**
  - Outlier detection via robust median absolute deviation ($MAD$).
  - Cloud-masking algorithms for Sentinel-2 optical imagery with spatiotemporal Kriging imputation for cloud gaps.
- **FAIR Compliance & Metadata Governance:**
  - Schema mapping to ISO 19115 / Dublin Core.
  - Comprehensive open data dictionary (`data_dictionary.csv`) with machine-readable URI definitions.

---

### CAPA 3: MODELADO HÍBRIDO (Hybrid Biophysical-AI Modeling Layer)
- **Coupled Mechanistic Biophysical Engine:**
  - Carbonate equilibrium solver calculating aragonite saturation $\Omega_{\text{arag}}$ from $pH$, $SST$, and salinity.
  - Dynamical population equations (Mumby-Hastings-Edwards ODEs) modeling competitive space preemption between corals ($C$), turf algae ($T$), and macroalgae ($M$).
- **Supervised Machine Learning Suite:**
  - *Ensemble Classifiers:* Random Forest (100–500 estimators) and XGBoost (Gradient Boosted Trees with regularization).
  - *Deep Architectures:* Multi-Layer Perceptron (MLP) with Batch Normalization and Dropout for non-linear state mapping.
  - *Explainability:* TreeSHAP calculation for exact marginal feature contributions and cross-stressor interaction terms.

---

### CAPA 4: SIMULACIÓN DE ESCENARIOS (Forward Scenario Simulation Layer)
- **Scenario 1 (Severe Thermal Stress - SSP5-8.5):** Unmitigated emissions ($+4.4^\circ\text{C}$ by 2100), MHW recurrence every $1.2\text{ years}$, mean $DHW \ge 12^\circ\text{C-weeks}$, $pH \to 7.75$.
- **Scenario 2 (Moderate Mitigation - SSP2-4.5):** Paris Agreement mid-road pathway ($+2.7^\circ\text{C}$ by 2100), decadal MHW recurrence, stabilization at $pH \approx 7.95$.
- **Scenario 3 (Active Coral Restoration):** Micro-fragment outplanting of thermally hardened *Acropora* / *Porites* strains ($\Phi_{\text{restoration}} = 2.5\% \text{ cover yr}^{-1}$, $+1.5^\circ\text{C}$ thermal tolerance).
- **Scenario 4 (Marine Protected Area & Integrated Conservation):** Full no-take MPA enforcement boosting herbivorous fish biomass ($g \to 0.65\text{ yr}^{-1}$) combined with terrestrial runoff control, reducing baseline macroalgae colonization.

---

### CAPA 5: VALIDACIÓN Y ANÁLISIS DE INCERTIDUMBRE (Validation & Uncertainty Layer)
- **Spatial Block Cross-Validation:** 5-fold cross-validation partitioned into spatially isolated geographical reef clusters to eliminate spatial autocorrelation bias.
- **Backtesting Evaluation (2015–2024):** Validation against historical mass bleaching events (2016 Great Barrier Reef, 2023 Caribbean Heatwave).
- **Monte Carlo Uncertainty Propagation:** $N = 10,000$ stochastic iterations drawing parameter distributions for grazing rate ($g$), calcification sensitivity ($\eta$), and mortality coefficients ($\alpha, \beta$).

---

### CAPA 6: VISUALIZACIÓN Y SOPORTE A DECISIONES (Visualization & Decision Layer)
- **Spatial Restoration Priority Index (SRPI):**
  $$\text{SRPI} = w_1 (1 - V_{\text{thermal}}) + w_2 (1 - C_{\text{current}}) + w_3 R_{\text{structural}} + w_4 H_{\text{connectivity}}$$
  Where $V_{\text{thermal}}$ is thermal vulnerability, $C_{\text{current}}$ is current coral cover, $R_{\text{structural}}$ is rugosity, and $H_{\text{connectivity}}$ is larval dispersal retention.
- **Interactive Environmental Dashboard:** Real-time risk dials, temporal trajectory projections, and GIS cartographic maps.
