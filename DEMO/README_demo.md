# CoralTwin-DT: Interactive Scientific Prototype Demo

Welcome to the interactive demonstration of **CoralTwin-DT**, the cyber-physical digital twin engineered for coral reef restoration prioritization under thermal stress and ocean acidification.

[![Streamlit: App](https://img.shields.io/badge/Streamlit-Interactive%20Demo-FF4B4B.svg)](app.py)
[![Plotly: Enabled](https://img.shields.io/badge/Plotly-Dynamic%20Charts-3F4F75.svg)](https://plotly.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

---

## 1. How to Launch the Demo Locally (< 1 minute)

```bash
# 1. Navigate to the repository root
cd CoralTwin-DT

# 2. Activate your virtual environment
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install demo requirements (if not already installed)
pip install -r DEMO/requirements.txt

# 4. Launch the Streamlit application
streamlit run DEMO/app.py
```

The interactive application will automatically open in your default browser at `http://localhost:8501`.

---

## 2. Interactive Demonstration Features & Tabs

### 🌐 Tab 1: Real-Time Reef Telemetry & State Vector $\mathbf{S}(t)$
- **Interactive Global Map:** Visualizes 30 benchmark reef stations across 5 ocean basins ingested from NOAA CRW (5km) and Sentinel-2 (10m).
- **Live State Inspection:** Inspect individual station metrics (SST, DHW, pH, $K_d490$, Rugosity) and view dynamic benthic composition pie charts (Coral % vs Macroalgae % vs Turf %).

### 🤖 Tab 2: Live AI Bleaching Inference Sandbox (XGBoost + TreeSHAP)
- **Interactive Sliders:** Adjust SST, accumulated Degree Heating Weeks ($DHW$), seawater pH, turbidity, live coral cover, and structural rugosity in real time.
- **Instant Inference:** Triggers real-time XGBoost classification (Low / Medium / High Risk with confidence probabilities) and quantitative cover loss % regression ($R^2 = 0.9995$).
- **Explainability (TreeSHAP):** Live horizontal bar chart showing positive vs negative marginal feature attributions.

### 🔮 Tab 3: 2025–2050 Decadal Forward Scenario Sandbox
- **Non-Linear ODE Solver:** Solves the coupled Mumby competition differential equations dynamically via Runge-Kutta 4th Order (`scipy.integrate.solve_ivp`).
- **Policy Sliders:** Test different warming rates (+0.5°C to +3.5°C), active nursery outplanting rates (0 to 8%/yr), thermal hardening bonuses (+0.0°C to +2.5°C), and MPA herbivory grazing capacity ($g$).
- **Dynamic Trajectories:** Graph updates in real-time showing whether the reef sustains live cover ($46.2\%$) or collapses into a macroalgal phase shift ($4.8\%$).

### 🗺️ Tab 4: Spatial Restoration Prioritization (SRPI)
- **Interactive Decision Matrix:** Filter and rank candidate reef stations by restoration priority tier (Tier 1 Active Outplanting, Tier 2 Marine Reserve Enforcement, Tier 3 Thermal Refugia).
- **GeoJSON Export:** Direct download button for open RFC-7946 `priority_restoration_zones.geojson`.

### ℹ️ Tab 5: System Architecture & Open Science Attribution
- Comprehensive specification of the 6-layer cyber-physical architecture and FAIR open-science licenses.

---

## 3. Demonstration Visual Overview

```text
DEMO/screenshots/
├── 01_dashboard_overview.png           # Global telemetry map & benthic state pie chart
├── 02_live_ai_inference.png             # Interactive TreeSHAP feature attribution sandbox
└── 03_decadal_sandbox_simulation.png    # Forward 2025-2050 Mumby ODE trajectory comparison
```

---

## 4. Automated Troubleshooting Guide

| Issue | Root Cause | Automated Resolution |
| :--- | :--- | :--- |
| **`Streamlit command not found`** | Virtual environment not active. | Activate `venv` and run `python -m streamlit run DEMO/app.py`. |
| **`Port 8501 already in use`** | Another instance running. | Run `streamlit run DEMO/app.py --server.port 8502`. |
| **`Dataset path warning`** | Running from different working directory. | Built-in fallback dataset automatically initializes with full functionality. |

---
*Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.*
