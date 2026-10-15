# ==========================================================
# CORALTWIN-DT: GEMELO DIGITAL DE ARRECIFES DE CORAL
# Aplicación Principal Integrada con Arquitectura Modular (Bilingüe i18n & Theming)
# ==========================================================
import os
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Configuración de página Streamlit
st.set_page_config(
    page_title="CoralTwin-DT — Digital Twin of Coral Reefs",
    page_icon="🪸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cargar configuración y módulos locales
import config
from modulo_seguridad.auth import formulario_acceso, cerrar_sesion
from modulo_seguridad.decoradores import verificar_permiso
from modulo_base_datos.repositorio_arrecifes import (
    cargar_resumen_estaciones,
    cargar_serie_temporal_estacion,
    obtener_kpis_ecosistema,
    cargar_ranking_srpi
)
from modulo_simulacion.motor_biofisico import resolver_mumby_extendido
from modulo_simulacion.escenarios_ipcc import simular_comparativa_escenarios, ESCENARIOS_CLIMATICOS
from modulo_simulacion.intervenciones import CATALOGO_INTERVENCIONES, calcular_impacto_cartera
from modulo_simulacion.evaluacion_hipotesis import evaluar_hipotesis_investigacion
from modulo_ia.inferencia import predecir_estado_arrecifal, obtener_matriz_benchmarking
from modulo_ia.explicabilidad import obtener_ranking_importancia, curva_sensibilidad_dhw
from modulo_ia.analisis_exploratorio import (
    calcular_matriz_correlacion,
    obtener_estadisticas_descriptivas,
    obtener_resumen_por_region
)
from modulo_visualizacion_3d.mapa_arrecifes import generar_mapa_global_estaciones
from modulo_visualizacion_3d.arrecife_3d import generar_gemelo_arrecife_3d
from modulo_reportes.generador import renderizar_interfaz_reportes
from modulo_chatbot.interfaz_chat import renderizar_interfaz_chatbot
from utilidades.validadores import categorizar_alerta_noaa
from utilidades.tema import aplicar_tema
from modulo_idioma import obtener_texto

# ==========================================================
# GESTIÓN DE ESTADO DE SESIÓN
# ==========================================================
def inicializar_estado():
    defaults = {
        "autenticado": False,
        "usuario": None,
        "nombre_completo": None,
        "rol": None,
        "permisos": {},
        "institucion": None,
        "idioma": config.IDIOMA_POR_DEFECTO,
        "tema": config.TEMA_POR_DEFECTO,
        "seccion_id": "dashboard",
        "estacion_activa": "GreatBarrier_Central_14",
        "historial_chat_coral": []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

inicializar_estado()

# Aplicar Tema Activo (Claro u Oscuro)
aplicar_tema(st.session_state.tema)

# Control de Autenticación
if not st.session_state.autenticado:
    formulario_acceso()
    st.stop()

# Idioma Activo
idioma_act = st.session_state.get("idioma", "es")

# ==========================================================
# BARRA LATERAL: PERFIL, SELECTOR DE ESTACIÓN Y NAVEGACIÓN
# ==========================================================
st.sidebar.markdown(f"### 🪸 **{obtener_texto('app_titulo', idioma_act).split('—')[0].strip()}**")
st.sidebar.markdown(f"👤 **{st.session_state.nombre_completo}**")
st.sidebar.markdown(f"🔐 {obtener_texto('rol', idioma_act)}: `{st.session_state.rol}`")
st.sidebar.markdown(f"🏛️ *{st.session_state.institucion}*")
st.sidebar.markdown("---")

# Selectores de Idioma y Tema (Claro / Oscuro)
col_cfg1, col_cfg2 = st.sidebar.columns(2)
with col_cfg1:
    idx_idioma = 0 if idioma_act == "es" else 1
    sel_idioma = st.selectbox(
        obtener_texto("idioma_lbl", idioma_act),
        ["🇪🇸 Español", "🇬🇧 English"],
        index=idx_idioma,
        key="sb_idioma"
    )
    nuevo_idioma = "es" if "Español" in sel_idioma else "en"
    if nuevo_idioma != st.session_state.idioma:
        st.session_state.idioma = nuevo_idioma
        st.rerun()

with col_cfg2:
    idx_tema = 0 if st.session_state.tema == "claro" else 1
    opc_claro = obtener_texto("tema_claro", idioma_act)
    opc_oscuro = obtener_texto("tema_oscuro", idioma_act)
    sel_tema = st.selectbox(
        obtener_texto("tema_lbl", idioma_act),
        [opc_claro, opc_oscuro],
        index=idx_tema,
        key="sb_tema"
    )
    nuevo_tema = "claro" if sel_tema == opc_claro else "oscuro"
    if nuevo_tema != st.session_state.tema:
        st.session_state.tema = nuevo_tema
        st.rerun()

st.sidebar.markdown("---")

# Cargar estaciones para el selector
df_estaciones = cargar_resumen_estaciones()
lista_estaciones = df_estaciones["Station_Name"].tolist() if not df_estaciones.empty else ["GreatBarrier_Central_14"]

st.sidebar.markdown(f"#### {obtener_texto('estacion_activa_lbl', idioma_act)}")
idx_default = 0
if st.session_state.estacion_activa in lista_estaciones:
    idx_default = lista_estaciones.index(st.session_state.estacion_activa)

estacion_sel = st.sidebar.selectbox(
    obtener_texto("seleccione_estacion", idioma_act),
    lista_estaciones,
    index=idx_default,
    key="sb_estacion"
)
st.session_state.estacion_activa = estacion_sel

# Definición estructurada de módulos del sistema
OPCIONES_MENU_DEF = [
    ("dashboard", "menu_dashboard"),
    ("mapa_3d", "menu_mapa_3d"),
    ("simulacion", "menu_simulacion"),
    ("ia", "menu_ia"),
    ("srpi", "menu_srpi"),
    ("hipotesis", "menu_hipotesis"),
    ("reportes", "menu_reportes"),
    ("chat", "menu_chat"),
]

if verificar_permiso("gestionar_usuarios"):
    OPCIONES_MENU_DEF.append(("admin", "menu_admin"))

etiquetas_menu = [obtener_texto(clave, idioma_act) for _, clave in OPCIONES_MENU_DEF]
mapa_etiqueta_a_id = {obtener_texto(clave, idioma_act): mod_id for mod_id, clave in OPCIONES_MENU_DEF}
ids_disponibles = [mod_id for mod_id, _ in OPCIONES_MENU_DEF]

if "seccion_id" not in st.session_state or st.session_state.seccion_id not in ids_disponibles:
    st.session_state.seccion_id = "dashboard"

idx_seccion = ids_disponibles.index(st.session_state.seccion_id)

st.sidebar.markdown("---")
seccion_seleccionada = st.sidebar.radio(
    obtener_texto("modulos_sistema", idioma_act),
    etiquetas_menu,
    index=idx_seccion
)
st.session_state.seccion_id = mapa_etiqueta_a_id[seccion_seleccionada]
seccion_id = st.session_state.seccion_id

st.sidebar.markdown("---")
if st.sidebar.button(obtener_texto("cerrar_sesion", idioma_act)):
    cerrar_sesion()
    st.rerun()

# ==========================================================
# MÓDULO 1: PANEL ECOSISTÉMICO (DASHBOARD)
# ==========================================================
if seccion_id == "dashboard":
    st.header(obtener_texto("header_dashboard", idioma_act))
    st.markdown(f"**{obtener_texto('sub_dashboard', idioma_act)}**")
    st.markdown("---")
    
    # KPIs Globales
    kpis = obtener_kpis_ecosistema()
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(obtener_texto("estaciones_activas", idioma_act), kpis["total_estaciones"])
    with col2:
        st.metric(obtener_texto("cobertura_media", idioma_act), f"{kpis['cobertura_promedio']} %")
    with col3:
        st.metric(obtener_texto("dhw_promedio", idioma_act), f"{kpis['dhw_promedio']} °C-sem")
    with col4:
        st.metric(obtener_texto("ph_promedio", idioma_act), kpis["ph_promedio"])
    with col5:
        st.metric(obtener_texto("estaciones_alerta", idioma_act), f"{kpis['estaciones_alerta']} / {kpis['total_estaciones']}")
        
    st.markdown("---")
    
    # Estado detallado de la estación seleccionada
    st.subheader(f"{obtener_texto('estado_actual', idioma_act)}: {estacion_sel}")
    
    row_est = df_estaciones[df_estaciones["Station_Name"] == estacion_sel]
    if not row_est.empty:
        r = row_est.iloc[0]
        alerta_noaa, color_alerta = categorizar_alerta_noaa(r["DHW_degC_weeks"])
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"**{obtener_texto('region_oceanica', idioma_act)}:** {r['Region']}")
            st.markdown(f"**{obtener_texto('zona_arrecife', idioma_act)}:** {r['Reef_Zone']}")
            st.markdown(f"**{obtener_texto('profundidad', idioma_act)}:** {r['Depth_m']:.1f} m")
        with c2:
            st.markdown(f"**{obtener_texto('estres_termico', idioma_act)}:** {r['DHW_degC_weeks']:.2f} °C-sem")
            st.markdown(f"**{obtener_texto('nivel_alerta', idioma_act)}:** <span style='color:{color_alerta}; font-weight:bold;'>{alerta_noaa}</span>", unsafe_allow_html=True)
            st.markdown(f"**{obtener_texto('ph_total', idioma_act)}:** {r['pH_total']:.3f}")
        with c3:
            st.markdown(f"**{obtener_texto('cobertura_coral_vivo', idioma_act)}:** {r['Live_Coral_Cover_Pct']:.1f} %")
            st.markdown(f"**{obtener_texto('macroalgas_comp', idioma_act)}:** {r['Macroalgae_Cover_Pct']:.1f} %")
            st.markdown(f"**{obtener_texto('rugosidad_estructural', idioma_act)}:** {r['Structural_Rugosity']:.2f}")
        with c4:
            st.markdown(f"**{obtener_texto('indice_srpi', idioma_act)}:** {r['Spatial_Restoration_Priority_Index_SRPI']:.3f}")
            tier_nombre = str(r['Priority_Tier']).replace("Tier_", "Tier ")
            st.markdown(f"**{obtener_texto('zonificacion', idioma_act)}:** `{tier_nombre}`")
            st.progress(float(r['Spatial_Restoration_Priority_Index_SRPI']))
            
    # Serie temporal histórica de la estación
    df_serie = cargar_serie_temporal_estacion(estacion_sel)
    if not df_serie.empty:
        st.markdown(f"#### {obtener_texto('dinamica_historica', idioma_act)}")
        
        fig_temp = px.line(
            df_serie,
            x="Date",
            y=["SST_degC", "DHW_degC_weeks"],
            title=obtener_texto("graf_sst_dhw_title", idioma_act).format(estacion=estacion_sel),
            labels={
                "value": obtener_texto("graf_sst_dhw_val", idioma_act),
                "Date": obtener_texto("graf_sst_dhw_date", idioma_act),
                "variable": obtener_texto("graf_sst_dhw_var", idioma_act)
            },
            color_discrete_map={"SST_degC": "#ff7f0e", "DHW_degC_weeks": "#d62728"},
            template="plotly_dark"
        )
        fig_temp.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_temp, use_container_width=True)
        
        fig_bio = px.line(
            df_serie,
            x="Date",
            y=["Live_Coral_Cover_Pct", "Macroalgae_Cover_Pct"],
            title=obtener_texto("graf_bio_title", idioma_act).format(estacion=estacion_sel),
            labels={
                "value": obtener_texto("graf_bio_val", idioma_act),
                "Date": obtener_texto("graf_bio_date", idioma_act),
                "variable": obtener_texto("graf_bio_var", idioma_act)
            },
            color_discrete_map={"Live_Coral_Cover_Pct": "#00CC96", "Macroalgae_Cover_Pct": "#AB63FA"},
            template="plotly_dark"
        )
        fig_bio.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bio, use_container_width=True)

