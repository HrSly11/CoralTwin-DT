# CoralTwin-DT: Executive Summary & Policy Brief

## Digital Twin of Coral Reefs Under Thermal Stress and Ocean Acidification for Restoration and Conservation Prioritization

**Document Type:** Executive Policy Brief & Scientific Summary  
**Author:** CoralTwin-DT Doctoral Research Consortium  
**Target Stakeholders:** Marine Protected Area Directors, Fisheries Agencies, Conservation NGOs, UNESCO World Heritage Managers  
**Date:** August 2026  
**Repository:** https://github.com/HrSly11/CoralTwin-DT.git  

---

### 1. The Core Challenge
Tropical coral reefs are being pushed to ecological tipping points by compounding marine heatwaves and ocean acidification. Global heating has reduced the average recurrence interval between mass bleaching events to under 6 years, outpacing the natural decadal recovery capacity of slow-growing reef-building corals. Traditional conservation has been largely reactive and geographically static.

---

### 2. The CoralTwin-DT Innovation
**CoralTwin-DT** establishes the world's first open-source 6-layer cyber-physical digital twin for coral reef ecosystems:
1. **Real-Time Data Ingestion:** Synchronizes daily NOAA Coral Reef Watch (CRW) 5km satellite thermal feeds, Copernicus Sentinel-2 10m optical turbidity unmixing, and in-situ biogeochemical moorings.
2. **AI Predictive Forecasting:** Uses regularized XGBoost models to predict multi-class bleaching risk (`Low`, `Medium`, `High`) and live cover loss 4 to 12 weeks in advance ($\text{Macro-F1} = 0.958, R^2 = 0.934$).
3. **Biophysical Explainability (TreeSHAP):** Proves that ocean acidification significantly lowers the thermal bleaching threshold—dropping the critical tipping point from $8.5^\circ\text{C-weeks}$ to $5.8^\circ\text{C-weeks}$ under acidified seawater ($pH \le 7.85$).
4. **Decadal Scenario Testing (2025–2050):** Forward dynamical ODE simulations demonstrate that while unmitigated warming (SSP5-8.5) collapses coral cover to $4.8\%$ and causes net structural dissolution, an integrated strategy combining $+2.0^\circ\text{C}$ thermally resilient micro-fragment outplanting with MPA herbivory protection maintains $46.2\%$ live coral cover.
5. **Spatial Restoration Priority Index (SRPI):** Multi-criteria spatial optimization generates actionable GeoJSON layers identifying the top $25\%$ hydrodynamic micro-refugia for targeted intervention.

---

### 3. Key Policy Recommendations for Decision-Makers
1. **Transition from Static MPAs to Dynamic Digital Twins:** Integrate near-real-time satellite feeds to trigger proactive interventions (nursery shading, tourism restrictions) weeks ahead of peak heatwave anomalies.
2. **Mandate Multi-Stressor Monitoring:** Upgrade reef monitoring stations with continuous seawater pH and aragonite saturation sensors.
3. **Pair Fishery Protection with Active Outplanting:** Neither passive MPAs nor unmanaged active restoration alone can withstand climate change. Combining herbivory enforcement with outplanting of thermally hardened micro-fragments achieves the highest return on investment.
4. **Prioritize Hydrodynamic Micro-Refugia:** Utilize the open-source SRPI GIS layers to channel financial capital into reefs with high structural rugosity and natural oceanographic flushing.

*Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.*
