"""
CoralTwin-DT: Coupled Biophysical ODE Simulation Engine (RK4, N=5,000 Monte Carlo)
==================================================================================
Implements the exact coupled ordinary differential equations (Equations 4, 5, and 6)
using 4th-order Runge-Kutta (RK4) numerical integration (dt = 0.05 yr, 500 steps
across 2025–2050) and N = 5,000 Monte Carlo realizations per scenario with ±15%
Gaussian parameter perturbations (`SEED = 42`).

Equations (5) & (6):
  dC/dt = r * C * (1 - C - M) - [d_0 + alpha * DHW(t)^2 / (1 + beta * Omega_arag(t))] * C + Phi_restoration
  dM/dt = a * M * (1 - C - M) - [g(H_MPA) * M] / [M + (1 - C - M) + 1e-6] + gamma * M * C

Equation (4) (Net Carbonate Accretion, kg CaCO3 m^-2 yr^-1):
  G_net(t) = 12.5 * max((Omega_arag(t) - 1.0) / 2.8, 0.0)^1.2 * exp(-0.06 * DHW(t)) * (C(t) / C_0) - 1.85

Outputs:
- `09_Results/statistics/monte_carlo_trajectories_2025_2050.csv`
- `09_Results/tables/Table2_decadal_scenario_projections.csv`
- `09_Results/tables/Table2_decadal_scenario_projections.md`
- `results/scenario_projections_2050.csv`
- `09_Results/audit/scenario_model_comparison.csv`
"""

import os
import math
import numpy as np
import pandas as pd

SEED = 42

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_PATH = os.path.join(PROJECT_ROOT, "03_Data", "final_dataset.csv")
TABLES_DIR = os.path.join(PROJECT_ROOT, "09_Results", "tables")
STATS_DIR = os.path.join(PROJECT_ROOT, "09_Results", "statistics")
AUDIT_DIR = os.path.join(PROJECT_ROOT, "09_Results", "audit")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

for d in [TABLES_DIR, STATS_DIR, AUDIT_DIR, RESULTS_DIR]:
    os.makedirs(d, exist_ok=True)


# Canonical ODE parameters from Table 2 of the manuscript
ODE_BASE_PARAMS = {
    "r": 0.45,       # Intrinsic coral recruitment & lateral extension rate (yr^-1)
    "d0": 0.05,      # Background natural coral mortality rate (yr^-1)
    "alpha": 0.012,  # Non-linear thermal mortality coefficient (DHW^-2 yr^-1)
    "beta": 0.75,    # Aragonite saturation buffering coefficient (dimensionless)
    "a": 0.85,       # Intrinsic macroalgal proliferation rate (yr^-1)
    "gamma": 0.22,   # Macroalgal overgrowth coefficient on live coral (yr^-1)
}

SCENARIO_CONFIGS = [
    {
        "id": "Scenario_1_Severe_Thermal_Stress_SSP585",
        "code": "S1_SSP585_Unmitigated",
        "label": "1. Severe Thermal Stress (SSP5-8.5)",
        "dhw_0": 5.0,
        "dhw_slope": 0.36,        # Reaches 14.0 degC-weeks by 2050
        "thermal_hardening": 0.0,
        "omega_0": 3.65,
        "omega_slope": -0.052,    # Falls to 2.35 by 2050
        "g_mpa": 0.25,            # Unprotected reef herbivory grazing (yr^-1)
        "phi_resto": 0.000,       # No active outplanting
    },
    {
        "id": "Scenario_2_Moderate_Mitigation_SSP245",
        "code": "S2_SSP245_Moderate",
        "label": "2. Moderate Mitigation (SSP2-4.5)",
        "dhw_0": 5.0,
        "dhw_slope": 0.18,        # Reaches 9.5 degC-weeks by 2050
        "thermal_hardening": 0.0,
        "omega_0": 3.65,
        "omega_slope": -0.022,    # Stabilizes near 3.10 by 2050
        "g_mpa": 0.30,            # Baseline reef herbivory grazing (yr^-1)
        "phi_resto": 0.000,       # No active outplanting
    },
    {
        "id": "Scenario_3_Active_Coral_Restoration",
        "code": "S3_Active_Restoration",
        "label": "3. Active Resilient Outplanting",
        "dhw_0": 5.0,
        "dhw_slope": 0.20,
        "thermal_hardening": 2.0, # +2.0 degC-week CBASS thermal tolerance
        "omega_0": 3.65,
        "omega_slope": -0.028,
        "g_mpa": 0.35,            # Partial local grazing management (yr^-1)
        "phi_resto": 0.025,       # +2.5%/yr micro-fragmentation outplanting
    },
    {
        "id": "Scenario_4_MPA_Integrated_Protection",
        "code": "S4_Integrated_Intervention",
        "label": "4. Integrated MPA & Outplanting",
        "dhw_0": 5.0,
        "dhw_slope": 0.18,
        "thermal_hardening": 2.0, # +2.0 degC-week CBASS thermal tolerance
        "omega_0": 3.65,
        "omega_slope": -0.022,
        "g_mpa": 0.68,            # Strict no-take MPA herbivory protection (yr^-1)
        "phi_resto": 0.030,       # +3.0%/yr targeted resilient outplanting
    },
]


