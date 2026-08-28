# Satellite Processing & Remote Sensing Workflows

## 1. Copernicus Sentinel-2 MSI Atmospheric Correction & Water Column Unmixing

- **Atmospheric Correction:** Processed via ACOLITE (Dark Spectrum Fitting) to isolate shallow water surface reflectance ($R_{rs}(\lambda)$).
- **Water Column Correction:** Lyzenga (1981) depth-invariant bottom-reflectance indices computed between Blue ($490\text{ nm}$) and Green ($560\text{ nm}$) bands:
  $$Y_{ij} = \ln(R_{rs}(\lambda_i)) - \frac{k_i}{k_j} \ln(R_{rs}(\lambda_j))$$
- **Turbidity Inversion ($K_d(490)$):** Diffuse attenuation coefficient extracted to estimate optical shading depth.

---

## 2. NOAA Coral Reef Watch (CRW) Operational Gridding

- Daily Level-3 SST products mapped onto bilinear interpolated $500\text{m}$ coastal grids.
- Rolling 84-day accumulation windows calculating $DHW$ and Bleaching Alert Area ($BAA$) operational alert levels (No Stress, Watch, Warning, Alert Level 1, Alert Level 2).
