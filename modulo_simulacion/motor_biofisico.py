# modulo_simulacion/motor_biofisico.py
"""
Motor dinámico biofísico acoplado para el ecosistema arrecifal
Implementa las Ecuaciones Diferenciales Ordinarias (ODEs) de Mumby et al. (2007)
ampliadas para estrés térmico (DHW) y acidificación oceánica (pH, saturación de aragonita).
"""
import numpy as np

def resolver_mumby_extendido(
    c0: float = 0.35,
    m0: float = 0.25,
    años: int = 25,
    paso_dt: float = 0.05,
    tasa_crecimiento_r: float = 0.10,
    tasa_competencia_a: float = 0.18,
    pastoreo_g: float = 0.35,
    mortalidad_base_d: float = 0.04,
    dhw_acumulado: float = 2.0,
    ph_oceano: float = 8.08,
    tasa_restauracion: float = 0.0,
    endurecimiento_termico: float = 0.0,
    reduccion_turbidez: float = 0.0
):
    """
    Integra numéricamente el modelo tridimensional de espacio arrecifal:
    C: Cobertura Coralina Viva [0, 1]
    M: Cobertura de Macroalgas [0, 1]
    T: Césped Algal Pastoreable (Turf) = 1 - C - M

    Ecuaciones:
    dC/dt = r * C * T - d_eff(DHW, pH) * C + gamma_resto
    dM/dt = a * M * T - (g / (1 - C)) * M + mu(pH)
    """
    n_pasos = int(años / paso_dt)
    t_eval = np.linspace(0, años, n_pasos)
    
    C_traj = np.zeros(n_pasos)
    M_traj = np.zeros(n_pasos)
    T_traj = np.zeros(n_pasos)
    calc_traj = np.zeros(n_pasos)
    
    # Condiciones iniciales
    C = float(np.clip(c0, 0.01, 0.95))
    M = float(np.clip(m0, 0.01, 0.95 - C))
    
    # Impacto de acidificación sobre calcificación: delta pH desde 8.10
    delta_ph = max(0.0, 8.10 - ph_oceano)
    factor_calcificacion = max(0.2, 1.0 - 0.75 * delta_ph)
    
    # Mortalidad coralina sensible a olas de calor (DHW)
    # Mitigada si los corales tienen endurecimiento térmico (super-corales)
    dhw_efectivo = max(0.0, dhw_acumulado - endurecimiento_termico)
    mortalidad_termica = 0.015 * (dhw_efectivo ** 1.35)
    d_eff = mortalidad_base_d + mortalidad_termica
    
    # Crecimiento coralino ajustado por calcificación y claridad del agua
    r_eff = tasa_crecimiento_r * factor_calcificacion * (1.0 + 0.15 * reduccion_turbidez)
    
    # Crecimiento macroalgal estimulado si el pH baja o falta pastoreo
    mu_acid = 0.02 * delta_ph
    
    for i in range(n_pasos):
        C_traj[i] = C
        M_traj[i] = M
        T = max(0.0, 1.0 - C - M)
        T_traj[i] = T
        calc_traj[i] = C * factor_calcificacion * 12.5  # kg CaCO3/m2/año estimado
        
        # Derivadas de Mumby
        dC = r_eff * C * T - d_eff * C + tasa_restauracion
        # Término de pastoreo con límite biológico para evitar asíntotas cuando C -> 1
        denominador_g = max(0.08, 1.0 - C)
        dM = tasa_competencia_a * M * T - (pastoreo_g / denominador_g) * M + mu_acid
        
        # Integración Runge-Kutta de 2do orden (Heun)
        C_next = np.clip(C + dC * paso_dt, 0.005, 0.95)
        M_next = np.clip(M + dM * paso_dt, 0.005, 0.95 - C_next)
        
        C = C_next
        M = M_next
        
    return {
        "tiempo_años": t_eval,
        "cobertura_coral": C_traj * 100.0,       # en porcentaje
        "cobertura_macroalgas": M_traj * 100.0,  # en porcentaje
        "cesped_turf": T_traj * 100.0,           # en porcentaje
        "tasa_calcificacion": calc_traj,
        "cobertura_final": float(C_traj[-1] * 100.0),
        "macroalgas_final": float(M_traj[-1] * 100.0),
        "resiliencia_estado": "Dominado por Coral" if C_traj[-1] > M_traj[-1] else "Colapso / Fase Macroalgal"
    }
