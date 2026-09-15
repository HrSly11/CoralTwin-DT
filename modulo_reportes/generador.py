# modulo_reportes/generador.py
"""Interfaz gráfica en Streamlit para generación y descarga de reportes multi-formato"""
import streamlit as st
from .reporte_pdf import generar_pdf_ejecutivo
from .reporte_word import generar_word_tecnico
from .reporte_excel import generar_excel_datos

def renderizar_interfaz_reportes():
    """Muestra el panel de configuración y descarga de informes"""
    st.markdown("### 📑 Centro de Generación de Reportes Técnicos y Ejecutivos")
    st.markdown("Exporte diagnósticos, zonificaciones espaciales de restauración y series temporales para entidades gubernamentales y científicas.")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    # 1. Reporte PDF
    with col1:
        st.markdown("#### 📄 Informe Ejecutivo (PDF)")
        st.info("Resumen de alto nivel con KPIs, tabla de priorización de estaciones Tier 1 y recomendaciones operativas de restauración.")
        if st.button("🔄 Generar PDF", key="btn_gen_pdf"):
            with st.spinner("Compilando documento PDF..."):
                pdf_data = generar_pdf_ejecutivo()
                st.download_button(
                    label="⬇️ Descargar Reporte PDF",
                    data=pdf_data,
                    file_name="CoralTwin_DT_Reporte_Ejecutivo.pdf",
                    mime="application/pdf",
                    key="dl_pdf"
                )
                st.success("✅ PDF compilado exitosamente.")
                
    # 2. Documento Word
    with col2:
        st.markdown("#### 📝 Dictamen Técnico (Word .docx)")
        st.info("Documento exhaustivo con metodología de acoplamiento de ODEs, marco de asimilación NOAA y tablas formateadas.")
        if st.button("🔄 Generar Word", key="btn_gen_word"):
            with st.spinner("Estructurando archivo .docx..."):
                word_data = generar_word_tecnico()
                st.download_button(
                    label="⬇️ Descargar Documento Word",
                    data=word_data,
                    file_name="CoralTwin_DT_Dictamen_Tecnico.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="dl_word"
                )
                st.success("✅ Word generado exitosamente.")
                
    # 3. Libro de Cálculo Excel
    with col3:
        st.markdown("#### 📊 Datos y Modelos (Excel .xlsx)")
        st.info("Libro de cálculo con 3 hojas: Resumen de KPIs, Ranking completo SRPI de 25 estaciones y series históricas.")
        if st.button("🔄 Generar Excel", key="btn_gen_excel"):
            with st.spinner("Extrayendo matrices de datos a Excel..."):
                excel_data = generar_excel_datos()
                st.download_button(
                    label="⬇️ Descargar Libro Excel",
                    data=excel_data,
                    file_name="CoralTwin_DT_Datos_Completos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_excel"
                )
                st.success("✅ Excel generado exitosamente.")
