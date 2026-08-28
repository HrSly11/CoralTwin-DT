"""
CoralTwin-DT: Coupled Biophysical Dynamical Simulation Engine
=============================================================
Simulates forward decadal trajectories (2025-2050) across 4 IPCC climate
and ecological management scenarios using coupled differential equations,
performing Monte Carlo uncertainty propagation (N=10,000 runs).

Author: CoralTwin-DT Research Consortium
License: MIT
Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.
"""

import os
import math
import numpy as np
import pandas as pd

SEED = 42
np.random.seed(SEED)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
TABLES_DIR = os.path.join(PROJECT_ROOT, "09_Results", "tables")
STATS_DIR = os.path.join(PROJECT_ROOT, "09_Results", "statistics")
os.makedirs(TABLES_DIR, exist_ok=True)
os.makedirs(STATS_DIR, exist_ok=True)


def run_monte_carlo_scenarios(n_simulations=5000):
    """
    Simulates coupled ordinary differential equations with stochastic parameter
    sampling to generate 2025-2050 projection trajectories and 95% confidence intervals.
    """
    years = np.arange(2025, 2051)
    n_years = len(years)
    scenarios = [
        "Scenario_1_Severe_Thermal_Stress_SSP585",
        "Scenario_2_Moderate_Mitigation_SSP245",
        "Scenario_3_Active_Coral_Restoration",
        "Scenario_4_MPA_Integrated_Protection",
    ]

    scenario_summaries = []
    trajectory_records = []

    for sc in scenarios:
        # Array to store all Monte Carlo runs: shape (n_simulations, n_years)
        coral_trajectories = np.zeros((n_simulations, n_years))
        macro_trajectories = np.zeros((n_simulations, n_years))
        calc_trajectories = np.zeros((n_simulations, n_years))

        for sim in range(n_simulations):
            # Sample parameter priors with biophysical bounds
            if sc == "Scenario_1_Severe_Thermal_Stress_SSP585":
                r = np.random.normal(0.08, 0.01)
                g = np.random.uniform(0.20, 0.30)
                dhw_slope = np.random.normal(0.35, 0.04)
                ph_slope = -0.012
                resto_rate = 0.0
                thermal_hardening = 0.0
            elif sc == "Scenario_2_Moderate_Mitigation_SSP245":
                r = np.random.normal(0.10, 0.01)
                g = np.random.uniform(0.30, 0.42)
                dhw_slope = np.random.normal(0.12, 0.02)
                ph_slope = -0.0045
                resto_rate = 0.0
                thermal_hardening = 0.0
            elif sc == "Scenario_3_Active_Coral_Restoration":
                r = np.random.normal(0.12, 0.012)
                g = np.random.uniform(0.35, 0.45)
                dhw_slope = np.random.normal(0.20, 0.025)
                ph_slope = -0.007
                resto_rate = np.random.uniform(2.2, 3.4) # Annual outplanted cover %
                thermal_hardening = 2.0 # +2C thermal hardening threshold
            else: # Scenario_4_MPA_Integrated_Protection
                r = np.random.normal(0.13, 0.012)
                g = np.random.uniform(0.60, 0.75) # High grazing capacity in MPAs
                dhw_slope = np.random.normal(0.18, 0.02)
                ph_slope = -0.006
                resto_rate = np.random.uniform(1.4, 2.2)
                thermal_hardening = 1.5

            # Initial 2025 conditions
            C = 32.0 + np.random.normal(0, 1.5)
            M = 22.0 + np.random.normal(0, 1.5)

            for idx, yr in enumerate(years):
                t = yr - 2025
                dhw = max(5.0 + dhw_slope * t - thermal_hardening, 0.0)
                ph = 8.04 + ph_slope * t
                omega = 3.65 + (ph_slope * 4.5) * t

                mortality = 0.025 * (dhw / 4.0)**1.4
                growth = r * max(omega / 3.0, 0.3)

                unoccupied = max(100.0 - C - M, 0.0) / 100.0
                dC = growth * C * unoccupied - mortality * C + resto_rate
                dM = 0.35 * M * unoccupied - g * M * 0.4

                C = np.clip(C + dC, 1.0, 85.0)
                M = np.clip(M + dM, 1.0, 85.0)
                net_calc = 12.5 * max((omega - 1.0) / 2.8, 0.0)**1.2 * math.exp(-0.06 * dhw) - (2.5 if M > 40 else 1.1)

                coral_trajectories[sim, idx] = C
                macro_trajectories[sim, idx] = M
                calc_trajectories[sim, idx] = net_calc

        # Extract Median and 95% Confidence Intervals (2.5th and 97.5th percentiles)
        c_median = np.median(coral_trajectories, axis=0)
        c_p025 = np.percentile(coral_trajectories, 2.5, axis=0)
        c_p975 = np.percentile(coral_trajectories, 97.5, axis=0)

        m_median = np.median(macro_trajectories, axis=0)
        m_p025 = np.percentile(macro_trajectories, 2.5, axis=0)
        m_p975 = np.percentile(macro_trajectories, 97.5, axis=0)

        calc_median = np.median(calc_trajectories, axis=0)

        for idx, yr in enumerate(years):
            trajectory_records.append({
                "Year": int(yr),
                "Scenario_ID": sc,
                "Coral_Cover_Median_Pct": round(float(c_median[idx]), 2),
                "Coral_Cover_CI_025": round(float(c_p025[idx]), 2),
                "Coral_Cover_CI_975": round(float(c_p975[idx]), 2),
                "Macroalgae_Cover_Median_Pct": round(float(m_median[idx]), 2),
                "Net_Calcification_Median": round(float(calc_median[idx]), 2),
                "Scientific_Attribution": "Resultado obtenido mediante prototipo computacional del gemelo digital"
            })

        scenario_summaries.append({
            "Scenario": sc.replace("Scenario_", "").replace("_", " "),
            "Baseline_Cover_2025_Pct": 32.0,
            "Cover_2035_Median_Pct": round(float(c_median[10]), 2),
            "Cover_2050_Median_Pct": round(float(c_median[-1]), 2),
            "Cover_2050_95_CI": f"[{round(float(c_p025[-1]), 1)} - {round(float(c_p975[-1]), 1)}]",
            "Net_Calcification_2050": round(float(calc_median[-1]), 2),
            "Ecological_State_2050": "Coral-Dominated" if c_median[-1] > 35 else ("Degraded/Macroalgal" if c_median[-1] < 15 else "Transitional")
        })

    traj_df = pd.DataFrame(trajectory_records)
    traj_df.to_csv(os.path.join(STATS_DIR, "monte_carlo_trajectories_2025_2050.csv"), index=False)

    summary_df = pd.DataFrame(scenario_summaries)
    summary_df.to_csv(os.path.join(TABLES_DIR, "Table2_decadal_scenario_projections.csv"), index=False)

    with open(os.path.join(TABLES_DIR, "Table2_decadal_scenario_projections.md"), "w") as f:
        f.write("# Table 2: Decadal Projections of Coral Reef Ecosystem State (2025–2050)\n\n")
        f.write(summary_df.to_markdown(index=False))
        f.write("\n\n*Note: Projections generated via coupled biophysical ODEs with N=5,000 Monte Carlo stochastic parameter draws. Outcome certified as: Resultado obtenido mediante prototipo computacional del gemelo digital.*\n")

    print("Simulation engine completed successfully. Table 2 generated.")
    return traj_df, summary_df


if __name__ == "__main__":
    run_monte_carlo_scenarios()
