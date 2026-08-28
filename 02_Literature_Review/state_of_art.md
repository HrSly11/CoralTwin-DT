# State of the Art: Digital Twins in Marine Ecology & Coral Reef Conservation

## 1. Evolution of Coral Bleaching & Biogeochemical Modeling

The modeling of coral reef ecosystems under anthropogenically forced climate warming has evolved through three distinct paradigms:

```
+-------------------------------------------------------------------------------+
|  1. Empirical Climatological Indices (1998 - 2012)                           |
|     NOAA CRW Degree Heating Weeks (DHW), HotSpot thermal anomaly calculations |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|  2. Dynamical Ecological Systems & Niche Models (2012 - 2020)                |
|     Mumby et al. ODE phase shifts, species distribution models (MaxEnt)       |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|  3. Cyber-Physical Digital Twins & Physics-Informed ML (2020 - Present)      |
|     CoralTwin-DT: Coupled multi-stressor assimilation, XAI & active outplant  |
+-------------------------------------------------------------------------------+
```

---

## 2. Deep Literature Synthesis by Domain

### 2.1 Thermal Stress & Climatology (NOAA Coral Reef Watch)
- **Foundations:** Hughes et al. (2018), Liu et al. (2014), Skirving et al. (2019).
- **Core Concept:** Marine Heatwaves (MHWs) are quantified via accumulated thermal stress anomalies relative to the Maximum Monthly Mean ($MMM$).
- **State-of-the-Art:** While $DHW \ge 8^\circ\text{C-weeks}$ reliably predicts Level 2 Bleaching Alerts globally, standard products lack micro-bathymetric shading, internal wave cooling, and chemical buffering modifiers.

### 2.2 Ocean Acidification & Carbonate Kinetics
- **Foundations:** Hoegh-Guldberg et al. (2007), Anthony et al. (2011).
- **Core Concept:** Elevated seawater $p\text{CO}_2$ drives down pH and aragonite saturation ($\Omega_{\text{arag}}$), depressing calcification rates ($G_{\text{net}}$) and accelerating macroborer bioerosion.
- **State-of-the-Art:** The interaction between thermal stress and acidification exhibits strong non-linear synergy. Bleaching weakens the energetic budget needed for active proton-pumping at the sub-calicoblastic extracellular fluid (SCEF).

### 2.3 Remote Sensing & High-Resolution Benthic Mapping
- **Foundations:** Lyons et al. (2020), Allen Coral Atlas (2021).
- **Core Concept:** PlanetScope (3.7m) and Sentinel-2 (10m) multispectral imagery provide global geomorphic and benthic habitat classification (coral/algae, rubble, sand, seagrass).
- **State-of-the-Art:** Satellite-derived turbidity ($K_d(490)$) and bottom-reflectance provide high-resolution proxies for optical attenuation and benthic substrate shifts.

### 2.4 Environmental Digital Twins & Explainable AI (XAI)
- **Foundations:** Rasheed et al. (2020), Lundberg & Lee (2017).
- **Core Concept:** Digital Twins integrate continuous sensory telemetry with computational models to forecast future states and test hypothetical interventions.
- **State-of-the-Art:** CoralTwin-DT pioneers the application of TreeSHAP to quantify the exact marginal contribution of physical oceanographic variables to coral bleaching risk.
