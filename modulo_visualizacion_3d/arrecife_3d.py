# modulo_visualizacion_3d/arrecife_3d.py
"""Visualización 3D estructural interactiva del gemelo digital de arrecife de coral"""
import numpy as np
import plotly.graph_objects as go

def generar_gemelo_arrecife_3d(
    cobertura_coral_pct: float = 35.0,
    blanqueamiento_pct: float = 15.0,
    macroalgas_pct: float = 25.0,
    rugosidad_estructural: float = 2.4
) -> go.Figure:
    """
    Construye un modelo tridimensional procedural del arrecife de coral:
    - Sustrato calcáreo batimétrico con rugosidad fractal
    - Colonias coralinas vivas pigmentadas
    - Colonias en estado de blanqueamiento térmico tisular
    - Tapetes y frondas de macroalgas invasoras
    """
    np.random.seed(42)
    
    # 1. Malla Batimétrica del Sustrato (Fondo Marino)
    x = np.linspace(-10, 10, 30)
    y = np.linspace(-10, 10, 30)
    X, Y = np.meshgrid(x, y)
    
    # Altura batimétrica modulada por rugosidad estructural
    amplitud = 0.5 * rugosidad_estructural
    Z = (
        np.sin(X * 0.4) * np.cos(Y * 0.4) * amplitud +
        np.sin(X * 0.8 + 1.2) * 0.3 * amplitud +
        np.random.normal(0, 0.08, X.shape)
    )
    
    fig = go.Figure()
    
    # Superficie del sustrato calcáreo
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z,
        colorscale="Earth",
        showscale=False,
        opacity=0.82,
        name="Sustrato Calcáreo"
    ))
    
    # 2. Generación de Colonias Tridimensionales
    n_colonias_total = 180
    x_pos = np.random.uniform(-8.5, 8.5, n_colonias_total)
    y_pos = np.random.uniform(-8.5, 8.5, n_colonias_total)
    
    # Interpolar altura Z para cada colonia en el sustrato
    z_pos = (
        np.sin(x_pos * 0.4) * np.cos(y_pos * 0.4) * amplitud +
        np.sin(x_pos * 0.8 + 1.2) * 0.3 * amplitud + 0.25
    )
    
    # Proporciones dinámicas según el estado del gemelo
    frac_coral_vivo = max(0.05, (cobertura_coral_pct * (1.0 - blanqueamiento_pct / 100.0)) / 100.0)
    frac_blanqueado = max(0.02, (cobertura_coral_pct * (blanqueamiento_pct / 100.0)) / 100.0)
    frac_macroalga = max(0.05, macroalgas_pct / 100.0)
    
    total_frac = frac_coral_vivo + frac_blanqueado + frac_macroalga
    n_vivos = int((frac_coral_vivo / total_frac) * n_colonias_total)
    n_blanqueados = int((frac_blanqueado / total_frac) * n_colonias_total)
    n_macro = n_colonias_total - n_vivos - n_blanqueados
    
    # Índices particionados
    idx_vivo = slice(0, n_vivos)
    idx_blanq = slice(n_vivos, n_vivos + n_blanqueados)
    idx_macro = slice(n_vivos + n_blanqueados, n_colonias_total)
    
    # Colonias Vivas (Pigmentadas: Rosa / Coral / Turquesa)
    if n_vivos > 0:
        fig.add_trace(go.Scatter3d(
            x=x_pos[idx_vivo], y=y_pos[idx_vivo], z=z_pos[idx_vivo],
            mode="markers",
            marker=dict(
                size=np.random.uniform(7, 13, n_vivos),
                color="#FF6F61", # Color Coral vivo
                opacity=0.95,
                symbol="diamond"
            ),
            name="Coral Vivo Saludable"
        ))
        
    # Colonias Blanqueadas (Blanco tiza / Estrés térmico)
    if n_blanqueados > 0:
        fig.add_trace(go.Scatter3d(
            x=x_pos[idx_blanq], y=y_pos[idx_blanq], z=z_pos[idx_blanq],
            mode="markers",
            marker=dict(
                size=np.random.uniform(6, 11, n_blanqueados),
                color="#FFFFFF", # Blanco fluorescente blanqueado
                opacity=0.98,
                symbol="circle"
            ),
            name="Coral Blanqueado (Estrés Térmico)"
        ))
        
    # Tapetes de Macroalgas Invasoras (Verde Oliva / Turf)
    if n_macro > 0:
        fig.add_trace(go.Scatter3d(
            x=x_pos[idx_macro], y=y_pos[idx_macro], z=z_pos[idx_macro],
            mode="markers",
            marker=dict(
                size=np.random.uniform(5, 9, n_macro),
                color="#2E7D32", # Verde Alga invasora
                opacity=0.88,
                symbol="square"
            ),
            name="Macroalgas / Césped Algal"
        ))
        
    # Configuración de Cámara y Escena 3D
    fig.update_layout(
        title="Gemelo Digital 3D: Estructura Arrecifal y Biomasa Bentónica",
        template="plotly_dark",
        scene=dict(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=""),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=""),
            zaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title="Profundidad / Relieve"),
            camera=dict(
                eye=dict(x=1.35, y=-1.45, z=1.15),
                up=dict(x=0, y=0, z=1)
            ),
            aspectratio=dict(x=1.2, y=1.2, z=0.45)
        ),
        margin=dict(l=0, r=0, t=35, b=0),
        height=540,
        legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.02, bgcolor="rgba(15,25,40,0.85)")
    )
    
    return fig
