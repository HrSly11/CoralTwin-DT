# modulo_chatbot/asistente_ecologico.py
"""
Motor de respuesta del Asistente CoralAI con arquitectura híbrida e internacionalización:
1. Langflow REST API (cuando el servidor local está activo en puerto 7860)
2. Google Gemini SDK nativo (fallback de alta disponibilidad usando google-genai)
3. Base de conocimiento heurística local (modo offline de contingencia)
"""
import os
from pathlib import Path
import requests

# Cargar variables de entorno si existen
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

LANGFLOW_HOST = os.getenv("LANGFLOW_HOST", "127.0.0.1")
LANGFLOW_PORT = os.getenv("LANGFLOW_PORT", "7860")
LANGFLOW_URL = os.getenv("LANGFLOW_URL") or f"http://{LANGFLOW_HOST}:{LANGFLOW_PORT}/api/v1/run"

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

PROMPT_SISTEMA_CORAL_ES = """
Eres CoralAI, el asistente científico y técnico integrado en el Gemelo Digital de Arrecifes de Coral (CoralTwin-DT).
Tu propósito es responder consultas sobre:
1. Estrés térmico acumulado NOAA (Degree Heating Weeks, DHW) y umbrales de blanqueamiento.
2. Acidificación oceánica (pH superficial, estado de saturación de aragonita Ω_arag y su impacto en Ca²⁺/H⁺-ATPase).
3. Dinámica biofísica con ecuaciones diferenciales de Mumby et al. (2007) para competencia coral-macroalga-turf y pastoreo herbívoro.
4. Índice de Priorización de Restauración Espacial (SRPI) y categorización de estaciones en Tiers 1, 2 y 3.
5. Inferencia de Machine Learning: arquitectura XGBoost multi-tarea (exactitud 98.85%, latencia de 0.009 ms/muestra) y explicabilidad TreeSHAP.
6. Proyecciones decenales 2025–2050 (escenarios climáticos SSP5-8.5 y SSP2-4.5 con siembra de super-corales).
7. Arquitectura ciberfísica de seis capas y literatura de ingeniería de software (Dalibor et al., 2022; Guinea-Cabrera & Holgado-Terriza, 2024).

Instrucciones:
- Responde de forma clara, rigurosa, profesional y concisa en español.
- Utiliza formato Markdown y fórmulas LaTeX cuando clarifiquen la explicación.
"""

PROMPT_SISTEMA_CORAL_EN = """
You are CoralAI, the scientific and technical assistant integrated into the Digital Twin of Coral Reefs (CoralTwin-DT).
Your purpose is to answer queries regarding:
1. NOAA accumulated heat stress (Degree Heating Weeks, DHW) and bleaching alert thresholds.
2. Ocean acidification (surface pH, aragonite saturation state Ω_arag, and impacts on Ca²⁺/H⁺-ATPase proton extrusion).
3. Biophysical dynamics via coupled differential equations of Mumby et al. (2007) for coral-macroalgal-turf competition and herbivory.
4. Spatial Restoration Priority Index (SRPI) and station tier ranking (Tiers 1, 2, and 3).
5. Machine Learning inference: multi-task XGBoost architecture (98.85% accuracy, 0.009 ms/sample latency) and TreeSHAP explainability.
6. Decadal projections 2025–2050 (SSP5-8.5 collapse vs SSP2-4.5 active restoration with super-corals).
7. Six-layer cyber-physical architecture and software engineering literature (Dalibor et al., 2022; Guinea-Cabrera & Holgado-Terriza, 2024).

Instructions:
- Respond clearly, rigorously, professionally, and concisely in English.
- Use Markdown and LaTeX formatting for formulas when helpful.
"""

