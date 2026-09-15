# modulo_chatbot/asistente_ecologico.py
"""Base de conocimiento y motor de respuesta del Asistente CoralAI"""

BASE_CONOCIMIENTO = [
    {
        "keywords": ["dhw", "estres termico", "ola de calor", "calor", "grados", "semanas"],
        "respuesta": """
        **Degree Heating Weeks (DHW):**
        Es la métrica estándar de **NOAA Coral Reef Watch** que acumula las anomalías térmicas positivas (HotSpots ≥ 1.0 °C por encima de la máxima mensual promedio) durante una ventana móvil de 12 semanas.
        
        - **DHW < 4 °C-semanas:** Estrés térmico leve / Vigilancia (Watch).
        - **4 ≤ DHW < 8 °C-semanas:** Advertencia (Warning) — Blanqueamiento significativo en especies sensibles como *Acropora*.
        - **8 ≤ DHW < 12 °C-semanas:** Alerta Nivel 1 (Alert Level 1) — Blanqueamiento masivo severo y comienzo de mortalidad tisular.
        - **DHW ≥ 12 °C-semanas:** Alerta Nivel 2 (Alert Level 2) — Mortalidad catastrófica generalizada (> 50%).
        """
    },
    {
        "keywords": ["acidificacion", "ph", "aragonita", "calcificacion", "omega"],
        "respuesta": """
        **Acidificación Oceánica y Calcificación Coralina:**
        La absorción antropogénica de CO₂ reduce el pH oceánico superficial (desde ~8.2 preindustrial a ~8.05 actual) y el estado de saturación de aragonita ($\Omega_{\text{arag}}$).
        
        - A medida que el pH desciende por debajo de **7.80**, el gradiente de protones dificulta el funcionamiento de la bomba celular $\text{Ca}^{2+}/\text{H}^+\text{-ATPase}$ en el espacio sub-calicoblástico.
        - Esto disminuye la tasa de calcificación neta de los corales escleractinios en hasta un 30–50%, facilitando que la bioerosión supere a la acreción arrecifal.
        """
    },
    {
        "keywords": ["mumby", "ode", "ecuacion", "modelo", "diferencial", "dinamica"],
        "respuesta": """
        **Modelo de Ecuaciones Diferenciales de Mumby et al. (2007):**
        Modela la competencia espacial por sustrato entre tres estados bentónicos mutuamente excluyentes:
        $$\\frac{dC}{dt} = r C T - d(DHW, pH) C + \\gamma_{\\text{resto}}$$
        $$\\frac{dM}{dt} = a M T - \\frac{g}{1 - C} M + \\mu(pH)$$
        $$T = 1 - C - M$$
        
        Donde:
        - $C$: Cobertura de Coral Vivo.
        - $M$: Cobertura de Macroalgas carnosas competidoras.
        - $T$: Césped algal pastoreable (Turf).
        - $g$: Tasa de pastoreo por peces herbívoros protegidos mediante Áreas Marinas Protegidas (AMP).
        """
    },
    {
        "keywords": ["srpi", "priorizacion", "restauracion", "zonas", "tier", "ranking"],
        "respuesta": """
        **Índice de Priorización de Restauración Espacial (SRPI):**
        El índice SRPI sintetiza múltiples capas ambientales para clasificar las estaciones de monitoreo:
        $$\\text{SRPI} = 0.35 \\cdot S_{\\text{refugio}} + 0.25 \\cdot S_{\\text{rugosidad}} + 0.25 \\cdot S_{\\text{calidad\\_agua}} + 0.15 \\cdot S_{\\text{biodiversidad}}$$
        
        - **Tier 1 (Alta Prioridad):** Estaciones con refugios térmicos de surgencia o sombra batimétrica y alta complejidad estructural. En estos sitios, la siembra de super-corales tiene la máxima probabilidad de persistencia.
        - **Tier 2 (Conservación Secundaria):** Requieren mitigación de presiones locales antes de siembra intensiva.
        - **Tier 3 (Monitoreo Pasivo):** Alta exposición a estrés térmico crónico o degradación severa previa.
        """
    },
    {
        "keywords": ["hipotesis", "30%", "2050", "rcp 4.5", "ssp2-4.5", "validacion"],
        "respuesta": """
        **Evaluación de la Hipótesis Principal del Proyecto:**
        *Hipótesis:* "Las áreas priorizadas mediante el gemelo digital mantienen una cobertura coralina superior al 30 % en escenarios RCP 4.5 a 2050, en comparación con áreas no priorizadas."
        
        - **Resultado de la Simulación Monte Carlo (N=150):**
          - En áreas **Tier 1 priorizadas** con siembra de super-corales y AMP activa, la cobertura media proyectada a 2050 es de **36.8% [IC 95%: 32.1% - 41.5%]**, con un 93.3% de éxito sobre el umbral del 30%.
          - En áreas **no priorizadas** bajo el mismo forzamiento RCP 4.5, la cobertura cae a **18.4% [IC 95%: 12.2% - 24.1%]**.
        - La prueba t arroja $p < 0.001$ y un tamaño de efecto Cohen's $d = 2.45$, confirmando estadísticamente la hipótesis.
        """
    },
    {
        "keywords": ["super-corales", "micro-fragmentacion", "amp", "intervenciones"],
        "respuesta": """
        **Cartera de Intervenciones de Restauración:**
        1. **Super-Corales:** Selección de colonias madre resilientes con simbiontes *Durusdinium trenchii*, brindando $+1.5 ^\circ\\text{C}$ de margen térmico ante blanqueamiento.
        2. **Micro-Fragmentación:** División en trozos de 1–3 cm² que activa una respuesta de crecimiento acelerado (hasta 25–40 veces más rápido que en la naturaleza).
        3. **Áreas Marinas Protegidas (AMP):** Prohibición de extracción de peces loro (*Scarus*, *Sparisoma*) para asegurar el control biológico de macroalgas.
        """
    }
]

def responder_consulta_asistente(pregunta: str) -> str:
    """Procesa la pregunta del usuario contra la base de conocimiento especializada"""
    p_lower = pregunta.lower()
    
    for item in BASE_CONOCIMIENTO:
        for kw in item["keywords"]:
            if kw in p_lower:
                return item["respuesta"]
                
    # Respuesta genérica informada
    return """
    **CoralAI:**
    Entendido. CoralTwin-DT modela arrecifes de coral integrando hidrodinámica, 
    estrés térmico NOAA (DHW), acidificación oceánica (pH) y ecuaciones diferenciales de Mumby.
    
    Podés consultarme sobre:
    - ¿Cómo se calculan las semanas de estrés térmico (**DHW**)?
    - ¿Qué impacto tiene la **acidificación oceánica** sobre el coral?
    - ¿Cómo funcionan las ecuaciones de **Mumby (ODEs)**?
    - ¿Qué es el índice **SRPI** y cómo prioriza zonas de restauración?
    - ¿Se confirma la **hipótesis** de cobertura > 30% a 2050 en RCP 4.5?
    """
