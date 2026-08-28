# Uncertainty Quantification & Sensitivity Analysis: CoralTwin-DT

## 1. Sources of Epistemic & Aleatoric Uncertainty

```
+-------------------------------------------------------------------------------+
|                       UNCERTAINTY TAXONOMY IN CORALTWIN-DT                   |
+-------------------------------------------------------------------------------+
| 1. Aleatoric (Environmental Stochasticity)                                    |
|    - Interannual MHW frequency variance, cyclone frequency, storm surges     |
| 2. Epistemic (Model Parameter Uncertainty)                                    |
|    - Grazing rate g, thermal tolerance slope alpha, baseline mortality d_0   |
| 3. Observational & Measurement Error                                          |
|    - Sentinel-2 bottom-reflectance unmixing, satellite SST sensor noise       |
+-------------------------------------------------------------------------------+
```

---

## 2. Monte Carlo Simulation Engine ($N = 10,000$)

To quantify prediction intervals on projected coral cover $C(t)$ from 2025 to 2050, parameters are sampled from empirically bounded probability distributions:

$$\theta \sim \begin{cases}
g \sim \mathcal{U}(0.35, 0.65) & \text{Grazing capacity} \\
r \sim \mathcal{N}(0.10, 0.015^2) & \text{Coral lateral growth rate} \\
\alpha \sim \mathcal{Lognormal}(-2.3, 0.25^2) & \text{Thermal bleaching sensitivity} \\
\Omega_{\text{crit}} \sim \mathcal{N}(2.80, 0.10^2) & \text{Aragonite dissolution threshold}
\end{cases}$$

At each time step $t$, the $95\%$ credible envelope is extracted via the empirical percentiles:
$$C_{95\% \text{ CI}}(t) = \left[ Q_{0.025}\left(\{C_k(t)\}_{k=1}^N\right), \, Q_{0.975}\left(\{C_k(t)\}_{k=1}^N\right) \right]$$

---

## 3. Global Sensitivity Analysis (Sobol Indices)

Variance-based global sensitivity analysis decomposes output variance $V(Y)$ into fractional contributions from individual parameters:
$$S_i = \frac{V_i}{V(Y)} = \frac{V_{\theta_i}(E_{\theta_{\sim i}}[Y \mid \theta_i])}{V(Y)}$$
$$S_{T_i} = 1 - \frac{V_{\theta_{\sim i}}(E_{\theta_i}[Y \mid \theta_{\sim i}])}{V(Y)}$$

Where $S_i$ is the first-order Sobol index and $S_{T_i}$ is the total-order index including all non-linear interactions.
