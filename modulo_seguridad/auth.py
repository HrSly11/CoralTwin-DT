# modulo_seguridad/auth.py
"""Autenticación de usuarios e interfaz de inicio de sesión"""
import streamlit as st
from .db_usuarios import buscar_usuario, verificar_contraseña, actualizar_ultimo_acceso
from .roles_permisos import ROLES

def formulario_acceso():
    """Muestra el formulario de login y la portada informativa"""
    st.sidebar.markdown("## 🔐 Iniciar Sesión")
    
    with st.sidebar.form("form_login_coraltwin"):
        identificador = st.text_input("👤 Usuario o Correo")
        contraseña = st.text_input("🔑 Contraseña", type="password")
        enviar = st.form_submit_button("🌊 Acceder al Gemelo", type="primary")
        
        if enviar:
            if not identificador or not contraseña:
                st.sidebar.error("⚠️ Complete todos los campos.")
                return
            
            usuario = buscar_usuario(identificador)
            
            if usuario and verificar_contraseña(contraseña, usuario["contraseña_hash"]):
                st.session_state.autenticado = True
                st.session_state.usuario = usuario["usuario"]
                st.session_state.nombre_completo = usuario["nombre_completo"]
                st.session_state.id_usuario = usuario["id_usuario"]
                st.session_state.rol = usuario["rol"]
                st.session_state.institucion = usuario["institucion"]
                st.session_state.permisos = ROLES.get(usuario["rol"], {}).get("permisos", {})
                st.session_state.idioma = usuario.get("idioma_preferido", "es")
                st.session_state.tema = usuario.get("tema", "claro")
                
                actualizar_ultimo_acceso(usuario["id_usuario"])
                st.sidebar.success(f"✅ Bienvenido/a, {usuario['nombre_completo']}")
                st.rerun()
            else:
                st.sidebar.error("❌ Credenciales incorrectas.")
    
    # Portada del Sistema en Panel Principal
    st.markdown("""
    # 🪸 CoralTwin-DT
    ### Gemelo Digital de Arrecifes de Coral bajo Estrés Térmico y Acidificación Oceánica
    **Priorización de Restauración y Conservación Marina**
    ---
    """)
    
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("""
        #### 🎯 Propósito del Sistema
        CoralTwin-DT es un gemelo digital ciber-físico que integra:
        - **Dinámica Abiótica y Térmica:** Asimilación de temperatura superficial del mar (**SST**) y semanas de estrés térmico (**DHW**) calibradas con **NOAA Coral Reef Watch**.
        - **Biogeoquímica Oceánica:** Simulación de pH, saturación de aragonita ($\Omega_{\text{arag}}$), turbidez y flujo fotónico (**PAR**).
        - **Ecosistema y Biodiversidad:** Ecuaciones diferenciales acopladas de **Mumby (ODEs)** para modelar cobertura coralina viva, macroalgas invasoras y biodiversidad de Shannon ($H'$).
        - **Inteligencia Artificial Multitarea:** Modelos **XGBoost** y **Random Forest** para predicción de riesgo de blanqueamiento y pérdida tisular.
        - **Toma de Decisiones Espaciales:** Cálculo del **Índice de Priorización de Restauración Espacial (SRPI)** para zonificación en Áreas Marinas Protegidas.
        
        > Ingrese con sus credenciales desde el panel lateral izquierdo para interactuar con los módulos.
        """)
        
    with col2:
        st.info("""
        #### 🔑 Credenciales de Demostración
        
        | 👤 Rol | Usuario | Contraseña |
        |---|---|---|
        | 👑 **Admin** | `admin` | `AdminCoral2026!` |
        | 🔬 **Investigador** | `investigador` | `InvestigaCoral123!` |
        | 🛡️ **Gestor AMP** | `gestor` | `GestionCoral123!` |
        | 🌍 **Consultor** | `consultor` | `ConsultaCoral123!` |
        
        *Recomendado: Iniciar como **Investigador** o **Admin** para probar todas las simulaciones y modelos de IA.*
        """)

def cerrar_sesion():
    """Limpia el estado de sesión actual"""
    st.session_state.autenticado = False
    st.session_state.usuario = None
    st.session_state.rol = None
    st.session_state.permisos = {}
