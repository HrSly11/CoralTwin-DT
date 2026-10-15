# utilidades/tema.py
"""Gestor de temas dinámicos (Claro y Oscuro) para CoralTwin-DT en Streamlit"""
import streamlit as st

CSS_TEMA_OSCURO = """
<style>
/* === TEMA OSCURO OCEÁNICO CORALTWIN-DT === */
.stApp {
    background-color: #0b1120 !important;
    color: #f1f5f9 !important;
}

/* Barra lateral */
[data-testid="stSidebar"] {
    background-color: #0f172a !important;
    border-right: 1px solid #1e293b !important;
}
[data-testid="stSidebar"] * {
    color: #cbd5e1 !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 {
    color: #38bdf8 !important;
}

/* Tarjetas y métricas */
div[data-testid="stMetric"] {
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    padding: 12px !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
}
div[data-testid="stMetricValue"] {
    color: #38bdf8 !important;
    font-weight: 700 !important;
}
div[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
}

/* Títulos y textos principales */
h1, h2, h3, h4, h5, h6 {
    color: #f8fafc !important;
}
p, span, label {
    color: #cbd5e1 !important;
}

/* Botones */
div.stButton > button {
    background-color: #1e293b !important;
    color: #38bdf8 !important;
    border: 1px solid #0284c7 !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
div.stButton > button:hover {
    background-color: #0284c7 !important;
    color: #ffffff !important;
    border-color: #38bdf8 !important;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.5) !important;
}

/* Pestañas (Tabs) */
button[data-baseweb="tab"] {
    color: #94a3b8 !important;
    background-color: transparent !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #38bdf8 !important;
    border-bottom: 2px solid #38bdf8 !important;
    font-weight: bold !important;
}

/* Chatbot */
[data-testid="stChatMessage"] {
    background-color: #162032 !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
}

/* Inputs y Selectboxes */
div[data-baseweb="select"] > div {
    background-color: #1e293b !important;
    color: #f1f5f9 !important;
    border-color: #334155 !important;
}

/* Dataframes y Tablas */
[data-testid="stDataFrame"] {
    background-color: #1e293b !important;
    border-radius: 6px !important;
}
</style>
"""

CSS_TEMA_CLARO = """
<style>
/* === TEMA CLARO OCEÁNICO CORALTWIN-DT === */
.stApp {
    background-color: #f8fafc !important;
    color: #0f172a !important;
}

/* Barra lateral */
[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
}
[data-testid="stSidebar"] * {
    color: #334155 !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 {
    color: #0284c7 !important;
}

/* Tarjetas y métricas */
div[data-testid="stMetric"] {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    padding: 12px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
}
div[data-testid="stMetricValue"] {
    color: #0284c7 !important;
    font-weight: 700 !important;
}
div[data-testid="stMetricLabel"] {
    color: #64748b !important;
}

/* Títulos y textos principales */
h1, h2, h3, h4, h5, h6 {
    color: #0f172a !important;
}
p, span, label {
    color: #334155 !important;
}

/* Botones */
div.stButton > button {
    background-color: #ffffff !important;
    color: #0284c7 !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
div.stButton > button:hover {
    background-color: #0284c7 !important;
    color: #ffffff !important;
    border-color: #0284c7 !important;
    box-shadow: 0 2px 6px rgba(2, 132, 199, 0.3) !important;
}

/* Pestañas (Tabs) */
button[data-baseweb="tab"] {
    color: #64748b !important;
    background-color: transparent !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #0284c7 !important;
    border-bottom: 2px solid #0284c7 !important;
    font-weight: bold !important;
}

/* Chatbot */
[data-testid="stChatMessage"] {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
}

/* Inputs y Selectboxes */
div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    color: #0f172a !important;
    border-color: #cbd5e1 !important;
}
</style>
"""

def aplicar_tema(tema: str = "claro"):
    """Inyecta los estilos CSS correspondientes al tema seleccionado"""
    if tema == "oscuro":
        st.markdown(CSS_TEMA_OSCURO, unsafe_allow_html=True)
    else:
        st.markdown(CSS_TEMA_CLARO, unsafe_allow_html=True)
