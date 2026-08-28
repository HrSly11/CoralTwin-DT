# Theoretical & Biophysical Framework: CoralTwin-DT

## 1. Biophysical Foundations of Coral Reef Ecosystems

```
                      +-----------------------------+
                      |   Incident Solar PAR & SST  |
                      +-----------------------------+
                                     |
                                     v
+-----------------------+   Photoinhibition   +-----------------------+
|   Symbiodiniaceae     | ------------------> |   Reactive Oxygen     |
|   Photosystem II      |                     |   Species (ROS)       |
+-----------------------+                     +-----------------------+
            |                                             |
   Disruption of Translocation                   Cellular Apoptosis / Expulsion
            |                                             |
            +---------------------->+<--------------------+
                                    |
                                    v
                      +-----------------------------+
                      |   Coral Bleaching & State   |
                      |   Shift to Macroalgae       |
                      +-----------------------------+
```

### 1.1 Thermal Stress & Degree Heating Weeks (DHW)
Accumulated heat stress is parameterized using the NOAA Coral Reef Watch (CRW) operational formulation. The Maximum Monthly Mean ($MMM$) climatology represents the warmest baseline monthly average. The coral bleaching threshold is defined as $MMM + 1.0^\circ\text{C}$.

The Thermal Stress Anomaly ($HotSpot$) at day $t$ is formulated as:
$$\text{HotSpot}(t) = \max\left(SST(t) - MMM, \, 0\right)$$

Accumulated thermal stress over a rolling 12-week (84-day) window is computed as:
$$DHW(t) = \frac{1}{7} \sum_{i=0}^{83} \text{HotSpot}(t - i) \cdot \mathbb{I}\left(\text{HotSpot}(t - i) \ge 1.0^\circ\text{C}\right) \quad [^\circ\text{C-weeks}]$$

Ecological threshold classifications:
- $DHW < 4^\circ\text{C-weeks}$: No significant bleaching risk (`Low`).
- $4 \le DHW < 8^\circ\text{C-weeks}$: Moderate bleaching risk (`Medium`); partial colony bleaching.
- $DHW \ge 8^\circ\text{C-weeks}$: Severe bleaching risk (`High`); widespread mortality and structural breakdown.

---

### 1.2 Ocean Acidification & Carbonate System Dynamics
Dissolved inorganic carbon ($DIC$) speciation governs the availability of carbonate ions ($[\text{CO}_3^{2-}]$) required for scleractinian calcification:
$$\text{CO}_2(\text{aq}) + \text{H}_2\text{O} \rightleftharpoons \text{H}_2\text{CO}_3 \rightleftharpoons \text{HCO}_3^- + \text{H}^+ \rightleftharpoons \text{CO}_3^{2-} + 2\text{H}^+$$

The aragonite saturation state ($\Omega_{\text{arag}}$) is defined as:
$$\Omega_{\text{arag}} = \frac{[\text{Ca}^{2+}] [\text{CO}_3^{2-}]}{K'_{\text{sp}}(\text{arag})}$$

Where $K'_{\text{sp}}(\text{arag})$ is the stoichiometric solubility product at local temperature, salinity, and hydrostatic pressure. Net reef calcification ($G_{\text{net}}$) responds non-linearly to $\Omega_{\text{arag}}$ and thermal stress:
$$G_{\text{net}} = G_0 \cdot \left( \frac{\Omega_{\text{arag}} - 1}{\Omega_0 - 1} \right)^{\eta} \cdot \exp\left( - \kappa \cdot DHW \right) - E_{\text{bioerosion}}$$

Where $\eta \approx 1.1 - 1.4$ is the calcification sensitivity exponent and $E_{\text{bioerosion}}$ represents chemical and biological dissolution by endolithic microborers and sponges.

---

### 1.3 Dynamical Coral-Macroalgae Competition Model
Building upon the non-linear dynamical systems framework of Mumby, Hastings & Edwards (2007), the fractional benthic cover of live coral ($C$), macroalgae ($M$), and grazed algal turf/crustose coralline algae ($T = 1 - C - M$) is modeled via coupled differential equations:

$$\frac{dC}{dt} = r C T - d(DHW, \Omega_{\text{arag}}) C + \Phi_{\text{restoration}}$$

$$\frac{dM}{dt} = a M T - \frac{g(H_{\text{MPA}}) M}{M + T} + \gamma M C$$

Where:
- $r$: Intrinsic coral lateral recruitment and growth rate ($0.10 \text{ yr}^{-1}$).
- $d(DHW, \Omega_{\text{arag}}) = d_0 + \alpha \frac{DHW^2}{1 + \beta \Omega_{\text{arag}}}$: Compounded mortality function.
- $a$: Macroalgae colonization rate onto bare substrate ($0.55 \text{ yr}^{-1}$).
- $g(H_{\text{MPA}})$: Herbivory grazing capacity modulated by Marine Protected Area enforcement ($0.20 - 0.70 \text{ yr}^{-1}$).
- $\gamma$: Overgrowth rate of living coral by macroalgal fronds ($0.15 \text{ yr}^{-1}$).
- $\Phi_{\text{restoration}}$: Active intervention seeding rate ($\text{fraction yr}^{-1}$).

---

## 2. Digital Twin Cyber-Physical Paradigm

A digital twin is a multi-physics, multiscale, probabilistic digital counterpart of an evolving physical system (Grieves 2014; Rasheed et al. 2020). For marine ecosystems, CoralTwin-DT implements a bidirectional cyber-physical coupling:

1. **Physical Reef Space:** Oceanographic telemetry (buoys, satellite constellations, benthic transects).
2. **Digital Twin Space:** High-fidelity data assimilation, hybrid physics-AI state estimation, and forward Monte Carlo scenario projection.
3. **Decision & Actuation Space:** Targeted micro-fragment outplanting, enforcement of spatial fishing moratoria, and proactive intervention scheduling prior to forecasted heatwaves.
