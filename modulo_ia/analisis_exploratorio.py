# modulo_ia/analisis_exploratorio.py
"""Análisis exploratorio de datos, correlaciones oceanográficas y distribuciones multivariadas"""
import pandas as pd
import numpy as np
from modulo_base_datos.repositorio_arrecifes import cargar_dataset_completo

VARIABLES_ANALISIS = [
    "SST_degC",
    "SST_Anomaly_degC",
    "DHW_degC_weeks",
    "pH_total",
    "Turbidity_NTU",
    "Live_Coral_Cover_Pct",
    "Macroalgae_Cover_Pct",
    "Structural_Rugosity",
    "Shannon_Diversity_H",
    "Bleaching_Severity_Pct"
]

def calcular_matriz_correlacion() -> pd.DataFrame:
    """Calcula matriz de correlación de Pearson entre las variables clave"""
    df = cargar_dataset_completo()
    if df.empty:
        return pd.DataFrame()
    
    cols_existentes = [c for c in VARIABLES_ANALISIS if c in df.columns]
    corr = df[cols_existentes].corr(method="pearson").round(3)
    return corr

def obtener_estadisticas_descriptivas() -> pd.DataFrame:
    """Calcula resumen estadístico descriptivo del ecosistema"""
    df = cargar_dataset_completo()
    if df.empty:
        return pd.DataFrame()
    
    cols_existentes = [c for c in VARIABLES_ANALISIS if c in df.columns]
    desc = df[cols_existentes].describe().T[["mean", "std", "min", "50%", "max"]].round(2)
    desc.columns = ["Media", "Desv. Estándar", "Mínimo", "Mediana", "Máximo"]
    return desc

def obtener_resumen_por_region() -> pd.DataFrame:
    """Agrupa métricas clave por cuenca oceánica / región"""
    df = cargar_dataset_completo()
    if df.empty or "Region" not in df.columns:
        return pd.DataFrame()
    
    resumen = df.groupby("Region").agg({
        "Live_Coral_Cover_Pct": "mean",
        "DHW_degC_weeks": "mean",
        "pH_total": "mean",
        "Shannon_Diversity_H": "mean",
        "Bleaching_Severity_Pct": "mean"
    }).round(2).reset_index()
    
    resumen.columns = ["Región Oceánica", "Cobertura Coralina Media (%)", "DHW Medio (°C-sem)", "pH Medio", "Diversidad H'", "Blanqueamiento Medio (%)"]
    return resumen
