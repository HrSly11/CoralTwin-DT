# Cover Letter for Submission to Ecological Informatics

**To:** Prof. Dr. Friedrich Recknagel, Editor-in-Chief, *Ecological Informatics*  
**From:** CoralTwin-DT Doctoral Research Consortium  
**Date:** August 27, 2026  
**Subject:** Submission of Original Research Article: *"CoralTwin-DT: A Cyber-Physical Digital Twin Coupling Machine Learning and Dynamical Biophysics for Coral Reef Restoration Prioritization under Thermal Stress and Ocean Acidification"*

Dear Prof. Dr. Recknagel,

On behalf of the CoralTwin-DT International Research Consortium, we are pleased to submit our original research manuscript entitled **"CoralTwin-DT: A Cyber-Physical Digital Twin Coupling Machine Learning and Dynamical Biophysics for Coral Reef Restoration Prioritization under Thermal Stress and Ocean Acidification"** for consideration for publication as a Full Research Article in *Ecological Informatics*.

### Context and Novelty:
Scleractinian coral reefs face compounding existential crises from marine heatwaves (MHWs) and ocean acidification. Contemporary conservation frameworks rely heavily on static spatial planning and retrospective ecological surveys, which fail to capture non-linear multi-stressor tipping points or dynamically guide active restoration interventions.

In this study, we develop and validate **CoralTwin-DT**, the first open-source cyber-physical digital twin engineered specifically for coral reef conservation. Operating across a Six-Layer Architecture, the system harmonizes daily NOAA Coral Reef Watch (CRW) 5km satellite thermal feeds, Copernicus Sentinel-2 multispectral turbidity unmixing, and in-situ biogeochemical moorings onto standardized 500m benthic grids ($N = 15,000$ spatio-temporal observations across 30 global benchmark stations).

### Primary Methodological & Ecological Breakthroughs:
1. **Multi-Task Predictive Power:** Under 5-Fold Spatially Stratified Cross-Validation (25 km buffer), regularized XGBoost achieved $98.85\%$ classification accuracy ($\text{Macro-F1} = 0.7298$) and regression $R^2 = 0.9995$ with sub-millisecond latency ($0.009\text{ ms/sample}$).
2. **Synergistic Tipping Point Discovery:** TreeSHAP explainability demonstrates that ocean acidification ($pH \le 7.85$) reduces the critical thermal mortality tipping point from $8.5$ to $5.8^\circ\text{C-weeks}$ due to metabolic exhaustion of the sub-calicoblastic $\text{Ca}^{2+}/\text{H}^+\text{-ATPase}$ proton pump.
3. **Decadal Intervention Symmetries (2025–2050):** Non-linear dynamical simulations ($N = 5,000$ Monte Carlo runs) demonstrate that while unmitigated warming (SSP5-8.5) collapses live coral cover to $4.8\%$, combining thermally hardened micro-fragment outplanting ($+2.0^\circ\text{C}$ tolerance) with no-take Marine Protected Area herbivory enforcement ($g = 0.68$) sustains $46.2\%$ live coral cover and positive framework accretion ($+6.80\text{ kg CaCO}_3\text{ m}^{-2}\text{ yr}^{-1}$).
4. **Spatial Optimization & Open Science:** We operationalize these findings via the Spatial Restoration Priority Index (SRPI), delivering open GeoJSON zoning layers and a 100% reproducible computational workflow.

This manuscript represents original work that has not been published and is not under review elsewhere. All authors have approved the submission.

### Suggested Expert Reviewers:
1. **Prof. Terry P. Hughes** (James Cook University, Australia) — *Email:* terry.hughes@jcu.edu.au — Expert in mass coral bleaching and Anthropocene reef dynamics.
2. **Prof. Kenneth R. N. Anthony** (Australian Institute of Marine Science, Australia) — *Email:* k.anthony@aims.gov.au — Expert in ocean acidification, bioenergetics, and intervention modeling.
3. **Prof. Adil Rasheed** (Norwegian University of Science and Technology, Norway) — *Email:* adil.rasheed@ntnu.no — Expert in digital twins, cyber-physical systems, and environmental physics-AI integration.

Thank you very much for your time and consideration of our manuscript.

Sincerely,

**The CoralTwin-DT Doctoral Research Consortium**  
Computational Oceanography & Ecological Informatics Laboratory  
Open Repository: https://github.com/HrSly11/CoralTwin-DT.git
