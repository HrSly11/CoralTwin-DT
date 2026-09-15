# modulo_base_datos/conexion.py
"""Gestión de conexiones a base de datos (SQLite por defecto, PostgreSQL opcional)"""
import os
import sqlite3
from pathlib import Path
import config

def obtener_conexion_sqlite():
    """Devuelve conexión SQLite a la base de datos de CoralTwin-DT"""
    db_path = Path(config.DB_SQLITE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def obtener_conexion_postgres():
    """Devuelve conexión PostgreSQL si está configurada"""
    import psycopg2
    return psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PUERTO,
        dbname=config.DB_NOMBRE,
        user=config.DB_USUARIO,
        password=config.DB_CONTRASEÑA
    )

def obtener_conexion():
    """Obtiene la conexión activa según configuración"""
    if config.DB_TIPO == "postgres":
        try:
            return obtener_conexion_postgres()
        except Exception:
            return obtener_conexion_sqlite()
    return obtener_conexion_sqlite()

def probar_conexion():
    """Prueba el estado de conexión a la base de datos"""
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        res = cursor.fetchone()
        conn.close()
        return True, "Conexión a base de datos operativa"
    except Exception as e:
        return False, str(e)