BASE_CONOCIMIENTO_ES = [
    {
        "keywords": ["dhw", "estres termico", "ola de calor", "calor", "grados", "semanas"],
        "respuesta": """
        **Degree Heating Weeks (DHW):**
        Métrica estándar de **NOAA Coral Reef Watch** que acumula anomalías térmicas positivas en 12 semanas móviles:
        - **DHW < 4 °C-semanas:** Vigilancia (Watch).
        - **4 ≤ DHW < 8 °C-semanas:** Advertencia (Warning) — Blanqueamiento en especies sensibles.
        - **8 ≤ DHW < 12 °C-semanas:** Alerta Nivel 1 — Blanqueamiento masivo severo.
        - **DHW ≥ 12 °C-semanas:** Alerta Nivel 2 — Mortalidad catastrófica (> 50%).
        """
    },
    {
        "keywords": ["acidificacion", "ph", "aragonita", "calcificacion", "omega"],
        "respuesta": """
        **Acidificación Oceánica y Calcificación:**
        La absorción antropogénica de CO₂ reduce el pH oceánico superficial y el estado de saturación de aragonita ($\\Omega_{\\text{arag}}$).
        - Con pH $\\le 7.85$, el gradiente de protones dificulta el bombeo $\\text{Ca}^{2+}/\\text{H}^+\\text{-ATPase}$.
        - Esto comprime el umbral térmico crítico en **2.6 °C-semanas** (de 8.4 a 5.8 DHW, reducción del 30.95%).
        """
    },
    {
        "keywords": ["mumby", "ode", "ecuacion", "modelo", "diferencial", "dinamica"],
        "respuesta": """
        **Modelo de Ecuaciones Diferenciales de Mumby et al. (2007):**
        $$\\frac{dC}{dt} = r C T - d(DHW, pH) C + \\gamma_{\\text{resto}}$$
        $$\\frac{dM}{dt} = a M T - \\frac{g}{1 - C} M + \\mu(pH)$$
        $$T = 1 - C - M$$
        """
    },
    {
        "keywords": ["srpi", "priorizacion", "restauracion", "zonas", "tier", "ranking"],
        "respuesta": """
        **Índice de Priorización de Restauración Espacial (SRPI):**
        $$\\text{SRPI} = 0.35 \\cdot S_{\\text{refugio}} + 0.25 \\cdot S_{\\text{rugosidad}} + 0.25 \\cdot S_{\\text{calidad\\_agua}} + 0.15 \\cdot S_{\\text{biodiversidad}}$$
        - **Tier 1:** Refugios térmicos y alta rugosidad para siembra activa de super-corales.
        - **Tier 2:** Mitigación de presiones locales antes de siembra intensiva.
        - **Tier 3:** Monitoreo pasivo o zonas crónicamente degradadas.
        """
    },
    {
        "keywords": ["hipotesis", "30%", "2050", "rcp 4.5", "ssp2-4.5", "validacion"],
        "respuesta": """
        **Evaluación de la Hipótesis Principal:**
        En áreas **Tier 1 priorizadas** bajo SSP2-4.5 con siembra de super-corales y AMP activa, la cobertura media proyectada a 2050 se sostiene en **46.2%** con acreción positiva (+6.80 kg CaCO₃ m⁻² yr⁻¹), superando ampliamente el umbral del 30% ($p < 0.001$).
        """
    }
]

BASE_CONOCIMIENTO_EN = [
    {
        "keywords": ["dhw", "thermal stress", "heatwave", "degree", "weeks"],
        "respuesta": """
        **Degree Heating Weeks (DHW):**
        Standard NOAA Coral Reef Watch bioclimatic metric accumulating thermal anomalies over a 12-week window:
        - **DHW < 4 °C-weeks:** Watch — Mild thermal stress.
        - **4 ≤ DHW < 8 °C-weeks:** Warning — Significant bleaching in sensitive taxa (*Acropora*).
        - **8 ≤ DHW < 12 °C-weeks:** Alert Level 1 — Severe mass bleaching and initial mortality.
        - **DHW ≥ 12 °C-weeks:** Alert Level 2 — Catastrophic mortality (> 50%).
        """
    },
    {
        "keywords": ["acidification", "ph", "aragonite", "calcification", "omega"],
        "respuesta": """
        **Ocean Acidification & Calcification:**
        Anthropogenic CO₂ absorption lowers surface seawater pH and aragonite saturation ($\\Omega_{\\text{arag}}$).
        - Below pH $\\le 7.85$, proton extrusion demands elevated cellular ATP via $\\text{Ca}^{2+}/\\text{H}^+\\text{-ATPase}$.
        - This compresses the critical thermal tipping point by **2.6 °C-weeks** (8.4 down to 5.8 DHW, a 30.95% reduction).
        """
    },
    {
        "keywords": ["mumby", "ode", "differential", "equation", "dynamics"],
        "respuesta": """
        **Coupled Benthic Differential Equations (Mumby et al., 2007):**
        $$\\frac{dC}{dt} = r C T - d(DHW, pH) C + \\gamma_{\\text{resto}}$$
        $$\\frac{dM}{dt} = a M T - \\frac{g}{1 - C} M + \\mu(pH)$$
        $$T = 1 - C - M$$
        """
    },
    {
        "keywords": ["srpi", "priority", "restoration", "tier", "ranking"],
        "respuesta": """
        **Spatial Restoration Priority Index (SRPI):**
        $$\\text{SRPI} = 0.35 \\cdot S_{\\text{refugia}} + 0.25 \\cdot S_{\\text{rugosity}} + 0.25 \\cdot S_{\\text{water\\_quality}} + 0.15 \\cdot S_{\\text{biodiversity}}$$
        - **Tier 1:** Thermal refugia and high rugosity selected for super-coral outplanting.
        - **Tier 2:** Local stressor mitigation prior to outplanting.
        - **Tier 3:** Passive monitoring and chronic exposure zones.
        """
    },
    {
        "keywords": ["hypothesis", "30%", "2050", "rcp 4.5", "ssp2-4.5"],
        "respuesta": """
        **Scientific Hypothesis Evaluation:**
        Under SSP2-4.5 with active outplanting and protected herbivory, **Tier 1 priority areas** sustain **46.2%** mean coral cover by 2050, significantly outperforming non-prioritized areas ($p < 0.001$).
        """
    }
]


