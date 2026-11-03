"""
CoralTwin-DT: S3 -> S4 factor isolation (reviewer-requested analysis, manuscript Section 3.3)
==============================================================================================
S3 and S4 differ in the scenario parameters listed in FACTORS below. This script reuses the
repository's own integrator (`simulation_engine.rk4_coupled_ode_simulate`, RK4, dt = 0.05 yr,
500 steps, N = 5,000 Monte Carlo runs, +-15 % Gaussian parameter perturbation) and:

  1. Re-runs S3 and S4 with their canonical per-scenario seeds (SEED + scenario index, exactly
     as in simulation_engine.run_monte_carlo_scenarios) and checks them against
     results/scenario_projections_2050.csv (reproduction check).
  2. Runs ALL 2^4 = 16 factor combinations between S3 and S4 with ONE common seed
     (common random numbers: every variant draws the same standard-normal stream, so paired
     differences are free of Monte Carlo noise from different seeds).
  3. Reports 2050 coral cover and 2050 net carbonate balance (mean, 2.5-97.5 % percentile
     interval of the Monte Carlo distribution, as in Table 7) and paired differences vs S3
     (mean difference with 95 % CI of the mean).
  4. Computes the exact Shapley decomposition of the S4-S3 gap over the factors.
  5. Repeats the key quantities over four common seeds (42..45) as a robustness check.

Outputs (results/):
  s4_factor_isolation_variants.csv, s4_factor_isolation_shapley.csv,
  s4_factor_isolation_seed_robustness.csv, s4_factor_isolation_reproduction_check.csv,
  s4_factor_isolation_summary.json
"""

import os
import sys
import json
import itertools
import math
import copy

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, BASE_DIR)

import simulation_engine as se  # noqa: E402  (repository integrator)

RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

N_SIM = 5000
DT = 0.05
N_YEARS = 25
COMMON_SEED = se.SEED  # 42, the repository seed
ROBUSTNESS_SEEDS = [42, 43, 44, 45]

S3 = next(c for c in se.SCENARIO_CONFIGS if c["code"] == "S3_Active_Restoration")
S4 = next(c for c in se.SCENARIO_CONFIGS if c["code"] == "S4_Integrated_Intervention")

# Every scenario-level parameter in which S3 and S4 differ in the repository configuration.
FACTORS = {
    "g": "g_mpa",
    "Phi": "phi_resto",
    "DHW": "dhw_slope",
    "Omega": "omega_slope",
}
# Sanity: nothing else differs between S3 and S4.
_differing = [k for k in S3 if k not in ("id", "code", "label") and S3[k] != S4[k]]
assert sorted(_differing) == sorted(FACTORS.values()), _differing


def baseline_covers():
    df = pd.read_csv(se.DATA_PATH)
    c0 = round(float(df["Live_Coral_Cover_Pct"].mean()), 2)
    m0 = round(float(df["Macroalgae_Cover_Pct"].mean()), 2)
    return c0, m0


def build_cfg(s4_factors):
    """Start from S3 and switch the listed factors to their S4 value."""
    cfg = copy.deepcopy(S3)
    for f in s4_factors:
        cfg[FACTORS[f]] = S4[FACTORS[f]]
    return cfg


def run(cfg, seed, c0, m0):
    coral, macro, calc_sc, _ = se.rk4_coupled_ode_simulate(
        cfg, c0_pct=c0, m0_pct=m0, n_simulations=N_SIM, dt=DT, n_years=N_YEARS, seed=seed
    )
    return {
        "cover": coral[:, -1].copy(),
        "macro": macro[:, -1].copy(),
        "carb": calc_sc[:, -1].copy(),
    }


def pct_ci(x):
    return float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))


def paired_diff(x, ref):
    d = x - ref
    m = float(d.mean())
    se_ = float(d.std(ddof=1) / math.sqrt(len(d)))
    return m, m - 1.96 * se_, m + 1.96 * se_


