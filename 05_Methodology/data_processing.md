# Data Processing & Harmonization Pipeline: CoralTwin-DT

## 1. Multi-Source Ingestion & Spatial Resampling

The harmonization pipeline unifies heterogenous raster, vector, and point-source data into a standardized spatio-temporal matrix.

### Mathematical Resampling Pipeline:
For continuous raster feeds ($SST$, $K_d$, bathymetry), bilinear spatial interpolation maps raw cell values to a target $500\text{m}$ grid:
$$V(x, y) = \sum_{i=1}^2 \sum_{j=1}^2 w_{ij} V(x_i, y_j), \quad \sum w_{ij} = 1$$

Categorical benthic classes from the Allen Coral Atlas are aggregated via majority focal statistics within each target cell:
$$\text{BenthicClass}(x, y) = \operatorname{mode}\left(\{B(u, v) \mid (u, v) \in \mathcal{N}_{500\text{m}}(x, y)\}\right)$$

---

## 2. Feature Engineering & Oceanographic Index Calculation

1. **Sea Surface Temperature Anomaly ($SSTA$):**
   $$SSTA(t) = SST(t) - \overline{SST}_{\text{clim}}(\text{month}(t))$$
2. **Degree Heating Weeks ($DHW$):**
   $$DHW(t) = \frac{1}{7} \sum_{k=0}^{83} \max(SST(t-k) - MMM, 0) \cdot \mathbb{I}(SST(t-k) - MMM \ge 1.0)$$
3. **Aragonite Saturation State ($\Omega_{\text{arag}}$):**
   $$\Omega_{\text{arag}} \approx 10^{-0.015 \cdot (SST - 25)} \cdot \left( \frac{10^{-\text{pH}}}{10^{-8.1}} \right)^{-0.85} \cdot 3.85$$
4. **Diffuse Optical Attenuation ($K_d(490)$) from Sentinel-2:**
   $$K_d(490) = 0.0166 + 0.078 \cdot \left(\frac{R_{rs}(490)}{R_{rs}(560)}\right)^{-1.24}$$
5. **Shannon Diversity Index ($H'$):**
   $$H' = - \sum_{i=1}^S p_i \ln(p_i)$$
   Where $p_i$ is the relative benthic abundance of coral species/morphotypes.
