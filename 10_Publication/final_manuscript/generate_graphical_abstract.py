"""
CoralTwin-DT: Graphical Abstract Generator (300 DPI)
====================================================
Renders the formal Graphical Abstract for Ecological Informatics / ERL.

Author: CoralTwin-DT Publication Team
License: MIT
Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PNG = os.path.join(BASE_DIR, "graphical_abstract.png")


def render_graphical_abstract():
    print(f"Rendering Graphical Abstract: {OUT_PNG} (300 DPI)...")
    # Standard Graphical Abstract Aspect Ratio: 16:9 (14 x 7.875 inches)
    fig, ax = plt.subplots(figsize=(14, 7.875), facecolor="#f8fafc")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Header
    ax.text(50, 95, "CoralTwin-DT: Cyber-Physical Digital Twin for Coral Reef Restoration",
            ha="center", va="center", fontsize=15, fontweight="bold", color="#1a365d")
    ax.text(50, 91.5, "Coupled Machine Learning, Biophysical ODEs & Multi-Criteria Spatial Prioritization",
            ha="center", va="center", fontsize=10.5, fontstyle="italic", color="#4a5568")

    # Panel 1: Input Data Feeds (Left)
    b1 = patches.FancyBboxPatch((2, 10), 28, 76, boxstyle="round,pad=0.6",
                                facecolor="#ebf8ff", edgecolor="#3182ce", lw=1.8)
    ax.add_patch(b1)
    tag1 = patches.FancyBboxPatch((2, 78), 28, 8, boxstyle="round,pad=0.3",
                                  facecolor="#3182ce", edgecolor="#2b6cb0", lw=1.0)
    ax.add_patch(tag1)
    ax.text(16, 82, "1. MULTI-SOURCE FEEDS", ha="center", va="center", fontsize=11, fontweight="bold", color="white")

    p1_txt = (
        "• NOAA Coral Reef Watch (5km):\n"
        "  - Daily SST, SSTA, HotSpots\n"
        "  - 84-day Degree Heating Weeks (DHW)\n\n"
        "• Copernicus Sentinel-2 (10m):\n"
        "  - Multi-spectral Rrs(490), Rrs(560)\n"
        "  - Turbidity NTU & Kd(490) unmixing\n\n"
        "• Biogeochemical Moorings:\n"
        "  - Seawater pH & practical salinity\n"
        "  - Aragonite saturation (Omega_arag)\n\n"
        "• Allen Coral Atlas:\n"
        "  - Benthic habitat ground-truths"
    )
    ax.text(3.5, 45, p1_txt, fontsize=8.8, color="#2d3748", linespacing=1.35)

    # Panel 2: Cybernetic Digital Twin Core (Center)
    b2 = patches.FancyBboxPatch((35, 10), 30, 76, boxstyle="round,pad=0.6",
                                facecolor="#feebc8", edgecolor="#dd6b20", lw=1.8)
    ax.add_patch(b2)
    tag2 = patches.FancyBboxPatch((35, 78), 30, 8, boxstyle="round,pad=0.3",
                                  facecolor="#dd6b20", edgecolor="#c05621", lw=1.0)
    ax.add_patch(tag2)
    ax.text(50, 82, "2. DIGITAL TWIN CORE", ha="center", va="center", fontsize=11, fontweight="bold", color="white")

    p2_txt = (
        "• State Vector S(t):\n"
        "  - Live Coral C(t), Macroalgae M(t)\n"
        "  - Rugosity R(t), Diversity H'\n\n"
        "• XGBoost Predictive Engine:\n"
        "  - Bleaching Risk: Low / Med / High\n"
        "  - Accuracy = 98.85%, R² = 0.9995\n"
        "  - Inference Latency = 0.009 ms\n\n"
        "• TreeSHAP Tipping Discovery:\n"
        "  - Acidification drops threshold\n"
        "    from 8.5 to 5.8 °C-weeks\n\n"
        "• Decadal ODE Sandbox (2050):\n"
        "  - Mumby differential dynamical model\n"
        "  - N = 5,000 Monte Carlo uncertainty"
    )
    ax.text(36.5, 44, p2_txt, fontsize=8.8, color="#2d3748", linespacing=1.35)

    # Panel 3: Spatial Decision & Actuation (Right)
    b3 = patches.FancyBboxPatch((70, 10), 28, 76, boxstyle="round,pad=0.6",
                                facecolor="#e6fffa", edgecolor="#319795", lw=1.8)
    ax.add_patch(b3)
    tag3 = patches.FancyBboxPatch((70, 78), 28, 8, boxstyle="round,pad=0.3",
                                  facecolor="#319795", edgecolor="#285e61", lw=1.0)
    ax.add_patch(tag3)
    ax.text(84, 82, "3. DECISION ACTUATION", ha="center", va="center", fontsize=11, fontweight="bold", color="white")

    p3_txt = (
        "• Spatial Restoration Priority (SRPI):\n"
        "  - Top 25% Hydrodynamic Refugia\n"
        "  - GeoJSON spatial zoning layers\n\n"
        "• Active Micro-Outplanting:\n"
        "  - Heat-hardened strains (+2.0°C)\n"
        "  - Substrate larval propagation\n\n"
        "• MPA Herbivory Enforcement:\n"
        "  - Parrotfish grazing capacity (g=0.68)\n"
        "  - Algal overgrowth suppression\n\n"
        "• Decadal Outcome (2050):\n"
        "  - 46.2% Live Coral Cover\n"
        "  - Positive Calcification (+6.8 kg/m²/yr)"
    )
    ax.text(71.5, 45, p3_txt, fontsize=8.8, color="#2d3748", linespacing=1.35)

    # Connecting Flow Arrows
    ax.annotate("", xy=(35, 50), xytext=(30, 50),
                arrowprops=dict(arrowstyle="->", color="#3182ce", lw=2.5, mutation_scale=18))
    ax.annotate("", xy=(70, 50), xytext=(65, 50),
                arrowprops=dict(arrowstyle="->", color="#dd6b20", lw=2.5, mutation_scale=18))

    # Closed-Loop Feedback Arrow along bottom
    ax.annotate("", xy=(16, 8), xytext=(84, 8),
                arrowprops=dict(arrowstyle="->", color="#2f855a", lw=2.2,
                                connectionstyle="arc3,rad=0.08", mutation_scale=18))
    ax.text(50, 4.5, "Closed-Loop Feedback: Evidence-Based Intervention in Physical Marine Parks",
            ha="center", va="center", fontsize=9.2, fontweight="bold", color="#22543d")

    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
    plt.close()
    print("Graphical abstract PNG rendered at 300 DPI.")


if __name__ == "__main__":
    render_graphical_abstract()
