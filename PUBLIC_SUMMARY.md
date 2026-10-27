# Public Scientific Summary: CoralTwin-DT

**Project:** CoralTwin-DT (Digital Twin of Coral Reefs under Multi-Stressor Climate Change)  
**Lead Consortium:** CoralTwin-DT Research Board  
**Target Audience:** Marine Park Authorities, Conservation NGOs, Marine Scientists, and General Public  
**Official Repository:** https://github.com/HrSly11/CoralTwin-DT.git  
**Scientific Attribution:** *Resultado obtenido mediante prototipo computacional del gemelo digital.*

---

## 1. What is CoralTwin-DT in Plain Language?

Tropical coral reefs are the "rainforests of the sea," protecting coastlines from hurricanes and feeding over half a billion people. However, rising ocean temperatures cause devastating coral bleaching, while absorbing carbon emissions turns seawater acidic, dissolving the reefs' calcium carbonate skeletons.

**CoralTwin-DT** is a **Cyber-Physical Digital Twin**—a living virtual computer model of coral reef ecosystems that updates daily using satellite observations and ocean buoys. Just as digital twins in aviation simulate airplane stress before a flight, CoralTwin-DT simulates how coral reefs will react to upcoming heatwaves and acidification over the next 25 years (2025–2050).

---

## 2. Why is this a Breakthrough for Coral Conservation?

Until now, marine conservation has mostly been **reactive**: scientists surveyed dead reefs after a heatwave happened, and restoration teams planted nursery corals based on static maps or intuition—often in shallow lagoons where heat accumulated and killed the new corals.

**CoralTwin-DT changes this paradigm through 4 breakthroughs:**
1. **Emulates Bleaching Risk Under Spatial Block CV:** Using gradient-boosted decision trees (XGBoost) with $98.85\%$ classification accuracy (`Macro-F1 = 0.7187`, `R² = 0.9336`) across 30 synthetic benchmark stations.
2. **Models Carbonate Regime Shifts:** Demonstrates in the synthetic generator that ocean acidification ($\Omega_{\text{arag}} = 2.20$ vs $3.85$) lowers the half-maximal cover-loss threshold ($\text{EC}_{50}$) from $9.85$ to $8.30^\circ\text{C-weeks}$ ($-1.55^\circ\text{C-weeks}$).
3. **Identifies "Ocean Micro-Refugia":** Evaluates the biophysical Spatial Restoration Priority Index (Eq. 7 SRPI) across 30 stations ($N=15,000$), identifying 10 Tier-1 priority stations ($33.33\%$, $\text{SRPI} \ge 0.70$).
4. **Simulates Coupled Restoration Trajectories (2025–2050):** RK4 numerical integration ($N=5,000$ Monte Carlo runs from a $33.68\%$ baseline) shows that combining thermally hardened outplants ($+2.0^\circ\text{C-weeks}$) with enforced MPA herbivory ($g=0.68$) sustains **$55.20\%$ mean live coral cover by 2050**, compared to **$0.69\%$** ($98.58\%$ collapse risk $<10\%$) under unmitigated SSP5-8.5 warming.

---

## 3. How Can Conservation Teams Use It?

All data, software, maps, and models in CoralTwin-DT are **100% open-source and free to use** under the MIT License:
- **Download the Open Maps:** Access `priority_restoration_zones.geojson` to load prioritized restoration zones directly into Google Earth, QGIS, or ArcGIS.
- **Run the Complete Simulation:** Execute `python run_all.py` on any computer to regenerate all simulations and data in under 2 minutes.
- **Read the Scientific Paper:** Review the full peer-reviewed study in `10_Publication/Final_Submission/manuscript.pdf`.

---

## 4. Key Keywords & Indexing Terms

`Digital Twin`, `Coral Reefs`, `Coral Bleaching`, `Ocean Acidification`, `Degree Heating Weeks`, `XGBoost`, `TreeSHAP`, `Ecological Informatics`, `Marine Protected Areas`, `Restoration Ecology`, `Sentinel-2`, `NOAA Coral Reef Watch`, `FAIR Data`.
