"""
CoralTwin-DT: Demo Screenshot Generator
=======================================
Generates high-resolution dashboard mockups for DEMO/screenshots/.

Author: CoralTwin-DT Engineering Team
License: MIT
"""

import os
import matplotlib.pyplot as plt
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")


def generate_screenshots():
    print("Generating demonstration screenshots in DEMO/screenshots/...")

    # 1. Dashboard Overview Screenshot
    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300)
    fig1.patch.set_facecolor("#F8FAFC")

    # Global Station Distribution Mock
    lats = np.random.uniform(-20, 20, 30)
    lons = np.random.uniform(-100, 150, 30)
    colors = np.random.choice(["#38A169", "#D69E2E", "#E53E3E"], 30)
    sizes = np.random.uniform(50, 200, 30)

    ax1.scatter(lons, lats, c=colors, s=sizes, alpha=0.8, edgecolors="white", linewidth=1.5)
    ax1.set_title("CoralTwin-DT: Global Telemetry Map (30 Pilot Stations)", fontsize=12, fontweight="bold", color="#1A365D")
    ax1.set_xlabel("Longitude (°)", fontsize=10)
    ax1.set_ylabel("Latitude (°)", fontsize=10)
    ax1.set_facecolor("#EDF2F7")

    # Benthic Composition Pie
    labels = ["Live Coral (38.5%)", "Macroalgae (18.2%)", "Turf Algae (43.3%)"]
    vals = [38.5, 18.2, 43.3]
    pie_colors = ["#3182CE", "#DD6B20", "#718096"]
    ax2.pie(vals, labels=labels, colors=pie_colors, autopct="%1.1f%%", startangle=140,
            textprops={"fontsize": 10, "weight": "bold"})
    ax2.set_title("Live Benthic State Vector S(t) - Station Mesoamerican_Fore_01", fontsize=12, fontweight="bold", color="#1A365D")

    plt.tight_layout()
    p1 = os.path.join(SCREENSHOTS_DIR, "01_dashboard_overview.png")
    plt.savefig(p1, dpi=300)
    plt.close()

    # 2. Live AI Inference Screenshot
    fig2, ax = plt.subplots(figsize=(10, 5), dpi=300)
    fig2.patch.set_facecolor("#F8FAFC")
    drivers = ["DHW Heat Stress", "Structural Rugosity", "Ocean Acidification (pH)", "Turbidity Attenuation", "Baseline SST Anomaly"]
    vals = [18.5, -6.2, 8.4, -3.1, 4.2]
    bar_colors = ["#E53E3E" if v > 0 else "#3182CE" for v in vals]

    ax.barh(drivers, vals, color=bar_colors, edgecolor="none", height=0.55)
    ax.axvline(0, color="gray", linestyle="--", alpha=0.7)
    ax.set_title("Real-Time XGBoost + TreeSHAP Feature Attribution Sandbox", fontsize=13, fontweight="bold", color="#1A365D")
    ax.set_xlabel("Marginal Risk Attribution Score (SHAP Value)", fontsize=10)

    plt.tight_layout()
    p2 = os.path.join(SCREENSHOTS_DIR, "02_live_ai_inference.png")
    plt.savefig(p2, dpi=300)
    plt.close()

    # 3. Decadal Sandbox Simulation Screenshot
    fig3, ax = plt.subplots(figsize=(12, 5.5), dpi=300)
    fig3.patch.set_facecolor("#F8FAFC")
    years = np.linspace(2025, 2050, 100)
    c_unmit = 32.0 * np.exp(-0.08 * (years - 2025)) + 4.8 * (1 - np.exp(-0.08 * (years - 2025)))
    c_resto = 32.0 + 14.2 * (1 - np.exp(-0.12 * (years - 2025)))

    ax.plot(years, c_unmit, color="#E53E3E", linewidth=3.0, label="Unmitigated Warming (SSP5-8.5 -> 4.8% Cover)")
    ax.plot(years, c_resto, color="#3182CE", linewidth=3.5, label="CoralTwin-DT Hybrid Restoration (Scenario 4 -> 46.2% Cover)")
    ax.fill_between(years, c_unmit, c_resto, color="#BEE3F8", alpha=0.3, label="Ecological Resilience Dividend (+41.4%)")

    ax.set_title("Forward Decadal Simulation Sandbox (Mumby ODEs 2025–2050)", fontsize=13, fontweight="bold", color="#1A365D")
    ax.set_xlabel("Simulation Year", fontsize=11)
    ax.set_ylabel("Live Coral Cover (%)", fontsize=11)
    ax.set_ylim(0, 60)
    ax.legend(loc="upper left", frameon=True, facecolor="white", framealpha=0.9)

    plt.tight_layout()
    p3 = os.path.join(SCREENSHOTS_DIR, "03_decadal_sandbox_simulation.png")
    plt.savefig(p3, dpi=300)
    plt.close()

    print("Screenshots successfully generated in DEMO/screenshots/.")


if __name__ == "__main__":
    generate_screenshots()