# ==========================================================
# MÓDULO 2: GEMELO ESPACIAL & 3D
# ==========================================================
elif seccion_id == "mapa_3d":
    st.header(obtener_texto("header_mapa_3d", idioma_act))
    st.markdown(f"**{obtener_texto('sub_mapa_3d', idioma_act)}**")
    st.markdown(f"*{obtener_texto('sub_desc_mapa_3d', idioma_act)}*")
    st.markdown("---")
    
    tab_mapa, tab_3d = st.tabs([obtener_texto("tab_mapa", idioma_act), obtener_texto("tab_3d", idioma_act)])
    
    with tab_mapa:
        st.markdown(f"#### {obtener_texto('cartografia_marina', idioma_act)}")
        criterio = st.selectbox(
            obtener_texto("criterio_vis_mapa", idioma_act),
            ["Priority_Tier", "DHW_degC_weeks", "Live_Coral_Cover_Pct"],
            format_func=lambda x: {
                "Priority_Tier": obtener_texto("crit_tier", idioma_act),
                "DHW_degC_weeks": obtener_texto("crit_dhw", idioma_act),
                "Live_Coral_Cover_Pct": obtener_texto("crit_cover", idioma_act)
            }[x]
        )
        fig_mapa = generar_mapa_global_estaciones(criterio)
        st.plotly_chart(fig_mapa, use_container_width=True)
        
    with tab_3d:
        st.markdown(f"#### {obtener_texto('gemelo_3d_title', idioma_act)}")
        st.info(obtener_texto("gemelo_3d_info", idioma_act))
        
        c1, c2, c3 = st.columns(3)
        with c1:
            cov_c = st.slider(obtener_texto("slider_cov_coral", idioma_act), 5.0, 85.0, 35.0, 1.0)
        with c2:
            blanq = st.slider(obtener_texto("slider_blanq_tisular", idioma_act), 0.0, 100.0, 20.0, 1.0)
        with c3:
            macro = st.slider(obtener_texto("slider_macroalgas", idioma_act), 5.0, 75.0, 25.0, 1.0)
            
        fig_3d = generar_gemelo_arrecife_3d(cov_c, blanq, macro)
        st.plotly_chart(fig_3d, use_container_width=True)

