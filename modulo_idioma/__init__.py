# modulo_idioma/__init__.py
"""Módulo de internacionalización (i18n) para CoralTwin-DT"""
from .textos_es import TEXTOS_ES
from .textos_en import TEXTOS_EN

def obtener_texto(clave: str, idioma: str = "es") -> str:
    """Devuelve la traducción para una clave dada según el idioma seleccionado"""
    diccionario = TEXTOS_EN if idioma == "en" else TEXTOS_ES
    return diccionario.get(clave, clave)
