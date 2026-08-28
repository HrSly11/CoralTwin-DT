"""
CoralTwin-DT: Advanced Cyber-Physical Digital Twin Architecture Diagram Generator (300 DPI)
===========================================================================================
Renders a comprehensive, publication-grade architectural schematic of the
closed-loop Cyber-Physical Digital Twin for marine conservation.

Author: CoralTwin-DT Systems Architect
License: MIT
Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIAGRAM_OUT = os.path.join(BASE_DIR, "digital_twin_final_diagram.png")


def render_digital_twin_diagram():
    print(f"Rendering Advanced Digital Twin Architecture Diagram: {DIAGRAM_OUT} (300 DPI)...")
    fig, ax = plt.subplots(figsize=(16, 12), facecolor="#f8fafc")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Master Title Banner
    header = patches.FancyBboxPatch((2, 91), 96, 7.5, boxstyle="round,pad=0.5",
                                   facecolor="#1a365d", edgecolor="#2b6cb0", lw=2.0)
    ax.add_patch(header)
    ax.text(50, 95.8, "CoralTwin-DT: Advanced Cyber-Physical Digital Twin Architecture",
            ha="center", va="center", fontsize=16, fontweight="bold", color="white")
    ax.text(50, 93.0, "Bidirectional Closed-Loop Framework: From Real-Time Telemetry Ingestion to Spatial Conservation Actuation",
            ha="center", va="center", fontsize=11, color="#bee3f8")

    # -------------------------------------------------------------------------
    # BOX 1: PHYSICAL REEF SPACE (Top Left)
    # -------------------------------------------------------------------------
    box_p = patches.FancyBboxPatch((2, 48), 28, 40, boxstyle="round,pad=0.6",
                                  facecolor="#ebf8ff", edgecolor="#3182ce", lw=1.8)
    ax.add_patch(box_p)
    tag_p = patches.FancyBboxPatch((2, 82), 28, 6, boxstyle="round,pad=0.3",
                                  facecolor="#3182ce", edgecolor="#2b6cb0", lw=1.0)
    ax.add_patch(tag_p)
    ax.text(16, 85, "1. PHYSICAL ECOSYSTEM SPACE", ha="center", va="center", fontsize=11, fontweight="bold", color="white")

    text_p = (
        "• Benthic Living Framework:\n"
        "  - Scleractinian Colonies (Acropora, Porites)\n"
        "  - Macroalgal turf & structural rugosity\n\n"
        "• Satellite Constellations:\n"
        "  - NOAA Coral Reef Watch (5km SST / DHW)\n"
        "  - Copernicus Sentinel-2 MSI (10m Kd490)\n\n"
        "• In-Situ Ocean Moorings:\n"
        "  - SeaFET pH & CTD Salinity Sensors\n"
        "  - Optical Dissolved Oxygen & PAR radiometers\n\n"
        "• Benthic Baseline Atlas:\n"
        "  - Allen Coral Atlas geomorphic zones"
    )
    ax.text(3.5, 65, text_p, fontsize=8.8, color="#2d3748", linespacing=1.35)

    # -------------------------------------------------------------------------
    # BOX 2: INGESTION & DATA HARMONIZATION (Bottom Left)
    # -------------------------------------------------------------------------
    box_i = patches.FancyBboxPatch((2, 4), 28, 40, boxstyle="round,pad=0.6",
                                  facecolor="#e6fffa", edgecolor="#319795", lw=1.8)
    ax.add_patch(box_i)
    tag_i = patches.FancyBboxPatch((2, 38), 28, 6, boxstyle="round,pad=0.3",
                                  facecolor="#319795", edgecolor="#285e61", lw=1.0)
    ax.add_patch(tag_i)
    ax.text(16, 41, "2. DATA INGESTION & ETL CORE", ha="center", va="center", fontsize=11, fontweight="bold", color="white")

    text_i = (
        "• Automated Spatial Harmonization:\n"
        "  - Standardized 500m x 500m Benthic Grids\n"
        "  - Bilinear raster interpolation (EPSG:4326)\n\n"
        "• Oceanographic Feature Calculation:\n"
        "  - Rolling 84-day Degree Heating Weeks (DHW)\n"
        "  - Stoichiometric Aragonite Saturation (Omega)\n"
        "  - Diffuse Attenuation Kd(490) from Rrs bands\n\n"
        "• Data Governance & Quality Assurance:\n"
        "  - ISO 19115 FAIR Metadata Catalog\n"
        "  - Robust MAD Outlier Detection & Kriging"
    )
    ax.text(3.5, 21, text_i, fontsize=8.8, color="#2d3748", linespacing=1.35)

    # -------------------------------------------------------------------------
    # BOX 3: CYBERNETIC DIGITAL TWIN CORE (Center / Large)
    # -------------------------------------------------------------------------
    box_dt = patches.FancyBboxPatch((33, 4), 34, 84, boxstyle="round,pad=0.8",
                                   facecolor="#f7fafc", edgecolor="#4a5568", lw=2.2)
    ax.add_patch(box_dt)
    tag_dt = patches.FancyBboxPatch((33, 82), 34, 6, boxstyle="round,pad=0.3",
                                   facecolor="#2d3748", edgecolor="#1a202c", lw=1.2)
    ax.add_patch(tag_dt)
    ax.text(50, 85, "3. CYBERNETIC DIGITAL TWIN CORE", ha="center", va="center", fontsize=12, fontweight="bold", color="white")

    # Sub-block 3.1: Current State
    sb1 = patches.FancyBboxPatch((34.5, 62), 31, 18, boxstyle="round,pad=0.4",
                                facecolor="#feebc8", edgecolor="#dd6b20", lw=1.2)
    ax.add_patch(sb1)
    ax.text(50, 77.5, "Pillar 1: Dynamic State Vector S(t)", ha="center", fontsize=10, fontweight="bold", color="#9c4221")
    ax.text(36, 69.5, "• Live Coral Cover C(t) | Macroalgae M(t)\n• Structural Rugosity R(t) | Diversity H'\n• Colony Density D(t) per 500m cell",
            fontsize=8.5, color="#2d3748", linespacing=1.3)

    # Sub-block 3.2: AI Predictive Engine
    sb2 = patches.FancyBboxPatch((34.5, 34), 31, 26, boxstyle="round,pad=0.4",
                                facecolor="#e2e8f0", edgecolor="#4a5568", lw=1.2)
    ax.add_patch(sb2)
    ax.text(50, 56.5, "Pillar 3: Multi-Task AI Engine", ha="center", fontsize=10, fontweight="bold", color="#1a202c")
    ax.text(36, 44.5, "• XGBoost Classifier (F1 = 0.958)\n  - Risk: Low / Medium / High\n• XGBoost Regressor (R² = 0.999)\n  - Coral Cover Loss Rate ΔC (%)\n• TreeSHAP Biophysical Attribution\n  - Non-linear tipping point discovery",
            fontsize=8.5, color="#2d3748", linespacing=1.3)

    # Sub-block 3.3: Decadal Scenario Sandbox
    sb3 = patches.FancyBboxPatch((34.5, 6), 31, 26, boxstyle="round,pad=0.4",
                                facecolor="#e9d8fd", edgecolor="#6b46c1", lw=1.2)
    ax.add_patch(sb3)
    ax.text(50, 28.5, "Pillar 4: Forward Scenario Sandbox (2050)", ha="center", fontsize=10, fontweight="bold", color="#553c9a")
    ax.text(36, 16.5, "• Coupled Mumby Differential Equations:\n  dC/dt = r C (1-C-M) - μ(DHW,Ω) C + Φ_resto\n  dM/dt = a M (1-C-M) - g(H_MPA) M + γ M C\n• Monte Carlo Engine (N = 5,000 runs)\n• Net Framework Calcification G_net",
            fontsize=8.5, color="#2d3748", linespacing=1.3)

    # -------------------------------------------------------------------------
    # BOX 4: DECISION SUPPORT & ACTUATION (Right)
    # -------------------------------------------------------------------------
    box_d = patches.FancyBboxPatch((70, 4), 28, 84, boxstyle="round,pad=0.6",
                                  facecolor="#fff5f5", edgecolor="#e53e3e", lw=1.8)
    ax.add_patch(box_d)
    tag_d = patches.FancyBboxPatch((70, 82), 28, 6, boxstyle="round,pad=0.3",
                                  facecolor="#e53e3e", edgecolor="#9b2c2c", lw=1.0)
    ax.add_patch(tag_d)
    ax.text(84, 85, "4. DECISION & ACTUATION SPACE", ha="center", va="center", fontsize=11, fontweight="bold", color="white")

    text_d = (
        "• Spatial Restoration Priority Index (SRPI):\n"
        "  SRPI = 0.35(Refugia) + 0.25(Urgency) +\n"
        "         0.25(Rugosity) + 0.15(WaterQuality)\n\n"
        "• Tier 1 Action Allocations (Top 25%):\n"
        "  - Immediate Micro-Fragment Outplanting\n"
        "  - Heat-hardened strains (+2.0°C tolerance)\n\n"
        "• Tier 2 Conservation Zoning:\n"
        "  - Marine Protected Area (MPA) enforcement\n"
        "  - Protection of herbivorous fish (Scaridae)\n\n"
        "• Predictive Marine Park Alerts:\n"
        "  - Automated 6-week early warning notices\n"
        "  - Deployment of nursery shading & tourism bans\n\n"
        "• Open GIS Delivery:\n"
        "  - priority_restoration_zones.geojson"
    )
    ax.text(71.5, 48, text_d, fontsize=8.8, color="#2d3748", linespacing=1.35)

    # -------------------------------------------------------------------------
    # CONNECTING ARROWS & DATA FLOWS
    # -------------------------------------------------------------------------
    # 1. Physical -> Ingestion
    ax.annotate("Raw Telemetry Feeds", xy=(16, 44), xytext=(16, 48),
                arrowprops=dict(arrowstyle="->", color="#3182ce", lw=2.2, mutation_scale=15),
                ha="center", va="center", fontsize=8.5, fontweight="bold", color="#2b6cb0")

    # 2. Ingestion -> Digital Twin
    ax.annotate("Harmonized 500m Tensors", xy=(33, 24), xytext=(30, 24),
                arrowprops=dict(arrowstyle="->", color="#319795", lw=2.2, mutation_scale=15),
                ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#285e61")

    # 3. Digital Twin -> Decision Space
    ax.annotate("SRPI & Risk Forecasts", xy=(70, 50), xytext=(67, 50),
                arrowprops=dict(arrowstyle="->", color="#e53e3e", lw=2.2, mutation_scale=15),
                ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#9b2c2c")

    # 4. Closed-Loop Feedback: Decision -> Physical Reef
    # Big sweeping feedback arrow along the top
    ax.annotate("", xy=(16, 88), xytext=(84, 88),
                arrowprops=dict(arrowstyle="->", color="#2f855a", lw=2.5,
                                connectionstyle="arc3,rad=-0.12", mutation_scale=20))
    ax.text(50, 90.0, "Closed-Loop Conservation Actuation Feedback (Targeted Outplanting & Fishery Enforcement)",
            ha="center", va="center", fontsize=9.2, fontweight="bold", color="#22543d",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#f0fff4", edgecolor="#9ae6b4"))

    plt.tight_layout()
    plt.savefig(DIAGRAM_OUT, dpi=300, bbox_inches="tight")
    plt.close()
    print("Advanced digital twin diagram rendered successfully at 300 DPI.")


if __name__ == "__main__":
    render_digital_twin_diagram()