# ==========================================================
# MÓDULO 3: SIMULACIÓN BIOFÍSICA & ESCENARIOS IPCC
# ==========================================================
elif seccion_id == "simulacion":
    st.header(obtener_texto("header_simulacion", idioma_act))
    st.markdown(f"**{obtener_texto('sub_simulacion', idioma_act)}**")
    st.markdown(f"*{obtener_texto('sub_desc_sim', idioma_act)}*")
    st.markdown("---")
    
    tab_sim, tab_ipcc, tab_resto = st.tabs([
        obtener_texto("tab_sim", idioma_act),
        obtener_texto("tab_ipcc", idioma_act),
        obtener_texto("tab_resto", idioma_act)
    ])
    
    with tab_sim:
        st.markdown(f"#### {obtener_texto('param_ecosistema', idioma_act)}")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            c0_input = st.slider(obtener_texto("slider_c0", idioma_act), 5.0, 60.0, 35.0) / 100.0
            m0_input = st.slider(obtener_texto("slider_m0", idioma_act), 5.0, 50.0, 25.0) / 100.0
            horizonte_anos = st.slider(obtener_texto("slider_horizonte", idioma_act), 5, 35, 25)
        with col_p2:
            dhw_input = st.slider(obtener_texto("slider_dhw", idioma_act), 0.0, 14.0, 3.2, 0.2)
            ph_input = st.slider(obtener_texto("slider_ph", idioma_act), 7.70, 8.20, 8.05, 0.01)
            pastoreo_input = st.slider(obtener_texto("slider_pastoreo", idioma_act), 0.15, 0.65, 0.35, 0.02)
        with col_p3:
            tasa_resto_input = st.slider(obtener_texto("slider_tasa_resto", idioma_act), 0.0, 0.05, 0.015, 0.005)
            endurecimiento_input = st.slider(obtener_texto("slider_endurecimiento", idioma_act), 0.0, 2.5, 1.2, 0.1)
            turb_input = st.slider(obtener_texto("slider_turbidez", idioma_act), 0.0, 0.5, 0.15, 0.05)
            
        if st.button(obtener_texto("btn_ejecutar_mumby", idioma_act)):
            res_sim = resolver_mumby_extendido(
                c0=c0_input,
                m0=m0_input,
                años=horizonte_anos,
                dhw_acumulado=dhw_input,
                ph_oceano=ph_input,
                pastoreo_g=pastoreo_input,
                tasa_restauracion=tasa_resto_input,
                endurecimiento_termico=endurecimiento_input,
                reduccion_turbidez=turb_input
            )
            
            lbl_ano = "Año" if idioma_act == "es" else "Year"
            lbl_coral = "Coral Vivo (%)" if idioma_act == "es" else "Live Coral (%)"
            lbl_macro = "Macroalgas (%)" if idioma_act == "es" else "Macroalgae (%)"
            lbl_turf = "Césped Algal Turf (%)" if idioma_act == "es" else "Turf Algae (%)"
            
            df_sim_traj = pd.DataFrame({
                lbl_ano: 2025 + res_sim["tiempo_años"],
                lbl_coral: res_sim["cobertura_coral"],
                lbl_macro: res_sim["cobertura_macroalgas"],
                lbl_turf: res_sim["cesped_turf"]
            })
            
            fig_traj = px.line(
                df_sim_traj,
                x=lbl_ano,
                y=[lbl_coral, lbl_macro, lbl_turf],
                title=obtener_texto("traj_dinamica_title", idioma_act),
                color_discrete_map={
                    lbl_coral: "#00CC96",
                    lbl_macro: "#EF553B",
                    lbl_turf: "#FECB52"
                },
                template="plotly_dark"
            )
            fig_traj.add_hline(y=30.0, line_dash="dash", line_color="cyan", annotation_text=obtener_texto("umbral_resiliencia", idioma_act))
            st.plotly_chart(fig_traj, use_container_width=True)
            
            c_res1, c_res2, c_res3 = st.columns(3)
            with c_res1:
                st.metric(obtener_texto("met_coral_final", idioma_act), f"{res_sim['cobertura_final']:.1f} %")
            with c_res2:
                st.metric(obtener_texto("met_macro_final", idioma_act), f"{res_sim['macroalgas_final']:.1f} %")
            with c_res3:
                st.metric(obtener_texto("met_estado_eco", idioma_act), res_sim["resiliencia_estado"])
                
    with tab_ipcc:
        st.markdown(f"#### {obtener_texto('comp_ipcc_title', idioma_act)}")
        activar_resto_ipcc = st.checkbox(obtener_texto("chk_resto_ipcc", idioma_act), value=True)
        
        tiempo_arr, res_ipcc = simular_comparativa_escenarios(con_restauracion=activar_resto_ipcc)
        
        lbl_ano = "Año" if idioma_act == "es" else "Year"
        df_ipcc_plot = pd.DataFrame({lbl_ano: tiempo_arr})
        for k, v in res_ipcc.items():
            df_ipcc_plot[f"Coral {k}"] = v["coral"]
            
        fig_ipcc = px.line(
            df_ipcc_plot,
            x=lbl_ano,
            y=[f"Coral {k}" for k in res_ipcc.keys()],
            title=obtener_texto("graf_ipcc_title", idioma_act),
            labels={
                "value": obtener_texto("graf_ipcc_y", idioma_act),
                "variable": obtener_texto("graf_ipcc_var", idioma_act)
            },
            template="plotly_dark"
        )
        fig_ipcc.add_hline(y=30.0, line_dash="dash", line_color="cyan", annotation_text=obtener_texto("meta_cobertura_30", idioma_act))
        st.plotly_chart(fig_ipcc, use_container_width=True)
        
        st.markdown(f"##### {obtener_texto('resumen_escenario_2050', idioma_act)}")
        col_sc1, col_sc2, col_sc3 = st.columns(3)
        for i, (k, datos) in enumerate(res_ipcc.items()):
            col_target = [col_sc1, col_sc2, col_sc3][i]
            with col_target:
                lbl_cob = obtener_texto('cobertura_coral_2050', idioma_act)
                lbl_est = obtener_texto('estado_label', idioma_act)
                st.info(f"**{k}**\n\n- {lbl_cob}: **{datos['cobertura_final']:.1f}%**\n- {lbl_est}: `{datos['estado']}`")
                
    with tab_resto:
        st.markdown(f"#### {obtener_texto('diseno_cartera_title', idioma_act)}")
        st.markdown(obtener_texto("diseno_cartera_desc", idioma_act))
        
        nombres_en = {
            "super_corals": "Thermally Resilient Super-Corals Propagation",
            "micro_fragmentacion": "Micro-Fragmentation & Intensive Outplanting",
            "creacion_amp_herbivoros": "Marine Protected Area (Strict Herbivore Ban)",
            "reduccion_escorrentia": "Local Pressure Mitigation (Turbidity & Nutrients Control)",
            "sombreado_marino": "Marine Cloud Brightening & Dynamic Shading"
        }
        
        estrategias_sel = st.multiselect(
            obtener_texto("sel_intervenciones", idioma_act),
            list(CATALOGO_INTERVENCIONES.keys()),
            default=["super_corals", "micro_fragmentacion", "creacion_amp_herbivoros"],
            format_func=lambda x: nombres_en.get(x, CATALOGO_INTERVENCIONES[x]["nombre"]) if idioma_act == "en" else CATALOGO_INTERVENCIONES[x]["nombre"]
        )
        
        impacto = calcular_impacto_cartera(estrategias_sel)
        
        c_i1, c_i2, c_i3, c_i4 = st.columns(4)
        with c_i1:
            st.metric(obtener_texto("met_margen_termico", idioma_act), f"+{impacto['endurecimiento_termico']:.1f} °C")
        with c_i2:
            st.metric(obtener_texto("met_tasa_siembra", idioma_act), f"{impacto['tasa_restauracion']:.3f} /año")
        with c_i3:
            st.metric(obtener_texto("met_inc_pastoreo", idioma_act), f"+{impacto['incremento_pastoreo']:.2f}")
        with c_i4:
            st.metric(obtener_texto("met_costo_ha", idioma_act), f"${impacto['costo_estimado_ha_usd']:,} USD")

