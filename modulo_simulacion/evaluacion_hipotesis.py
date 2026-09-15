# modulo_simulacion/evaluacion_hipotesis.py
"""
Evaluación cuantitativa de la hipótesis principal de investigación:
'Las áreas priorizadas mediante el gemelo digital mantienen una cobertura coralina
superior al 30 % en escenarios RCP 4.5 a 2050, en comparación con áreas no priorizadas.'
"""
import numpy as np
import scipy.stats as stats
from .motor_biofisico import resolver_mumby_extendido

def evaluar_hipotesis_investigacion(n_simulaciones: int = 150):
    """
    Ejecuta un experimento Monte Carlo comparando:
    - Grupo A (Áreas Priorizadas SRPI con Restauración Focalizada y Protección AMP)
    - Grupo B (Áreas No Priorizadas / Gestión Pasiva bajo RCP 4.5)
    """
    np.random.seed(42)
    
    coberturas_priorizadas_2050 = []
    coberturas_no_priorizadas_2050 = []
    
    # Parámetros climáticos SSP2-4.5 (RCP 4.5) hacia 2050
    dhw_medio = 2.8
    ph_medio = 7.98
    
    for _ in range(n_simulaciones):
        # Ruido ambiental estocástico
        ruido_dhw = np.random.normal(0, 0.4)
        ruido_ph = np.random.normal(0, 0.02)
        
        # 1. ÁREA PRIORIZADA POR EL GEMELO (Tier 1 SRPI)
        # Cuenta con refugio térmico natural, alta rugosidad, restauración con super-corales y AMP
        sim_prio = resolver_mumby_extendido(
            c0=np.random.uniform(0.32, 0.42),
            m0=np.random.uniform(0.18, 0.28),
            años=25,
            dhw_acumulado=max(0.5, dhw_medio + ruido_dhw - 0.6), # efecto refugio térmico
            ph_oceano=ph_medio + ruido_ph,
            pastoreo_g=np.random.uniform(0.42, 0.52),             # AMP herbívoros protegidos
            tasa_restauracion=0.022,                              # Siembra de micro-fragmentos
            endurecimiento_termico=1.6,                           # Super-corales
            reduccion_turbidez=0.25                               # Control de cuencas
        )
        coberturas_priorizadas_2050.append(sim_prio["cobertura_final"])
        
        # 2. ÁREA NO PRIORIZADA (Línea base sin gestión adaptativa)
        sim_no_prio = resolver_mumby_extendido(
            c0=np.random.uniform(0.28, 0.38),
            m0=np.random.uniform(0.25, 0.38),
            años=25,
            dhw_acumulado=max(0.8, dhw_medio + ruido_dhw),
            ph_oceano=ph_medio + ruido_ph,
            pastoreo_g=np.random.uniform(0.22, 0.32),             # Sobrepesca de herbívoros
            tasa_restauracion=0.0,
            endurecimiento_termico=0.0,
            reduccion_turbidez=0.0
        )
        coberturas_no_priorizadas_2050.append(sim_no_prio["cobertura_final"])
        
    arr_prio = np.array(coberturas_priorizadas_2050)
    arr_no_prio = np.array(coberturas_no_priorizadas_2050)
    
    media_prio = float(np.mean(arr_prio))
    std_prio = float(np.std(arr_prio))
    ci95_prio = (float(np.percentile(arr_prio, 2.5)), float(np.percentile(arr_prio, 97.5)))
    
    media_no_prio = float(np.mean(arr_no_prio))
    std_no_prio = float(np.std(arr_no_prio))
    ci95_no_prio = (float(np.percentile(arr_no_prio, 2.5)), float(np.percentile(arr_no_prio, 97.5)))
    
    # Porcentaje de casos que superan el umbral crítico del 30%
    exito_prio_pct = float(np.mean(arr_prio >= 30.0) * 100.0)
    exito_no_prio_pct = float(np.mean(arr_no_prio >= 30.0) * 100.0)
    
    # Prueba t de Student y tamaño del efecto (d de Cohen)
    t_stat, p_val = stats.ttest_ind(arr_prio, arr_no_prio, equal_var=False)
    pooled_std = np.sqrt((std_prio**2 + std_no_prio**2) / 2.0)
    cohen_d = (media_prio - media_no_prio) / pooled_std if pooled_std > 0 else 0.0
    
    # Dictamen de Hipótesis
    hipotesis_confirmada = bool(media_prio >= 30.0 and p_val < 0.001 and media_prio > media_no_prio)
    
    return {
        "hipotesis_confirmada": hipotesis_confirmada,
        "dictamen": "HIPÓTESIS CONFIRMADA" if hipotesis_confirmada else "HIPÓTESIS NO DEMOSTRADA",
        "umbral_esperado_pct": 30.0,
        "media_areas_priorizadas": round(media_prio, 2),
        "ci95_priorizadas": (round(ci95_prio[0], 2), round(ci95_prio[1], 2)),
        "probabilidad_superar_30_prio": round(exito_prio_pct, 1),
        "media_areas_no_priorizadas": round(media_no_prio, 2),
        "ci95_no_priorizadas": (round(ci95_no_prio[0], 2), round(ci95_no_prio[1], 2)),
        "probabilidad_superar_30_no_prio": round(exito_no_prio_pct, 1),
        "diferencia_cobertura_pct": round(media_prio - media_no_prio, 2),
        "estadistico_t": round(float(t_stat), 3),
        "p_valor": float(p_val),
        "cohen_d": round(float(cohen_d), 2),
        "distribucion_priorizada": arr_prio,
        "distribucion_no_priorizada": arr_no_prio
    }
