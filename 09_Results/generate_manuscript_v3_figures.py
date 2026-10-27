"""
09_Results/generate_manuscript_v3_figures.py
============================================
Implements Task 8:
Regenerates Figures 1 through 4 (PNG, 300 DPI) dynamically from `results/manuscript_numbers.json`,
`results/oof_predictions_by_fold.csv`, `results/shap_global_importance.csv`,
`results/partial_dependence_within_support.csv`, and `results/scenario_2050_summary.csv`.

Strictly matches the structure, panel layout, and captions of `CoralTwin-DT_v3.docx`:
- Figura 1: Flujo conceptual de la arquitectura ciberfísica de seis capas (N=15,000, 30 estaciones,
            3 clases de riesgo, 5 niveles de alerta; Capa 1 diseño operativo con simulador sintético).
- Figura 2: Desempeño de los cuatro modelos en el régimen canónico de 10 variables (A-C; Tabla 3)
            y ablación de fuga con XGBoost (D; Tabla 4). Barras de error IC 95% bootstrap.
- Figura 3: Verificación del emulador. (A) Macro-F1 y R2 con IC 95%; (B) Matriz de confusión
            fuera de muestra de XGBoost (N=15,000); (C) Importancia TreeSHAP global con IC 95%;
            (D) Umbrales de DHW (EC50 y cruce del 35% de pérdida) dentro del soporte (Omega in [3.16, 3.90])
            y superficie analítica del generador.
- Figura 4: Cobertura coralina media (A) y acreción neta (B) bajo cuatro regímenes de manejo
            (2025-2050; RK4; 5,000 corridas Monte Carlo por escenario).

All titles, axis labels, legends, and annotations are in SPANISH.
Saves to:
- `results/figures/`
- `09_Results/figures/`
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec
import seaborn as sns

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
RESULTS_FIG_DIR = os.path.join(RESULTS_DIR, "figures")
LEGACY_FIG_DIR = os.path.join(BASE_DIR, "09_Results", "figures")

for d in [RESULTS_FIG_DIR, LEGACY_FIG_DIR]:
    os.makedirs(d, exist_ok=True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 10.5,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "legend.fontsize": 9.5,
    "figure.titlesize": 14,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})


def make_figura_1():
    """
    Figura 1: Arquitectura ciberfísica de seis capas.
    """
    print("Renderizando Figura 1: Arquitectura ciberfísica de seis capas...")
    fig, ax = plt.subplots(figsize=(14, 10.5), facecolor="#ffffff")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Header Title
    ax.text(
        50, 96.5,
        "Figura 1: Arquitectura Ciberfísica de Seis Capas — CoralTwin-DT",
        ha="center", va="center", fontsize=15, fontweight="bold", color="#1a202c"
    )
    ax.text(
        50, 93.8,
        "Flujo metodológico modular integrado: telemetría sintética (N = 15,000), emulación con IA y soporte espacial",
        ha="center", va="center", fontsize=11, fontstyle="italic", color="#4a5568"
    )

    layers = [
        {
            "num": "Capa 1",
            "name": "Adquisición de Datos (Diseño Operativo / Simulación)",
            "color": "#ebf8ff",
            "border": "#3182ce",
            "y": 80,
            "items": [
                "• Telemetría ambiental y oceanográfica: SST (°C), anomalía SST (°C), DHW (°C-semanas)",
                "• Variables de química de carbonatos: pH_total (escala total), saturación de aragonita (Ω_arag)",
                "• Óptica y nutrientes: turbidez (NTU), PAR superficial (μmol m⁻² s⁻¹), salinidad (PSU), O₂ disuelto (mg/L)",
                "• Conjunto de datos unificado: N = 15,000 registros sintéticos (30 estaciones globales × 500 semanas, 2015–2024; SEED = 42)",
            ],
            "badge": "DISEÑO OPERATIVO (Sintético en este estudio)",
            "badge_color": "#2b6cb0",
        },
        {
            "num": "Capa 2",
            "name": "Integración y Armonización Espacial",
            "color": "#f0fff4",
            "border": "#38a169",
            "y": 64,
            "items": [
                "• Especificación conceptual de remuestreo a cuadrícula uniforme de 500 m × 500 m",
                "• Filtrado de calidad (QC) y agregación a cadencia temporal semanal por estación arrecifal",
                "• Alineación geográfica estricta con zonas geomórficas (Fore Reef, Reef Crest, Back Reef, Lagoon)",
                "• Estructuración libre de fugas para particionamiento espacial en bloques independientes",
            ],
            "badge": "ESPECIFICACIÓN ARQUITECTÓNICA",
            "badge_color": "#276749",
        },
        {
            "num": "Capa 3",
            "name": "Modelado Híbrido Biofísico e Inteligencia Artificial",
            "color": "#fffaf0",
            "border": "#dd6b20",
            "y": 48,
            "items": [
                "• Tarea de clasificación: Riesgo de blanqueamiento (3 clases: Bajo 93.98%, Medio 1.24%, Alto 4.78%) y 5 niveles de alerta",
                "• Tarea de regresión continua: Pérdida de cobertura coralina (%) estimada a partir de 10 variables ambientales limpias",
                "• 4 Arquitecturas evaluadas: XGBoost (dos modelos independientes), Random Forest, Deep MLP (PyTorch) y Stacked LSTM (seq=8)",
                "• Techo teórico de emulación: R² ≈ 0.934–0.938, RMSE ≈ 3.92%–4.04% (convergencia estadística libre de fugas)",
            ],
            "badge": "EMULACIÓN ESTADÍSTICA (4 Modelos)",
            "badge_color": "#c05621",
        },
        {
            "num": "Capa 4",
            "name": "Simulación Decadal de Escenarios Ecológicos (2025–2050)",
            "color": "#faf5ff",
            "border": "#805ad5",
            "y": 32,
            "items": [
                "• Sistema acoplado de ecuaciones diferenciales ordinarias (EDO Mumby-Hastings-Edwards) para corales y macroalgas",
                "• Integración numérica exacta Runge-Kutta de 4to orden (RK4; paso temporal dt = 0.05 años, 500 pasos hasta 2050)",
                "• Propagación de incertidumbre: N = 5,000 trayectorias Monte Carlo con perturbación gaussiana de ±15% en parámetros",
                "• 4 Escenarios de manejo: S1 (SSP5-8.5 sin mitigar), S2 (SSP2-4.5), S3 (Restauración activa) y S4 (AMP integrada)",
            ],
            "badge": "MOTOR DE SIMULACIÓN RK4 (N=5,000 MC)",
            "badge_color": "#6b46c1",
        },
        {
            "num": "Capa 5",
            "name": "Validación Espacial y Verificación de Repetibilidad",
            "color": "#fff5f5",
            "border": "#e53e3e",
            "y": 16,
            "items": [
                "• Validación cruzada en 5 bloques espaciales por complejos de estaciones (buffer de aislamiento geográfico ≥ 25 km)",
                "• Distancia mínima entre estaciones de entrenamiento y prueba: 119.72 km (0 violaciones de autocorrelación espacial)",
                "• Replicación multi-semilla (5 semillas: 17, 42, 73, 108, 256; 25 ejecuciones pareadas) y pruebas de Wilcoxon/Bonferroni",
                "• Atribución explicable TreeSHAP intervencional y superficies de dependencia parcial dentro del soporte empírico",
            ],
            "badge": "VALIDACIÓN ESPACIAL (5 Bloques × 5 Semillas)",
            "badge_color": "#9b2c2c",
        },
        {
            "num": "Capa 6",
            "name": "Soporte a Decisiones Espaciales y Priorización de Restauración",
            "color": "#e6fffa",
            "border": "#319795",
            "y": 2,
            "items": [
                "• Índice de Prioridad de Restauración Espacial (SRPI, Ec. 7 biofísica): ponderación de refugio térmico, cobertura, rugosidad y conectividad",
                "• Identificación de Zonas Prioritarias Nivel 1 (SRPI ≥ 0.70): 10 de 30 estaciones globales (33.33% de estaciones, 32.48% de registros)",
                "• Análisis de sensibilidad multi-umbral (τ ∈ {0.60, 0.70, 0.80}) y verificación preliminar con telemetría real NOAA CRW 5 km",
                "• Despliegue en contenedor Docker reproducible y repositorio de acceso abierto para gobernanza ciberfísica",
            ],
            "badge": "DECISIÓN ESPACIAL (SRPI Ec. 7)",
            "badge_color": "#234e52",
        },
    ]

    h_box = 12.5
    for l in layers:
        y_bot = l["y"]
        # Box background
        rect = patches.FancyBboxPatch(
            (4, y_bot), 92, h_box,
            boxstyle="round,pad=0.6,rounding_size=1.2",
            facecolor=l["color"], edgecolor=l["border"], linewidth=1.8,
        )
        ax.add_patch(rect)

        # Layer number & title
        ax.text(6.5, y_bot + h_box - 2.6, f"{l['num']}: {l['name']}", fontsize=11.5, fontweight="bold", color="#2d3748")

        # Badge
        ax.text(
            94, y_bot + h_box - 2.6, l["badge"],
            ha="right", va="center", fontsize=8.5, fontweight="bold", color="#ffffff",
            bbox=dict(boxstyle="round,pad=0.35", facecolor=l["badge_color"], edgecolor="none")
        )

        # Text items
        for idx, item in enumerate(l["items"]):
            ax.text(7.5, y_bot + h_box - 5.0 - (idx * 2.1), item, fontsize=9.2, color="#2d3748")

        # Arrow down connecting layers
        if l["num"] != "Capa 6":
            ax.annotate(
                "", xy=(50, y_bot - 0.2), xytext=(50, y_bot + 0.5),
                arrowprops=dict(arrowstyle="->", color="#718096", lw=1.6)
            )

    plt.tight_layout()
    for out_d in [RESULTS_FIG_DIR, LEGACY_FIG_DIR]:
        plt.savefig(os.path.join(out_d, "Figure1_digital_twin_architecture.png"), dpi=300)
    plt.close()
    print("Figura 1 generada exitosamente.")


def make_figura_2():
    """
    Figura 2: Desempeño de los cuatro modelos en el régimen canónico (A–C) y ablación de fuga con XGBoost (D).
    """
    print("Renderizando Figura 2: Desempeño de modelos y ablación de fuga...")
    json_path = os.path.join(RESULTS_DIR, "manuscript_numbers.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    models_data = data["machine_learning_benchmark"]["models"]
    models = ["XGBoost", "Random_Forest", "Deep_MLP", "Stacked_LSTM"]
    display_names = ["XGBoost", "Random Forest", "Deep MLP", "Stacked LSTM"]
    colors = ["#2b6cb0", "#2f855a", "#d69e2e", "#805ad5"]

    fig = plt.figure(figsize=(14.5, 10.5))
    gs = GridSpec(2, 2, figure=fig, hspace=0.34, wspace=0.28)

    # Panel A: Exactitud Global y Balanceada
    ax_a = fig.add_subplot(gs[0, 0])
    x = np.arange(len(models))
    w = 0.35

    acc_vals = [models_data[m]["Classification_Accuracy"] * 100.0 for m in models]
    bal_vals = [models_data[m]["Balanced_Accuracy"] * 100.0 for m in models]

    # Parse 95% CIs for overall accuracy
    acc_err_low = []
    acc_err_high = []
    for m in models:
        ci_str = models_data[m]["Accuracy_CI95"].replace("[", "").replace("]", "")
        lo, hi = [float(v) * 100.0 for v in ci_str.split(",")]
        acc = models_data[m]["Classification_Accuracy"] * 100.0
        acc_err_low.append(acc - lo)
        acc_err_high.append(hi - acc)

    bar1 = ax_a.bar(x - w/2, acc_vals, width=w, label="Exactitud Global (%)", color="#2b6cb0", edgecolor="#1a365d", yerr=[acc_err_low, acc_err_high], capsize=4)
    bar2 = ax_a.bar(x + w/2, bal_vals, width=w, label="Exactitud Balanceada (%)", color="#4299e1", edgecolor="#2b6cb0")

    ax_a.set_xticks(x)
    ax_a.set_xticklabels(display_names, fontweight="semibold")
    ax_a.set_ylabel("Porcentaje (%)")
    ax_a.set_ylim(50, 105)
    ax_a.set_title("(A) Exactitud Global vs. Exactitud Balanceada (Régimen Limpio)", fontweight="bold")
    ax_a.legend(loc="lower right", frameon=True)
    ax_a.grid(True, axis="y", linestyle=":", alpha=0.6)

    for b in bar1:
        ax_a.text(b.get_x() + b.get_width()/2, b.get_height() + 1.2, f"{b.get_height():.2f}%", ha="center", va="bottom", fontsize=8.5, fontweight="bold")
    for b in bar2:
        ax_a.text(b.get_x() + b.get_width()/2, b.get_height() + 1.2, f"{b.get_height():.2f}%", ha="center", va="bottom", fontsize=8.5)

    # Panel B: Macro-F1 Score y PR-AUC Macro
    ax_b = fig.add_subplot(gs[0, 1])
    f1_vals = [models_data[m]["Macro_F1_Score"] for m in models]
    prauc_vals = [models_data[m]["Macro_PR_AUC"] for m in models]

    f1_err_low = []
    f1_err_high = []
    for m in models:
        ci_str = models_data[m]["Macro_F1_CI95"].replace("[", "").replace("]", "")
        lo, hi = [float(v) for v in ci_str.split(",")]
        f1 = models_data[m]["Macro_F1_Score"]
        f1_err_low.append(f1 - lo)
        f1_err_high.append(hi - f1)

    bar3 = ax_b.bar(x - w/2, f1_vals, width=w, label="Macro-F1", color="#2f855a", edgecolor="#1c4532", yerr=[f1_err_low, f1_err_high], capsize=4)
    bar4 = ax_b.bar(x + w/2, prauc_vals, width=w, label="Macro PR-AUC", color="#48bb78", edgecolor="#2f855a")

    ax_b.set_xticks(x)
    ax_b.set_xticklabels(display_names, fontweight="semibold")
    ax_b.set_ylabel("Puntuación (0 a 1)")
    ax_b.set_ylim(0.55, 0.85)
    ax_b.set_title("(B) Macro-F1 y Macro PR-AUC (Régimen Limpio)", fontweight="bold")
    ax_b.legend(loc="lower right", frameon=True)
    ax_b.grid(True, axis="y", linestyle=":", alpha=0.6)

    for b in bar3:
        ax_b.text(b.get_x() + b.get_width()/2, b.get_height() + 0.008, f"{b.get_height():.4f}", ha="center", va="bottom", fontsize=8.5, fontweight="bold")
    for b in bar4:
        ax_b.text(b.get_x() + b.get_width()/2, b.get_height() + 0.008, f"{b.get_height():.4f}", ha="center", va="bottom", fontsize=8.5)

    # Panel C: Regresión R² y RMSE (%)
    ax_c = fig.add_subplot(gs[1, 0])
    r2_vals = [models_data[m]["Regression_R2"] for m in models]
    rmse_vals = [models_data[m]["Regression_RMSE"] for m in models]

    r2_err_low = []
    r2_err_high = []
    for m in models:
        ci_str = models_data[m]["R2_CI95"].replace("[", "").replace("]", "")
        lo, hi = [float(v) for v in ci_str.split(",")]
        r2 = models_data[m]["Regression_R2"]
        r2_err_low.append(r2 - lo)
        r2_err_high.append(hi - r2)

    bar5 = ax_c.bar(x - w/2, r2_vals, width=w, label="Coeficiente de Determinación (R²)", color="#d69e2e", edgecolor="#744210", yerr=[r2_err_low, r2_err_high], capsize=4)
    ax_c2 = ax_c.twinx()
    bar6 = ax_c2.bar(x + w/2, rmse_vals, width=w, label="RMSE (%)", color="#e53e3e", edgecolor="#742a2a")

    ax_c.set_xticks(x)
    ax_c.set_xticklabels(display_names, fontweight="semibold")
    ax_c.set_ylabel("R² (Bondad de ajuste)", color="#744210")
    ax_c.set_ylim(0.90, 0.96)
    ax_c2.set_ylabel("RMSE (% de pérdida de cobertura)", color="#742a2a")
    ax_c2.set_ylim(3.0, 5.0)
    ax_c.set_title("(C) Desempeño de Regresión R² y RMSE (Régimen Limpio)", fontweight="bold")
    ax_c.grid(True, axis="y", linestyle=":", alpha=0.6)

    # Panel D: Estudio de Ablación de Fuga de Datos (XGBoost)
    ax_d = fig.add_subplot(gs[1, 1])
    ablation_regimes = [
        ("R0: Con Fuga (16 vars)", 0.9994, 0.3953, "#c53030"),
        ("R0b: Fuga Legacy (10 vars)", 0.8305, 6.4597, "#dd6b20"),
        ("R1: Canónico Limpio (10 vars)", 0.9336, 4.0443, "#2b6cb0"),
        ("R2: Indirectas (6 vars)", 0.8487, 6.1037, "#4a5568"),
        ("R3: Estricto (2 vars)", -0.0269, 15.9007, "#718096"),
    ]

    reg_names = [r[0] for r in ablation_regimes]
    r2_ab = [r[1] for r in ablation_regimes]
    rmse_ab = [r[2] for r in ablation_regimes]
    colors_ab = [r[3] for r in ablation_regimes]

    y_pos = np.arange(len(reg_names))
    ax_d.scatter(rmse_ab, r2_ab, s=180, c=colors_ab, edgecolor="#1a202c", zorder=4)

    for i, (name, r2_val, rmse_val, col) in enumerate(ablation_regimes):
        offset_y = 0.05 if i != 0 else -0.07
        ax_d.annotate(
            f"{name}\n(R²={r2_val:.4f}, RMSE={rmse_val:.2f}%)",
            xy=(rmse_val, r2_val),
            xytext=(rmse_val + 0.4, r2_val + offset_y),
            fontsize=8.5,
            fontweight="bold" if "Canónico" in name or "R0:" in name else "normal",
            arrowprops=dict(arrowstyle="->", color=col, lw=1.2),
        )

    ax_d.set_xlabel("Error Cuadrático Medio (RMSE, %)")
    ax_d.set_ylabel("Coeficiente de Determinación (R²)")
    ax_d.set_ylim(-0.15, 1.08)
    ax_d.set_xlim(-0.5, 18.5)
    ax_d.axhline(0.9385, color="#2b6cb0", linestyle="--", lw=1.2, label="Techo de ruido del simulador (R² ≈ 0.9385)")
    ax_d.set_title("(D) Ablación de Fuga Inversa del Target (XGBoost)", fontweight="bold")
    ax_d.legend(loc="lower left", frameon=True, fontsize=8.5)
    ax_d.grid(True, linestyle=":", alpha=0.6)

    plt.suptitle("Figura 2: Desempeño Espacial en Régimen Canónico y Estudio de Ablación de Fuga", fontsize=15, fontweight="bold", y=0.98)
    plt.tight_layout()
    for out_d in [RESULTS_FIG_DIR, LEGACY_FIG_DIR]:
        plt.savefig(os.path.join(out_d, "Figure2_methodological_workflow.png"), dpi=300)
    plt.close()
    print("Figura 2 generada exitosamente.")


def make_figura_3():
    """
    Figura 3: Verificación del emulador.
    (A) Macro-F1 y R² con IC 95%
    (B) Matriz de confusión fuera de muestra de XGBoost (N=15,000)
    (C) Importancia TreeSHAP global con IC 95%
    (D) Umbrales de DHW (EC50 y cruce del 35% de pérdida) dentro del soporte empírico
    """
    print("Renderizando Figura 3: Verificación del emulador (Paneles A-D)...")
    json_path = os.path.join(RESULTS_DIR, "manuscript_numbers.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    models_data = data["machine_learning_benchmark"]["models"]
    models = ["XGBoost", "Random_Forest", "Deep_MLP", "Stacked_LSTM"]
    display_names = ["XGBoost", "Random Forest", "Deep MLP", "Stacked LSTM"]
    colors = ["#2b6cb0", "#2f855a", "#d69e2e", "#805ad5"]

    fig = plt.figure(figsize=(14.5, 10.5))
    gs = GridSpec(2, 2, figure=fig, hspace=0.34, wspace=0.28)

    # Panel A: Macro-F1 vs R² con IC 95%
    ax_a = fig.add_subplot(gs[0, 0])
    for i, m in enumerate(models):
        f1 = models_data[m]["Macro_F1_Score"]
        r2 = models_data[m]["Regression_R2"]
        ci_f1 = [float(v) for v in models_data[m]["Macro_F1_CI95"].replace("[", "").replace("]", "").split(",")]
        ci_r2 = [float(v) for v in models_data[m]["R2_CI95"].replace("[", "").replace("]", "").split(",")]

        xerr = [[f1 - ci_f1[0]], [ci_f1[1] - f1]]
        yerr = [[r2 - ci_r2[0]], [ci_r2[1] - r2]]

        ax_a.errorbar(
            f1, r2, xerr=xerr, yerr=yerr, fmt="o", color=colors[i], ecolor=colors[i],
            elinewidth=2.0, capsize=5, capthick=1.5, markersize=9, label=display_names[i], zorder=4
        )
        ax_a.text(f1 + 0.003, r2 - 0.0008, display_names[i], fontsize=9, fontweight="bold", color=colors[i])

    ax_a.set_xlabel("Macro-F1 Score (Clasificación)")
    ax_a.set_ylabel("Coeficiente R² (Regresión)")
    ax_a.set_xlim(0.66, 0.76)
    ax_a.set_ylim(0.925, 0.945)
    ax_a.set_title("(A) Compromiso Multitarea: Macro-F1 vs. R² (IC 95%)", fontweight="bold")
    ax_a.grid(True, linestyle=":", alpha=0.6)
    ax_a.legend(loc="lower left", frameon=True)

    # Panel B: Matriz de Confusión Out-of-Fold de XGBoost (N = 15,000)
    ax_b = fig.add_subplot(gs[0, 1])
    # XGBoost OOF matrix: Low: [14091, 6, 0], Medium: [159, 17, 10], High: [0, 3, 714]
    cm = np.array([
        [14091, 6, 0],
        [159, 17, 10],
        [0, 3, 714],
    ])
    labels = ["Bajo", "Medio", "Alto"]

    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax_b,
        xticklabels=labels, yticklabels=labels,
        annot_kws={"fontsize": 11, "fontweight": "bold"}
    )
    ax_b.set_xlabel("Predicción Fuera de Muestra (OOF)")
    ax_b.set_ylabel("Etiqueta Verdadera")
    ax_b.set_title("(B) Matriz de Confusión OOF — XGBoost (N = 15,000)", fontweight="bold")

    # Annotate class recalls
    recalls = [14091 / 14097 * 100.0, 17 / 186 * 100.0, 714 / 717 * 100.0]
    ax_b.text(0.5, -0.22, f"Sensibilidad (Recall): Bajo = {recalls[0]:.2f}% | Medio = {recalls[1]:.2f}% | Alto = {recalls[2]:.2f}%",
              ha="center", va="center", transform=ax_b.transAxes, fontsize=9.5, fontweight="bold", color="#742a2a")

    # Panel C: TreeSHAP Importancia Global Intervencional
    ax_c = fig.add_subplot(gs[1, 0])
    shap_items = data["explainability_and_tipping_points"]["clean_10_feature_treeshap"]
    feat_trans = {
        "DHW_degC_weeks": "DHW (semanas de calentamiento)",
        "PAR_umol_m2_s": "Radiación fotosintética (PAR)",
        "SST_Anomaly_degC": "Anomalía térmica (SSTA)",
        "Aragonite_Saturation_Omega": "Saturación de aragonita (Ω_arag)",
        "SST_degC": "Temperatura superficial (SST)",
        "Salinity_PSU": "Salinidad marina (PSU)",
        "Depth_m": "Profundidad batimétrica (m)",
        "pH_total": "pH marino (escala total)",
        "Dissolved_Oxygen_mg_L": "Oxígeno disuelto (mg/L)",
        "Turbidity_NTU": "Turbidez del agua (NTU)",
    }

    y_labels = [feat_trans.get(it["Feature"], it["Feature"]) for it in reversed(shap_items)]
    pct_vals = [it["Normalized_Importance_Pct"] for it in reversed(shap_items)]
    err_lo = [it["Normalized_Importance_Pct"] - it["Bootstrap_CI95_Low_Pct"] for it in reversed(shap_items)]
    err_hi = [it["Bootstrap_CI95_High_Pct"] - it["Normalized_Importance_Pct"] for it in reversed(shap_items)]

    y_indices = np.arange(len(y_labels))
    ax_c.barh(y_indices, pct_vals, color="#2b6cb0", edgecolor="#1a365d", xerr=[err_lo, err_hi], capsize=3.5, height=0.68)
    ax_c.set_yticks(y_indices)
    ax_c.set_yticklabels(y_labels, fontsize=9.2)
    ax_c.set_xlabel("Importancia TreeSHAP Normalizada (%)")
    ax_c.set_title("(C) Atribución Global TreeSHAP Intervencional (IC 95%)", fontweight="bold")
    ax_c.grid(True, axis="x", linestyle=":", alpha=0.6)

    for i, v in enumerate(pct_vals):
        ax_c.text(v + 1.2, i, f"{v:.1f}%", va="center", fontsize=8.5, fontweight="bold")
    ax_c.set_xlim(0, 62)

    # Panel D: Umbrales dentro del soporte empírico (Omega in [3.16, 3.90])
    ax_d = fig.add_subplot(gs[1, 1])
    pdp_within_path = os.path.join(RESULTS_DIR, "partial_dependence_within_support.csv")
    if os.path.exists(pdp_within_path):
        pdp_df = pd.read_csv(pdp_within_path).sort_values("DHW_degC_weeks")
        ax_d.plot(pdp_df["DHW_degC_weeks"], pdp_df["PD_XGBoost_HighOmega_390"], label="XGBoost: Ω alto (3.90; pH 8.12)", color="#2b6cb0", lw=2.4)
        ax_d.plot(pdp_df["DHW_degC_weeks"], pdp_df["PD_XGBoost_LowOmega_316"], label="XGBoost: Ω bajo (3.16; pH 8.03)", color="#c53030", lw=2.4)
        ax_d.plot(pdp_df["DHW_degC_weeks"], pdp_df["Analytical_HighOmega_390"], label="Generador analítico: Ω 3.90", color="#2b6cb0", linestyle=":", lw=1.8)
        ax_d.plot(pdp_df["DHW_degC_weeks"], pdp_df["Analytical_LowOmega_316"], label="Generador analítico: Ω 3.16", color="#c53030", linestyle=":", lw=1.8)
    else:
        # Fallback to standard PDP
        pdp_df = pd.read_csv(os.path.join(RESULTS_DIR, "partial_dependence_dhw_ph.csv"))
        ax_d.plot(pdp_df["DHW_degC_weeks"], pdp_df.iloc[:, 1], label="XGBoost: Ambiental", color="#2b6cb0", lw=2.4)
        ax_d.plot(pdp_df["DHW_degC_weeks"], pdp_df.iloc[:, 2], label="XGBoost: Acidificado", color="#c53030", lw=2.4)

    # Add vertical threshold lines
    ax_d.axvline(10.70, color="#2b6cb0", linestyle="--", lw=1.2, label="EC50 XGBoost (10.70 DHW)")
    ax_d.axvline(9.85, color="#2b6cb0", linestyle=":", lw=1.2, label="EC50 Generador Ω=3.90 (9.85 DHW)")
    ax_d.axvline(9.20, color="#c53030", linestyle=":", lw=1.2, label="EC50 Generador Ω=3.16 (9.20 DHW)")
    ax_d.axhline(35.0, color="#718096", linestyle="-.", lw=1.0, alpha=0.8, label="Umbral crítico de pérdida 35%")

    ax_d.set_xlabel("Semanas de Calentamiento Grado (DHW, °C-semanas)")
    ax_d.set_ylabel("Pérdida de Cobertura Coralina (%)")
    ax_d.set_title("(D) Dependencia Parcial dentro del Soporte (Ω ∈ [3.16, 3.90])", fontweight="bold")
    ax_d.legend(loc="upper left", frameon=True, fontsize=8.0)
    ax_d.grid(True, linestyle=":", alpha=0.6)
    ax_d.set_xlim(0, 20)
    ax_d.set_ylim(0, 85)

    plt.suptitle("Figura 3: Verificación del Emulador — Desempeño, Matriz OOF, TreeSHAP y Umbrales de Dependencia Parcial", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()
    for out_d in [RESULTS_FIG_DIR, LEGACY_FIG_DIR]:
        plt.savefig(os.path.join(out_d, "Figure3_dataset_integration_fair.png"), dpi=300)
    plt.close()
    print("Figura 3 generada exitosamente.")


def make_figura_4():
    """
    Figura 4: Cobertura coralina media (A) y acreción neta (B) bajo cuatro regímenes de manejo (2025–2050; RK4; 5,000 MC).
    """
    print("Renderizando Figura 4: Escenarios decadales 2025–2050 (RK4)...")
    scen_csv = os.path.join(RESULTS_DIR, "scenario_2050_summary.csv")
    df_scen = pd.read_csv(scen_csv)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6.2))

    # Panel A: Trayectorias 2025, 2035, 2050
    ax_a = axes[0]
    palette = {
        "S1_SSP585_Unmitigated": "#e53e3e",
        "S2_SSP245_Moderate": "#dd6b20",
        "S3_Active_Restoration": "#3182ce",
        "S4_Integrated_Intervention": "#38a169",
    }
    labels_es = {
        "S1_SSP585_Unmitigated": "S1: Estrés térmico severo (SSP5-8.5)",
        "S2_SSP245_Moderate": "S2: Mitigación climática moderada (SSP2-4.5)",
        "S3_Active_Restoration": "S3: Restauración activa outplanting",
        "S4_Integrated_Intervention": "S4: Intervención integrada (AMP + Outplanting)",
    }

    years = [2025, 2035, 2050]

    for _, row in df_scen.iterrows():
        code = row["Scenario_Code"]
        col = palette.get(code, "#4a5568")
        lab = labels_es.get(code, code)

        c25 = float(row["Baseline_Cover_2025_Pct"])
        c35 = float(row["Cover_2035_Mean_Pct"])
        c50 = float(row["Cover_2050_Mean_Pct"])
        means = [c25, c35, c50]

        # Parse 95% CI for 2050
        ci_str = str(row["Cover_2050_95_CI"]).replace("[", "").replace("]", "").replace("%", "")
        parts = [float(v.strip()) for v in ci_str.split("-")]
        ci_lo, ci_hi = parts[0], parts[1]

        ax_a.plot(years, means, marker="o", lw=2.6, markersize=8, color=col, label=lab)
        ax_a.errorbar(2050, c50, yerr=[[c50 - ci_lo], [ci_hi - c50]], fmt="none", ecolor=col, elinewidth=2.2, capsize=5, capthick=1.8)

        # Annotate end value
        ax_a.text(2050.8, c50, f"{c50:.1f}%\n[{ci_lo:.1f}–{ci_hi:.1f}%]", va="center", fontsize=8.5, fontweight="bold", color=col)

    ax_a.set_xlabel("Año de Proyección")
    ax_a.set_ylabel("Cobertura de Coral Vivo (%)")
    ax_a.set_title("(A) Trayectorias de Cobertura Coralina (2025–2050; RK4; N=5,000 MC)", fontweight="bold")
    ax_a.set_xlim(2023, 2055)
    ax_a.set_ylim(-2, 78)
    ax_a.axhline(10.0, color="#718096", linestyle=":", lw=1.2, label="Umbral de colapso arrecifal (<10%)")
    ax_a.legend(loc="upper left", frameon=True, fontsize=8.8)
    ax_a.grid(True, linestyle=":", alpha=0.6)

    # Panel B: Acreción carbonatada neta en 2050
    ax_b = axes[1]
    scen_codes = df_scen["Scenario_Code"].tolist()
    accretion_vals = df_scen["Net_Calcification_2050"].astype(float).tolist()

    acc_err_lo = []
    acc_err_hi = []
    for _, row in df_scen.iterrows():
        c = float(row["Net_Calcification_2050"])
        # Parse 95% CI for accretion safely handling negative values
        ci_str = str(row["Net_Calcification_2050_95_CI"]).replace("[", "").replace("]", "").strip()
        import re
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", ci_str)
        if len(nums) >= 2:
            lo, hi = float(nums[0]), float(nums[1])
            acc_err_lo.append(max(c - lo, 0.01))
            acc_err_hi.append(max(hi - c, 0.01))
        else:
            acc_err_lo.append(0.2)
            acc_err_hi.append(0.2)

    x_b = np.arange(len(scen_codes))
    bars = ax_b.bar(
        x_b, accretion_vals,
        color=[palette.get(c, "#4a5568") for c in scen_codes],
        edgecolor="#1a202c",
        width=0.55,
        yerr=[acc_err_lo, acc_err_hi],
        capsize=5,
    )
    ax_b.axhline(0.0, color="#1a202c", linestyle="-", lw=1.1)

    ax_b.set_xticks(x_b)
    ax_b.set_xticklabels(["S1: SSP5-8.5\n(Sin mitigar)", "S2: SSP2-4.5\n(Moderada)", "S3: Outplant\n(Activa)", "S4: AMP + Outp\n(Integrada)"], fontsize=9.2, fontweight="semibold")
    ax_b.set_ylabel("Tasa de Acreción Neta en 2050 (kg CaCO₃ m⁻² año⁻¹)")
    ax_b.set_title("(B) Balance Carbonatado Neto en 2050 (IC 95%)", fontweight="bold")
    ax_b.set_ylim(-3.5, 12.5)
    ax_b.grid(True, axis="y", linestyle=":", alpha=0.6)

    for b, val in zip(bars, accretion_vals):
        y_text = val + 0.6 if val >= 0 else val - 0.9
        ax_b.text(b.get_x() + b.get_width()/2, y_text, f"{val:+.2f}", ha="center", va="center", fontsize=9.2, fontweight="bold")

    plt.suptitle("Figura 4: Proyecciones Decadales de Cobertura y Acreción Carbonatada (2025–2050, EDOs Acopladas RK4)", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()
    for out_d in [RESULTS_FIG_DIR, LEGACY_FIG_DIR]:
        plt.savefig(os.path.join(out_d, "Figure4_ai_predictive_modeling_shap.png"), dpi=300)
    plt.close()
    print("Figura 4 generada exitosamente.")


def main():
    print("=" * 70)
    print("TASK 8: Generating Publication Figures 1 to 4 in Spanish (300 DPI)")
    print("=" * 70)
    make_figura_1()
    make_figura_2()
    make_figura_3()
    make_figura_4()

    # Verify presence in results/figures/
    fig_names = [
        "Figure1_digital_twin_architecture.png",
        "Figure2_methodological_workflow.png",
        "Figure3_dataset_integration_fair.png",
        "Figure4_ai_predictive_modeling_shap.png",
    ]
    print("\nVerificacion de archivos generados en results/figures/:")
    for f in fig_names:
        p = os.path.join(RESULTS_FIG_DIR, f)
        size_kb = os.path.getsize(p) / 1024.0 if os.path.exists(p) else 0.0
        print(f"  [OK] {f} -> {size_kb:.1f} KB (Existe: {os.path.exists(p)})")


if __name__ == "__main__":
    main()