# ==========================================================
# MÓDULO 4: MOTOR DE IA PREDICTIVO
# ==========================================================
elif seccion_id == "ia":
    st.header(obtener_texto("header_ia", idioma_act))
    st.markdown(f"**{obtener_texto('sub_ia', idioma_act)}**")
    st.markdown(f"*{obtener_texto('sub_desc_ia', idioma_act)}*")
    st.markdown("---")
    
    tab_pred, tab_bench, tab_shap, tab_eda = st.tabs([
        obtener_texto("tab_pred", idioma_act),
        obtener_texto("tab_bench", idioma_act),
        obtener_texto("tab_shap", idioma_act),
        obtener_texto("tab_eda", idioma_act)
    ])
    
    with tab_pred:
        st.markdown(f"#### {obtener_texto('sim_inferencia_title', idioma_act)}")
        c1, c2, c3 = st.columns(3)
        with c1:
            in_dhw = st.slider(obtener_texto("slider_dhw", idioma_act), 0.0, 16.0, 4.8, 0.2)
            in_sst = st.slider(obtener_texto("slider_sst", idioma_act), 24.0, 33.0, 29.8, 0.1)
            in_anom = st.slider(obtener_texto("slider_anom", idioma_act), -0.5, 3.5, 1.4, 0.1)
        with c2:
            in_ph = st.slider(obtener_texto("slider_ph", idioma_act), 7.60, 8.25, 8.02, 0.01)
            in_omega = st.slider(obtener_texto("slider_omega", idioma_act), 2.0, 4.5, 3.4, 0.1)
            in_turb = st.slider(obtener_texto("slider_turb", idioma_act), 0.2, 5.0, 0.9, 0.1)
        with c3:
            in_cov = st.slider(obtener_texto("slider_cov", idioma_act), 5.0, 80.0, 36.0, 1.0)
            in_rug = st.slider(obtener_texto("slider_rug", idioma_act), 1.0, 3.8, 2.3, 0.1)
            in_depth = st.slider(obtener_texto("slider_depth", idioma_act), 2.0, 30.0, 12.0, 0.5)
            alg_sel = st.selectbox(obtener_texto("algoritmo_inferencia", idioma_act), ["XGBoost", "Random Forest"])
            
        prediccion = predecir_estado_arrecifal(
            depth_m=in_depth,
            sst_degc=in_sst,
            sst_anomaly=in_anom,
            dhw_weeks=in_dhw,
            ph_total=in_ph,
            aragonite_omega=in_omega,
            turbidity_ntu=in_turb,
            structural_rugosity=in_rug,
            live_coral_cover=in_cov,
            algoritmo=alg_sel
        )
        
        st.markdown(f"##### {obtener_texto('res_inferencia_title', idioma_act)}")
        res_col1, res_col2, res_col3, res_col4 = st.columns(4)
        
        color_riesgo = {"Low": "#00CC96", "Medium": "#FFA15A", "High": "#EF553B"}.get(prediccion["riesgo_blanqueamiento"], "cyan")
        
        with res_col1:
            st.markdown(f"**{obtener_texto('riesgo_blanq_lbl', idioma_act)}**")
            st.markdown(f"<h3 style='color:{color_riesgo};'>{prediccion['riesgo_blanqueamiento']}</h3>", unsafe_allow_html=True)
        with res_col2:
            st.metric(obtener_texto("met_sev_blanq", idioma_act), f"{prediccion['severidad_blanqueamiento_pct']}%")
        with res_col3:
            st.metric(obtener_texto("met_perd_cob", idioma_act), f"{prediccion['perdida_cobertura_pct']}%")
        with res_col4:
            st.metric(obtener_texto("met_cob_remanente", idioma_act), f"{prediccion['cobertura_remanente_pct']}%")
            
        col_r_lbl = obtener_texto("col_riesgo", idioma_act)
        col_p_lbl = obtener_texto("col_prob", idioma_act)
        df_probs = pd.DataFrame(list(prediccion["probabilidades"].items()), columns=[col_r_lbl, col_p_lbl])
        fig_prob = px.bar(
            df_probs,
            x=col_r_lbl,
            y=col_p_lbl,
            color=col_r_lbl,
            color_discrete_map={"Low": "#00CC96", "Medium": "#FFA15A", "High": "#EF553B"},
            template="plotly_dark",
            title=obtener_texto("graf_prob_title", idioma_act)
        )
        fig_prob.update_layout(height=280)
        st.plotly_chart(fig_prob, use_container_width=True)

    with tab_bench:
        st.markdown(f"#### {obtener_texto('bench_title', idioma_act)}")
        st.markdown(obtener_texto("bench_desc", idioma_act))
        st.info(obtener_texto("bench_info_xgboost", idioma_act))
        
        df_bench = obtener_matriz_benchmarking()
        
        # Adaptar tabla de benchmarking para inglés si está activo
        if idioma_act == "en":
            df_bench_disp = df_bench.rename(columns={
                "Modelo": "Model",
                "Arquitectura": "Architecture",
                "Latencia Inferencia": "Inference Latency",
                "Tamaño": "Size",
                "Explicabilidad (XAI)": "Explainability (XAI)",
                "Estado": "Status"
            }).copy()
            df_bench_disp["Model"] = df_bench_disp["Model"].replace({
                "XGBoost (Ganador Operacional)": "XGBoost (Operational Winner)",
                "LSTM (Recurrente)": "LSTM (Recurrent)"
            })
            df_bench_disp["Status"] = df_bench_disp["Status"].replace({
                "Producción / Operacional": "Production / Operational",
                "Ensamble / Alternativa": "Ensemble / Alternative",
                "Descartado (Alta Latencia)": "Discarded (High Latency)"
            })
        else:
            df_bench_disp = df_bench
            
        st.dataframe(df_bench_disp, use_container_width=True, hide_index=True)
        
        st.markdown(f"##### {obtener_texto('comp_rend_lat_title', idioma_act)}")
        
        c_b1, c_b2 = st.columns(2)
        with c_b1:
            opc_f1 = obtener_texto("opt_f1", idioma_act)
            opc_err = obtener_texto("opt_tasa_error", idioma_act)
            opc_rmse = obtener_texto("opt_rmse", idioma_act)
            opc_acc = obtener_texto("opt_acc", idioma_act)
            
            opcion_metrica = st.selectbox(
                obtener_texto("sel_metrica_comp", idioma_act),
                [opc_f1, opc_err, opc_rmse, opc_acc],
                index=0
            )
            
            if opcion_metrica == opc_f1:
                df_plot = pd.DataFrame({"Modelo": df_bench["Modelo"], "Valor": df_bench["Macro-F1"]})
                y_titulo = obtener_texto("y_f1", idioma_act)
                rango_y = [0, 0.90]
                text_plantilla = "%{y:.4f}"
            elif opcion_metrica == opc_err:
                err_vals = [round(100.0 - float(x.replace("%", "")), 2) for x in df_bench["Accuracy"]]
                df_plot = pd.DataFrame({"Modelo": df_bench["Modelo"], "Valor": err_vals})
                y_titulo = obtener_texto("y_tasa_error", idioma_act)
                rango_y = [0, max(err_vals) * 1.25]
                text_plantilla = "%{y:.2f}%"
            elif opcion_metrica == opc_rmse:
                rmse_vals = [float(x.replace("%", "")) for x in df_bench["RMSE (%)"]]
                df_plot = pd.DataFrame({"Modelo": df_bench["Modelo"], "Valor": rmse_vals})
                y_titulo = obtener_texto("y_rmse", idioma_act)
                rango_y = [0, max(rmse_vals) * 1.15]
                text_plantilla = "%{y:.2f}%"
            else:
                acc_vals = [float(x.replace("%", "")) for x in df_bench["Accuracy"]]
                df_plot = pd.DataFrame({"Modelo": df_bench["Modelo"], "Valor": acc_vals})
                y_titulo = obtener_texto("y_acc", idioma_act)
                rango_y = [92, 100.8]
                text_plantilla = "%{y:.2f}%"
                
            fig_met = px.bar(
                df_plot,
                x="Modelo",
                y="Valor",
                text="Valor",
                title=obtener_texto("graf_comp_title", idioma_act).format(metrica=opcion_metrica),
                labels={"Valor": y_titulo},
                color="Modelo",
                color_discrete_map={
                    "XGBoost (Ganador Operacional)": "#00CC96",
                    "Random Forest": "#636EFA",
                    "LSTM (Recurrente)": "#EF553B"
                },
                template="plotly_dark"
            )
            fig_met.update_traces(texttemplate=text_plantilla, textposition='outside')
            fig_met.update_layout(height=340, yaxis=dict(range=rango_y), showlegend=False)
            st.plotly_chart(fig_met, use_container_width=True)
            
        with c_b2:
            st.markdown(f"**{obtener_texto('velocidad_inferencia_lbl', idioma_act)}**")
            lat_vals = [float(x.replace(" ms", "")) for x in df_bench["Latencia Inferencia"]]
            df_plot_lat = pd.DataFrame({"Modelo": df_bench["Modelo"], "Latencia": lat_vals})
            fig_lat = px.bar(
                df_plot_lat,
                x="Modelo",
                y="Latencia",
                text="Latencia",
                title=obtener_texto("graf_lat_title", idioma_act),
                labels={"Latencia": obtener_texto("graf_lat_y", idioma_act)},
                color="Modelo",
                color_discrete_map={
                    "XGBoost (Ganador Operacional)": "#00CC96",
                    "Random Forest": "#636EFA",
                    "LSTM (Recurrente)": "#EF553B"
                },
                template="plotly_dark"
            )
            fig_lat.update_traces(texttemplate='%{text:.4f} ms', textposition='outside')
            fig_lat.update_layout(height=340, yaxis=dict(range=[0, max(lat_vals) * 1.25]), showlegend=False)
            st.plotly_chart(fig_lat, use_container_width=True)
            
        st.markdown("---")
        st.markdown(f"##### {obtener_texto('discus_tecnica_title', idioma_act)}")
        
        c_an1, c_an2, c_an3 = st.columns(3)
        with c_an1:
            st.markdown(f"**{obtener_texto('disc_1_tit', idioma_act)}**\n\n{obtener_texto('disc_1_body', idioma_act)}")
        with c_an2:
            st.markdown(f"**{obtener_texto('disc_2_tit', idioma_act)}**\n\n{obtener_texto('disc_2_body', idioma_act)}")
        with c_an3:
            st.markdown(f"**{obtener_texto('disc_3_tit', idioma_act)}**\n\n{obtener_texto('disc_3_body', idioma_act)}")
        
    with tab_shap:
        st.markdown(f"#### {obtener_texto('shap_title', idioma_act)}")
        df_shap = obtener_ranking_importancia()
        
        fig_shap = px.bar(
            df_shap,
            x="Importancia_SHAP",
            y="Variable",
            orientation="h",
            color="Importancia_SHAP",
            color_continuous_scale="Viridis",
            title=obtener_texto("graf_shap_title", idioma_act),
            template="plotly_dark"
        )
        fig_shap.update_layout(yaxis=dict(autorange="reversed"), height=360)
        st.plotly_chart(fig_shap, use_container_width=True)
        
        st.dataframe(df_shap[["Variable", "Importancia_SHAP", "Efecto_Direccional", "Mecanismo_Ecológico"]], use_container_width=True)
        
        st.markdown(f"#### {obtener_texto('curva_dhw_title', idioma_act)}")
        df_curva = curva_sensibilidad_dhw()
        fig_curva = px.line(
            df_curva,
            x="DHW_degC_weeks",
            y=["Severidad_Blanqueamiento_Pct", "Perdida_Cobertura_Pct"],
            title=obtener_texto("graf_curva_title", idioma_act),
            labels={
                "value": obtener_texto("graf_curva_y", idioma_act),
                "DHW_degC_weeks": obtener_texto("graf_curva_x", idioma_act)
            },
            template="plotly_dark"
        )
        st.plotly_chart(fig_curva, use_container_width=True)
        
        st.info(obtener_texto("interp_ecologica_box", idioma_act))
        
    with tab_eda:
        st.markdown(f"#### {obtener_texto('eda_corr_title', idioma_act)}")
        corr = calcular_matriz_correlacion()
        if not corr.empty:
            fig_corr = px.imshow(
                corr,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="RdBu_r",
                title=obtener_texto("graf_corr_title", idioma_act),
                template="plotly_dark"
            )
            fig_corr.update_layout(height=520)
            st.plotly_chart(fig_corr, use_container_width=True)
            
        st.markdown(f"#### {obtener_texto('eda_region_title', idioma_act)}")
        st.dataframe(obtener_resumen_por_region(), use_container_width=True)

