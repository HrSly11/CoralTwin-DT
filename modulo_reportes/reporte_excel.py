# modulo_reportes/reporte_excel.py
"""Generación de libro de cálculo multi-hoja en formato Excel (.xlsx) utilizando openpyxl"""
import io
import pandas as pd
from modulo_base_datos.repositorio_arrecifes import cargar_ranking_srpi, cargar_dataset_completo, obtener_kpis_ecosistema
import config

def generar_excel_datos() -> bytes:
    """Genera archivo Excel con datos crudos, ranking SRPI y resumen de KPIs"""
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        # Hoja 1: Resumen de KPIs
        kpis = obtener_kpis_ecosistema()
        df_kpis = pd.DataFrame([
            {"Indicador": "Estaciones Monitoreadas", "Valor": kpis["total_estaciones"]},
            {"Indicador": "Cobertura Coralina Media (%)", "Valor": kpis["cobertura_promedio"]},
            {"Indicador": "DHW Medio (°C-semanas)", "Valor": kpis["dhw_promedio"]},
            {"Indicador": "pH Medio", "Valor": kpis["ph_promedio"]},
            {"Indicador": "Estaciones en Alerta Térmica", "Valor": kpis["estaciones_alerta"]},
            {"Indicador": "Sitios Tier 1 Alta Prioridad", "Valor": kpis["prioridad_alta_restauracion"]},
            {"Indicador": "Versión del Gemelo Digital", "Valor": config.VERSION}
        ])
        df_kpis.to_excel(writer, sheet_name="Resumen_KPIs", index=False)
        
        # Hoja 2: Ranking de Priorización SRPI
        df_ranking = cargar_ranking_srpi()
        if not df_ranking.empty:
            df_ranking.to_excel(writer, sheet_name="Ranking_SRPI", index=False)
            
        # Hoja 3: Muestra de Series Históricas (últimos 500 registros)
        df_all = cargar_dataset_completo()
        if not df_all.empty:
            cols_export = [c for c in [
                "Record_ID", "Date", "Station_Name", "Region", "Reef_Zone",
                "SST_degC", "DHW_degC_weeks", "pH_total", "Live_Coral_Cover_Pct",
                "Macroalgae_Cover_Pct", "Bleaching_Severity_Pct", "Bleaching_Risk"
            ] if c in df_all.columns]
            df_sample = df_all[cols_export].tail(500)
            df_sample.to_excel(writer, sheet_name="Series_Temporales_Recientes", index=False)
            
    excel_bytes = buffer.getvalue()
    buffer.close()
    return excel_bytes
