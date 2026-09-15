# modulo_visualizacion_3d/mapa_arrecifes.py
"""Visualización geoespacial interactiva de las estaciones de monitoreo y zonificación SRPI"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from modulo_base_datos.repositorio_arrecifes import cargar_ranking_srpi

def generar_mapa_global_estaciones(criterio_color: str = "Priority_Tier") -> go.Figure:
    """
    Genera un mapa global interactivo con las 25 estaciones arrecifales
    Criterios: 'Priority_Tier', 'DHW_degC_weeks', 'Live_Coral_Cover_Pct', 'pH_total'
    """
    df = cargar_ranking_srpi()
    if df.empty:
        return go.Figure()
    
    df_plot = df.copy()
    
    # Textos de tooltip enriquecidos
    df_plot["Info_Hover"] = (
        "<b>Estación:</b> " + df_plot["Station_Name"] + "<br>" +
        "<b>Región:</b> " + df_plot["Region"] + "<br>" +
        "<b>Zona:</b> " + df_plot["Reef_Zone"] + "<br>" +
        "<b>Profundidad:</b> " + df_plot["Depth_m"].round(1).astype(str) + " m<br>" +
        "<b>DHW:</b> " + df_plot["DHW_degC_weeks"].round(2).astype(str) + " °C-sem<br>" +
        "<b>pH:</b> " + df_plot["pH_total"].round(3).astype(str) + "<br>" +
        "<b>Cobertura Coralina:</b> " + df_plot["Live_Coral_Cover_Pct"].round(1).astype(str) + "%<br>" +
        "<b>Índice SRPI:</b> " + df_plot["Spatial_Restoration_Priority_Index_SRPI"].round(3).astype(str) + "<br>" +
        "<b>Zonificación:</b> " + df_plot["Priority_Tier"]
    )
    
    if criterio_color == "Priority_Tier":
        color_map = {
            "Tier_1_High_Priority_Restoration": "#00CC96",
            "Tier_2_Secondary_Conservation": "#FFA15A",
            "Tier_3_Low_Monitoring": "#EF553B"
        }
        fig = px.scatter_geo(
            df_plot,
            lat="Latitude",
            lon="Longitude",
            color="Priority_Tier",
            color_discrete_map=color_map,
            hover_name="Station_Name",
            size="Live_Coral_Cover_Pct",
            size_max=18,
            title="Priorización Espacial de Restauración (Zonificación SRPI)"
        )
    elif criterio_color == "DHW_degC_weeks":
        fig = px.scatter_geo(
            df_plot,
            lat="Latitude",
            lon="Longitude",
            color="DHW_degC_weeks",
            color_continuous_scale="Reds",
            hover_name="Station_Name",
            size="DHW_degC_weeks",
            size_max=20,
            title="Estrés Térmico Acumulado NOAA (Degree Heating Weeks - °C-semanas)"
        )
    else:
        fig = px.scatter_geo(
            df_plot,
            lat="Latitude",
            lon="Longitude",
            color="Live_Coral_Cover_Pct",
            color_continuous_scale="Viridis",
            hover_name="Station_Name",
            size="Live_Coral_Cover_Pct",
            size_max=18,
            title="Cobertura Coralina Viva Actual (%)"
        )
        
    fig.update_geos(
        showcoastlines=True,
        coastlinecolor="DarkBlue",
        showland=True,
        landcolor="#202530",
        showocean=True,
        oceancolor="#0d1b2a",
        showlakes=False,
        projection_type="natural earth",
        resolution=110
    )
    
    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=0, r=0, t=40, b=0),
        height=520,
        legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.02, bgcolor="rgba(10,20,35,0.85)")
    )
    
    return fig
