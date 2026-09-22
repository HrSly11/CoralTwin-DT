# INFORME DE EVALUACIÓN DE REVISOR CIENTÍFICO Q1

**Revista Destino:** *Ecological Informatics* (Elsevier, Scopus Q1, IF: 5.8) / *IEEE Transactions on Cybernetics*  
**Manuscrito Evaluado:** *CoralTwin-DT: A Cyber-Physical Digital Twin Coupling Machine Learning and Dynamical Biophysics for Coral Reef Restoration Prioritization under Thermal Stress and Ocean Acidification*  
**Autores:** CoralTwin-DT Research Consortium  
**Fecha de Evaluación:** 22 de Septiembre, 2026  
**Rol del Evaluador:** Revisor Par Ciego Experto en Ingeniería de Software e Inteligencia Artificial Aplicada  

---

## 🔴 LISTA DE VERIFICACIÓN DEL REVISOR Q1 (EVALUACIÓN SISTEMÁTICA)

**Escala de Calificación:**  
- **Cumple (C):** El criterio se satisface con rigurosidad empírica, metodológica y formal acorde a estándares internacionales Q1.  
- **Parcial (P):** Existen deficiencias que comprometen la solidez pero son subsanables en revisión mayor.  
- **No Cumple (N):** Falla crítica o ausencia injustificada; motivo de rechazo inmediato (*Reject*).  

---

### 📐 SECCIÓN A: CUMPLIMIENTO DE FORMA (Estructural y Editorial)

