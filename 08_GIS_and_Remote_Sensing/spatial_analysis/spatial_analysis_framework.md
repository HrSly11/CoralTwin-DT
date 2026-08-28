# Spatial Analysis & Multi-Criteria Prioritization Framework

## 1. Multi-Criteria Evaluation (MCE) Mathematical Formulation

The Spatial Restoration Priority Index ($\text{SRPI}$) integrates four orthogonal ecological criteria:

$$\text{SRPI}(s) = \sum_{k=1}^4 w_k \cdot f_k(s), \quad \sum_{k=1}^4 w_k = 1.0$$

Where:
1. $f_1(s) = 1 - \frac{\overline{DHW}(s) - \min(DHW)}{\max(DHW) - \min(DHW)}$: **Thermal Refugia Potential** ($w_1 = 0.35$).
2. $f_2(s) = \frac{\Delta C(s) - \min(\Delta C)}{\max(\Delta C) - \min(\Delta C)}$: **Ecological Restoration Urgency** ($w_2 = 0.25$).
3. $f_3(s) = \frac{R(s) - \min(R)}{\max(R) - \min(R)}$: **Structural Benthic Rugosity Viability** ($w_3 = 0.25$).
4. $f_4(s) = 1 - \frac{\text{Turb}(s) - \min(\text{Turb})}{\max(\text{Turb}) - \min(\text{Turb})}$: **Optical Water Quality & Hydrodynamic Flushing** ($w_4 = 0.15$).

---

## 2. Priority Tier Stratification

- **Tier 1 (High-Priority Active Restoration):** Top $25\%$ of SRPI values ($\text{SRPI} \ge 0.68$). Targeted for immediate micro-fragment outplanting and larval seeding.
- **Tier 2 (Secondary Conservation & Monitoring):** Interquartile range ($0.45 \le \text{SRPI} < 0.68$). Managed through MPA fishing closures and water quality mitigation.
- **Tier 3 (Baseline Monitoring & Passive Resilience):** Lower $40\%$ ($\text{SRPI} < 0.45$). Subject to long-term passive surveillance.
