# modulo_seguridad/roles_permisos.py
"""Definición de roles y matriz de permisos para CoralTwin-DT"""

ROLES = {
    "administrador": {
        "nombre": "Administrador del Sistema",
        "descripcion": "Acceso total a la configuración, gestión de usuarios, bases de datos y sincronización de sensores NOAA.",
        "permisos": {
            "ver_dashboard": True,
            "ver_mapa_3d": True,
            "ejecutar_simulacion": True,
            "ajustar_parametros_sim": True,
            "acceso_motor_ia": True,
            "evaluar_hipotesis": True,
            "priorizar_restauracion": True,
            "generar_reportes": True,
            "sincronizar_noaa": True,
            "gestionar_usuarios": True,
            "exportar_datos_completos": True
        }
    },
    "investigador_marino": {
        "nombre": "Científico / Investigador Marino",
        "descripcion": "Acceso a simulación biofísica avanzada, modelos predictivos de IA, análisis de hipótesis y descarga científica.",
        "permisos": {
            "ver_dashboard": True,
            "ver_mapa_3d": True,
            "ejecutar_simulacion": True,
            "ajustar_parametros_sim": True,
            "acceso_motor_ia": True,
            "evaluar_hipotesis": True,
            "priorizar_restauracion": True,
            "generar_reportes": True,
            "sincronizar_noaa": False,
            "gestionar_usuarios": False,
            "exportar_datos_completos": True
        }
    },
    "gestor_conservacion": {
        "nombre": "Gestor de Áreas Marinas Protegidas",
        "descripcion": "Especializado en priorización espacial SRPI, evaluación de intervenciones y generación de reportes ejecutivos.",
        "permisos": {
            "ver_dashboard": True,
            "ver_mapa_3d": True,
            "ejecutar_simulacion": True,
            "ajustar_parametros_sim": False,
            "acceso_motor_ia": True,
            "evaluar_hipotesis": True,
            "priorizar_restauracion": True,
            "generar_reportes": True,
            "sincronizar_noaa": False,
            "gestionar_usuarios": False,
            "exportar_datos_completos": False
        }
    },
    "consultor_publico": {
        "nombre": "Consultor Público / Educador",
        "descripcion": "Visualización general de estaciones arrecifales, gemelo digital 3D y resúmenes de impacto ecológico.",
        "permisos": {
            "ver_dashboard": True,
            "ver_mapa_3d": True,
            "ejecutar_simulacion": False,
            "ajustar_parametros_sim": False,
            "acceso_motor_ia": False,
            "evaluar_hipotesis": False,
            "priorizar_restauracion": False,
            "generar_reportes": True,
            "sincronizar_noaa": False,
            "gestionar_usuarios": False,
            "exportar_datos_completos": False
        }
    }
}