def main():
    c0, m0 = baseline_covers()
    print(f"Baseline: coral {c0} %, macroalgae {m0} %  | N={N_SIM}, dt={DT}, RK4, common seed={COMMON_SEED}")

    # ---- 1. Reproduction check with canonical per-scenario seeds ---------------------------
    ref = pd.read_csv(os.path.join(RESULTS_DIR, "scenario_projections_2050.csv")).set_index("Scenario_Code")
    repro_rows = []
    for idx, sc in enumerate(se.SCENARIO_CONFIGS):
        if sc["code"] not in ("S3_Active_Restoration", "S4_Integrated_Intervention"):
            continue
        out = run(sc, se.SEED + idx, c0, m0)
        lo, hi = pct_ci(out["cover"])
        clo, chi = pct_ci(out["carb"])
        r = ref.loc[sc["code"]]
        repro_rows.append({
            "Scenario_Code": sc["code"],
            "Seed_used": se.SEED + idx,
            "Cover_2050_rerun": round(float(out["cover"].mean()), 2),
            "Cover_2050_repo_csv": float(r["Cover_2050_Mean_Pct"]),
            "Cover_CI_rerun": f"[{lo:.1f} - {hi:.1f}]",
            "Cover_CI_repo_csv": r["Cover_2050_95_CI"],
            "Net_Carbonate_rerun": round(float(out["carb"].mean()), 2),
            "Net_Carbonate_repo_csv": float(r["Net_Calcification_2050"]),
            "Net_Carbonate_CI_rerun": f"[{clo:.2f} - {chi:.2f}]",
            "Net_Carbonate_CI_repo_csv": r["Net_Calcification_2050_95_CI"],
            "Macroalgae_2050_rerun": round(float(out["macro"].mean()), 2),
            "Macroalgae_2050_repo_csv": float(r["Macroalgae_2050_Mean_Pct"]),
            "Collapse_pct_rerun": round(float((out["cover"] < 10.0).mean() * 100.0), 2),
            "Collapse_pct_repo_csv": float(r["Collapse_Probability_Below_10Pct"]),
        })
    repro = pd.DataFrame(repro_rows)
    repro.to_csv(os.path.join(RESULTS_DIR, "s4_factor_isolation_reproduction_check.csv"), index=False)
    print("\nReproduction check (canonical seeds):")
    print(repro.T.to_string())

    # ---- 2. Full 2^4 factorial with a common seed -----------------------------------------
    names = list(FACTORS.keys())

    def key(subset):
        return tuple(sorted(subset, key=names.index))

    def factorial(seed):
        res = {}
        for r in range(len(names) + 1):
            for subset in itertools.combinations(names, r):
                res[key(subset)] = run(build_cfg(subset), seed, c0, m0)
        return res

    res = factorial(COMMON_SEED)
    base = res[()]

    def label(subset):
        if subset == ():
            return "S3 (referencia)"
        if len(subset) == len(names):
            return "S4 (referencia)"
        if len(subset) == 1:
            return f"S3 con solo {subset[0]} de S4"
        if len(subset) == len(names) - 1:
            missing = [n for n in names if n not in subset][0]
            return f"S4 con {missing} de S3"
        return "S3 con " + "+".join(subset) + " de S4"

    rows = []
    for subset, out in res.items():
        lo, hi = pct_ci(out["cover"])
        clo, chi = pct_ci(out["carb"])
        dc = paired_diff(out["cover"], base["cover"])
        dg = paired_diff(out["carb"], base["carb"])
        rows.append({
            "Variant": label(subset),
            "Factors_switched_to_S4": "+".join(subset) if subset else "none",
            "n_factors": len(subset),
            "Cover_2050_Mean_Pct": round(float(out["cover"].mean()), 2),
            "Cover_2050_CI_lo": round(lo, 1),
            "Cover_2050_CI_hi": round(hi, 1),
            "Cover_diff_vs_S3_pp": round(dc[0], 2),
            "Cover_diff_CI_lo": round(dc[1], 2),
            "Cover_diff_CI_hi": round(dc[2], 2),
            "NetCarbonate_2050_Mean": round(float(out["carb"].mean()), 2),
            "NetCarbonate_CI_lo": round(clo, 2),
            "NetCarbonate_CI_hi": round(chi, 2),
            "NetCarbonate_diff_vs_S3": round(dg[0], 2),
            "NetCarbonate_diff_CI_lo": round(dg[1], 2),
            "NetCarbonate_diff_CI_hi": round(dg[2], 2),
            "Macroalgae_2050_Mean_Pct": round(float(out["macro"].mean()), 2),
            "Collapse_pct": round(float((out["cover"] < 10.0).mean() * 100.0), 2),
        })
    var_df = pd.DataFrame(rows).sort_values(["n_factors", "Factors_switched_to_S4"]).reset_index(drop=True)
    var_df.to_csv(os.path.join(RESULTS_DIR, "s4_factor_isolation_variants.csv"), index=False)
    print("\nAll 16 variants (common seed {}):".format(COMMON_SEED))
    print(var_df[["Variant", "Cover_2050_Mean_Pct", "Cover_2050_CI_lo", "Cover_2050_CI_hi",
                  "Cover_diff_vs_S3_pp", "NetCarbonate_2050_Mean", "NetCarbonate_diff_vs_S3"]].to_string())

    # ---- 3. Shapley decomposition of the S4 - S3 gap -------------------------------------
    def shapley(metric_fn):
        n = len(names)
        phi = {}
        for f in names:
            others = [x for x in names if x != f]
            total = 0.0
            for r in range(len(others) + 1):
                for subset in itertools.combinations(others, r):
                    w = math.factorial(r) * math.factorial(n - r - 1) / math.factorial(n)
                    total += w * (metric_fn(res[key(subset + (f,))]) - metric_fn(res[key(subset)]))
            phi[f] = total
        return phi

    metrics = {
        "Cover_2050_pp": lambda o: float(o["cover"].mean()),
        "NetCarbonate_2050": lambda o: float(o["carb"].mean()),
    }
    full = key(tuple(names))
    sh_rows = []
    shap_summary = {}
    for mname, fn in metrics.items():
        phi = shapley(fn)
        gap = fn(res[full]) - fn(res[()])
        # Bootstrap CI of the Shapley values over Monte Carlo runs (paired resampling of runs)
        rng = np.random.default_rng(COMMON_SEED)
        B = 1000
        boots = {f: [] for f in names}
        arr = {k: (v["cover"] if mname.startswith("Cover") else v["carb"]) for k, v in res.items()}
        for _ in range(B):
            idx = rng.integers(0, N_SIM, N_SIM)
            sub = {k: float(a[idx].mean()) for k, a in arr.items()}
            for f in names:
                others = [x for x in names if x != f]
                tot = 0.0
                for r in range(len(others) + 1):
                    for subset in itertools.combinations(others, r):
                        w = math.factorial(r) * math.factorial(len(names) - r - 1) / math.factorial(len(names))
                        tot += w * (sub[key(subset + (f,))] - sub[key(subset)])
                boots[f].append(tot)
        shap_summary[mname] = {"gap": gap, "phi": phi}
        for f in names:
            lo, hi = np.percentile(boots[f], [2.5, 97.5])
            sh_rows.append({
                "Metric": mname,
                "Factor": f,
                "Shapley_contribution": round(phi[f], 2),
                "Shapley_CI_lo": round(float(lo), 2),
                "Shapley_CI_hi": round(float(hi), 2),
                "Share_of_gap_pct": round(100.0 * phi[f] / gap, 1),
                "Total_gap_S4_minus_S3": round(gap, 2),
                "Sum_of_Shapley": round(sum(phi.values()), 2),
            })
    sh_df = pd.DataFrame(sh_rows)
    sh_df.to_csv(os.path.join(RESULTS_DIR, "s4_factor_isolation_shapley.csv"), index=False)
    print("\nShapley decomposition of S4 - S3:")
    print(sh_df.to_string())

    # ---- 4. Seed robustness ----------------------------------------------------------------
    rob_rows = []
    for sd in ROBUSTNESS_SEEDS:
        r_ = factorial(sd) if sd != COMMON_SEED else res
        b = r_[()]
        for subset in [(), ("g",), ("Phi",), ("DHW",), ("Omega",),
                       key(("Phi", "DHW", "Omega")), key(("g", "DHW", "Omega")),
                       key(("g", "Phi", "Omega")), key(("g", "Phi", "DHW")), full]:
            o = r_[subset]
            rob_rows.append({
                "Seed": sd,
                "Factors_switched_to_S4": "+".join(subset) if subset else "none",
                "Cover_2050_Mean_Pct": round(float(o["cover"].mean()), 2),
                "Cover_diff_vs_S3_pp": round(float((o["cover"] - b["cover"]).mean()), 2),
                "NetCarbonate_2050_Mean": round(float(o["carb"].mean()), 2),
                "NetCarbonate_diff_vs_S3": round(float((o["carb"] - b["carb"]).mean()), 2),
            })
        # Shapley per seed for the record
        for mname, fn in metrics.items():
            n = len(names)
            for f in names:
                others = [x for x in names if x != f]
                tot = 0.0
                for r in range(len(others) + 1):
                    for subset in itertools.combinations(others, r):
                        w = math.factorial(r) * math.factorial(n - r - 1) / math.factorial(n)
                        tot += w * (fn(r_[key(subset + (f,))]) - fn(r_[key(subset)]))
                rob_rows.append({"Seed": sd, "Factors_switched_to_S4": f"SHAPLEY[{mname}]:{f}",
                                 "Cover_2050_Mean_Pct": np.nan, "Cover_diff_vs_S3_pp": round(tot, 2)
                                 if mname.startswith("Cover") else np.nan,
                                 "NetCarbonate_2050_Mean": np.nan,
                                 "NetCarbonate_diff_vs_S3": round(tot, 2) if mname.startswith("Net") else np.nan})
    rob_df = pd.DataFrame(rob_rows)
    rob_df.to_csv(os.path.join(RESULTS_DIR, "s4_factor_isolation_seed_robustness.csv"), index=False)
    print("\nSeed robustness:")
    print(rob_df.to_string())

    with open(os.path.join(RESULTS_DIR, "s4_factor_isolation_summary.json"), "w", encoding="utf-8") as f:
        json.dump({
            "n_monte_carlo": N_SIM, "dt_years": DT, "integrator": "RK4", "common_seed": COMMON_SEED,
            "baseline_coral_pct": c0, "baseline_macroalgae_pct": m0,
            "s3_params": {k: S3[k] for k in FACTORS.values()},
            "s4_params": {k: S4[k] for k in FACTORS.values()},
            "shapley": shap_summary,
        }, f, indent=2)


if __name__ == "__main__":
    main()