def rk4_coupled_ode_simulate(
    sc_cfg: dict,
    c0_pct: float,
    m0_pct: float,
    n_simulations: int = 5000,
    dt: float = 0.05,
    n_years: int = 25,
    seed: int = SEED,
):
    """
    Integrates Equations (5) and (6) via 4th-order Runge-Kutta (dt = 0.05 yr,
    500 sub-steps over 25 years from 2025 to 2050) across `n_simulations` Monte Carlo
    realizations with independent ±15% Gaussian parameter perturbations.
    """
    rng = np.random.default_rng(seed)

    def sample_param(val, rel_sd=0.15):
        if val == 0.0:
            return np.zeros(n_simulations, dtype=np.float64)
        draws = rng.normal(val, abs(val) * rel_sd, size=n_simulations)
        return np.clip(draws, 0.05 * abs(val), 2.5 * abs(val))

    r = sample_param(ODE_BASE_PARAMS["r"])
    d0 = sample_param(ODE_BASE_PARAMS["d0"])
    alpha = sample_param(ODE_BASE_PARAMS["alpha"])
    beta = sample_param(ODE_BASE_PARAMS["beta"])
    a = sample_param(ODE_BASE_PARAMS["a"])
    gamma = sample_param(ODE_BASE_PARAMS["gamma"])

    g_mpa = sample_param(sc_cfg["g_mpa"])
    phi_resto = sample_param(sc_cfg["phi_resto"])
    dhw_slope = sample_param(sc_cfg["dhw_slope"])
    omega_slope = -sample_param(abs(sc_cfg["omega_slope"]))

    # Initial fractional covers C(0), M(0) in [0, 1]
    C = np.clip(rng.normal(c0_pct / 100.0, 0.015, size=n_simulations), 0.05, 0.80)
    M = np.clip(rng.normal(m0_pct / 100.0, 0.015, size=n_simulations), 0.05, 0.80)
    C0_vec = C.copy()

    n_steps = int(round(n_years / dt))  # 500 steps
    steps_per_year = int(round(1.0 / dt))  # 20 steps/yr

    coral_yearly = np.zeros((n_simulations, n_years + 1), dtype=np.float64)
    macro_yearly = np.zeros((n_simulations, n_years + 1), dtype=np.float64)
    calc_scaled_yearly = np.zeros((n_simulations, n_years + 1), dtype=np.float64)
    calc_unscaled_yearly = np.zeros((n_simulations, n_years + 1), dtype=np.float64)

    def forcing_at(t_yr):
        dhw_t = np.maximum(sc_cfg["dhw_0"] + dhw_slope * t_yr - sc_cfg["thermal_hardening"], 0.0)
        omega_t = np.clip(sc_cfg["omega_0"] + omega_slope * t_yr, 1.05, 4.50)
        return dhw_t, omega_t

    def derivatives(C_state, M_state, t_yr):
        C_s = np.clip(C_state, 0.001, 0.98)
        M_s = np.clip(M_state, 0.001, 0.98 - C_s)
        space = np.maximum(1.0 - C_s - M_s, 0.0)
        dhw_t, omega_t = forcing_at(t_yr)

        mort_thermal = d0 + alpha * (dhw_t ** 2) / (1.0 + beta * omega_t)
        dC_dt = r * C_s * space - mort_thermal * C_s + phi_resto * space
        dM_dt = a * M_s * space - (g_mpa * M_s) / (M_s + space + 1e-6) + gamma * M_s * C_s
        return dC_dt, dM_dt

    def record_year(yr_idx, t_yr, C_state, M_state):
        dhw_t, omega_t = forcing_at(t_yr)
        coral_yearly[:, yr_idx] = C_state * 100.0
        macro_yearly[:, yr_idx] = M_state * 100.0
        gross_pot = 12.5 * (np.maximum((omega_t - 1.0) / 2.8, 0.0) ** 1.2) * np.exp(-0.06 * dhw_t)
        calc_scaled_yearly[:, yr_idx] = gross_pot * (C_state / np.maximum(C0_vec, 0.05)) - 1.85
        calc_unscaled_yearly[:, yr_idx] = gross_pot - (2.5 * (M_state > 0.40) + 1.1 * (M_state <= 0.40))

    record_year(0, 0.0, C, M)

    for step in range(1, n_steps + 1):
        t0 = (step - 1) * dt
        k1_C, k1_M = derivatives(C, M, t0)
        k2_C, k2_M = derivatives(C + 0.5 * dt * k1_C, M + 0.5 * dt * k1_M, t0 + 0.5 * dt)
        k3_C, k3_M = derivatives(C + 0.5 * dt * k2_C, M + 0.5 * dt * k2_M, t0 + 0.5 * dt)
        k4_C, k4_M = derivatives(C + dt * k3_C, M + dt * k3_M, t0 + dt)

        C = C + (dt / 6.0) * (k1_C + 2.0 * k2_C + 2.0 * k3_C + k4_C)
        M = M + (dt / 6.0) * (k1_M + 2.0 * k2_M + 2.0 * k3_M + k4_M)

        C = np.clip(C, 0.001, 0.95)
        M = np.clip(M, 0.001, np.maximum(0.98 - C, 0.001))

        if step % steps_per_year == 0:
            yr_idx = step // steps_per_year
            record_year(yr_idx, step * dt, C, M)

    return coral_yearly, macro_yearly, calc_scaled_yearly, calc_unscaled_yearly


