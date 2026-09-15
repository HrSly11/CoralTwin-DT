# modulo_chatbot/interfaz_chat.py
"""Interfaz conversacional para el asistente científico CoralAI en Streamlit"""
import streamlit as st
from .asistente_ecologico import responder_consulta_asistente

def renderizar_interfaz_chatbot():
    """Renderiza el chat interactivo en el panel principal o pestaña dedicada"""
    st.markdown("### 🤖 Asistente Científico CoralAI")
    st.markdown("Consulte dudas sobre dinámicas ecológicas, parámetros oceanográficos, formulación de modelos y resultados de la investigación.")
    st.markdown("---")
    
    if "historial_chat_coral" not in st.session_state:
        st.session_state["historial_chat_coral"] = [
            {"rol": "asistente", "mensaje": "👋 ¡Hola! Soy **CoralAI**, tu asistente para el Gemelo Digital de Arrecifes de Coral. ¿En qué puedo ayudarte hoy?"}
        ]
        
    # Preguntas rápidas recomendadas
    st.markdown("**💡 Consultas rápidas sugeridas:**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🌡️ ¿Qué es el DHW?", key="btn_q1"):
            _procesar_pregunta("¿Cómo se calcula el estrés térmico acumulado DHW y qué umbrales tiene?")
    with col2:
        if st.button("🧪 Impacto del pH", key="btn_q2"):
            _procesar_pregunta("¿Cómo afecta la acidificación oceánica a la calcificación del coral?")
    with col3:
        if st.button("📈 Ecuaciones de Mumby", key="btn_q3"):
            _procesar_pregunta("Explícame las ecuaciones diferenciales de Mumby para arrecifes")
    with col4:
        if st.button("🎯 Validación de Hipótesis", key="btn_q4"):
            _procesar_pregunta("¿Se cumple la hipótesis de cobertura superior al 30% a 2050 en RCP 4.5?")
            
    st.markdown("---")
    
    # Historial de mensajes
    for chat in st.session_state["historial_chat_coral"]:
        if chat["rol"] == "usuario":
            with st.chat_message("user", avatar="👤"):
                st.markdown(chat["mensaje"])
        else:
            with st.chat_message("assistant", avatar="🪸"):
                st.markdown(chat["mensaje"])
                
    # Entrada de texto del usuario
    pregunta_usuario = st.chat_input("Escribí tu consulta sobre el gemelo digital...")
    if pregunta_usuario:
        _procesar_pregunta(pregunta_usuario)
        st.rerun()

def _procesar_pregunta(pregunta: str):
    """Agrega al historial la pregunta y genera la respuesta de CoralAI"""
    st.session_state["historial_chat_coral"].append({"rol": "usuario", "mensaje": pregunta})
    respuesta = responder_consulta_asistente(pregunta)
    st.session_state["historial_chat_coral"].append({"rol": "asistente", "mensaje": respuesta})
