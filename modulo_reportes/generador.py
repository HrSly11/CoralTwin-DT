# modulo_reportes/generador.py
"""Interfaz gráfica en Streamlit para generación y descarga de reportes multi-formato (Bilingüe)"""
import streamlit as st
from modulo_idioma import obtener_texto
from .reporte_pdf import generar_pdf_ejecutivo
from .reporte_word import generar_word_tecnico
from .reporte_excel import generar_excel_datos

def renderizar_interfaz_reportes():
    """Muestra el panel de configuración y descarga de informes bilingüe"""
    idioma = st.session_state.get("idioma", "es")
    
    st.markdown(f"### {obtener_texto('rep_header', idioma)}")
    st.markdown(obtener_texto('rep_desc', idioma))
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    # 1. Reporte PDF
    with col1:
        st.markdown(f"#### {obtener_texto('rep_pdf_title', idioma)}")
        st.info(obtener_texto('rep_pdf_desc', idioma))
        if st.button(obtener_texto('btn_gen_pdf', idioma), key="btn_gen_pdf"):
            with st.spinner("Compiling PDF..." if idioma == "en" else "Compilando documento PDF..."):
                pdf_data = generar_pdf_ejecutivo()
                st.download_button(
                    label=obtener_texto('btn_dl_pdf', idioma),
                    data=pdf_data,
                    file_name="CoralTwin_DT_Executive_Report.pdf" if idioma == "en" else "CoralTwin_DT_Reporte_Ejecutivo.pdf",
                    mime="application/pdf",
                    key="dl_pdf"
                )
                st.success(obtener_texto('pdf_success', idioma))
                
    # 2. Documento Word
    with col2:
        st.markdown(f"#### {obtener_texto('rep_word_title', idioma)}")
        st.info(obtener_texto('rep_word_desc', idioma))
        if st.button(obtener_texto('btn_gen_word', idioma), key="btn_gen_word"):
            with st.spinner("Structuring Word document..." if idioma == "en" else "Estructurando archivo .docx..."):
                word_data = generar_word_tecnico()
                st.download_button(
                    label=obtener_texto('btn_dl_word', idioma),
                    data=word_data,
                    file_name="CoralTwin_DT_Technical_Report.docx" if idioma == "en" else "CoralTwin_DT_Dictamen_Tecnico.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="dl_word"
                )
                st.success(obtener_texto('word_success', idioma))
                
    # 3. Libro de Cálculo Excel
    with col3:
        st.markdown(f"#### {obtener_texto('rep_excel_title', idioma)}")
        st.info(obtener_texto('rep_excel_desc', idioma))
        if st.button(obtener_texto('btn_gen_excel', idioma), key="btn_gen_excel"):
            with st.spinner("Extracting datasets to Excel..." if idioma == "en" else "Extrayendo matrices de datos a Excel..."):
                excel_data = generar_excel_datos()
                st.download_button(
                    label=obtener_texto('btn_dl_excel', idioma),
                    data=excel_data,
                    file_name="CoralTwin_DT_Complete_Data.xlsx" if idioma == "en" else "CoralTwin_DT_Datos_Completos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_excel"
                )
                st.success(obtener_texto('excel_success', idioma))