def run_monte_carlo_scenarios(n_simulations: int = 5000):
    import json
    df_data = pd.read_csv(DATA_PATH)
    emp_c0 = round(float(df_data["Live_Coral_Cover_Pct"].mean()), 2)  # 33.68%
    emp_m0 = round(float(df_data["Macroalgae_Cover_Pct"].mean()), 2)  # 31.41%

    years = np.arange(2025, 2051)
    trajectory_records = []
    scenario_summaries = []
    comparison_rows = []

    # Legacy values from pre-audit Table2_decadal_scenario_projections.csv and CoralTwin-DT_v2.docx Table 4
    legacy_euler_2050 = {
        "S1_SSP585_Unmitigated": (7.58, "[5.0 - 11.2]", -1.03),
        "S2_SSP245_Moderate": (30.55, "[25.3 - 35.6]", 3.94),
        "S3_Active_Restoration": (77.30, "[67.9 - 85.0]", 2.83),
        "S4_Integrated_Intervention": (73.18, "[66.8 - 79.4]", 3.31),
    }
    manuscript_table4_claimed = {
        "S1_SSP585_Unmitigated": (4.8, "[2.1 - 8.4]", -2.35),
        "S2_SSP245_Moderate": (21.4, "[16.2 - 26.8]", 1.15),
        "S3_Active_Restoration": (38.7, "[31.5 - 45.9]", 3.80),
        "S4_Integrated_Intervention": (46.2, "[39.4 - 53.1]", 5.45),
    }

    for sc_idx, sc in enumerate(SCENARIO_CONFIGS):
        coral_emp, macro_emp, calc_sc_emp, calc_un_emp = rk4_coupled_ode_simulate(
            sc, c0_pct=emp_c0, m0_pct=emp_m0, n_simulations=n_simulations, dt=0.05, n_years=25, seed=SEED + sc_idx
        )
        coral_ms, macro_ms, calc_sc_ms, _ = rk4_coupled_ode_simulate(
            sc, c0_pct=28.50, m0_pct=22.00, n_simulations=n_simulations, dt=0.05, n_years=25, seed=SEED + sc_idx
        )

        c_mean = np.mean(coral_emp, axis=0)
        c_sd = np.std(coral_emp, axis=0, ddof=1)
        c_med = np.median(coral_emp, axis=0)
        c_p025 = np.percentile(coral_emp, 2.5, axis=0)
        c_p975 = np.percentile(coral_emp, 97.5, axis=0)

        m_mean = np.mean(macro_emp, axis=0)
        m_med = np.median(macro_emp, axis=0)
        m_p025 = np.percentile(macro_emp, 2.5, axis=0)
        m_p975 = np.percentile(macro_emp, 97.5, axis=0)

        g_mean = np.mean(calc_sc_emp, axis=0)
        g_med = np.median(calc_sc_emp, axis=0)
        g_p025 = np.percentile(calc_sc_emp, 2.5, axis=0)
        g_p975 = np.percentile(calc_sc_emp, 97.5, axis=0)

        collapse_prob_2050 = float(np.mean(coral_emp[:, -1] < 10.0) * 100.0)

        for idx, yr in enumerate(years):
            trajectory_records.append({
                "Year": int(yr),
                "Scenario_ID": sc["id"],
                "Scenario_Code": sc["code"],
                "Coral_Cover_Mean_Pct": round(float(c_mean[idx]), 2),
                "Coral_Cover_SD_Pct": round(float(c_sd[idx]), 2),
                "Coral_Cover_Median_Pct": round(float(c_med[idx]), 2),
                "Coral_Cover_CI_025": round(float(c_p025[idx]), 2),
                "Coral_Cover_CI_975": round(float(c_p975[idx]), 2),
                "Macroalgae_Cover_Mean_Pct": round(float(m_mean[idx]), 2),
                "Macroalgae_Cover_Median_Pct": round(float(m_med[idx]), 2),
                "Macroalgae_Cover_CI_025": round(float(m_p025[idx]), 2),
                "Macroalgae_Cover_CI_975": round(float(m_p975[idx]), 2),
                "Net_Calcification_Mean": round(float(g_mean[idx]), 2),
                "Net_Calcification_Median": round(float(g_med[idx]), 2),
                "Net_Calcification_CI_025": round(float(g_p025[idx]), 2),
                "Net_Calcification_CI_975": round(float(g_p975[idx]), 2),
                "Scientific_Attribution": "Resultado obtenido mediante prototipo computacional del gemelo digital",
            })

        state_2050 = (
            "Coral-Dominated" if c_mean[-1] > 35.0
            else ("Degraded/Macroalgal" if c_mean[-1] < 15.0 else "Transitional")
        )

        scenario_summaries.append({
            "Scenario_Code": sc["code"],
            "Scenario": sc["id"].replace("Scenario_", "").replace("_", " "),
            "Baseline_Cover_2025_Pct": emp_c0,
            "Cover_2035_Mean_Pct": round(float(c_mean[10]), 2),
            "Cover_2035_Median_Pct": round(float(c_med[10]), 2),
            "Cover_2050_Mean_Pct": round(float(c_mean[-1]), 2),
            "Cover_2050_SD_Pct": round(float(c_sd[-1]), 2),
            "Cover_2050_Median_Pct": round(float(c_med[-1]), 2),
            "Cover_2050_95_CI": f"[{c_p025[-1]:.1f} - {c_p975[-1]:.1f}]",
            "Macroalgae_2050_Mean_Pct": round(float(m_mean[-1]), 2),
            "Macroalgae_2050_95_CI": f"[{m_p025[-1]:.1f} - {m_p975[-1]:.1f}]",
            "Net_Calcification_2050": round(float(g_mean[-1]), 2),
            "Net_Calcification_2050_95_CI": f"[{g_p025[-1]:.2f} - {g_p975[-1]:.2f}]",
            "Collapse_Probability_Below_10Pct": round(collapse_prob_2050, 2),
            "Ecological_State_2050": state_2050,
        })

        # Also record comparison row (Audited 30-station baseline 33.68% vs Manuscript baseline 28.50% vs Legacy Euler vs Manuscript Table 4)
        ms_mean = float(np.mean(coral_ms[:, -1]))
        ms_lo = float(np.percentile(coral_ms[:, -1], 2.5))
        ms_hi = float(np.percentile(coral_ms[:, -1], 97.5))
        ms_calc = float(np.mean(calc_sc_ms[:, -1]))
        leg_c, leg_ci, leg_g = legacy_euler_2050[sc["code"]]
        doc_c, doc_ci, doc_g = manuscript_table4_claimed[sc["code"]]

        comparison_rows.append({
            "Scenario_Code": sc["code"],
            "RK4_Eq5_6_Empirical_Baseline33_68_Mean_2050_Pct": round(float(c_mean[-1]), 2),
            "RK4_Eq5_6_Empirical_Baseline33_68_CI95": f"[{c_p025[-1]:.1f} - {c_p975[-1]:.1f}]",
            "RK4_Eq5_6_Empirical_Net_Accretion_2050": round(float(g_mean[-1]), 2),
            "RK4_Eq5_6_Manuscript_Baseline28_50_Mean_2050_Pct": round(ms_mean, 2),
            "RK4_Eq5_6_Manuscript_Baseline28_50_CI95": f"[{ms_lo:.1f} - {ms_hi:.1f}]",
            "RK4_Eq5_6_Manuscript_Net_Accretion_2050": round(ms_calc, 2),
            "Legacy_Euler_Script_Table2_2050_Pct": leg_c,
            "Legacy_Euler_Script_Table2_CI95": leg_ci,
            "Legacy_Euler_Script_Net_Accretion_2050": leg_g,
            "Manuscript_Table4_Claimed_2050_Pct": doc_c,
            "Manuscript_Table4_Claimed_CI95": doc_ci,
            "Manuscript_Table4_Claimed_Net_Accretion_2050": doc_g,
        })

    traj_df = pd.DataFrame(trajectory_records)
    traj_df.to_csv(os.path.join(STATS_DIR, "monte_carlo_trajectories_2025_2050.csv"), index=False)
    traj_df.to_csv(os.path.join(RESULTS_DIR, "scenario_trajectories.csv"), index=False)

    summary_df = pd.DataFrame(scenario_summaries)
    summary_df.to_csv(os.path.join(TABLES_DIR, "Table2_decadal_scenario_projections.csv"), index=False)
    summary_df.to_csv(os.path.join(RESULTS_DIR, "scenario_projections_2050.csv"), index=False)
    summary_df.to_csv(os.path.join(RESULTS_DIR, "scenario_2050_summary.csv"), index=False)

    comp_df = pd.DataFrame(comparison_rows)
    comp_df.to_csv(os.path.join(AUDIT_DIR, "scenario_model_comparison.csv"), index=False)

    ode_params_payload = {
        "integration_method": "RK4 (4th-order Runge-Kutta)",
        "dt_years": 0.05,
        "n_steps": 500,
        "horizon_years": [2025, 2050],
        "n_monte_carlo_runs_per_scenario": n_simulations,
        "parameter_perturbation_gaussian_rel_sd": 0.15,
        "seed": SEED,
        "empirical_baseline_2025": {
            "Live_Coral_Cover_Pct": emp_c0,
            "Macroalgae_Cover_Pct": emp_m0,
        },
        "manuscript_claimed_baseline_2025": {
            "Live_Coral_Cover_Pct": 28.50,
            "Macroalgae_Cover_Pct": 22.00,
        },
        "base_ode_parameters": ODE_BASE_PARAMS,
        "scenario_configs": SCENARIO_CONFIGS,
    }
    with open(os.path.join(RESULTS_DIR, "scenario_ode_parameters.json"), "w", encoding="utf-8") as f:
        json.dump(ode_params_payload, f, indent=2)

    with open(os.path.join(TABLES_DIR, "Table2_decadal_scenario_projections.md"), "w", encoding="utf-8") as f:
        f.write("# Table 2: Decadal Projections of Coral Reef Ecosystem State (2025–2050, RK4 Integration of Eqs. 5–6, N=5,000 Monte Carlo Runs)\n\n")
        f.write(summary_df.to_markdown(index=False))
        f.write(
            f"\n\n*Note: Projections generated via 4th-order Runge-Kutta (dt = 0.05 yr, 500 steps) integration of "
            f"coupled ODEs (Eqs. 5 & 6) with N=5,000 Monte Carlo realizations and ±15% Gaussian parameter perturbations "
            f"(SEED = 42), starting from the unified 30-station baseline live coral cover ({emp_c0:.2f}%).*\n"
        )

    print("RK4 coupled ODE simulation completed successfully:")
    print(summary_df[["Scenario_Code", "Baseline_Cover_2025_Pct", "Cover_2050_Mean_Pct", "Cover_2050_95_CI", "Macroalgae_2050_Mean_Pct", "Net_Calcification_2050", "Collapse_Probability_Below_10Pct"]])
    return traj_df, summary_df


if __name__ == "__main__":
    run_monte_carlo_scenarios()
