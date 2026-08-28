# Research Objectives: CoralTwin-DT

## General Objective

Construir un gemelo digital de arrecife de coral de nivel doctoral que simule el blanqueamiento coralino, el crecimiento de corales, la biodiversidad y la dinámica ambiental abiótica para la priorización cuantitativa de acciones de restauración y conservación marina bajo escenarios de cambio climático global.

*(To engineer a doctoral-grade coral reef digital twin simulating bleaching dynamics, structural coral growth, benthic biodiversity, and abiotic oceanographic processes for quantitative spatial prioritization of restoration and conservation actions under global climate change scenarios).*

---

## Specific Objectives (SOs)

### Specific Objective 1: Integrated Biophysical-AI Hybrid Model
- **Description:** Formular e implementar un modelo computacional híbrido que acople la termodinámica del estrés térmico coralino, la química del carbonato oceánico y algoritmos avanzados de aprendizaje automático.
- **Key Deliverable:** Módulo de acoplamiento biofísico-computacional en `06_AI_and_Modeling/`.

### Specific Objective 2: Automated Environmental Data Ingestion & FAIR Harmonization
- **Description:** Diseñar e implementar un pipeline automatizado de adquisición, control de calidad, normalización espacial (500m / 5km) y temporal (semanal / mensual) de datos satelitales (NOAA CRW, Sentinel-2), atlas bentónicos (Allen Coral Atlas) y monitoreo in-situ (GCRMN).
- **Key Deliverable:** Pipeline ETL reproducible y repositorio de metadatos ISO 19115 en `03_Data/`.

### Specific Objective 3: Predictive Modeling of Coral Degradation & Bleaching Risk
- **Description:** Entrenar, calibrar y validar modelos de aprendizaje supervisado (Random Forest, XGBoost, Redes Neuronales MLP) para la clasificación probabilística del riesgo de blanqueamiento (`Bajo`, `Medio`, `Alto`) y regresión de pérdida de cobertura coralina ($\Delta C$), evaluados mediante validación cruzada espacial de 5 pliegues.
- **Key Deliverable:** Modelos entrenados, matrices de confusión, curvas ROC-AUC y análisis SHAP en `06_AI_and_Modeling/`.

### Specific Objective 4: Forward Scenario Simulation Engine (2025–2050)
- **Description:** Desarrollar un motor de simulación basado en ecuaciones diferenciales acopladas no lineales que proyecte la trayectoria de cobertura coralina, macroalgas y biodiversidad (Shannon $H'$) bajo 4 escenarios:
  1. *Estrés Térmico Severo (SSP5-8.5)*
  2. *Mitigación Climática Moderada (SSP2-4.5)*
  3. *Restauración Coralina Activa (Micro-fragmentación resistente)*
  4. *Áreas Marinas Protegidas (MPA) y Manejo Integrado.*
- **Key Deliverable:** Motor de simulación ODE y series temporales proyectadas en `07_Scenarios_and_Simulations/`.

### Specific Objective 5: Conceptual Decision-Support & Spatial Prioritization Tool
- **Description:** Diseñar un marco espacial multi-criterio que genere el Índice de Prioridad de Restauración Espacial (SRPI), mapas geoespaciales interactivos y un dashboard analítico para la toma de decisiones basada en evidencia.
- **Key Deliverable:** Salidas geoespaciales (GeoJSON), mapas de zonificación en `08_GIS_and_Remote_Sensing/` y mockup visual de dashboard en `09_Results/`.