# ==========================================================
# MÓDULO 5: PRIORIZACIÓN ESPACIAL (SRPI)
# ==========================================================
elif seccion_id == "srpi":
    st.header(obtener_texto("header_srpi", idioma_act))
    st.markdown(f"**{obtener_texto('sub_srpi', idioma_act)}**")
    st.markdown(f"*{obtener_texto('sub_desc_srpi', idioma_act)}*")
    st.markdown("---")
    
    df_srpi = cargar_ranking_srpi()
    
    if not df_srpi.empty:
        c1, c2, c3 = st.columns(3)
        with c1:
            n_t1 = int((df_srpi["Priority_Tier"].str.contains("Tier_1")).sum())
            st.success(obtener_texto("tier1_box", idioma_act).format(n=n_t1))
        with c2:
            n_t2 = int((df_srpi["Priority_Tier"].str.contains("Tier_2")).sum())
            st.warning(obtener_texto("tier2_box", idioma_act).format(n=n_t2))
        with c3:
            n_t3 = int((df_srpi["Priority_Tier"].str.contains("Tier_3")).sum())
            st.error(obtener_texto("tier3_box", idioma_act).format(n=n_t3))
            
        st.markdown(f"#### {obtener_texto('ranking_completo_title', idioma_act)}")
        cols_mostrar = [
            "Station_Name", "Region", "Reef_Zone", "Depth_m",
            "DHW_degC_weeks", "pH_total", "Live_Coral_Cover_Pct",
            "Spatial_Restoration_Priority_Index_SRPI", "Priority_Tier"
        ]
        st.dataframe(
            df_srpi[cols_mostrar].style.format({
                "Depth_m": "{:.1f}",
                "DHW_degC_weeks": "{:.2f}",
                "pH_total": "{:.3f}",
                "Live_Coral_Cover_Pct": "{:.1f}%",
                "Spatial_Restoration_Priority_Index_SRPI": "{:.3f}"
            }),
            use_container_width=True
        )

