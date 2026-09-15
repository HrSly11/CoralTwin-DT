# modulo_reportes/reporte_pdf.py
"""Generación de informe ejecutivo en formato PDF utilizando ReportLab"""
import io
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from modulo_base_datos.repositorio_arrecifes import cargar_ranking_srpi, obtener_kpis_ecosistema
import config

def generar_pdf_ejecutivo(nombre_estacion: str = "Todas las Estaciones") -> bytes:
    """Genera un archivo PDF estructurado con el estado ecológico y la priorización SRPI"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    titulo_estilo = ParagraphStyle(
        'TituloCoral',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f2b48'),
        spaceAfter=6
    )
    subtitulo_estilo = ParagraphStyle(
        'SubtituloCoral',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#008080'),
        spaceAfter=14
    )
    cuerpo_estilo = ParagraphStyle(
        'CuerpoCoral',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#222222')
    )
    
    elementos = []
    
    # 1. Encabezado
    elementos.append(Paragraph("🪸 CoralTwin-DT — Informe Técnico Ejecutivo", titulo_estilo))
    elementos.append(Paragraph(f"Gemelo Digital de Arrecifes de Coral | Fecha: {datetime.date.today().strftime('%d/%m/%Y')}", subtitulo_estilo))
    elementos.append(Spacer(1, 10))
    
    # 2. Resumen Ejecutivo
    kpis = obtener_kpis_ecosistema()
    resumen_texto = f"""
    Este reporte consolida el diagnóstico ecológico multivariado y la priorización de restauración
    para la red de monitoreo de arrecifes bajo estrés térmico (DHW) y acidificación oceánica.
    Se registran <b>{kpis['total_estaciones']} estaciones activas</b> con una cobertura coralina media de 
    <b>{kpis['cobertura_promedio']}%</b>, un pH medio de <b>{kpis['ph_promedio']}</b> y <b>{kpis['estaciones_alerta']} estaciones en alerta térmica</b>.
    """
    elementos.append(Paragraph(resumen_texto, cuerpo_estilo))
    elementos.append(Spacer(1, 15))
    
    # 3. Tabla de KPIs Principales
    datos_kpis = [
        ["Indicador Ecosistémico", "Valor Medido", "Estado / Nivel de Riesgo"],
        ["Cobertura Coralina Viva Promedio", f"{kpis['cobertura_promedio']} %", "Moderado"],
        ["Estrés Térmico Medio (DHW)", f"{kpis['dhw_promedio']} °C-sem", "Alerta Temprana"],
        ["pH Oceánico Promedio", f"{kpis['ph_promedio']}", "Acidificación Moderada"],
        ["Estaciones Prioridad Alta (Tier 1)", f"{kpis['prioridad_alta_restauracion']} estaciones", "Acción Prioritaria Inmediata"]
    ]
    t_kpis = Table(datos_kpis, colWidths=[240, 120, 170])
    t_kpis.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f2b48')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f8fb')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0dbe5')),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    elementos.append(t_kpis)
    elementos.append(Spacer(1, 20))
    
    # 4. Tabla de Estaciones de Alta Prioridad (Top 6 SRPI)
    elementos.append(Paragraph("<b>Top Estaciones Priorizadas para Restauración (Zonificación SRPI)</b>", subtitulo_estilo))
    df_ranking = cargar_ranking_srpi()
    
    if not df_ranking.empty:
        filas_ranking = [["Estación", "Región", "DHW", "pH", "Coral %", "Índice SRPI", "Zonificación"]]
        top_df = df_ranking.head(8)
        for _, r in top_df.iterrows():
            filas_ranking.append([
                str(r["Station_Name"])[:18],
                str(r["Region"])[:12],
                f"{r['DHW_degC_weeks']:.2f}",
                f"{r['pH_total']:.2f}",
                f"{r['Live_Coral_Cover_Pct']:.1f}%",
                f"{r['Spatial_Restoration_Priority_Index_SRPI']:.3f}",
                str(r["Priority_Tier"]).replace("Tier_", "T").replace("_", " ")[:14]
            ])
            
        t_ranking = Table(filas_ranking, colWidths=[110, 80, 50, 45, 55, 65, 125])
        t_ranking.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#008080')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c0d0d0')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
        ]))
        elementos.append(t_ranking)
        
    elementos.append(Spacer(1, 20))
    
    # 5. Recomendaciones Científicas
    elementos.append(Paragraph("<b>Recomendaciones de Acción Ecológica Inmediata</b>", subtitulo_estilo))
    recom_texto = """
    1. <b>Despliegue de Super-Corales:</b> Enfocar viveros de micro-fragmentos en estaciones de Tier 1 (ej. GreatBarrier_Central_14 y CoralTriangle_RajaAmpat_16).<br/>
    2. <b>Refuerzo de Áreas Marinas Protegidas:</b> Establecer veda total sobre peces loro para mantener la tasa de pastoreo sobre macroalgas por encima de 0.40.<br/>
    3. <b>Monitoreo Satelital Continuo:</b> Realizar asimilación diaria de productos NOAA Coral Reef Watch 5km ante alertas tempranas de olas de calor.
    """
    elementos.append(Paragraph(recom_texto, cuerpo_estilo))
    elementos.append(Spacer(1, 15))
    elementos.append(Paragraph(f"<i>{config.ATTRIBUTION_TEXT} | Versión {config.VERSION}</i>", ParagraphStyle('Pie', fontSize=8, textColor=colors.gray)))
    
    doc.build(elementos)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
