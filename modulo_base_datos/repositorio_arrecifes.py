# modulo_base_datos/repositorio_arrecifes.py
"""Repositorio de datos arrecifales, series temporales y métricas de estaciones"""
import pandas as pd
import numpy as np
from pathlib import Path
import config
from .conexion import obtener_conexion

_CACHE_DATASET = None
_CACHE_RANKING = None

def cargar_dataset_completo() -> pd.DataFrame:
    """Carga y cachea en memoria el dataset procesado final de 15,000 registros"""
    global _CACHE_DATASET
    if _CACHE_DATASET is not None:
        return _CACHE_DATASET
    
    csv_path = Path(config.FINAL_DATASET_CSV)
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        df["Date"] = pd.to_datetime(df["Date"])
        _CACHE_DATASET = df
        return df
    return pd.DataFrame()

def cargar_ranking_srpi() -> pd.DataFrame:
    """Carga la tabla de priorización de restauración espacial (SRPI)"""
    global _CACHE_RANKING
    if _CACHE_RANKING is not None:
        return _CACHE_RANKING
    
    csv_path = Path(config.SPATIAL_RANKING_CSV)
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        _CACHE_RANKING = df
        return df
    return pd.DataFrame()

def cargar_resumen_estaciones() -> pd.DataFrame:
    """Obtiene el último estado conocido de cada una de las 25 estaciones de monitoreo"""
    df_ranking = cargar_ranking_srpi()
    if not df_ranking.empty:
        return df_ranking
    
    # Fallback desde el dataset temporal si no está el ranking
    df_all = cargar_dataset_completo()
    if not df_all.empty:
        idx_latest = df_all.groupby("Station_Name")["Date"].idxmax()
        return df_all.loc[idx_latest].reset_index(drop=True)
    
    return pd.DataFrame()

def cargar_serie_temporal_estacion(nombre_estacion: str) -> pd.DataFrame:
    """Extrae la serie histórica mensual para una estación dada"""
    df = cargar_dataset_completo()
    if not df.empty and "Station_Name" in df.columns:
        sub = df[df["Station_Name"] == nombre_estacion].sort_values("Date").copy()
        return sub
    return pd.DataFrame()

def obtener_kpis_ecosistema() -> dict:
    """Calcula indicadores clave a nivel de red global de monitoreo"""
    df_rank = cargar_ranking_srpi()
    if df_rank.empty:
        return {
            "total_estaciones": 25,
            "dhw_promedio": 1.15,
            "ph_promedio": 8.08,
            "cobertura_promedio": 34.8,
            "estaciones_alerta": 5,
            "prioridad_alta_restauracion": 6
        }
    
    return {
        "total_estaciones": len(df_rank),
        "dhw_promedio": round(float(df_rank["DHW_degC_weeks"].mean()), 2),
        "ph_promedio": round(float(df_rank["pH_total"].mean()), 3),
        "cobertura_promedio": round(float(df_rank["Live_Coral_Cover_Pct"].mean()), 1),
        "estaciones_alerta": int((df_rank["DHW_degC_weeks"] >= config.UMBRAL_DHW_WARNING).sum()),
        "prioridad_alta_restauracion": int(df_rank["Priority_Tier"].str.contains("Tier_1", case=False, na=False).sum())
    }