# ==========================================================
# MÓDULO 6: EVALUACIÓN DE HIPÓTESIS CIENTÍFICA
# ==========================================================
elif seccion_id == "hipotesis":
    st.header(obtener_texto("header_hipotesis", idioma_act))
    st.markdown(f"**{obtener_texto('sub_hipotesis', idioma_act)}**")
    st.markdown("---")
    
    st.info(obtener_texto("hipotesis_enunciado_box", idioma_act))
    
    col_btn, col_opt = st.columns([1, 2])
    with col_btn:
        ejecutar_exp = st.button(obtener_texto("btn_ejecutar_mc", idioma_act))
    with col_opt:
        st.caption(obtener_texto("caption_mc", idioma_act))
        
    res_hip = evaluar_hipotesis_investigacion(n_simulaciones=150)
    
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        color_dic = "green" if res_hip["hipotesis_confirmada"] else "red"
        st.markdown(f"### {obtener_texto('dictamen_lbl', idioma_act)}")
        st.markdown(f"<h2 style='color:{color_dic};'>{res_hip['dictamen']}</h2>", unsafe_allow_html=True)
    with col_v2:
        st.metric(obtener_texto("met_media_prio", idioma_act), f"{res_hip['media_areas_priorizadas']} %", f"IC 95%: {res_hip['ci95_priorizadas']}")
        st.metric(obtener_texto("met_prob_30", idioma_act), f"{res_hip['probabilidad_superar_30_prio']} %")
    with col_v3:
        st.metric(obtener_texto("met_media_noprio", idioma_act), f"{res_hip['media_areas_no_priorizadas']} %", f"IC 95%: {res_hip['ci95_no_priorizadas']}")
        st.metric(obtener_texto("met_ganancia_neta", idioma_act), f"+{res_hip['diferencia_cobertura_pct']} %")
        
    st.markdown("---")
    st.markdown(f"#### {obtener_texto('dist_comparativa_title', idioma_act)}")
    
    grp_prio = obtener_texto("grupo_prio", idioma_act)
    grp_noprio = obtener_texto("grupo_noprio", idioma_act)
    
    df_dist = pd.DataFrame({
        "Cobertura_2050": np.concatenate([res_hip["distribucion_priorizada"], res_hip["distribucion_no_priorizada"]]),
        "Grupo": [grp_prio] * len(res_hip["distribucion_priorizada"]) + [grp_noprio] * len(res_hip["distribucion_no_priorizada"])
    })
    
    color_map_box = {
        grp_prio: "#00CC96",
        grp_noprio: "#EF553B"
    }
    
    fig_box = px.box(
        df_dist,
        x="Grupo",
        y="Cobertura_2050",
        color="Grupo",
        points="all",
        title=obtener_texto("graf_dist_title", idioma_act),
        labels={"Cobertura_2050": obtener_texto("graf_dist_y", idioma_act)},
        color_discrete_map=color_map_box,
        template="plotly_dark"
    )
    fig_box.add_hline(y=30.0, line_dash="dash", line_color="cyan", annotation_text=obtener_texto("umbral_critico_hip", idioma_act))
    st.plotly_chart(fig_box, use_container_width=True)
    
    st.markdown(obtener_texto("evidencia_estadistica_md", idioma_act).format(
        t=res_hip['estadistico_t'],
        d=res_hip['cohen_d']
    ))

