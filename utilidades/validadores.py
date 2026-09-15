# utilidades/validadores.py
"""Funciones de validación de entradas numéricas y rangos biofísicos"""

def validar_rango_ph(ph: float) -> bool:
    """Valida que el pH marino se encuentre en rango físico plausible [7.0, 8.6]"""
    return 7.0 <= ph <= 8.6

def validar_rango_dhw(dhw: float) -> bool:
    """Valida que el estrés térmico acumulado sea positivo [0.0, 35.0]"""
    return 0.0 <= dhw <= 35.0

def validar_cobertura(cobertura: float) -> bool:
    """Valida porcentaje de cobertura bentónica [0.0, 100.0]"""
    return 0.0 <= cobertura <= 100.0

def categorizar_alerta_noaa(dhw: float) -> tuple:
    """Devuelve la categoría de alerta NOAA y su color hexadecimal"""
    if dhw < 1.0:
        return "Sin Estrés (No Stress)", "#2ca02c"
    elif dhw < 4.0:
        return "Vigilancia (Watch)", "#ffbb78"
    elif dhw < 8.0:
        return "Advertencia (Warning)", "#ff7f0e"
    elif dhw < 12.0:
        return "Alerta Nivel 1 (Alert 1)", "#d62728"
    else:
        return "Alerta Nivel 2 (Alert 2)", "#7f0000"