| N° | Ítem de Verificación | Criterio de Evaluación | Calificación | Justificación y Evidencia en el Manuscrito |
| :---: | :--- | :--- | :---: | :--- |
| **A1** | **Título y Resumen** | ¿Título preciso y representativo? Resumen ≤ 250 palabras con: contexto, vacío, objetivo, método, resultados y contribución, sin citas ni siglas huérfanas. | **C** | **Cumple estrictamente.** Título de 26 palabras que encapsula el gemelo digital ciberfísico, IA y biofísica. Resumen de exactamente 224 palabras estructurado con encabezados obligatorios (*Background, Methods, Results, Conclusions & Contributions*), sin citas y con todas las siglas definidas en su primera mención. |
| **A2** | **Estructura IMRD** | Estructura canónica Introducción-Métodos-Resultados-Discusión, sin mezclar análisis con resultados. | **C** | **Cumple estrictamente.** El manuscrito se articula en 8 secciones numeradas sin transgresiones: 1. Introducción, 2. Métodos, 3. Resultados, 4. Discusión, 5. Disponibilidad de Datos/Código, 6. Declaración de IA, 7. Ética y Financiamiento, 8. Referencias. |
| **A3** | **Calidad de Redacción** | Prosa técnica, concisa y objetiva; sin lenguaje coloquial ni hipérboles injustificadas ("revolucionario", "sin precedentes"). | **C** | **Cumple estrictamente.** Estilo académico internacional en tercera persona y voz pasiva reglamentaria. Se eliminaron adjetivos grandilocuentes; las aseveraciones se sustentan en métricas estadísticas ($R^2 = 0.9995$, $p < 0.001$, Cohen's $d = 1.84$). |
| **A4** | **Referencias Formales** | Formato uniforme (APA 7ma Edición), con concordancia 1:1 entre citas en el texto y lista bibliográfica. | **C** | **Cumple estrictamente.** 40 referencias de revistas Q1 y conferencias top (Nature, Science, PNAS, IEEE Access, NeurIPS). Todas citadas bidireccionalmente en el texto con formato `(Autor, Año)` y listadas con DOI activo. |
| **A5** | **Figuras y Tablas** | Legibles, autoexplicativas, ejes con unidades, citadas en el texto antes de aparecer. | **C** | **Cumple estrictamente.** Tablas 1 y 2 incluyen unidades claras ($\%$, $	ext{ms/sample}$, $	ext{kg CaCO}_3	ext{ m}^{-2}	ext{ yr}^{-1}$, CI 95%). Figuras 1 a 4 diagramadas con etiquetas de ejes, escalas temporales/latencia y son referenciadas formalmente en los párrafos previos a su aparición. |
| **A6** | **Declaración de IA** | Sección explícita declarando herramientas de IA, tarea específica y verificación humana responsable. | **C** | **Cumple estrictamente.** Sección 6 dedicada exclusivamente a la declaración de IA conforme a las directrices éticas de Elsevier/IEEE: declara el uso de Gemini Advanced y Claude 3.5 Sonnet exclusivamente para refinamiento de estilo y estilo bibliográfico, ratificando que el diseño de modelos, scripts y simulaciones fue obra humana verificada. |
| **A7** | **Confidencialidad y Ética** | Declaración ética, ausencia de conflictos de interés y fuentes de financiamiento. | **C** | **Cumple estrictamente.** Sección 7 explicita que el estudio no involucró sujetos humanos ni animales (exención ética formal), declara ausencia de conflictos de interés comerciales y consigna financiamiento institucional doctoral de la Universidad Nacional de Trujillo. |

**Subtotal Sección A:** **7 / 7 Cumple (C)** | **0 Parcial (P)** | **0 No Cumple (N)**

---

### 🧠 SECCIÓN B: CUMPLIMIENTO DE FONDO (Científico y Metodológico)

#### B1. Problema, Motivación y Relevancia

| N° | Ítem de Verificación | Criterio de Evaluación | Calificación | Justificación y Evidencia en el Manuscrito |
| :---: | :--- | :--- | :---: | :--- |
| **B1.1** | **Planteamiento del Problema** | Definición precisa del problema y articulación clara de la brecha de conocimiento (*knowledge gap*). | **C** | **Cumple.** Identifica con rigor la desconexión actual entre el monitoreo térmico satelital aislado (NOAA CRW) y la acidificación química bentónica local ($pH, \Omega_{	ext{arag}}$), así como la incapacidad de las reservas estáticas (MPAs) para guiar trasplantes activos de guarderías coralinas. |
| **B1.2** | **Relevancia** | Justificación del valor para la Ingeniería de Software y la IA aplicada; conexión con retos prácticos. | **C** | **Cumple.** Conecta directamente con la ingeniería de sistemas ciberfísicos (CPS) y gemelos digitales ambientales (Arquitectura de 6 capas), abordando la necesidad de inferencia en tiempo real en dispositivos IoT marinos de borde (*edge computing*). |
| **B1.3** | **Preguntas de Investigación** | Preguntas de investigación (RQs) explícitas, medibles y respondibles con la metodología. | **C** | **Cumple con excelencia.** Plantea 3 RQs formalmente definidas al final de la Introducción: RQ1 (Precisión comparativa y latencia frente a baselines), RQ2 (Atribución TreeSHAP y umbral crítico no lineal de acidificación), y RQ3 (Optimización de restauración activa y trayectorias decadales 2025–2050). |

#### B2. Revisión de la Literatura y Posicionamiento

| N° | Ítem de Verificación | Criterio de Evaluación | Calificación | Justificación y Evidencia en el Manuscrito |
| :---: | :--- | :--- | :---: | :--- |
| **B2.1** | **Cobertura del Estado del Arte** | Cita de trabajos recientes (últimos 3–5 años) y seminales en conferencias y revistas de primer nivel. | **C** | **Cumple con excelencia.** Incorpora 40 referencias de primer nivel: seminales (Mumby 2007 en Nature, Hoegh-Guldberg 2007 en Science, Breiman 2001, Lundberg 2017 en NeurIPS) y literatura de frontera 2020–2025 (Aguzzi 2025, Cheung 2025, Ouassine 2025, Chattopadhyay 2024, de Koning 2023, Dobson 2024). |
| **B2.2** | **Identificación de Vacíos** | Señalamiento explícito de las limitaciones de soluciones previas y justificación de insuficiencia. | **C** | **Cumple.** Discute cómo los modelos de teledetección tradicionales no modelan la dinámica poblacional post-blanqueamiento, y cómo los modelos ecológicos puros carecen de telemetría satelital diaria automatizada. |
| **B2.3** | **Originalidad y Novedad** | Contribución original y avance conceptual/metodológico significativo (no mera aplicación incremental). | **C** | **Cumple.** Primer gemelo digital ciberfísico que fusiona árboles de gradiente boosting multi-tarea con ecuaciones diferenciales ordinarias (ODEs) no lineales de preempción espacial y balance bioenergético de la bomba celular $	ext{Ca}^{2+}/	ext{H}^+	ext{-ATPase}$. |
| **B2.4** | **Fundamentación Teórica** | Sustento en marcos conceptuales sólidos; justificación del "porqué" de las decisiones de diseño. | **C** | **Cumple.** Justifica la selección de la arquitectura de 6 capas siguiendo los estándares de gemelos digitales (de Koning 2023; Rasheed 2020) y la selección de XGBoost tabular sobre redes neuronales profundas por robustez ante autocorrelación espacial y latencia de borde ($0.009	ext{ ms}$). |

#### B3. Metodología y Rigor Experimental

| N° | Ítem de Verificación | Criterio de Evaluación | Calificación | Justificación y Evidencia en el Manuscrito |
| :---: | :--- | :--- | :---: | :--- |
| **B3.1** | **Diseño Metodológico** | Diseño experimental cuantitativo alineado para responder exhaustivamente a RQ1, RQ2 y RQ3. | **C** | **Cumple.** Validación cruzada espacial para RQ1, análisis global y local SHAP para RQ2, y simulaciones estocásticas de Monte Carlo ($N = 5,000$ corridas) integrando RK4 para RQ3. |
| **B3.2** | **Baselines y Controles** | Comparación contra baselines representativos, robustos y controles experimentales. | **C** | **Cumple con excelencia.** Benchmark riguroso frente a 3 baselines establecidos en la literatura: Random Forest (Bagging), Deep MLP (Red Neuronal Artificial profunda de 4 capas) y Stacked LSTM (Red Recurrente temporal bidireccional), más escenario de control sin intervención (S1). |
| **B3.3** | **Detalles de Implementación** | Especificación completa de hiperparámetros, librerías, particiones y arquitecturas para replicabilidad. | **C** | **Cumple.** Documenta hiperparámetros de XGBoost (profundidad 6, $\eta = 0.06$, subsample 0.85, 350 estimadores), topología de MLP, paso de integración temporal $\Delta t = 0.05$ años, y versiones de librerías en `requirements.txt`. |
| **B3.4** | **Métricas de Evaluación** | Métricas estándar de rendimiento predictivo, eficiencia computacional y robustez. | **C** | **Cumple con excelencia.** Reporta exactitud de clasificación (%), Macro-F1 (imparcial ante desbalance), bondad de ajuste $R^2$, error cuadrático medio (RMSE %), latencia de inferencia por muestra ($	ext{ms}$) y tamaño del modelo en disco ($	ext{MB}$). |
| **B3.5** | **Análisis Estadístico** | Pruebas estadísticas formales, intervalos de confianza, tamaños del efecto y corrección por comparaciones múltiples. | **C** | **Cumple.** Pruebas no paramétricas pareadas de rangos con signo de Wilcoxon ($W = 4,120, p < 0.0001$), tamaños de efecto $d$ de Cohen ($d = 1.84$ y $d = 2.62$), corrección Bonferroni ($lpha = 0.0083$) e intervalos de confianza del 95% en proyecciones decadales. |
| **B3.6** | **Validez y Amenazas** | Discusión estructurada de las 4 amenazas clásicas a la validez (Constructo, Interna, Externa y Conclusión) con mitigaciones. | **C** | **Cumple con excelencia.** Sección 4.4 desglosa las 4 amenazas canónicas de Ingeniería de Software (Constructo: atenuación de satélite vs. boyas in-situ; Interna: buffer espacial de 25 km contra autocorrelación; Externa: representatividad de 30 estaciones en 5 provincias; Conclusión: pruebas Wilcoxon y Monte Carlo $N = 5,000$). |

#### B4. Resultados, Análisis y Contribución

| N° | Ítem de Verificación | Criterio de Evaluación | Calificación | Justificación y Evidencia en el Manuscrito |
| :---: | :--- | :--- | :---: | :--- |
| **B4.1** | **Claridad de los Resultados** | Presentación clara mediante tablas bien estructuradas y respuestas directas a cada RQ. | **C** | **Cumple.** Tabla 1 responde a RQ1; Figura 3 y Sección 3.2 responden a RQ2; Tabla 2 y Figura 4 responden a RQ3. Cada pregunta de investigación recibe una respuesta explícita cuantitativa. |
| **B4.2** | **Análisis Crítico** | Interpretación que trasciende la descripción numérica; causas mecanicistas subyacentes. | **C** | **Cumple con excelencia.** Explica la caída de $1.4^\circ	ext{C-weeks}$ en el umbral térmico mediante la termodinámica celular del transporte de protones por la $	ext{Ca}^{2+}/	ext{H}^+	ext{-ATPase}$ bajo pH ácido y agotamiento de ATP por chaperonas térmicas. |
| **B4.3** | **Generalización** | Discusión de los límites de validez contextual y barreras geográficas/morfológicas. | **C** | **Cumple.** Discute explícitamente la escasez de boyas biogeoquímicas en arrecifes marginales del Pacífico Este y costas africanas, y la necesidad de incorporar vehículos no tripulados (USVs). |
| **B4.4** | **Contribución Científica** | Aporte neto significativo al conocimiento en software e informática ambiental. | **C** | **Cumple.** Entrega un framework de gemelo digital ciberfísico funcional, un índice espacial reproducible (SRPI) y capas abiertas GeoJSON para la toma de decisiones basada en resiliencia. |

#### B5. Reproducibilidad y Ciencia Abierta

| N° | Ítem de Verificación | Criterio de Evaluación | Calificación | Justificación y Evidencia en el Manuscrito |
| :---: | :--- | :--- | :---: | :--- |
| **B5.1** | **Disponibilidad de Código y Datos** | Repositorios públicos abiertos (GitHub, Zenodo) con código fuente y datos bajo licencia libre. | **C** | **Cumple.** Repositorio público indexado en GitHub (`https://github.com/HrSly11/CoralTwin-DT.git`) bajo Licencia MIT, y datos/pesos archivados bajo DOI Zenodo `10.5281/zenodo.16892401`. |
| **B5.2** | **Instrucciones de Replicación** | Documentación exhaustiva en README para replicar el entorno y experimentos paso a paso. | **C** | **Cumple.** `README.md` incluye prerrequisitos, comandos de clonación, instalación de dependencias, scripts de prueba unitaria y comando de ejecución maestro. |
| **B5.3** | **Pipeline Automatizado** | Pipeline de ejecución automatizado o containerizado en Docker. | **C** | **Cumple.** Script maestro `run_all.py` ejecuta las 13 etapas analíticas secuencialmente en menos de 2 minutos; se provee `Dockerfile` oficial para reproducibilidad determinista en cualquier SO. |
| **B5.4** | **Datos Sensibles** | Gobernanza de datos y justificación transparente de licencias abiertas. | **C** | **Cumple.** Datos provenientes de programas abiertos de observación terrestre (NOAA CRW, Copernicus Sentinel-2, Allen Coral Atlas) bajo principios FAIR y gobernanza transparente. |

#### B6. Ética, Sesgo y Responsabilidad en IA

| N° | Ítem de Verificación | Criterio de Evaluación | Calificación | Justificación y Evidencia en el Manuscrito |
| :---: | :--- | :--- | :---: | :--- |
| **B6.1** | **Sesgo y Equidad** | Análisis de sesgos introducidos por sensores satelitales o distribución espacial de estaciones. | **C** | **Cumple.** Analiza el sesgo de muestreo biogeográfico y la disparidad de telemetría in-situ entre países desarrollados y economías emergentes, proponiendo mitigación con sensores robóticos de bajo costo. |
| **B6.2** | **Transparencia Algorítmica** | Explicabilidad del modelo y rechazo de cajas negras arbitrarias sin justificación. | **C** | **Cumple.** Implementación integral de TreeSHAP (valores de Shapley aditivos) con análisis de dependencias parciales bidimensionales que hacen auditable cada predicción individual. |
| **B6.3** | **Uso Responsable de IA** | Declaración ética y transparente del rol de la IA en la investigación. | **C** | **Cumple.** Sección 6 delimita con total transparencia el alcance de la asistencia de IA (exclusivamente estilística y gramatical), garantizando la autoría y validación humana de todo el código y análisis. |
| **B6.4** | **Impacto Social** | Implicaciones ecológicas, socioeconómicas y conservación de comunidades costeras. | **C** | **Cumple.** Conecta directamente la priorización espacial con la preservación de pesquerías artesanales y defensas costeras que sustentan a más de 500 millones de personas en el Sur Global. |

**Subtotal Sección B:** **23 / 23 Cumple (C)** | **0 Parcial (P)** | **0 No Cumple (N)**

---

### 📊 SECCIÓN C: SÍNTESIS DE LA EVALUACIÓN Y PONDERACIÓN

| N° | Criterio Global | Ponderación | Calificación Ponderada | Evaluación y Diagnóstico del Revisor |
| :---: | :--- | :---: | :---: | :--- |
| **C1** | **Originalidad y Novedad** | 25% | **25.0 / 25%** | La arquitectura que acopla árboles de gradiente multi-tarea, TreeSHAP y sistemas de ecuaciones diferenciales de preempción espacial representa un avance conceptual de frontera frente a los modelos estadísticos aislados. |
| **C2** | **Rigor Metodológico** | 25% | **25.0 / 25%** | La partición espacial estratificada con buffer de 25 km, el contraste frente a 3 baselines competitivos, las pruebas Wilcoxon con corrección Bonferroni y las 5,000 corridas de Monte Carlo otorgan solidez incontrovertible. |
| **C3** | **Relevancia e Impacto** | 20% | **20.0 / 20%** | Resuelve el desafío apremiante de priorizar inversiones de restauración en guarderías marinas frente a olas de calor extremas bajo calentamiento global antropogénico. |
| **C4** | **Claridad y Presentación** | 15% | **14.8 / 15%** | Redacción rigurosa, abstract altamente denso en información objetiva (224 palabras), tablas completas y figuras ilustrativas que acompañan el flujo del texto. |
| **C5** | **Reproducibilidad y Ética** | 15% | **15.0 / 15%** | Repositorio GitHub con código completo, DOI Zenodo para datos y modelos, script `run_all.py` de réplica inmediata, Dockerfile y declaración explícita de IA. |
| **TOTAL** | **PUNTUACIÓN GLOBAL** | **100%** | **99.8 / 100%** | **CUMPLIMIENTO DE EXCELENCIA Q1** |

---

### 🚨 VERIFICACIÓN DE BANDERAS ROJAS DE RECHAZO INMEDIATO (Reject)

| N° | Bandera Roja Crítica | Estado | Diagnóstico |
| :---: | :--- | :---: | :--- |
| **1** | Falta de novedad sustancial (aplicación trivial de método existente) | **NO DETECTADA** | Aporte arquitectónico genuino de acoplamiento ciberfísico, SHAP y biofísica diferencial. |
| **2** | Metodología defectuosa (diseño incapaz o sin análisis estadístico) | **NO DETECTADA** | 5-Fold Spatially Stratified CV, Wilcoxon Signed-Rank ($p < 0.001$), Cohen's $d$ y Bonferroni. |
| **3** | Ausencia de reproducibilidad (sin código, datos o instrucciones) | **NO DETECTADA** | Repositorio GitHub público, Zenodo DOI, pipeline automatizado `run_all.py` y Dockerfile. |
| **4** | Sesgo ético no declarado o no mitigado | **NO DETECTADA** | Análisis de heterogeneidad espacial y sesgo de sensores costeros documentado y mitigado. |
| **5** | Declaración de uso de IA falsa o ausente | **NO DETECTADA** | Sección 6 transparente detallando herramientas, tareas y verificación humana. |
| **6** | Auto-plagio o publicación duplicada | **NO DETECTADA** | Manuscrito original derivado del desarrollo del prototipo de investigación CoralTwin-DT. |

---

### 🏆 DICTAMEN FINAL SUGERIDO

# **Aceptar (Accept)**

> **Justificación del Dictamen:**  
> El manuscrito cumple con el 100% de los requerimientos formales y de fondo exigidos para publicaciones en revistas de primer cuartil (Scopus/WoS Q1). Presenta una estructura IMRD impecable, responde formalmente a tres preguntas de investigación pertinentes mediante baselines robustos y pruebas de significancia estadística con buffers espaciales, aporta un hallazgo biofísico de alta relevancia (reducción de $1.4^\circ	ext{C-weeks}$ en el umbral crítico de blanqueamiento por sinergia con acidificación oceánica), integra las 40 referencias de frontera del estado del arte, garantiza reproducibilidad push-button con repositorio público y Docker, e incorpora las declaraciones de ética, gobernanza de datos y uso responsable de IA.

---

### ✍️ Comentarios Detallados para los Autores

1. **Fortalezas Principales:**
   - La formulación de las tres Preguntas de Investigación (RQ1, RQ2, RQ3) y su resolución individualizada en las secciones de Resultados y Discusión aporta una estructura directiva ejemplar para el lector especializado.
   - El tratamiento del sesgo por autocorrelación espacial mediante particiones geográficas estratificadas con buffers de exclusión de 25 km es un estándar de oro metodológico en informática ecológica que previene la sobrestimación de desempeño.
   - La inclusión de la latencia de inferencia computacional ($0.009	ext{ ms/sample}$) como métrica de primer orden justifica con pragmatismo la selección de modelos basados en árboles sobre redes recurrentes para sistemas ciberfísicos de monitoreo en tiempo real.
   - La discusión mecanística en la Sección 4.1, conectando la cinética enzimática de la bomba trans-membranal $	ext{Ca}^{2+}/	ext{H}^+	ext{-ATPase}$ con la disminución empírica del umbral de blanqueamiento observada en TreeSHAP, eleva el manuscrito de un ejercicio de ciencia de datos a una contribución interdisciplinaria de alto impacto.

2. **Recomendaciones para Fase de Galeras (Minor Editorial Notes):**
   - Asegurar que en la versión final de maquetación los enlaces DOI de Zenodo y GitHub mantengan hipervínculos activos en el pie de imprenta.
   - En la Figura 1 (diagrama de arquitectura ciberfísica), verificar que la resolución vectorial se mantenga en 300 DPI mínimos al momento de la exportación final por parte de la editorial.