# ==========================================================
# MÓDULO 7: CENTRO DE REPORTES
# ==========================================================
elif seccion_id == "reportes":
    st.header(obtener_texto("header_reportes", idioma_act))
    st.markdown(f"**{obtener_texto('sub_reportes', idioma_act)}**")
    renderizar_interfaz_reportes()

# ==========================================================
# MÓDULO 8: ASISTENTE CORALAI
# ==========================================================
elif seccion_id == "chat":
    st.header(obtener_texto("header_chat", idioma_act))
    renderizar_interfaz_chatbot()

# ==========================================================
# MÓDULO 9: ADMINISTRACIÓN DEL SISTEMA
# ==========================================================
elif seccion_id == "admin":
    st.header(obtener_texto("header_admin", idioma_act))
    st.markdown("---")
    
    st.subheader(obtener_texto("sub_admin_db", idioma_act))
    from modulo_base_datos.conexion import probar_conexion, config as cfg_db
    ok_db, msg_db = probar_conexion()
    if ok_db:
        st.success(f"✅ {msg_db} — Motor: `{cfg_db.DB_TIPO}`")
    else:
        st.error(f"❌ Error DB: {msg_db}")
        
    st.subheader(obtener_texto("sub_admin_noaa", idioma_act))
    st.info(obtener_texto("noaa_sync_info", idioma_act))
    
    if st.button(obtener_texto("btn_sync_noaa", idioma_act)):
        with st.spinner(obtener_texto("spinner_sync", idioma_act)):
            import time
            time.sleep(1.0)
            st.success(obtener_texto("sync_success", idioma_act))

# Pie de página general
st.markdown("---")
st.caption(f"🪸 **CoralTwin-DT** v{config.VERSION} — {config.ATTRIBUTION_TEXT}")
