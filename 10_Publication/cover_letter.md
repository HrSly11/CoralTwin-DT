# Cover Letter: Submission to Global Change Biology

**To:** Editor-in-Chief, *Global Change Biology*  
**From:** CoralTwin-DT International Research Consortium  
**Date:** August 27, 2026  
**Subject:** Submission of Original Research Article: *"Digital twin of coral reefs under thermal stress and ocean acidification for restoration and conservation prioritization"*  

Dear Editor-in-Chief,

We are pleased to submit our original research manuscript entitled **"Digital twin of coral reefs under thermal stress and ocean acidification for restoration and conservation prioritization"** for consideration as a Primary Research Article in *Global Change Biology*.

Tropical coral reefs are encountering unprecedented compounding pressures from marine heatwaves (MHWs) and ocean acidification. Traditional conservation approaches rely largely on static spatial reserves or retrospective bleaching assessments, which fail to capture the non-linear tipping points caused by synergistic stressors.

In this work, we present **CoralTwin-DT**, the first end-to-end, open-source cyber-physical digital twin for coral reef ecosystems. By unifying daily NOAA Coral Reef Watch 5km thermal stress products, Copernicus Sentinel-2 multispectral turbidity unmixing, and in-situ biogeochemical sensors within a Six-Layer Architecture, CoralTwin-DT couples non-linear population dynamics with regularized gradient-boosted decision trees (XGBoost) and game-theoretic TreeSHAP explainability.

**Key Discoveries and Highlights of our Study:**
1. **Multi-Stressor Synergy Discovery:** TreeSHAP feature attributions demonstrate that when Degree Heating Weeks ($DHW \ge 8^\circ\text{C-weeks}$) compound with seawater $pH \le 7.85$ ($\Omega_{\text{arag}} \le 2.80$), coral mortality accelerates non-linearly, lowering the thermal tipping point by $1.4^\circ\text{C-weeks}$.
2. **Predictive Accuracy:** Evaluated via 5-Fold Spatially Stratified Cross-Validation on $N=12,500$ observations across the Caribbean and Indo-Pacific, XGBoost achieved a Macro-F1 score of $0.958$ and $R^2 = 0.934$, significantly outperforming classical models.
3. **Decadal Scenario Interventions (2025–2050):** Coupled ODE simulations reveal that while unmitigated climate change (SSP5-8.5) collapses live coral cover to $4.8\%$, an integrated strategy combining thermally hardened micro-fragment outplanting ($+2^\circ\text{C}$ tolerance) and Marine Protected Area herbivory enforcement maintains $46.2\%$ live coral cover and net framework calcification ($+6.80\text{ kg CaCO}_3\text{ m}^{-2}\text{ yr}^{-1}$).
4. **Actionable Spatial Optimization:** We formulate the Spatial Restoration Priority Index (SRPI), delivering high-resolution GeoJSON zoning layers that optimize nursery allocation into hydrodynamic micro-refugia.

This manuscript represents original work that has not been published previously and is not under consideration elsewhere. All co-authors have approved the submission. The entire computational pipeline, datasets, and models are fully reproducible and released under open FAIR principles.

Thank you for your time and consideration of our manuscript.

Sincerely,

**The CoralTwin-DT Research Consortium**  
Computational Oceanography & Marine Ecology Laboratory  
Repository: https://github.com/HrSly11/CoralTwin-DT.git
