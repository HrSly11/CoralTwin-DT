"""
CoralTwin-DT: High-Resolution Scientific Conference Poster Generator (300 DPI)
=============================================================================
Renders a publication-grade scientific conference poster (A0 format, 300 DPI)
summarizing Background, Architecture, AI Benchmarks, Scenarios, and Spatial Prioritization.

Author: CoralTwin-DT Visualization Lead
License: MIT
Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTER_OUT = os.path.join(BASE_DIR, "poster.png")


def render_poster():
    print(f"Rendering Scientific Poster: {POSTER_OUT} (300 DPI)...")
    # A0 Aspect Ratio: 36 x 48 inches (scaled for matplotlib rendering)
    fig, ax = plt.subplots(figsize=(18, 24), facecolor="#f8fafc")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Top Header Banner
    header_box = patches.FancyBboxPatch((2, 88), 96, 10.5, boxstyle="round,pad=0.5",
                                        facecolor="#1a365d", edgecolor="#2b6cb0", lw=2.0)
    ax.add_patch(header_box)

    ax.text(50, 95.5, "CoralTwin-DT: Digital Twin of Coral Reefs Under Thermal Stress and Ocean Acidification",
            ha="center", va="center", fontsize=18, fontweight="bold", color="white")
    ax.text(50, 92.5, "Coupled Biophysical-AI Framework for Multi-Stressor Bleaching Prediction, Decadal Simulation & Restoration Prioritization",
            ha="center", va="center", fontsize=12, fontweight="medium", color="#bee3f8")
    ax.text(50, 89.8, "Doctoral Research Consortium | Target: Global Change Biology / Nature Climate Change (2026)",
            ha="center", va="center", fontsize=10, fontstyle="italic", color="#cbd5e0")

    # Column 1 (Left): Background, Problem, Architecture
    # Section 1: Motivation & Knowledge Gaps
    box1 = patches.FancyBboxPatch((2, 59), 30.5, 27.5, boxstyle="round,pad=0.5",
                                  facecolor="white", edgecolor="#cbd5e0", lw=1.2)
    ax.add_patch(box1)
    ax.text(3.5, 84.5, "1. Background & Knowledge Gaps", fontsize=13, fontweight="bold", color="#1b4965")
    text_s1 = (
        "• Climate Challenge: Marine heatwaves (MHWs) are\n"
        "  accelerating globally, reducing recurrence to <6 yrs.\n\n"
        "• Compound Acidification: Decreasing seawater pH\n"
        "  and aragonite saturation (Omega_arag) depress\n"
        "  calcification and lower critical thermal thresholds.\n\n"
        "• Knowledge Gap: Existing monitoring siloes thermal\n"
        "  metrics (NOAA CRW) from chemical and optical\n"
        "  stressors, lacking forward restoration simulation.\n\n"
        "• Core Hypothesis: Coupling satellite telemetry with\n"
        "  AI and dynamical biophysics enables high-accuracy\n"
        "  bleaching forecasting and spatial prioritization."
    )
    ax.text(3.5, 71.5, text_s1, fontsize=9.2, color="#2d3748", linespacing=1.3)

    # Section 2: Six-Layer Architecture
    box2 = patches.FancyBboxPatch((2, 29), 30.5, 28.5, boxstyle="round,pad=0.5",
                                  facecolor="white", edgecolor="#cbd5e0", lw=1.2)
    ax.add_patch(box2)
    ax.text(3.5, 55.5, "2. Six-Layer Cyber-Physical Twin", fontsize=13, fontweight="bold", color="#1b4965")
    text_s2 = (
        "• L1 (Acquisition): NOAA CRW 5km SST/DHW, Sentinel-2\n"
        "  MSI 10m reflectance, Allen Coral Atlas, Moorings.\n\n"
        "• L2 (Integration): 500m grid resampling, ISO 19115\n"
        "  metadata catalog, FAIR data pipeline.\n\n"
        "• L3 (Hybrid Engine): Multi-task XGBoost / RF / MLP\n"
        "  coupled with Mumby dynamical ODEs.\n\n"
        "• L4 (Forward Simulation): 2025-2050 scenario engine\n"
        "  under SSP5-8.5 vs SSP2-4.5 & active restoration.\n\n"
        "• L5 (Validation): 5-Fold Spatially Stratified CV,\n"
        "  backtesting (2016-2024), N=5,000 Monte Carlo.\n\n"
        "• L6 (Decision Layer): Interactive dashboard and\n"
        "  Spatial Restoration Priority Index (SRPI) maps."
    )
    ax.text(3.5, 42.0, text_s2, fontsize=9.2, color="#2d3748", linespacing=1.3)

    # Section 3: Harmonized Datasets
    box3 = patches.FancyBboxPatch((2, 2), 30.5, 25.5, boxstyle="round,pad=0.5",
                                  facecolor="white", edgecolor="#cbd5e0", lw=1.2)
    ax.add_patch(box3)
    ax.text(3.5, 25.5, "3. Unified Dataset (N=15,000, 30 Stations)", fontsize=13, fontweight="bold", color="#1b4965")
    text_s3 = (
        "• 30 Benchmark Stations (Caribbean, Indo-Pacific,\n"
        "  Red Sea, Pacific, Indian Ocean; 500 records/station).\n\n"
        "• 10 Clean Environmental Predictors: SST, SSTA, DHW,\n"
        "  pH, Omega_arag, Turbidity, PAR, Salinity, DO, Depth.\n\n"
        "• 100% Synthetic Digital Twin Benchmark (SEED = 42).\n\n"
        "• Explicit Attribution: Resultado obtenido mediante\n"
        "  prototipo computacional del gemelo digital."
    )
    ax.text(3.5, 13.5, text_s3, fontsize=9.2, color="#2d3748", linespacing=1.3)

    # Column 2 (Middle): AI Predictive Modeling & TreeSHAP
    box4 = patches.FancyBboxPatch((34.5, 46), 31.0, 40.5, boxstyle="round,pad=0.5",
                                  facecolor="white", edgecolor="#cbd5e0", lw=1.2)
    ax.add_patch(box4)
    ax.text(36.0, 84.5, "4. Spatial-CV Emulation & Verification", fontsize=13, fontweight="bold", color="#1b4965")
    text_s4 = (
        "• 5-Fold Spatial Block Cross-Validation (5 Seeds):\n"
        "  Enforces >25 km inter-fold buffer (min 119.72 km)\n"
        "  and eliminates co-generated benthic target leakage.\n\n"
        "• Clean 10-Feature Benchmark (Mean across 5 Seeds):\n"
        "  - XGBoost: Acc = 98.85% | Macro-F1 = 0.7187 | R² = 0.9336\n"
        "  - Random Forest: Acc = 98.88% | Macro-F1 = 0.7284 | R² = 0.9375\n"
        "  - Deep MLP: Acc = 98.79% | Macro-F1 = 0.6807 | R² = 0.9337\n"
        "  - Stacked LSTM: Acc = 98.81% | Macro-F1 = 0.6949 | R² = 0.9371\n\n"
        "• Noise Floor Verification: All 4 models approach the\n"
        "  theoretical R² ceiling (0.9385, RMSE_min = 3.89%)."
    )
    ax.text(36.0, 65.5, text_s4, fontsize=9.2, color="#2d3748", linespacing=1.3)

    # Section 5: TreeSHAP Explainability
    box5 = patches.FancyBboxPatch((34.5, 2), 31.0, 42.5, boxstyle="round,pad=0.5",
                                  facecolor="white", edgecolor="#cbd5e0", lw=1.2)
    ax.add_patch(box5)
    ax.text(36.0, 42.5, "5. Interventional TreeSHAP Attribution", fontsize=13, fontweight="bold", color="#1b4965")
    text_s5 = (
        "• Clean 10-Feature Global TreeSHAP Ranking:\n"
        "  1. Degree Heating Weeks (DHW): 53.71% importance\n"
        "  2. Downwelling Solar PAR: 11.35% importance\n"
        "  3. SST Anomaly (SSTA): 9.28% importance\n"
        "  4. Aragonite Saturation (Omega): 8.81% importance\n"
        "  5. Sea Surface Temperature (SST): 5.19% importance\n"
        "  6. Salinity / Depth / pH / DO / Turbidity: 11.66%\n\n"
        "• Carbonate Regime Shift:\n"
        "  Under ocean acidification (Omega 2.20 vs 3.85),\n"
        "  analytical EC50 shifts from 9.85 to 8.30 °C-weeks\n"
        "  (-1.55 °C-weeks), elevating baseline loss by +5.04%."
    )
    ax.text(36.0, 22.0, text_s5, fontsize=9.2, color="#2d3748", linespacing=1.3)

    # Column 3 (Right): Decadal Simulations, Spatial Prioritization, Conclusions
    box6 = patches.FancyBboxPatch((67.5, 46), 30.5, 40.5, boxstyle="round,pad=0.5",
                                  facecolor="white", edgecolor="#cbd5e0", lw=1.2)
    ax.add_patch(box6)
    ax.text(69.0, 84.5, "6. Forward Decadal Scenarios (2025–2050)", fontsize=13, fontweight="bold", color="#1b4965")
    text_s6 = (
        "• Coupled RK4 ODE Simulations (N=5,000 MC, C0=33.68%):\n\n"
        "  - S1 (SSP5-8.5 Severe): Live cover collapses to\n"
        "    0.69% [0.1-6.2%]; net dissolution (-1.80 kg/m²/yr).\n\n"
        "  - S2 (SSP2-4.5 Moderate): Transitional state at\n"
        "    18.55% [0.5-52.7%] cover (+0.94 kg/m²/yr).\n\n"
        "  - S3 (Active Outplanting): Thermally hardened\n"
        "    strains (+2°C-wk) sustain 48.92% [23.3-67.4%] cover.\n\n"
        "  - S4 (Integrated MPA + Outplant): Synergistic\n"
        "    recovery to 55.20% [36.2-70.5%] cover and net\n"
        "    accretion (+7.46 kg CaCO3 m⁻² yr⁻¹)."
    )
    ax.text(69.0, 65.0, text_s6, fontsize=9.2, color="#2d3748", linespacing=1.3)

    box7 = patches.FancyBboxPatch((67.5, 2), 30.5, 42.5, boxstyle="round,pad=0.5",
                                  facecolor="white", edgecolor="#cbd5e0", lw=1.2)
    ax.add_patch(box7)
    ax.text(69.0, 42.5, "7. Spatial Prioritization & Conclusions", fontsize=13, fontweight="bold", color="#1b4965")
    text_s7 = (
        "• Spatial Restoration Priority Index (Eq. 7 SRPI):\n"
        "  Combines Thermal Refugia (35%), Urgency (25%),\n"
        "  Rugosity (25%), and Water Quality (15%).\n\n"
        "• Tier 1 Priority Zones (SRPI >= 0.70):\n"
        "  Identifies 10/30 stations (33.33%) and 32.48% of\n"
        "  records in high-rugosity thermal refugia.\n\n"
        "• Policy Recommendations:\n"
        "  1. Account for carbonate saturation in heatwave alerts.\n"
        "  2. Pair MPA herbivory protection (g=0.68) with seeding.\n"
        "  3. Channel resources into verified high-SRPI refugia.\n\n"
        "• Open-Source FAIR Repo: github.com/HrSly11/CoralTwin-DT"
    )
    ax.text(69.0, 22.0, text_s7, fontsize=9.2, color="#2d3748", linespacing=1.3)

    plt.tight_layout()
    plt.savefig(POSTER_OUT, dpi=300, bbox_inches="tight")
    plt.close()
    print("Scientific conference poster generated successfully at 300 DPI.")


if __name__ == "__main__":
    render_poster()
