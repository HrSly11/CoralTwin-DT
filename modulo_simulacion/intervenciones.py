# modulo_simulacion/intervenciones.py
"""Estrategias y carteras de intervención para restauración y conservación de arrecifes"""

CATALOGO_INTERVENCIONES = {
    "super_corals": {
        "nombre": "Propagación de Super-Corales Térmicamente Resistentes",
        "descripcion": "Siembra de genotipos seleccionados con simbiontes Durusdinium trenchii (+1.5 °C de tolerancia a olas de calor).",
        "efecto_endurecimiento_termico": 1.8, # reduce el impacto de DHW
        "efecto_tasa_restauracion": 0.015,
        "efecto_pastoreo": 0.0,
        "costo_por_hectarea_usd": 18500,
        "viabilidad": "Alta en viveros in-situ"
    },
    "micro_fragmentacion": {
        "nombre": "Micro-Fragmentación y Micro-Outplanting Intensivo",
        "descripcion": "Técnica de corte rápido que acelera el crecimiento tisular masivo de corales masivos y ramificados.",
        "efecto_endurecimiento_termico": 0.3,
        "efecto_tasa_restauracion": 0.035,
        "efecto_pastoreo": 0.0,
        "costo_por_hectarea_usd": 12000,
        "viabilidad": "Probada a escala global"
    },
    "creacion_amp_herbivoros": {
        "nombre": "Área Marina Protegida con Veda Estricta de Herbívoros",
        "descripcion": "Protección de peces loro (Scaridae) y cirujanos para maximizar el pastoreo sobre macroalgas invasoras.",
        "efecto_endurecimiento_termico": 0.0,
        "efecto_tasa_restauracion": 0.005,
        "efecto_pastoreo": 0.22, # incrementa la tasa de pastoreo g
        "costo_por_hectarea_usd": 4500,
        "viabilidad": "Alta con gobernanza comunitaria"
    },
    "reduccion_escorrentia": {
        "nombre": "Mitigación de Presiones Locales (Control de Turbidez y Nutrientes)",
        "descripcion": "Reforestación de cuencas costeras y tratamiento de aguas para reducir sedimentación sobre el arrecife.",
        "efecto_endurecimiento_termico": 0.4,
        "efecto_tasa_restauracion": 0.008,
        "efecto_pastoreo": 0.08,
        "costo_por_hectarea_usd": 8500,
        "viabilidad": "Mediana (requiere coordinación municipal)"
    },
    "sombreado_marino": {
        "nombre": "Nebulización Marina y Sombreado Dinámico en Picos Térmicos",
        "descripcion": "Generación de microgotas salinas para atenuar la radiación solar incidente durante eventos DHW > 6.",
        "efecto_endurecimiento_termico": 1.2,
        "efecto_tasa_restauracion": 0.0,
        "efecto_pastoreo": 0.0,
        "costo_por_hectarea_usd": 25000,
        "viabilidad": "Tecnología emergente"
    }
}

def calcular_impacto_cartera(intervenciones_seleccionadas: list) -> dict:
    """Consolida los parámetros agregados de una cartera de intervenciones seleccionada"""
    total_endur = 0.0
    total_resto = 0.0
    total_pastoreo = 0.0
    costo_total = 0
    
    for clave in intervenciones_seleccionadas:
        if clave in CATALOGO_INTERVENCIONES:
            it = CATALOGO_INTERVENCIONES[clave]
            total_endur += it["efecto_endurecimiento_termico"]
            total_resto += it["efecto_tasa_restauracion"]
            total_pastoreo += it["efecto_pastoreo"]
            costo_total += it["costo_por_hectarea_usd"]
            
    return {
        "endurecimiento_termico": min(3.5, total_endur),
        "tasa_restauracion": min(0.08, total_resto),
        "incremento_pastoreo": min(0.40, total_pastoreo),
        "costo_estimado_ha_usd": costo_total
    }
