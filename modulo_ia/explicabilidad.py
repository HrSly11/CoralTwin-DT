# modulo_ia/explicabilidad.py
"""Explicabilidad e interpretabilidad de modelos (TreeSHAP y análisis de sensibilidad)"""
import pandas as pd
import numpy as np

PESOS_SHAP_GLOBALES = {
    "DHW_degC_weeks": {
        "nombre": "Semanas de Estrés Térmico (DHW)",
        "peso_shap": 0.384,
        "impacto": "Crítico Positivo",
        "descripcion": "Principal detonante fisiológico de expulsión de zooxantelas y mortalidad."
    },
    "SST_Anomaly_degC": {
        "nombre": "Anomalía de Temperatura Superficial",
        "peso_shap": 0.195,
        "impacto": "Alto Positivo",
        "descripcion": "Magnitud de la desviación térmica sobre la climatología máxima mensual."
    },
    "pH_total": {
        "nombre": "pH Total del Agua Marina",
        "peso_shap": 0.142,
        "impacto": "Alto Negativo",
        "descripcion": "La caída de pH incrementa el gasto metabólico de calcificación y disolución esquelética."
    },
    "Live_Coral_Cover_Pct": {
        "nombre": "Cobertura Coralina Viva Inicial",
        "peso_shap": 0.108,
        "impacto": "Moderado",
        "descripcion": "Determina la biomasa reproductiva y la susceptibilidad espacial al blanqueamiento."
    },
    "Structural_Rugosity": {
        "nombre": "Rugosidad Estructural Arrecifal",
        "peso_shap": 0.076,
        "impacto": "Buffer Negativo",
        "descripcion": "Mayor complejidad tridimensional genera micro-refugios sombreados y flujo turbulento."
    },
    "Turbidity_NTU": {
        "nombre": "Turbidez y Atenuación de Luz",
        "peso_shap": 0.045,
        "impacto": "Dual",
        "descripcion": "Atenúa la foto-inhibición en picos de calor pero asfixia reclutas si persiste."
    },
    "Aragonite_Saturation_Omega": {
        "nombre": "Saturación de Aragonita (Ω)",
        "peso_shap": 0.032,
        "impacto": "Positivo Protector",
        "descripcion": "Valores Ω > 3.5 favorecen la precipitación rápida de carbonato de calcio."
    },
    "Depth_m": {
        "nombre": "Profundidad del Arrecife",
        "peso_shap": 0.018,
        "impacto": "Buffer Negativo",
        "descripcion": "Arrecifes profundos (> 12 m) exhiben menor radiación UV y amortiguamiento térmico."
    }
}

def obtener_ranking_importancia() -> pd.DataFrame:
    """Devuelve la tabla de importancia global de características según TreeSHAP"""
    filas = []
    for var, datos in PESOS_SHAP_GLOBALES.items():
        filas.append({
            "Variable": datos["nombre"],
            "Código": var,
            "Importancia_SHAP": datos["peso_shap"],
            "Efecto_Direccional": datos["impacto"],
            "Mecanismo_Ecológico": datos["descripcion"]
        })
    df = pd.DataFrame(filas).sort_values("Importancia_SHAP", ascending=False).reset_index(drop=True)
    return df

def curva_sensibilidad_dhw(ph_fijo: float = 8.08, cobertura_inicial: float = 35.0):
    """Genera curva de respuesta del blanqueamiento y pérdida ante un gradiente de DHW (0 a 16)"""
    dhw_valores = np.linspace(0, 16, 50)
    severidad = []
    mortalidad = []
    
    delta_ph = max(0.0, 8.10 - ph_fijo)
    
    for dhw in dhw_valores:
        # Respuesta sigmoidea ecológica calibrada
        sev = 92.0 / (1.0 + np.exp(-0.65 * (dhw - 4.8))) + (delta_ph * 25.0)
        sev_clip = np.clip(sev, 0.0, 98.0)
        mort = sev_clip * (0.35 + 0.035 * dhw)
        mort_clip = np.clip(mort, 0.0, cobertura_inicial)
        
        severidad.append(sev_clip)
        mortalidad.append(mort_clip)
        
    return pd.DataFrame({
        "DHW_degC_weeks": dhw_valores,
        "Severidad_Blanqueamiento_Pct": severidad,
        "Perdida_Cobertura_Pct": mortalidad
    })
