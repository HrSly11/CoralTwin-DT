# modulo_seguridad/decoradores.py
"""Decoradores y utilidades de validación de permisos de usuario"""
import streamlit as st

def verificar_permiso(permiso: str) -> bool:
    """Verifica si el usuario activo posee un permiso específico"""
    if not st.session_state.get("autenticado", False):
        return False
    permisos = st.session_state.get("permisos", {})
    return permisos.get(permiso, False)

def requerir_permiso(permiso: str):
    """Bloquea la vista si el usuario no tiene el permiso requerido"""
    if not verificar_permiso(permiso):
        st.error("⛔ Acceso denegado: Su rol no cuenta con permisos suficientes para acceder a esta sección.")
        st.stop()