def _consultar_langflow(pregunta: str) -> str:
    """Intenta consultar el endpoint REST de Langflow si el servicio está corriendo"""
    try:
        payload = {
            "input_value": pregunta,
            "output_type": "chat",
            "input_type": "chat"
        }
        resp = requests.post(f"{LANGFLOW_URL}/CoralTwin-Chat", json=payload, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            outputs = data.get("outputs", [{}])[0].get("outputs", [{}])[0]
            msg = outputs.get("results", {}).get("message", {}).get("text") or outputs.get("artifacts", {}).get("message")
            if msg:
                return f"[Langflow]\n\n{msg}"
    except Exception:
        pass
    return None


def _consultar_gemini(pregunta: str, idioma: str = "es") -> str:
    """Consulta directa al SDK oficial de Gemini con selector de idioma"""
    if not GEMINI_API_KEY:
        return None
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        sys_prompt = PROMPT_SISTEMA_CORAL_EN if idioma == "en" else PROMPT_SISTEMA_CORAL_ES
        prompt_completo = f"{sys_prompt}\n\nUser Question: {pregunta}"
        res = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt_completo
        )
        if res and res.text:
            return res.text.strip()
    except Exception:
        pass
    return None


def responder_consulta_asistente(pregunta: str, idioma: str = "es") -> str:
    """
    Orquesta la respuesta:
    1. Intenta Langflow si está activo
    2. Si Langflow no responde, invoca Gemini vía google-genai
    3. Si no hay conexión o API Key, recurre a la base de conocimiento local
    """
    # 1. Probar Langflow
    resp_lf = _consultar_langflow(pregunta)
    if resp_lf:
        return resp_lf

    # 2. Probar Gemini directamente
    resp_gemini = _consultar_gemini(pregunta, idioma)
    if resp_gemini:
        return resp_gemini

    # 3. Fallback Heurístico local
    base = BASE_CONOCIMIENTO_EN if idioma == "en" else BASE_CONOCIMIENTO_ES
    p_lower = pregunta.lower()
    for item in base:
        for kw in item["keywords"]:
            if kw in p_lower:
                return item["respuesta"]

    if idioma == "en":
        return """
        **CoralAI (Offline Mode):**
        Unable to reach Langflow server or Gemini API.
        Local topics available:
        - What is **DHW** and how are bleaching alerts calculated?
        - How does **ocean acidification** impact coral reefs?
        - How do the **Mumby ODE** differential equations operate?
        - What is the **SRPI** spatial priority index?
        - Is the **hypothesis** of coral survival by 2050 supported?
        """
    else:
        return """
        **CoralAI (Modo Offline):**
        No se pudo conectar con el servidor de Langflow ni con la API de Gemini.
        Mostrando temas disponibles en la base de conocimiento local:
        - ¿Qué es el **DHW** y cómo se calculan las alertas de blanqueamiento?
        - ¿Cómo impacta la **acidificación oceánica** en los corales?
        - ¿Cómo funcionan las ecuaciones diferenciales de **Mumby**?
        - ¿Qué es el índice **SRPI** y cómo prioriza las estaciones?
        - ¿Se cumple la **hipótesis** de conservación a 2050?
        """
