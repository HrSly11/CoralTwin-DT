# modulo_chatbot/interfaz_chat.py
"""Interfaz conversacional para el asistente científico CoralAI en Streamlit (Bilingüe)"""
import streamlit as st
from modulo_idioma import obtener_texto
from .asistente_ecologico import responder_consulta_asistente

def renderizar_interfaz_chatbot():
    """Renderiza el chat interactivo con soporte de idioma español e inglés"""
    idioma = st.session_state.get("idioma", "es")
    
    st.markdown(f"### 🤖 {obtener_texto('chat_titulo', idioma)}")
    if idioma == "en":
        st.caption("⚡ **Artificial Intelligence Engine:** Google Gemini (`gemini-3.6-flash`) | Langflow Decoupled Architecture")
    else:
        st.caption("⚡ **Motor de Inteligencia Artificial:** Google Gemini (`gemini-3.6-flash`) | Arquitectura desacoplada Langflow")
        
    st.markdown(obtener_texto("chat_subtitulo", idioma))
    st.markdown("---")
    
    if "historial_chat_coral" not in st.session_state:
        msg_init = "👋 Hello! I am **CoralAI**, your scientific assistant for the Digital Twin of Coral Reefs. How can I help you today?" if idioma == "en" else "👋 ¡Hola! Soy **CoralAI**, tu asistente para el Gemelo Digital de Arrecifes de Coral. ¿En qué puedo ayudarte hoy?"
        st.session_state["historial_chat_coral"] = [
            {"rol": "asistente", "mensaje": msg_init}
        ]
        
    # Preguntas rápidas recomendadas
    txt_sug = "**💡 Suggested Quick Inquiries:**" if idioma == "en" else "**💡 Consultas rápidas sugeridas:**"
    st.markdown(txt_sug)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button(obtener_texto("btn_q1", idioma), key="btn_q1"):
            _procesar_pregunta(obtener_texto("txt_q1", idioma), idioma)
            st.rerun()
    with col2:
        if st.button(obtener_texto("btn_q2", idioma), key="btn_q2"):
            _procesar_pregunta(obtener_texto("txt_q2", idioma), idioma)
            st.rerun()
    with col3:
        if st.button(obtener_texto("btn_q3", idioma), key="btn_q3"):
            _procesar_pregunta(obtener_texto("txt_q3", idioma), idioma)
            st.rerun()
    with col4:
        if st.button(obtener_texto("btn_q4", idioma), key="btn_q4"):
            _procesar_pregunta(obtener_texto("txt_q4", idioma), idioma)
            st.rerun()
            
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
    pregunta_usuario = st.chat_input(obtener_texto("chat_placeholder", idioma))
    if pregunta_usuario:
        _procesar_pregunta(pregunta_usuario, idioma)
        st.rerun()

def _procesar_pregunta(pregunta: str, idioma: str = "es"):
    """Agrega al historial la pregunta y genera la respuesta de CoralAI"""
    st.session_state["historial_chat_coral"].append({"rol": "usuario", "mensaje": pregunta})
    spinner_msg = "CoralAI is analyzing reef models and telemetry..." if idioma == "en" else "CoralAI está analizando los datos y modelos..."
    with st.spinner(spinner_msg):
        respuesta = responder_consulta_asistente(pregunta, idioma)
    st.session_state["historial_chat_coral"].append({"rol": "asistente", "mensaje": respuesta})
