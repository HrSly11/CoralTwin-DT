# modulo_simulacion/escenarios_ipcc.py
"""Simulación de trayectorias climáticas decenales 2025-2050 según escenarios IPCC AR6"""
import numpy as np
import pandas as pd
from .motor_biofisico import resolver_mumby_extendido

ESCENARIOS_CLIMATICOS = {
    "SSP1-2.6": {
        "nombre": "SSP1-2.6 — Sostenibilidad y Fuerte Mitigación",
        "descripcion": "Emisiones netas cero hacia 2050. Calentamiento contenido bajo 1.8 °C. Olas de calor moderadas.",
        "dhw_promedio": 1.2,
        "dhw_tendencia_anual": 0.04,
        "ph_2025": 8.08,
        "ph_2050": 8.04,
        "color": "#2ca02c"
    },
    "SSP2-4.5": {
        "nombre": "SSP2-4.5 — Trayectoria Intermedia (Políticas Actuales)",
        "descripcion": "Mitigación moderada. Aumento térmico de ~2.7 °C al 2100. Frecuencia recurrente de eventos DHW > 8.",
        "dhw_promedio": 2.8,
        "dhw_tendencia_anual": 0.16,
        "ph_2025": 8.07,
        "ph_2050": 7.96,
        "color": "#ff7f0e"
    },
    "SSP5-8.5": {
        "nombre": "SSP5-8.5 — Alto Desarrollo Basado en Combustibles Fósiles",
        "descripcion": "Emisiones crecientes sin mitigación. Olas de calor extremas anuales (DHW > 14) y severa acidificación.",
        "dhw_promedio": 5.4,
        "dhw_tendencia_anual": 0.38,
        "ph_2025": 8.06,
        "ph_2050": 7.82,
        "color": "#d62728"
    }
}

def simular_comparativa_escenarios(c0=0.35, m0=0.25, años=25, con_restauracion=False):
    """
    Ejecuta la proyección decenal 2025-2050 para los 3 escenarios climáticos principales.
    Devuelve dataframe consolidado para gráficos y análisis.
    """
    resultados = {}
    tiempo = None
    
    for clave, datos in ESCENARIOS_CLIMATICOS.items():
        tasa_resto = 0.025 if con_restauracion else 0.0
        endur = 1.5 if con_restauracion else 0.0
        
        sim = resolver_mumby_extendido(
            c0=c0,
            m0=m0,
            años=años,
            dhw_acumulado=datos["dhw_promedio"],
            ph_oceano=(datos["ph_2025"] + datos["ph_2050"]) / 2.0,
            tasa_restauracion=tasa_resto,
            endurecimiento_termico=endur
        )
        
        if tiempo is None:
            tiempo = 2025 + sim["tiempo_años"]
            
        resultados[clave] = {
            "coral": sim["cobertura_coral"],
            "macroalgas": sim["cobertura_macroalgas"],
            "calcificacion": sim["tasa_calcificacion"],
            "cobertura_final": sim["cobertura_final"],
            "estado": sim["resiliencia_estado"],
            "color": datos["color"]
        }
        
    return tiempo, resultados
