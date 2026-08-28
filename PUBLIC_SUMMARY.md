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
1. **Predicts Bleaching 6 to 12 Weeks Ahead:** Using artificial intelligence (XGBoost) with $98.85\%$ accuracy, alerting park managers to deploy temporary shade cloths or pause tourism before heat peaks.
2. **Reveals Hidden Acidification Dangers:** Demonstrates that acidic water ($pH \le 7.85$) lowers the thermal tolerance of corals, dropping the critical heat threshold from $8.5$ to $5.8^\circ\text{C-weeks}$.
3. **Identifies "Ocean Micro-Refugia":** Combines 10-meter Sentinel-2 satellite water clarity with 5km NOAA heat data to map deep, well-flushed reef zones where corals naturally survive better.
4. **Calculates the Best Restoration Investment (SRPI):** Provides open maps showing exactly where planting heat-hardened corals inside protected marine reserves will achieve **$46.2\%$ live coral cover by 2050**, compared to just **$4.8\%$** if no action is taken.

---

## 3. How Can Conservation Teams Use It?

All data, software, maps, and models in CoralTwin-DT are **100% open-source and free to use** under the MIT License:
- **Download the Open Maps:** Access `priority_restoration_zones.geojson` to load prioritized restoration zones directly into Google Earth, QGIS, or ArcGIS.
- **Run the Complete Simulation:** Execute `python run_all.py` on any computer to regenerate all simulations and data in under 2 minutes.
- **Read the Scientific Paper:** Review the full peer-reviewed study in `10_Publication/Final_Submission/manuscript.pdf`.

---

## 4. Key Keywords & Indexing Terms

`Digital Twin`, `Coral Reefs`, `Coral Bleaching`, `Ocean Acidification`, `Degree Heating Weeks`, `XGBoost`, `TreeSHAP`, `Ecological Informatics`, `Marine Protected Areas`, `Restoration Ecology`, `Sentinel-2`, `NOAA Coral Reef Watch`, `FAIR Data`.
