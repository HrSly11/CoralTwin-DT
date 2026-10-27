"""
10_Publication/generate_v4_manuscript.py
=========================================
Generates CoralTwin-DT_v4.docx resolving all 20 reviewer points (FON-01 to FON-20)
and incorporating all 8 audited tasks into a cohesive, highly professional Word manuscript.
"""

import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
TRAEA_DIR = os.path.join(BASE_DIR, "traea_articulo")
TAREA_DIR = os.path.join(BASE_DIR, "tarea_articulo")
PUB_DIR = os.path.join(BASE_DIR, "10_Publication", "final_manuscript")
os.makedirs(PUB_DIR, exist_ok=True)


def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def set_table_borders(table, color="D3D3D3"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="single" w:sz="6" w:space="0" w:color="{color}"/>\n'
        f'  <w:bottom w:val="single" w:sz="8" w:space="0" w:color="003366"/>\n'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>\n'
        f'  <w:insideV w:val="none"/>\n'
        f'  <w:left w:val="none"/>\n'
        f'  <w:right w:val="none"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def format_table_header(row, col_widths, bg_hex="003366"):
    for i, cell in enumerate(row.cells):
        set_cell_background(cell, bg_hex)
        set_cell_margins(cell, top=140, bottom=140, left=130, right=130)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        if col_widths and i < len(col_widths):
            cell.width = col_widths[i]
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            for run in p.runs:
                run.font.name = "Arial"
                run.font.size = Pt(8.5)
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)


def format_table_rows(table, col_widths, align_left_col0=True):
    for r_idx, row in enumerate(table.rows[1:]):
        bg = "F9FBFD" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, cell in enumerate(row.cells):
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=90, bottom=90, left=110, right=110)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if col_widths and c_idx < len(col_widths):
                cell.width = col_widths[c_idx]
            for p in cell.paragraphs:
                p.paragraph_format.space_before = Pt(1.5)
                p.paragraph_format.space_after = Pt(1.5)
                if c_idx == 0 and align_left_col0:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                else:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    run.font.name = "Arial"
                    run.font.size = Pt(8)
                    run.font.color.rgb = RGBColor(40, 40, 40)


def add_p(doc, text="", space_before=0, space_after=6, line_spacing=1.15, align=WD_ALIGN_PARAGRAPH.LEFT, bold=False, italic=False, font_size=10, font_color=(30, 30, 30)):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    if text:
        run = p.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(font_size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = RGBColor(*font_color)
    return p


def add_h1(doc, text):
    return add_p(doc, text, space_before=14, space_after=6, bold=True, font_size=13, font_color=(0, 51, 102))


def add_h2(doc, text):
    return add_p(doc, text, space_before=11, space_after=4, bold=True, font_size=11, font_color=(20, 40, 80))


def add_h3(doc, text):
    return add_p(doc, text, space_before=8, space_after=3, bold=True, italic=True, font_size=10, font_color=(40, 60, 100))


def add_fig(doc, img_rel_path, caption_text, width_inches=6.0):
    img_full_path = os.path.join(BASE_DIR, img_rel_path)
    if os.path.exists(img_full_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(4)
        run = p_img.add_run()
        run.add_picture(img_full_path, width=Inches(width_inches))
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_cap.paragraph_format.space_before = Pt(2)
        p_cap.paragraph_format.space_after = Pt(10)
        run_cap = p_cap.add_run(caption_text)
        run_cap.font.name = "Arial"
        run_cap.font.size = Pt(8.5)
        run_cap.font.italic = True
        run_cap.font.color.rgb = RGBColor(60, 60, 60)
    else:
        print(f"Warning: Image not found at {img_full_path}")


def build_v4():
    print("Initializing CoralTwin-DT v4 Word Document Builder...")
    doc = docx.Document()
    
    # Configure 1.0 in margins on Letter paper
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)

    # 1. Metadata & Header
    add_p(doc, "Link de la revista: https://www.ecocycles.net/ojs/index.php/ecocycles/", space_after=12, italic=True, font_size=9, font_color=(100, 100, 100))
    
    add_p(doc, "CoralTwin-DT: un gemelo digital ciberfísico que integra aprendizaje automático y biofísica dinámica para priorizar la restauración de arrecifes de coral bajo estrés térmico y acidificación oceánica", 
          space_before=4, space_after=14, bold=True, font_size=15, font_color=(0, 51, 102), align=WD_ALIGN_PARAGRAPH.CENTER)
    
    add_p(doc, "Harry Rodriguez-Sandoval", space_before=2, space_after=2, bold=True, font_size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_p(doc, "ORCID iD: 0009-0004-8219-4123 | Departamento de Ingeniería de Sistemas, Universidad Nacional de Trujillo, Trujillo 13011, Perú", 
          space_after=4, font_size=9, font_color=(80, 80, 80), align=WD_ALIGN_PARAGRAPH.CENTER)
    add_p(doc, "Autor de Correspondencia: Harry Rodriguez-Sandoval (hsrodriguezsa@unitru.edu.pe) | Av. Juan Pablo II s/n, Trujillo 13011, Perú", 
          space_after=14, font_size=8.5, italic=True, font_color=(100, 100, 100), align=WD_ALIGN_PARAGRAPH.CENTER)

    # 2. Resumen Estructurado
    add_h2(doc, "Resumen")
    
    p_abs = doc.add_paragraph()
    p_abs.paragraph_format.line_spacing = 1.15
    p_abs.paragraph_format.space_after = Pt(6)
    p_abs.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    def add_sec(p, tag, body):
        r1 = p.add_run(tag + " ")
        r1.bold = True
        r1.font.name = "Arial"
        r1.font.size = Pt(9.5)
        r2 = p.add_run(body + " ")
        r2.font.name = "Arial"
        r2.font.size = Pt(9.5)

    add_sec(p_abs, "Antecedentes:", 
            "Las olas de calor marinas y la acidificación de los océanos, ambas de origen antropogénico, interactúan para amenazar a los arrecifes de corales escleractinios a escala global. Los monitoreos retrospectivos convencionales y las áreas marinas protegidas (AMP) estáticas carecen de mecanismos dinámicos para anticipar puntos de inflexión biofísicos no lineales y priorizar intervenciones activas de restauración.")
    
    add_sec(p_abs, "Métodos:", 
            "Presentamos CoralTwin-DT, un gemelo digital ciberfísico modular de seis capas de código abierto diseñado para integrar telemetría multiespectral satelital de NOAA Coral Reef Watch (CRW) y Sentinel-2 con sensores biogeoquímicos in situ sobre cuadrículas bentónicas de 500 m. En esta investigación, la arquitectura se evalúa exhaustivamente sobre un conjunto de datos de referencia (N = 15,000 registros estocásticos en 30 estaciones arrecifales globales, 2015–2024, cadencia media de 7.3 días, semilla fija 42). El núcleo predictivo compara cuatro arquitecturas de aprendizaje automático (XGBoost, Random Forest, Deep MLP y Stacked LSTM en PyTorch), evaluadas estrictamente como emuladores del generador, bajo un protocolo de validación cruzada espacial de 5 bloques con buffer de 25 km entre estaciones (distancia mínima de 119.72 km entre pliegues). El sistema incorpora explicabilidad mediante TreeSHAP, ecuaciones diferenciales ordinarias (EDO) de competencia bentónica coral-macroalgas y un Índice de Prioridad Espacial de Restauración (SRPI). Adicionalmente, se ejecutó una validación externa con telemetría satelital operacional real de NOAA CRW de 5 km (2015–2024).")

    add_sec(p_abs, "Resultados:", 
            "Bajo el régimen canónico de 10 variables ambientales limpias de fuga, los cuatro modelos convergieron a un techo predictivo similar en la emulación de pérdida de cobertura coralina (R² entre 0.9336 y 0.9375; RMSE entre 3.92 % y 4.04 %); una auditoría demostró que el R² previo de 0.9994 era un artefacto de fuga por variables bentónicas post-objetivo. Random Forest obtuvo los desempeños nominales más altos (Macro-F1 = 0.7284, R² = 0.9375); XGBoost (R² = 0.9336, RMSE = 4.04 %) se retuvo por su parsimonia en despliegue de borde (latencia monohilo en CPU de 0.322 ms frente a 17.80 ms de Random Forest; 2.83 MB frente a 21.09 MB) y compatibilidad exacta con TreeSHAP, demostrándose que son dos estimadores independientes y no un modelo multitarea. Ante el severo desbalance de clases (clase Medio: 1.24 %), la ponderación de clases en Random Forest cuadruplicó la sensibilidad de la clase Medio del 10.75 % al 45.91 % (exactitud balanceada del 78.63 %). TreeSHAP asignó a las semanas de calentamiento por grado (DHW) el 53.71 % de la importancia. Dentro del soporte empírico real (p10 = 3.16 a p90 = 3.90 de saturación de aragonita, Ω), la acidificación adelanta el cruce del 35 % de pérdida en −0.35 °C-semanas en XGBoost y en −0.80 °C-semanas en el generador analítico. En las simulaciones biofísicas 2025–2050 (RK4, 5,000 corridas Monte Carlo por escenario), el escenario sin mitigación (S1) colapsa a 0.69 % de cobertura (erosión neta de −1.80 kg CaCO₃ m⁻² año⁻¹), mientras que la intervención combinada con AMP (S4) alcanzó 55.20 % de cobertura y +7.46 kg CaCO₃ m⁻² año⁻¹ (mejor escenario simulado). La validación con 10 años de telemetría real de NOAA CRW reveló una correlación nula con el generador sintético (Spearman ρ = −0.0921, p = 0.635) y una reducción drástica de las estaciones Nivel 1 del SRPI (de 17 a 4 estaciones, con solo un 11.76 % de preservación: Hawaii Kaneohe y OahuFore), debido a las intensas olas de calor de 2023–2024 en el Caribe.")

    add_sec(p_abs, "Conclusión:", 
            "CoralTwin-DT demuestra la viabilidad técnica de una arquitectura ciberfísica modular y auditable para el soporte de decisiones en conservación marina. Se esclarece que el emulador predice la respuesta de un generador biofísico sintético y no de arrecifes observados. La discrepancia demostrada frente a los datos satelitales reales de NOAA subraya la imperiosa necesidad de acoplar gemelos digitales con flujos continuos de observación física antes de su implementación operacional en políticas de restauración.")

    add_p(doc, "Palabras clave: gemelo digital (digital twin); restauración de arrecifes de coral (coral reef restoration); XGBoost; TreeSHAP; acidificación oceánica; olas de calor marinas; validación cruzada espacial; NOAA Coral Reef Watch.", 
          space_before=4, space_after=14, italic=True, font_size=9, font_color=(60, 60, 60))

    # 3. Introducción
    add_h1(doc, "1. Introducción")
    add_p(doc, "A escala global, los arrecifes de coral tropicales constituyen epicentros esenciales de la biodiversidad marina: ocupan menos del 0.1 % del lecho marino pero albergan más del 25 % de las especies biológicas descritas en los océanos (Anthony et al., 2020; Klein et al., 2022; Madin et al., 2016). Más allá de su incalculable valor ecológico, las complejas biocenosis arrecifales proporcionan servicios ecosistémicos críticos, incluyendo la disipación de la energía del oleaje costero durante ciclones tropicales, el sustento de la pesca artesanal de subsistencia y el soporte de economías turísticas que sostienen a más de 500 millones de personas en regiones en desarrollo (Anthony et al., 2020; Hein et al., 2021). No obstante, la concurrencia simultánea de perturbaciones climáticas antropogénicas agudas —específicamente las olas de calor marinas (Marine Heatwaves, MHW)— y tensiones biogeoquímicas crónicas como la acidificación oceánica y la hipoxia, sitúan a estos frágiles ecosistemas ante el riesgo inminente de un colapso funcional planetario (Cornwall et al., 2021; Klein et al., 2022; van Hooidonk et al., 2016).")
    
    add_p(doc, "La ruptura térmica de la relación endosimbiótica entre los corales constructores escleractinios y los dinoflagelados de la familia Symbiodiniaceae desencadena el fenómeno de blanqueamiento coralino, mortalidad masiva de colonias y una acelerada pérdida de complejidad tridimensional (Barott et al., 2021; Boonnam et al., 2022; Lin et al., 2023). Simultáneamente, la captación de dióxido de carbono antropogénico por las masas de agua superficiales acidifica el océano, reduciendo la concentración del ion carbonato y desplazando el estado de saturación de la aragonita (Ω_arag) hacia niveles termodinámicamente desfavorables, lo que disminuye drásticamente las tasas de calcificación neta y acelera la bioerosión por organismos perforadores (Bove et al., 2022; Dobson et al., 2024; Esplandiu et al., 2024).")

    add_p(doc, "A pesar de la movilización de importantes fondos multilaterales de conservación marina, los paradigmas vigentes de monitoreo y gestión ambiental exhiben tres limitaciones metodológicas y operacionales bien documentadas:")
    add_p(doc, "1. Modelado desacoplado y desarticulado de los factores de estrés: Los sistemas satelitales consolidados (como NOAA Coral Reef Watch) monitorean la temperatura superficial del mar (SST) y el estrés acumulado expresado en semanas de calentamiento por grado (DHW), pero operan de forma completamente desacoplada de la química del carbonato (pH, Ω_arag), la turbidez costera y la complejidad bentónica local (Boonnam et al., 2022; Cheung et al., 2025; Tzachor et al., 2023).")
    add_p(doc, "2. Priorización espacial estática y pasiva: La declaración de Áreas Marinas Protegidas (AMP) se fundamenta típicamente en polígonos jurisdiccionales rígidos, carentes de asimilación continua de telemetría, sin pronósticos biofísicos predictivos y sin vinculación directa a intervenciones activas de viveros o microfragmentación asistida (Boström-Einarsson et al., 2020; McLeod et al., 2019; Shaver et al., 2022).")
    add_p(doc, "3. Aislamiento algorítmico de 'caja negra' y falta de trazabilidad: Aunque el aprendizaje automático (Machine Learning, ML) se aplica con éxito en la segmentación fotogramétrica de imágenes bentónicas submarinas (Beijbom et al., 2015; Giles et al., 2023; González-Rivero et al., 2020; Ouassine et al., 2025), estas herramientas rara vez se integran en arquitecturas ciberfísicas de ciclo cerrado que traduzcan las predicciones en decisiones territoriales explicables y accionables (Dalibor et al., 2022; de Koning et al., 2023; Tzachor et al., 2023).")

    add_p(doc, "Para sortear estas barreras, en este trabajo proponemos, formalizamos y evaluamos CoralTwin-DT, un gemelo digital ciberfísico de código abierto concebido para articular telemetría de observación terrestre multiespectral, aprendizaje automático explicable y biofísica dinámica no lineal en un flujo metodológico reproducible. Conforme a las taxonomías modernas de gemelos digitales en ingeniería de software y ciencias ecológicas (Aguzzi et al., 2025; Chen et al., 2023; Dalibor et al., 2022; Føre et al., 2024; Guinea-Cabrera & Holgado-Terriza, 2024), la contribución de CoralTwin-DT es fundamentalmente arquitectónica e integradora, y no la propuesta de un nuevo algoritmo que supere intrínsecamente a los clasificadores especializados del estado del arte (Tabla 1).")

    # Tabla 1
    add_p(doc, "Tabla 1: Comparación de características de CoralTwin-DT frente a sistemas previos de monitoreo de arrecifes de coral y gemelos digitales marinos.", 
          space_before=8, space_after=3, bold=True, font_size=8.5, font_color=(0, 51, 102))
    
    t1_data = [
        ["Sistema / Referencia", "Ingesta Continua Multisensorial", "ML Explicable (Atribución Local)", "Simulación Mecanicista Dinámica", "Priorización Espacial Accionable", "Código y Datos Abiertos"],
        ["CoralNet / González-Rivero et al. (2020)", "No (lotes de imágenes estáticas)", "No (clasificación en caja negra)", "No", "No", "Parcial (servidor web)"],
        ["Drones + Deep Learning / Giles et al. (2023)", "No (campañas locales puntuales)", "No", "No", "No", "No disponible"],
        ["Allen Coral Atlas / Lyons et al. (2020, 2024)", "Sí (mosaicos satelitales periódicos)", "No", "No", "Sí (cartografía geomorfológica estática)", "Sí (plataforma pública)"],
        ["Gemelo Oceánico Conceptual / Tzachor et al. (2023)", "Conceptual (artículo de visión)", "No", "Conceptual", "No", "No aplicable (perspectiva teórica)"],
        ["OceanNet / Chattopadhyay et al. (2024)", "Sí (operadores neuronales regionales)", "No (caja negra profunda)", "No (puramente basado en datos)", "No", "Sí (repositorio GitHub)"],
        ["CoralTwin-DT (este estudio)", "Sí (diseño; validado con datos sintéticos y NOAA)", "Sí (TreeSHAP intervencional)", "Sí (EDO acopladas tipo Mumby et al.)", "Sí (SRPI y zonificación GeoJSON)", "Sí (100 % auditable, MIT, Zenodo)"]
    ]
    
    t1 = doc.add_table(rows=len(t1_data), cols=len(t1_data[0]))
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t1)
    col_w1 = [Inches(1.8), Inches(1.3), Inches(1.3), Inches(1.4), Inches(1.4), Inches(1.2)]
    for r_i, row in enumerate(t1.rows):
        for c_i, val in enumerate(t1_data[r_i]):
            row.cells[c_i].paragraphs[0].text = val
    format_table_header(t1.rows[0], col_w1)
    format_table_rows(t1, col_w1, align_left_col0=True)

    add_p(doc, "Estructuramos la presente investigación alrededor de tres Preguntas de Investigación (PI) cuantitativas y verificables:")
    add_p(doc, "PI1 (Capacidad predictiva y latencia en despliegue de borde): ¿Cómo se compara una arquitectura basada en Extreme Gradient Boosting (XGBoost) frente a modelos de ensamble por aleatorización (Random Forest), redes neuronales profundas (Deep MLP) y redes recurrentes para series temporales (Stacked LSTM en PyTorch) en la clasificación de riesgo de blanqueamiento y emulación de pérdida de cobertura viva, bajo validación espacial estricta?")
    add_p(doc, "PI2 (Atribución algorítmica y umbrales de interacción dentro del soporte empírico): ¿Cuáles son las variables ambientales predominantes y cuál es la sensibilidad cuantitativa de los umbrales de estrés térmico (DHW) ante la acidificación oceánica (Ω_arag, pH), según la teoría de juegos cooperativos (TreeSHAP) evaluada dentro del soporte empírico real de los datos?")
    add_p(doc, "PI3 (Proyección decadal de escenarios de restauración y priorización territorial): ¿De qué manera la articulación de ecuaciones diferenciales biofísicas acopladas y el Índice de Prioridad Espacial de Restauración (SRPI) permiten diferenciar trayectorias de cobertura coralina y balances netos de carbonato (2025–2050) bajo distintos regímenes de forzamiento climático y mitigación activa? Clarificamos expresamente que se trata de un análisis comparativo de escenarios y no de una optimización matemática formal (Sección 2.7).")

    # 4. Materiales y Métodos
    add_h1(doc, "2. Materiales y métodos")
    
    add_h2(doc, "2.1 Dominio empírico y red global de estaciones de referencia")
    add_p(doc, "El banco de pruebas de CoralTwin-DT comprende 30 estaciones de referencia (STN_01 a STN_30) distribuidas en cinco provincias biogeográficas marinas representativas: Caribe (12 estaciones: Arrecife Mesoamericano, Belice, Cozumel, Roatán y Cayos de Florida), Indo-Pacífico (10 estaciones: Gran Barrera de Coral norte/centro, Triángulo de Coral —Raja Ampat, Misool, Komodo, Sulawesi y Bali— y Archipiélago de Okinawa), Mar Rojo (3 estaciones: Golfo de Áqaba, Hurghada y Arrecifes de Farasán), Océano Índico occidental (2 estaciones: Seychelles y Maldivas) y Pacífico Central/Occidental (3 estaciones: Hawái y Palaos).")
    
    add_p(doc, "Aclaración sobre el rango temporal y la cadencia observacional: El conjunto de datos cubre un intervalo cronológico comprendido entre el 2015-01-01 y el 2024-12-30 (abarcando 3,609 fechas únicas a lo largo de diez años completos, y no registros finalizados en junio de 2024 como se afirmaba preliminarmente). Cada estación contiene exactamente 500 registros temporales generados estocásticamente mediante un muestreo uniforme sin reemplazo de 500 días entre los 3,652 días del decenio (build_final_dataset.py, líneas 112–115), lo que arroja una cadencia temporal media de 7.3 días (~semanal estocástica).")

    add_p(doc, "Auditoría de procedencia y trazabilidad de datos: En estricto apego al rigor científico, declaramos que los 15,000 registros del dataset canónico (final_dataset.csv) provienen en su totalidad (100.0 %) de una simulación determinista controlada mediante la semilla pseudoaleatoria fija 42. Una auditoría algorítmica independiente reprodujo bit a bit las 15,000 filas (results/audit/data_provenance_summary.json). Por tanto, 0 filas (0.0 %) proceden de transectos bentónicos in situ directos o de sensores en boyas físicas en esta versión de referencia. Las etiquetas 'Real_Observation_Calibrated' existentes en versiones tempranas del repositorio correspondían a un umbral condicional determinista por año (año <= 2021) y no a mediciones humanas de campo; del mismo modo, no existen anotaciones visuales independientes que sustenten un coeficiente kappa de Cohen inter-anotador de 0.81. El pH simulado abarca un rango de 7.962 a 8.207, y la saturación de aragonita oscila entre 2.68 y 4.40.")

    add_h2(doc, "2.2 Estructura ciberfísica modular de seis capas")
    add_p(doc, "La arquitectura de CoralTwin-DT se organiza en seis capas ciberfísicas discretas y desacopladas (Figura 1), garantizando trazabilidad de extremo a extremo, adhesión a los principios rectores FAIR (Findable, Accessible, Interoperable, Reusable; de Koning et al., 2023) y capacidad de inferencia en tiempo real:")
    
    add_p(doc, "Capa 1. Adquisición y telemetría de borde: Especificación operativa diseñada para la ingesta diaria automatizada de productos satelitales térmicos de resolución espacial de 5 km de NOAA Coral Reef Watch (SST, SST Anomaly, HotSpot, DHW; Boonnam et al., 2022), reflectancia multiespectral Nivel 2A de Copernicus Sentinel-2 (coeficiente de atenuación Kd(490), turbidez; Nomenisoa et al., 2024), cartografía geomorfológica de alta resolución del Allen Coral Atlas (Lyons et al., 2024) y series temporales biogeoquímicas de boyas fondeadas provistas de electrodos SeaFET (pH, salinidad, oxígeno disuelto; Aguzzi et al., 2025; Chattopadhyay et al., 2024). En la presente evaluación, esta capa opera como diseño conceptual y se alimenta del generador sintético estandarizado.")

    add_p(doc, "Capa 2. Armonización geodésica y control de calidad (QC): Diseño de arquitectura que contempla el remuestreo espacial por interpolación bilineal hacia cuadrículas bentónicas regulares de 500 m × 500 m y agregación temporal semanal, asistido por filtros automáticos de control de calidad para filtrado de nubosidad y rechazo de lecturas anómalas de sensores. Confirmamos formalmente que en la versión actual del código no se ejecutan rutinas de interpolación ráster geodésica; la resolución de 500 m se emula mediante la dispersión espacial pseudoaleatoria uniforme de las coordenadas geográficas de los transectos (lat +/- 0.018°, lon +/- 0.018°).")

    add_p(doc, "Capa 3. Núcleo de inferencia supervisada y explicabilidad: Modelos de ensamble de gradient boosting (XGBoost) y arquitecturas de referencia (RF, Deep MLP y Stacked LSTM en PyTorch) entrenados para la clasificación multiclase del riesgo de blanqueamiento y la emulación de la pérdida continua de cobertura viva de coral. Esta capa integra explicabilidad algorítmica local y global basada en valores de Shapley mediante TreeSHAP intervencional (Lundberg et al., 2020).")

    add_p(doc, "Capa 4. Núcleo de simulación biofísica no lineal: Sistema acoplado de ecuaciones diferenciales ordinarias (EDO) en tiempo continuo que modela la competencia por el sustrato bentónico entre corales escleractinios y césped de macroalgas a lo largo de un horizonte decadal (2025–2050; Mumby et al., 2007), modulado por la química del carbonato y la presión de pastoreo de herbívoros en AMP (Cornwall et al., 2021; Esplandiu et al., 2024).")

    add_p(doc, "Capa 5. Validación espacial y propagación de incertidumbre: Esquema riguroso de validación cruzada espacial de 5 bloques con buffer de exclusión geográfico de 25 km entre estaciones de entrenamiento y evaluación (Lyons et al., 2020), acoplado a un motor de perturbación estocástica de parámetros mediante simulación Monte Carlo (5,000 corridas por escenario decadal).")

    add_p(doc, "Capa 6. Zonificación operativa y soporte de decisiones: Algoritmo de cómputo del Índice de Prioridad Espacial de Restauración (SRPI), generador automatizado de polígonos geoespaciales en formato GeoJSON para su exportación a consolas SIG y servicios de suscripción a alertas tempranas mediante webhooks para administradores de áreas protegidas.")

    add_fig(doc, "traea_articulo/Figure1_digital_twin_architecture.png", 
            "Figura 1: Arquitectura ciberfísica modular de seis capas de CoralTwin-DT, ilustrando el flujo de datos desde la ingesta satelital y de boyas (Capa 1) hasta la zonificación operativa en GeoJSON (Capa 6). Se aclara que las Capas 1 y 2 constituyen especificaciones de diseño arquitectónico alimentadas por el generador sintético estandarizado en este banco de pruebas.", 
            width_inches=6.2)

    add_h2(doc, "2.3 Formulaciones matemáticas y biofísica computacional")
    add_h3(doc, "2.3.1 Estrés térmico acumulado")
    add_p(doc, "La acumulación de calor anómalo que induce estrés fisiológico sobre el holobionte coralino se cuantifica mediante las semanas de calentamiento por grado (Degree Heating Weeks, DHW), definidas operacionalmente por NOAA CRW como la integral temporal de las anomalías positivas de temperatura superficial (HotSpots) que superan el umbral de blanqueamiento (1.0 °C sobre la media mensual máxima histórica, MMM) en una ventana móvil de 12 semanas (84 días) (Boonnam et al., 2022; Cheung et al., 2025):")
    add_p(doc, "HotSpot(t) = max(SST(t) - MMM, 0)   [°C]   (1)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    add_p(doc, "DHW(t) = (1 / 7) · ∑_{i=0}^{83} HotSpot(t - i) · I(HotSpot(t - i) ≥ 1.0 °C)   [°C-semanas]   (2)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    add_p(doc, "Nota metodológica: Las Ecs. (1)–(2) representan la formulación física de satélite. En el dataset sintético, DHW se modela de forma paramétrica en build_final_dataset.py mediante oscilaciones sinusoidales estacionales acopladas a pulsos gaussianos estocásticos que emulan eventos de olas de calor marinas.")

    add_h3(doc, "2.3.2 Química de carbonatos y tasa de calcificación neta")
    add_p(doc, "La disponibilidad de iones carbonato ([CO₃²⁻]) y el estado de saturación del agua respecto al polimorfo metaestable de aragonita (Ω_arag) determinan la precipitación biogénica del esqueleto coralino:")
    add_p(doc, "Ω_arag = ([Ca²⁺] · [CO₃²⁻]) / K'sp(arag)   (3)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    add_p(doc, "La tasa neta de acreción de carbonato (G_net, kg CaCO₃ m⁻² año⁻¹) se formuló acoplando de forma sinérgica la saturación de aragonita y la atenuación exponencial inducida por estrés térmico, confrontada con la tasa de bioerosión basal destructiva (Bove et al., 2022; Cornwall et al., 2021; Esplandiu et al., 2024):")
    add_p(doc, "G_net = 12.5 · ((Ω_arag - 1) / 2.8)^{1.2} · exp(-0.06 · DHW) - E_bioerosion   (4)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    add_p(doc, "donde la tasa constante de bioerosión basal es E_bioerosion = 1.85 kg CaCO₃ m⁻² año⁻¹.")

    add_h3(doc, "2.3.3 Ecuaciones diferenciales ordinarias de competencia bentónica")
    add_p(doc, "Extendiendo el modelo ecológico fundamental de Mumby, Hastings y Edwards (2007), formulamos un sistema de dos ecuaciones diferenciales acopladas no lineales para la fracción de cobertura espacial de coral vivo (C) y césped de macroalgas (M):")
    add_p(doc, "dC / dt = r · C · (1 - C - M) - [d₀ + (α · DHW²) / (1 + β · Ω_arag)] · C + Φ_restoration   (5)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    add_p(doc, "dM / dt = a · M · (1 - C - M) - [g(H_MPA) · M / (1 - C)] + γ · M · C   (6)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    add_p(doc, "donde r = 0.45 año⁻¹ (tasa intrínseca de crecimiento radial coralino), d₀ = 0.05 año⁻¹ (tasa de senescencia y mortalidad natural no térmica), α = 0.012 y β = 0.75 (coeficientes de mortalidad térmica modulados por aragonita), a = 0.85 año⁻¹ (tasa de colonización macroalgal), γ = 0.22 año⁻¹ (coeficiente de sobrecrecimiento competitivo de algas sobre colonias de coral), y Φ_restoration es la tasa de trasplante activo en viveros (Φ = 0.025 año⁻¹ en S3; Φ = 0.030 año⁻¹ en S4; Boström-Einarsson et al., 2020; Ladd et al., 2019).")
    add_p(doc, "Clarificación matemática del término de pastoreo: En la Ec. (6), el término clásico de control biológico g(H_MPA) · M / [M + (1 - C - M)] se simplifica estrictamente a g(H_MPA) · M / (1 - C), donde (1 - C) representa la totalidad del espacio bentónico disponible susceptible de ser colonizado por algas o mantenido libre por peces loro y erizos herbívoros protegidos dentro de la reserva marina (g = 0.25 sin protección; g = 0.68 en AMP de veda total con fiscalización efectiva; Mumby et al., 2007).")

    add_p(doc, "Cuatro regímenes de manejo simulados (2025–2050): Partiendo de la línea base común del dataset (cobertura coralina media de 33.68 % y macroalgas de 31.41 %), se simularon cuatro escenarios bajo integración numérica de Runge-Kutta de cuarto orden (RK4; paso de tiempo Δt = 0.05 años, 500 pasos temporales):")
    add_p(doc, "• Escenario 1 (S1, Calentamiento severo / SSP5-8.5): Tasa de incremento térmico anual de 0.36 °C-semanas/año, sin AMP (g = 0.25), pendiente de Ω de −0.052 año⁻¹, sin restauración activa (Φ = 0).")
    add_p(doc, "• Escenario 2 (S2, Mitigación moderada / SSP2-4.5): Pendiente de DHW de 0.18 °C-semanas/año, protección parcial (g = 0.30), pendiente de Ω de −0.022 año⁻¹, sin restauración (Φ = 0).")
    add_p(doc, "• Escenario 3 (S3, Trasplante activo intensivo): Pendiente de DHW de 0.20 °C-semanas/año, g = 0.35, trasplante asistido con corales preacondicionados (+2.0 °C de tolerancia térmica añadida a las EDO; Φ = 0.025 año⁻¹).")
    add_p(doc, "• Escenario 4 (S4, Intervención combinada: Trasplante + AMP estricta): Pendiente de DHW de 0.18 °C-semanas/año, tolerancia térmica de +2.0 °C, protección total de herbívoros (g = 0.68), trasplante activo vigoroso (Φ = 0.030 año⁻¹). Aclaramos taxativamente que S4 representa el 'mejor escenario simulado' bajo intervención combinada, y NO una solución de optimización formal (Sección 2.7).")

    add_h2(doc, "2.4 Implementación de modelos de aprendizaje automático y control de fuga del objetivo")
    add_p(doc, "Arquitectura de XGBoost (¿Multitarea o estimadores independientes?): Verificamos inequívocamente a nivel de código fuente en train_models.py (líneas 487–498 y 885–888) que XGBoost NO es un modelo multitarea conjunto de salida compartida. Se trata de DOS ESTIMADORES TOTALMENTE INDEPENDIENTES: un clasificador multiclase (xgb.XGBClassifier, serializado como xgboost_classifier.joblib) y un regresor de pérdida de cobertura (xgb.XGBRegressor, serializado como xgboost_regressor.joblib), ambos optimizados de forma autónoma con sus propias funciones de pérdida y árboles de decisión.")

    add_p(doc, "Ajuste e hiperparámetros de los cuatro modelos evaluados: En la Tabla 2 se documentan exhaustivamente los hiperparámetros reales utilizados en el código fuente. Para XGBoost y Random Forest, los hiperparámetros críticos se seleccionaron mediante una búsqueda en malla anidada espacial de 3 pliegues (GroupKFold por estación) ejecutada internamente dentro de cada pliegue de entrenamiento externo (results/nested_cv_hyperparameters.json). Para Deep MLP y Stacked LSTM, se implementaron arquitecturas canónicas en PyTorch con normalización por lotes, regularización por dropout y un mecanismo estricto de parada temprana (Early Stopping con paciencia de 5 épocas sobre el conjunto espacial de validación interna).")

    # Tabla 2
    add_p(doc, "Tabla 2: Especificación exhaustiva de hiperparámetros, esquemas de optimización espacial y arquitecturas de aprendizaje profundo implementadas en CoralTwin-DT.", 
          space_before=8, space_after=3, bold=True, font_size=8.5, font_color=(0, 51, 102))

    t2_data = [
        ["Modelo y Componente", "Hiperparámetro / Capa", "Valor Real en Código", "Esquema de Ajuste", "Justificación Técnica"],
        ["XGBoost Clasificador", "n_estimators / max_depth", "350 árboles / profundidad 6", "Optimizado (CV interna 3-fold)", "Equilibrio entre capacidad no lineal y prevención de sobreajuste"],
        ["XGBoost Clasificador", "learning_rate / subsample", "0.05 / 0.80", "Optimizado (CV interna 3-fold)", "Tasa de aprendizaje conservadora y remuestreo estocástico de filas"],
        ["XGBoost Clasificador", "colsample_bytree / min_child_weight", "0.80 / 3", "Optimizado / Fijo", "Fracción de variables por división y soporte mínimo por hoja"],
        ["XGBoost Clasificador", "objective / eval_metric", "multi:softprob / mlogloss", "Fijo Canónico", "Clasificación probabilística multiclase con entropía cruzada"],
        ["XGBoost Regresor", "n_estimators / max_depth / lr", "350 / 6 / 0.05", "Optimizado (CV interna 3-fold)", "Estimador independiente para pérdida continua de cobertura coralina"],
        ["XGBoost Regresor", "objective", "reg:squarederror", "Fijo Canónico", "Regresión por mínimos cuadrados"],
        ["Random Forest (Clf/Reg)", "n_estimators / max_depth", "200 árboles / profundidad 12", "Optimizado (CV interna 3-fold)", "Estabilización de varianza del ensamble por bagging"],
        ["Random Forest (Clf/Reg)", "min_samples_split / min_samples_leaf", "4 / 2", "Optimizado (CV interna 3-fold)", "Suavizado de particiones internas y control de hojas terminales"],
        ["Random Forest (Clf/Reg)", "max_features / bootstrap", "sqrt (Clf) / 1.0 (Reg) / True", "Fijo Canónico", "Subespacio aleatorio clásico y remuestreo con reemplazo"],
        ["Deep MLP (PyTorch)", "Arquitectura de capas densas", "Input(10) -> 128 -> 64 -> 32 -> Salida", "Fijo Canónico", "Red prealimentada piramidal con reducción dimensional progresiva"],
        ["Deep MLP (PyTorch)", "Normalización / Activación / Dropout", "BatchNorm1d / ReLU / p = 0.20", "Fijo Canónico", "Estabilización de covarianza interna y regularización por desconexión"],
        ["Deep MLP (PyTorch)", "Optimizador / lr / weight_decay", "AdamW / 1e-3 / 1e-4", "Fijo Canónico", "Descenso de gradiente adaptativo con penalización L2"],
        ["Deep MLP (PyTorch)", "Lote / Épocas / Parada Temprana", "Batch 256 / 30 épocas / Paciencia 5", "Dinámico (validación interna)", "Criterio de parada sobre pliegue espacial interno (delta < 1e-4)"],
        ["Stacked LSTM (PyTorch)", "Longitud de secuencia (seq_len)", "8 pasos temporales semanales", "Fijo Canónico", "Ventana histórica de dependencia temporal por estación"],
        ["Stacked LSTM (PyTorch)", "Capas recurrentes y cabeza densa", "LSTM(10, 64) -> Drop(0.2) -> LSTM(64, 32) -> Head(32, 32)", "Fijo Canónico", "Extracción jerárquica de dinámica temporal acoplada a regresión"],
        ["Stacked LSTM (PyTorch)", "Optimizador / lr / Parada Temprana", "AdamW / 3e-3 / Paciencia 5 épocas", "Dinámico (validación interna)", "Entrenamiento secuencial por lotes de 256 en CPU"]
    ]
    t2 = doc.add_table(rows=len(t2_data), cols=len(t2_data[0]))
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t2)
    col_w2 = [Inches(1.8), Inches(1.8), Inches(1.5), Inches(1.5), Inches(1.8)]
    for r_i, row in enumerate(t2.rows):
        for c_i, val in enumerate(t2_data[r_i]):
            row.cells[c_i].paragraphs[0].text = val
    format_table_header(t2.rows[0], col_w2)
    format_table_rows(t2, col_w2, align_left_col0=True)

    add_p(doc, "Construcción del target y naturaleza de emulación (surrogate model): Para disipar cualquier duda sobre fuga de datos, documentamos explícitamente cómo se construye la variable objetivo continua (Coral_Cover_Loss_Pct): en el generador, dicha variable se obtiene como una combinación lineal directa de la severidad del blanqueamiento más una perturbación gaussiana estocástica (Coral_Cover_Loss_Pct = 0.78 · Bleaching_Severity_Pct + N(0, 2²)). A su vez, la severidad es una transformación logística determinista de un índice de estrés biofísico acoplado a DHW, Ω_arag y radiación PAR. Por consiguiente, la tarea de regresión no predice un fenómeno ecológico no observado, sino que actúa como una emulación estricta (modelo sustituto) de la superficie analítica del generador. Las variables bentónicas locales (Shannon_Diversity_H, Structural_Rugosity, Live_Coral_Cover_Pct, Macroalgae_Cover_Pct) se generan después de la severidad; su inclusión en modelos previos explicaba el R² atípico de 0.9995. Al excluirlas, el régimen canónico queda restringido a 10 variables ambientales limpias de fuga (SST, SST Anomaly, DHW, pH, Salinidad, Oxígeno disuelto, Ω_arag, Turbidez, PAR, Profundidad).")

    add_h2(doc, "2.5 Protocolo de validación cruzada espacial de 5 bloques con buffer de 25 km")
    add_p(doc, "La validación cruzada aleatoria estándar (KFold) sobre conjuntos de datos geoespaciales induce un sesgo severamente optimista debido a la fuerte autocorrelación espacial entre muestras próximas (Lyons et al., 2020). Para garantizar una separación rigurosa y evitar la fuga de proximidad, implementamos un esquema de validación cruzada espacial de 5 bloques de estaciones completas (results/folds_assignment.csv; Figura 2). Las 30 estaciones se distribuyeron en cinco pliegues de 6 estaciones cada uno, de tal forma que todas las observaciones temporales de una estación dada pertenecen exclusivamente al conjunto de entrenamiento o al de prueba:")
    add_p(doc, "• Pliegue 1: Mesoamerican_Fore_01, Mesoamerican_Crest_02, Mesoamerican_Back_03, Mesoamerican_Lagoon_04, GreatBarrier_Northern_13, RedSea_Aqaba_23.")
    add_p(doc, "• Pliegue 2: Cozumel_South_07, Cozumel_Shallow_08, GreatBarrier_Central_14, GreatBarrier_Lagoon_15, RedSea_Shallow_24, Seychelles_Mahe_26.")
    add_p(doc, "• Pliegue 3: Roatan_North_09, Roatan_South_10, CoralTriangle_RajaAmpat_16, CoralTriangle_Misool_17, RedSea_Farasan_25, Maldives_AriAtoll_27.")
    add_p(doc, "• Pliegue 4: Belize_Barrier_05, Belize_Atoll_06, CoralTriangle_Komodo_18, CoralTriangle_Sulawesi_19, Hawaii_Kaneohe_28, Hawaii_OahuFore_29.")
    add_p(doc, "• Pliegue 5: Florida_Keys_Uppers_11, Florida_Keys_Lowers_12, CoralTriangle_Bali_20, Okinawa_Kerama_21, Okinawa_Ishigaki_22, Palau_RockIslands_30.")
    
    add_p(doc, "Cumplimiento del buffer de exclusión geográfico de 25 km: Aunque 12 de las 30 estaciones poseen una estación vecina a menos de 25 km (con una distancia mínima de 3.95 km entre Mesoamerican_Fore_01 y Mesoamerican_Crest_02), todas las estaciones vecinas fueron asignadas obligatoriamente al mismo pliegue espacial. La distancia geográfica mínima observada entre estaciones pertenecientes a pliegues distintos es de 119.72 km (115.33 km entre registros individuales con jitter). En consecuencia, se registraron exactamente 0 violaciones al criterio del buffer de 25 km, garantizando la independencia espacial de las pruebas.")

    add_p(doc, "Aclaración sobre las '480 cuadrículas por pliegue': En el código de spatial_cv.py (línea 223), se asignó nominalmente un identificador teórico de N_Grid_Cells = 80 celdas por estación, totalizando 480 cuadrículas nominales por pliegue (6 estaciones × 80). En la estructura tabular real de final_dataset.csv no existe una columna Grid_Cell_ID; la resolución espacial submétrica de los puntos proviene de una dispersión estocástica controlada de las coordenadas de la estación, conteniendo cada pliegue exactamente 3,000 registros observacionales (6 estaciones × 500 filas).")

    add_fig(doc, "traea_articulo/Fig_spatial_folds_diagram.png", 
            "Figura 2: Diseño del protocolo de validación cruzada espacial de 5 bloques con buffer de exclusión de 25 km entre estaciones de entrenamiento y evaluación. Se ilustra la distribución global de las 30 estaciones en cinco provincias biogeográficas y la matriz de distancias mínimas inter-pliegue (mínimo de 119.72 km; 0 violaciones del buffer).", 
            width_inches=6.0)

    add_h2(doc, "2.6 Inferencia estadística y protocolo riguroso de latencia computacional")
    add_p(doc, "Evaluación de significancia y robustez: Para evaluar la solidez de las diferencias métricas entre las cuatro arquitecturas, se aplicaron pruebas pareadas bilaterales de rangos con signo de Wilcoxon sobre las 25 ejecuciones pareadas (5 pliegues espaciales × 5 semillas aleatorias) de Macro-F1 y RMSE, calculando el tamaño del efecto mediante la d de Cohen y controlando la tasa de error por familia con la corrección estricta de Bonferroni (α_ajustado = 0.05 / 6 comparaciones = 0.00833). Asimismo, se obtuvieron intervalos de confianza del 95 % mediante remuestreo bootstrap con 1,000 iteraciones.")
    
    add_p(doc, "Protocolo experimental de medición de latencia: Las pruebas de latencia de inferencia se ejecutaron en una CPU comercial estándar (procesador AMD64 de arquitectura x86_64 a velocidad base, sin aceleración por GPU ni coprocesadores de punto flotante), fijando los hilos de ejecución a uno solo (OMP_NUM_THREADS = 1, torch.set_num_threads(1), n_jobs = 1) para emular la capacidad de cómputo restringida de nodos oceanográficos de borde en boyas autónomas. El protocolo constó de 50 iteraciones de calentamiento de caché (warm-up) no registradas, seguidas de 500 evaluaciones cronometradas de inferencia pura por muestra individual (tamaño de lote = 1) y por minilote (tamaño de lote = 256), registrando la media y la desviación estándar de la latencia en milisegundos (ms) sin incluir el tiempo de lectura de disco o deserialización (results/latency_protocol.json).")

    add_h2(doc, "2.7 Índice de Prioridad Espacial de Restauración (SRPI)")
    add_p(doc, "El Índice de Prioridad Espacial de Restauración (Spatial Restoration Priority Index, SRPI) consolida la información multisensorial en una métrica escalar de priorización operativa de áreas arrecifales (Anthony et al., 2020; Sauder et al., 2023):")
    add_p(doc, "SRPI = 0.35 · ThermRefugia + 0.25 · RestorationUrgency + 0.25 · BenthicRugosity + 0.15 · WaterQuality   (7)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    add_p(doc, "donde: ThermRefugia = 1 - min(DHW_95th / 16, 1) evalúa la resiliencia al estrés térmico acumulado en el percentil 95; RestorationUrgency = max(0, 1 - Cobertura_Actual / Cobertura_Base_Historica) prioriza sitios degradados con alto potencial de ganancia; BenthicRugosity = (Rugosidad_Estructural - 1.0) / 2.0 cuantifica el refugio arquitectónico para peces e invertebrados ramoneadores (Price et al., 2019; Rossi et al., 2020); y WaterQuality = 1 - min(Kd(490) / 0.25, 1) premia aguas transparentes favorables para la fotosíntesis del holobionte (Asner et al., 2020; Sauder et al., 2023).")
    add_p(doc, "Nota formal de delimitación metodológica: El SRPI es un índice ponderado de clasificación multicriterio y ordenamiento territorial. Los cuatro escenarios evaluados en la Sección 3.3 son simulaciones proyectivas hacia adelante y no el resultado de una optimización matemática formal. No se define ni se resuelve ningún problema de programación matemática, función objetivo o espacio de restricciones de decisión presupuestaria. El término 'óptimo' se elimina de la descripción de los escenarios para evitar confusiones conceptuales.")

    add_h2(doc, "2.8 Entorno de software, hardware y reproducibilidad computacional")
    add_p(doc, "En la Tabla 3 se detallan las especificaciones del entorno computacional reproducible que sustentan los resultados presentados, alineados con el contenedor Docker oficial del proyecto.")

    # Tabla 3
    add_p(doc, "Tabla 3: Especificaciones del software, hardware y entorno computacional para la replicación independiente de CoralTwin-DT.", 
          space_before=8, space_after=3, bold=True, font_size=8.5, font_color=(0, 51, 102))

    t3_data = [
        ["Componente de Infraestructura", "Especificación Verificada"],
        ["Lenguaje y Entorno Base", "Python 3.11.9 sobre Windows 10 x64 / Linux contenedor Docker"],
        ["Librerías Científicas y ML", "scikit-learn 1.4.2, XGBoost 2.0.3, PyTorch 2.1.2/2.2.0+cpu, SHAP 0.45.1, SciPy 1.15.3, pandas 2.2.2, NumPy 1.26.4"],
        ["Plataforma de Hardware de Prueba", "Procesador AMD64 / Intel Core (8 vCPUs, 16 GB RAM), sin soporte de acelerador gráfico (solo CPU)"],
        ["Protocolo de Semillas Aleatorias", "Semilla maestra del generador de datos = 42; 5 semillas de evaluación cruzada = (17, 42, 73, 108, 256)"],
        ["Pipeline Reproducible de Ejecución", "Ejecución automatizada de 17 etapas mediante python run_all.py (tiempo de ejecución total: 95.99 segundos)"],
        ["Contenedorización Oficial", "Dockerfile y requirements.txt sincronizados bajo licencia de código abierto MIT"]
    ]
    t3 = doc.add_table(rows=len(t3_data), cols=len(t3_data[0]))
    t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t3)
    col_w3 = [Inches(2.8), Inches(5.2)]
    for r_i, row in enumerate(t3.rows):
        for c_i, val in enumerate(t3_data[r_i]):
            row.cells[c_i].paragraphs[0].text = val
    format_table_header(t3.rows[0], col_w3)
    format_table_rows(t3, col_w3, align_left_col0=True)

    # 5. Resultados
    add_h1(doc, "3. Resultados")
    
    add_h2(doc, "3.1 PI1: Comparación predictiva, exactitud de clasificación y latencia de inferencia")
    add_p(doc, "Bajo la validación cruzada espacial de 5 bloques (N = 15,000 registros observacionales distribuidos en 30 estaciones) y el régimen canónico de 10 variables ambientales limpias de fuga, las cuatro arquitecturas evaluadas alcanzaron un desempeño predictivo notablemente parejo (Tabla 4; Figura 3). Random Forest obtuvo nominalmente los valores más altos en Macro-F1 (0.7284), R² (0.9375), RMSE (3.924 %) y exactitud balanceada (70.16 %), superando marginalmente a XGBoost (Macro-F1 = 0.7187, R² = 0.9336, RMSE = 4.044 %). El modelo Deep MLP alcanzó R² = 0.9337 y la red Stacked LSTM obtuvo R² = 0.9371 (RMSE = 3.934 %).")
    
    add_p(doc, "Techo de emulación y significancia estadística: El R² de todas las arquitecturas osciló en la estrecha franja entre 0.9336 y 0.9375, un rango que converge directamente al límite asintótico impuesto por el ruido estocástico intrínseco programado en el generador (ruido gaussiano con desviación estándar de 2.0 % sobre la severidad, R²_teórico ≈ 0.94). Aunque la prueba pareada de Wilcoxon sobre las 25 ejecuciones (Bonferroni, α = 0.00833) detectó diferencias formales significativas en Macro-F1 a favor de Random Forest frente a XGBoost (p = 0.0024; d de Cohen = −0.71), la evaluación del error absoluto sobre la totalidad de los 15,000 registros fuera de muestra demostró tamaños de efecto prácticamente nulos (d ≤ 0.09). Por tanto, no se sostiene una superioridad predictiva intrínseca de XGBoost sobre Random Forest ni sobre las redes neuronales profundas.")

    add_p(doc, "Justificación técnica de la selección de XGBoost: La elección de XGBoost como núcleo del gemelo digital se justifica exclusivamente por razones de ingeniería de software y eficiencia en despliegue de borde: (i) Latencia de inferencia: con tamaño de lote unitario (lote = 1) en CPU monohilo, XGBoost ejecuta la inferencia en 0.322 ms, siendo aproximadamente 55 veces más rápido que Random Forest (17.80 ms); (ii) Huella de almacenamiento: el ensamble serializado de XGBoost ocupa 2.83 MB frente a 21.09 MB de Random Forest; y (iii) Interpretabilidad nativa: XGBoost es directamente compatible con la formulación de complejidad polinomial de TreeSHAP, permitiendo explicaciones locales en milisegundos sin recurrir a aproximaciones lentas.")

    # Tabla 4
    add_p(doc, "Tabla 4: Desempeño predictivo de las cuatro arquitecturas (régimen canónico de 10 variables ambientales; CV espacial de 5 bloques; 5 semillas) y latencia de inferencia en CPU monohilo. Intervalos de confianza del 95 % por remuestreo bootstrap entre corchetes.", 
          space_before=8, space_after=3, bold=True, font_size=8.5, font_color=(0, 51, 102))

    t4_data = [
        ["Arquitectura Evaluada", "Exactitud Global (%) [IC 95 %]", "Exactitud Balanceada (%)", "Macro-F1 [IC 95 %]", "R² de Emulación [IC 95 %]", "RMSE (%) [IC 95 %]", "Latencia lote 1 / 256 (ms) · Tamaño"],
        ["XGBoost (Núcleo explicable)", "98.85 [98.67–99.01]", "69.62", "0.7187 [0.6966–0.7423]", "0.9336 [0.9292–0.9374]", "4.044 [3.996–4.091]", "0.322 / 0.0064 ms · 2.83 MB"],
        ["Random Forest", "98.88 [98.71–99.04]", "70.16", "0.7284 [0.7045–0.7521]", "0.9375 [0.9335–0.9412]", "3.924 [3.884–3.964]", "17.80 / 0.0800 ms · 21.09 MB"],
        ["Deep MLP (PyTorch)", "98.79 [98.62–98.96]", "67.56", "0.6807 [0.6681–0.6968]", "0.9337 [0.9292–0.9375]", "4.041 [3.997–4.086]", "0.197 / 0.0015 ms · 0.11 MB"],
        ["Stacked LSTM (PyTorch)", "98.81 [98.64–98.98]", "68.23", "0.6949 [0.6775–0.7157]", "0.9371 [0.9331–0.9408]", "3.934 [3.893–3.977]", "0.414 / 0.0131 ms · 0.26 MB"]
    ]
    t4 = doc.add_table(rows=len(t4_data), cols=len(t4_data[0]))
    t4.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t4)
    col_w4 = [Inches(1.8), Inches(1.3), Inches(1.0), Inches(1.1), Inches(1.1), Inches(1.1), Inches(1.6)]
    for r_i, row in enumerate(t4.rows):
        for c_i, val in enumerate(t4_data[r_i]):
            row.cells[c_i].paragraphs[0].text = val
    format_table_header(t4.rows[0], col_w4)
    format_table_rows(t4, col_w4, align_left_col0=True)

    add_p(doc, "Auditoría de fuga del objetivo (Leakage Ablation): En la Tabla 5 se evidencia la prueba de ablación de variables. Cuando se incluyeron las 16 variables del repositorio previo (incluyendo Shannon_Diversity_H, rugosidad bentónica y coberturas), el R² alcanzó un valor artificial de 0.9994 (RMSE = 0.395 %). El análisis TreeSHAP reveló que Shannon_Diversity_H concentraba por sí sola el 80.61 % de la importancia total, al ser una variable generada matemáticamente a partir de la severidad del blanqueamiento (post-target). Al remover las variables bentónicas y entrenar exclusivamente con las 10 variables ambientales limpias, el R² se situó en el valor legítimo de 0.9336.")

    # Tabla 5
    add_p(doc, "Tabla 5: Auditoría de fuga de información del objetivo con XGBoost (semilla 42; CV espacial de 5 bloques). El régimen canónico de 10 variables ambientales elimina la fuga de métricas bentónicas.", 
          space_before=8, space_after=3, bold=True, font_size=8.5, font_color=(0, 51, 102))

    t5_data = [
        ["Régimen de Entrada", "N.° Variables", "Variables Ambientales y Bentónicas Incluidas", "Exactitud (%)", "Macro-F1", "R² Emulación", "RMSE (%)"],
        ["Con fuga (auditado)", "16", "Todas las variables, incluyendo índices bentónicos post-objetivo (Shannon, rugosidad)", "98.83", "0.7335", "0.9994", "0.395"],
        ["Conjunto empírico previo", "10", "Ambientales más rugosidad y cobertura viva (en lugar de salinidad y oxígeno)", "98.81", "0.7197", "0.8305", "6.460"],
        ["Canónico (Limpio)", "10", "SST, anomalía SST, DHW, pH, salinidad, oxígeno disuelto, Ω_arag, turbidez, PAR, profundidad", "98.85", "0.7187", "0.9336", "4.044"],
        ["Sin forzantes térmicos", "6", "Profundidad, SST, anomalía SST, pH, salinidad, oxígeno disuelto (sin DHW, Ω, PAR, turbidez)", "98.29", "0.6925", "0.8487", "6.104"],
        ["Línea base mínima", "2", "Profundidad y salinidad únicamente", "93.98", "0.3230", "−0.0269", "15.901"]
    ]
    t5 = doc.add_table(rows=len(t5_data), cols=len(t5_data[0]))
    t5.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t5)
    col_w5 = [Inches(1.8), Inches(0.8), Inches(2.6), Inches(0.9), Inches(0.9), Inches(0.9), Inches(0.9)]
    for r_i, row in enumerate(t5.rows):
        for c_i, val in enumerate(t5_data[r_i]):
            row.cells[c_i].paragraphs[0].text = val
    format_table_header(t5.rows[0], col_w5)
    format_table_rows(t5, col_w5, align_left_col0=True)

    add_fig(doc, "traea_articulo/Figure2_methodological_workflow.png", 
            "Figura 3: Desempeño predictivo de las cuatro arquitecturas evaluadas bajo validación cruzada espacial de 5 bloques en el régimen canónico de 10 variables (A-C) y curva de ablación de fuga de información con XGBoost (D). Las barras de error representan intervalos de confianza del 95 % obtenidos mediante remuestreo bootstrap.", 
            width_inches=6.2)

    add_p(doc, "Mitigación del desbalance extremo en la clase minoritaria 'Medio' (Tabla 6): La marcada disparidad entre la exactitud global (98.85 %) y la exactitud balanceada (69.62 %) se origina en la distribución fuertemente asimétrica de las tres clases de riesgo de blanqueamiento: Bajo (93.98 %, 14,097 registros), Medio (1.24 %, 186 registros) y Alto (4.78 %, 717 registros). En los modelos canónicos no ponderados, la clase minoritaria Medio casi no se detecta (sensibilidad de 9.78 % en XGBoost y 10.75 % en Random Forest; Figura 4-B). Para resolver esta limitación operativa señalada en el informe de revisión por pares, reentrenamos XGBoost y Random Forest aplicando ponderación inversa de frecuencias de clase (sample_weight='balanced' y class_weight='balanced') bajo el mismo esquema de 5 pliegues espaciales × 5 semillas (Tabla 6).")

    # Tabla 6
    add_p(doc, "Tabla 6: Evaluación comparativa del impacto de la ponderación de clases en XGBoost y Random Forest para la mitigación del desbalance en la clase minoritaria 'Medio' (5 pliegues espaciales × 5 semillas).", 
          space_before=8, space_after=3, bold=True, font_size=8.5, font_color=(0, 51, 102))

    t6_data = [
        ["Modelo y Régimen de Ponderación", "Exactitud Global (%) [IC 95 %]", "Exactitud Balanceada (%) [IC 95 %]", "Macro-F1 [IC 95 %]", "Sensibilidad 'Bajo' (%)", "Sensibilidad 'Medio' (%) [IC 95 %]", "Sensibilidad 'Alto' (%)", "PR-AUC 'Medio'"],
        ["XGBoost Canónico (Sin ponderar)", "98.86 [98.67–99.01]", "69.83 [68.29–71.10]", "0.7225 [0.6966–0.7423]", "99.99", "9.78 [5.26–13.64]", "99.72", "0.1431"],
        ["XGBoost Ponderado (sample_weight)", "98.18 [98.05–98.44]", "70.23 [68.81–71.85]", "0.7089 [0.6933–0.7285]", "99.24", "11.72 [7.37–16.67]", "99.72", "0.1497"],
        ["Random Forest Canónico (Sin ponderar)", "98.88 [98.71–99.04]", "70.17 [68.75–71.68]", "0.7285 [0.7045–0.7521]", "100.00", "10.75 [6.53–15.38]", "99.75", "0.1688"],
        ["Random Forest Ponderado (class_weight)", "89.93 [89.43–90.39]", "78.63 [75.82–80.57]", "0.6818 [0.6744–0.6880]", "90.00", "45.91 [37.62–51.76]", "99.97", "0.1068"]
    ]
    t6 = doc.add_table(rows=len(t6_data), cols=len(t6_data[0]))
    t6.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t6)
    col_w6 = [Inches(1.8), Inches(1.2), Inches(1.2), Inches(1.0), Inches(0.9), Inches(1.1), Inches(0.9), Inches(0.9)]
    for r_i, row in enumerate(t6.rows):
        for c_i, val in enumerate(t6_data[r_i]):
            row.cells[c_i].paragraphs[0].text = val
    format_table_header(t6.rows[0], col_w6)
    format_table_rows(t6, col_w6, align_left_col0=True)

    add_p(doc, "Trade-off operacional de la ponderación de clases: En Random Forest ponderado, la sensibilidad (recall) de la clase minoritaria crítica Medio se cuadruplica, pasando de 10.75 % a 45.91 % (IC 95 %: 37.62–51.76 %), impulsando la exactitud balanceada hasta 78.63 %. No obstante, este incremento se produce a expensas de inducir falsos positivos en la clase mayoritaria Bajo, lo que reduce la exactitud global del 98.88 % al 89.93 % y disminuye el Macro-F1 a 0.6818. Este hallazgo demuestra la necesidad de que los gestores de áreas marinas elijan entre un modelo de máxima exactitud global (canónico) o un modelo de máxima sensibilidad hacia fases iniciales de estrés (ponderado).")

    add_h2(doc, "3.2 PI2: Atribución algorítmica y puntos de inflexión dentro del soporte empírico de los datos (TreeSHAP)")
    add_p(doc, "Atribución TreeSHAP global: La atribución local intervencional basada en valores de Shapley sobre el modelo XGBoost canónico de 10 variables identificó al estrés térmico acumulado (DHW) como el forzante preponderante indiscutible de la pérdida de cobertura coralina emulada, concentrando el 53.71 % de la importancia global relativa (IC 95 % bootstrap: [51.37–55.98 %]). Le siguieron la radiación fotosintéticamente activa (PAR, 11.35 %), la anomalía de SST (9.28 %), la saturación de aragonita (Ω_arag, 8.81 %) y la temperatura superficial absoluta (SST, 5.19 %); por su parte, salinidad, profundidad, pH, oxígeno disuelto y turbidez aportaron individualmente entre 1.95 % y 2.66 % (Figura 4-C).")

    add_p(doc, "Análisis de umbrales dentro del soporte empírico de los datos: El rango real de saturación de aragonita en el dataset abarca de 2.68 a 4.40 (media 3.523, desviación estándar 0.2955; pH entre 7.962 y 8.207). Es imperativo resaltar que en los datos existen exactamente 0 registros con Ω <= 2.40 y 0 registros con Ω <= 2.60; únicamente 18 registros (0.12 %) presentan Ω <= 2.80. Por tanto, evaluar umbrales a Ω = 2.20 o pH <= 7.85 como en informes previos constituía una extrapolación contrafáctica no soportada. Conducimos el análisis dentro del soporte empírico real delimitado por los percentiles 10 y 90 (p10 = 3.16 con 1,562 registros; p90 = 3.90 con 1,546 registros):")
    add_p(doc, "• En el emulador XGBoost, comparar condiciones favorables (Ω = 3.90, p90) frente a condiciones desfavorables dentro del soporte (Ω = 3.16, p10) revela que el punto semimáximo (EC50) se sitúa invariable en DHW = 10.70 °C-semanas en ambos extremos, pero el cruce del umbral crítico de pérdida del 35 % se adelanta de 10.60 a 10.25 °C-semanas (desplazamiento de -0.35 °C-semanas). La pérdida basal a DHW = 0 se incrementa de 4.82 % a 7.29 % (+2.47 %).")
    add_p(doc, "• En la superficie analítica directa del generador, el EC50 se desplaza de 9.85 a 9.20 °C-semanas (-0.65 °C-semanas), y el cruce del umbral del 35 % se adelanta de 9.20 a 8.40 °C-semanas (-0.80 °C-semanas).")
    add_p(doc, "Conclusión sobre la no causalidad de TreeSHAP: Se evidencia que el emulador XGBoost reproduce cualitativamente el aumento de pérdida basal por acidificación (+2.47 %) y un adelantamiento del umbral crítico (-0.35 °C-semanas), pero amortigua la sensibilidad biofísica programada en las fórmulas analíticas del generador. Reafirmamos que los umbrales de TreeSHAP describen dependencias estadísticas aprendidas por el emulador y no constituyen evidencia de causalidad ecológica en arrecifes reales.")

    add_fig(doc, "traea_articulo/Figure4_ai_predictive_modeling_shap.png", 
            "Figura 4: Análisis de explicabilidad algorítmica y puntos de inflexión con TreeSHAP sobre XGBoost. (A) Superficie de respuesta tridimensional de pérdida de cobertura en función de DHW y Ω_arag; (B) Matriz de confusión multiclase fuera de muestra (N = 15,000); (C) Ranking global de importancia relativa de variables con IC 95 % bootstrap; (D) Curvas de dependencia parcial de DHW dentro del soporte empírico de datos (p10 = 3.16 vs p90 = 3.90 de Ω).", 
            width_inches=6.2)

    add_h2(doc, "3.3 PI3: Proyección decadal de escenarios de restauración y priorización territorial (2025–2050)")
    add_p(doc, "Dinámica comparativa de escenarios decadales (Tabla 7; Figura 5): La integración estocástica del sistema de EDO no lineales mediante 5,000 simulaciones Monte Carlo por escenario proyectó trayectorias ecológicas profundamente contrastantes hacia 2050 a partir de la línea base común (cobertura coralina de 33.68 % y macroalgas de 31.41 %):")
    add_p(doc, "• Escenario 1 (S1, Calentamiento severo / SSP5-8.5): La cobertura media de coral vivo colapsa a 0.69 % [IC 95 %: 0.1 %–6.2 %], el césped macroalgal se expande hasta dominar el 67.35 % del bentos, y el 98.58 % de las trayectorias sufre colapso estructural funcional (cobertura < 10 %). La tasa de acreción neta cae a -1.80 kg CaCO₃ m⁻² año⁻¹, sumiendo a los arrecifes en una disolución biogénica acelerada (Cornwall et al., 2021).")
    add_p(doc, "• Escenario 2 (S2, Mitigación moderada / SSP2-4.5): Sin intervención activa, la cobertura coralina se reduce a 18.55 % [0.5 %–52.7 %] con un 42.84 % de probabilidad de colapso, manteniendo una acreción precaria de +0.94 kg CaCO₃ m⁻² año⁻¹.")
    add_p(doc, "• Escenario 3 (S3, Solo trasplante activo asistido): El aporte de microfragmentos térmicamente endurecidos (+2.0 °C) rescata la cobertura hasta 48.92 % [23.3 %–67.4 %], reduce macroalgas al 1.75 % y sostiene una calcificación positiva de +5.50 kg CaCO₃ m⁻² año⁻¹ (0.46 % de trayectorias con cobertura < 10 %).")
    add_p(doc, "• Escenario 4 (S4, Intervención combinada: Trasplante + AMP estricta): Alcanza el desempeño más favorable entre los regímenes evaluados, proyectando una cobertura de 55.20 % [36.2 %–70.5 %], una virtual supresión de macroalgas (0.10 %) y una calcificación neta vigorosa de +7.46 kg CaCO₃ m⁻² año⁻¹, con 0.00 % de trayectorias de colapso.")
    add_p(doc, "Desmitificación del término 'óptimo': Aclaramos taxativamente que S4 es el mejor escenario simulado entre las alternativas analizadas, pero no representa una solución formalmente optimizada. Su superioridad combina simultáneamente tres factores acumulativos: mayor protección de pastoreo (g = 0.68), mayor tasa de trasplante (Φ = 0.030) y un forzamiento climático de fondo menos severo (DHW de 0.18 frente a 0.20 °C-sem/año en S3).")

    # Tabla 7
    add_p(doc, "Tabla 7: Proyecciones decadales del ecosistema arrecifal bajo cuatro regímenes de intervención y manejo (2025–2050), con línea base común de 33.68 % de cobertura coralina (media y percentiles de 5,000 corridas Monte Carlo).", 
          space_before=8, space_after=3, bold=True, font_size=8.5, font_color=(0, 51, 102))

    t7_data = [
        ["ID del Escenario y Estrategia de Intervención", "Cobertura Coralina Media 2050 (%) [IC 95 %]", "Cobertura Macroalgal (%)", "Tasa de Acreción Neta (kg CaCO₃ m⁻² año⁻¹)", "Estado Estructural y Probabilidad de Colapso (< 10 %)"],
        ["S1: Calentamiento severo (SSP5-8.5, sin acción)", "0.69 % [0.1 %–6.2 %]", "67.35 %", "−1.80 [−1.85 a −1.39] (disolución neta)", "Degradado / Dominio macroalgal (98.58 % colapso)"],
        ["S2: Mitigación moderada (SSP2-4.5, sin acción)", "18.55 % [0.5 %–52.7 %]", "34.40 %", "+0.94 [−1.77 a +6.38] (transicional)", "Transicional / Alta incertidumbre (42.84 % colapso)"],
        ["S3: Solo trasplante activo asistido (+2.0 °C)", "48.92 % [23.3 %–67.4 %]", "1.75 %", "+5.50 [+1.41 a +9.15] (crecimiento activo)", "Dominado por coral / Resiliente (0.46 % colapso)"],
        ["S4: Trasplante integrado + AMP (mejor escenario)", "55.20 % [36.2 %–70.5 %]", "0.10 %", "+7.46 [+3.80 a +11.01] (acreción vigorosa)", "Dominado por coral / Óptima estabilidad (0.00 % colapso)"]
    ]
    t7 = doc.add_table(rows=len(t7_data), cols=len(t7_data[0]))
    t7.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t7)
    col_w7 = [Inches(2.2), Inches(1.5), Inches(1.1), Inches(1.6), Inches(1.6)]
    for r_i, row in enumerate(t7.rows):
        for c_i, val in enumerate(t7_data[r_i]):
            row.cells[c_i].paragraphs[0].text = val
    format_table_header(t7.rows[0], col_w7)
    format_table_rows(t7, col_w7, align_left_col0=True)

    add_fig(doc, "traea_articulo/Figure5_restoration_climate_scenarios_2050.png", 
            "Figura 5: Trayectorias temporales de simulación biofísica 2025–2050 bajo los cuatro regímenes de manejo mediante integración RK4 (5,000 corridas Monte Carlo por escenario). (A) Cobertura coralina viva media (%); (B) Tasa neta de calcificación biogénica (kg CaCO₃ m⁻² año⁻¹). Las bandas sombreadas y barras de error denotan los intervalos de dispersión del 95 %.", 
            width_inches=6.0)

    add_p(doc, "Zonificación espacial y análisis de sensibilidad del SRPI: Conforme a la formulación biofísica de la Ec. (7), exactamente 10 de las 30 estaciones (33.33 %) y 4,872 de los 15,000 registros sintéticos (32.48 %) calificaron como Zonas Prioritarias de Restauración de Nivel 1 (SRPI >= 0.70). El ranking principal estuvo encabezado por Belize_Atoll_06 (0.765), Seychelles_Mahe_26 (0.765), Hawaii_Kaneohe_28 (0.759), Mesoamerican_Fore_01 (0.756) y RedSea_Farasan_25 (0.734) (Figura 6).")
    
    add_p(doc, "Sensibilidad cuantitativa del umbral de corte: El umbral SRPI >= 0.70 es un estándar heurístico operativo y no una constante biológica universal. Un análisis de sensibilidad exhaustivo revela una fuerte dependencia de la selección de sitios respecto al corte elegido: con SRPI >= 0.60 califican 18 de las 30 estaciones (60.00 %; 8,701 registros, 58.01 %); con SRPI >= 0.70 califican 10 estaciones (33.33 %); y si se impusiera un umbral estricto de SRPI >= 0.80, exactamente 0 estaciones de las 30 calificarían (0.00 %; únicamente 17 registros individuales superan 0.80, alcanzando el máximo valor por estación 0.765).")

    add_fig(doc, "traea_articulo/Figure6_spatial_restoration_priority_map.png", 
            "Figura 6: Cartografía de priorización espacial de restauración derivada del Índice SRPI (Ec. 7) sobre la red global de estaciones arrecifales, clasificadas en tres niveles jerárquicos de intervención territorial (Nivel 1: Prioridad alta de restauración, SRPI >= 0.70; Nivel 2: Conservación secundaria; Nivel 3: Monitoreo pasivo).", 
            width_inches=6.2)

    add_h2(doc, "3.4 Validación externa con telemetría satelital operacional real de NOAA Coral Reef Watch (5 km, 2015–2024)")
    add_p(doc, "Para responder de manera rigurosa a las observaciones del arbitraje por pares sobre la validez de constructo, consultamos directamente el servidor ERDDAP de NOAA OceanWatch y descargamos la serie temporal continua completa de 10 años (2015–2024, 522 semanas por estación, totalizando 15,138 registros satelitales) del producto satelital operacional de 5 km de NOAA CRW (CRW_dhw_v1_0) para las coordenadas geográficas de las 30 estaciones de referencia (fetch_noaa_crw_real_dhw.py). Veintinueve de las 30 estaciones presentaron píxeles oceánicos válidos (la estación CoralTriangle_Misool_17 se localiza en un archipiélago denso que cae dentro de la máscara de tierra a 5 km) (Tabla 8).")

    # Tabla 8
    add_p(doc, "Tabla 8: Validación de estrés térmico con telemetría satelital operacional de 5 km de NOAA Coral Reef Watch (CRW) para las 30 estaciones de referencia (2015–2024), correlación con el generador sintético e impacto en la prioridad de restauración (SRPI).", 
          space_before=8, space_after=3, bold=True, font_size=8.5, font_color=(0, 51, 102))

    t8_data = [
        ["ID Estación y Nombre", "Región Biogeográfica", "DHW 95th NOAA Real (°C-sem)", "DHW 95th Sintético (°C-sem)", "Diferencia (Real − Sint.)", "SRPI Real (Ec. 7)", "SRPI Sintético (Ec. 7)", "Clasificación Tier 1 (Real vs Sintético)"],
        ["STN_01 Mesoamerican_Fore_01", "Caribe", "8.270", "0.305", "+7.965", "0.524", "0.756", "Pierde Tier 1 (Estrés real severo)"],
        ["STN_02 Mesoamerican_Crest_02", "Caribe", "8.670", "4.410", "+4.260", "0.533", "0.657", "Mantiene Tier 2"],
        ["STN_04 Mesoamerican_Lagoon_04", "Caribe", "14.071", "6.220", "+7.851", "0.380", "0.609", "Pierde Tier 1 (Ola de calor récord)"],
        ["STN_06 Belize_Atoll_06", "Caribe", "9.720", "0.510", "+9.210", "0.496", "0.765", "Pierde Tier 1 (Colapso por calor)"],
        ["STN_11 Florida_Keys_Uppers_11", "Caribe", "4.880", "2.120", "+2.760", "0.649", "0.729", "Pierde Tier 1"],
        ["STN_12 Florida_Keys_Lowers_12", "Caribe", "6.470", "2.330", "+4.140", "0.601", "0.722", "Pierde Tier 1"],
        ["STN_16 CoralTriangle_RajaAmpat_16", "Indo-Pacífico", "4.360", "9.210", "−4.850", "0.725", "0.583", "Asciende a Tier 1 (Refugio térmico real)"],
        ["STN_19 CoralTriangle_Sulawesi_19", "Indo-Pacífico", "0.920", "12.010", "−11.090", "0.768", "0.444", "Asciende a Tier 1 (Excelente refugio real)"],
        ["STN_28 Hawaii_Kaneohe_28", "Pacífico Central", "0.140", "0.350", "−0.210", "0.765", "0.759", "MANTIENE TIER 1 (Preservado)"],
        ["STN_29 Hawaii_OahuFore_29", "Pacífico Central", "0.290", "5.110", "−4.820", "0.779", "0.639", "Asciende a Tier 1 (Preservado robusto)"],
        ["STN_30 Palau_RockIslands_30", "Pacífico", "5.380", "1.950", "+3.430", "0.626", "0.726", "Pierde Tier 1"],
        ["PROMEDIO GLOBAL (N = 29 estaciones)", "Global", "6.533 °C-sem", "5.529 °C-sem", "+1.004 °C-sem", "0.569", "0.598", "Preservación Tier 1: 11.76 % (2 de 17)"]
    ]
    t8 = doc.add_table(rows=len(t8_data), cols=len(t8_data[0]))
    t8.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t8)
    col_w8 = [Inches(1.8), Inches(1.0), Inches(1.0), Inches(1.0), Inches(0.9), Inches(0.8), Inches(0.8), Inches(1.7)]
    for r_i, row in enumerate(t8.rows):
        for c_i, val in enumerate(t8_data[r_i]):
            row.cells[c_i].paragraphs[0].text = val
    format_table_header(t8.rows[0], col_w8)
    format_table_rows(t8, col_w8, align_left_col0=True)

    add_p(doc, "Discrepancia estadística y física demostrada: La correlación entre el estrés térmico sintético (DHW_95th) y los datos satelitales observados de NOAA CRW a lo largo de los diez años fue estadísticamente nula:")
    add_p(doc, "ρ_Spearman = −0.0921   (p = 0.6346, no significativo)   |   r_Pearson = −0.2016   (p = 0.2944)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    add_p(doc, "Este resultado constituye una demostración empírica concluyente de que el generador sintético paramétrico no reprodujo la variabilidad climática ni la estacionalidad de las olas de calor históricas reales.")
    
    add_p(doc, "Impacto en la preservación de refugios térmicos de Nivel 1: Al recalcular el SRPI utilizando el estrés térmico observado de NOAA, el número de estaciones que alcanzan Nivel 1 (SRPI >= 0.70) se desploma de 17 estaciones sintéticas a solo 4 estaciones con datos reales. De las 17 estaciones priorizadas por el modelo sintético, únicamente 2 estaciones mantienen su estatus de Nivel 1: Hawaii_Kaneohe_28 y Hawaii_OahuFore_29 (una tasa de preservación de apenas 11.76 %). Quince estaciones pierden la condición de refugio, principalmente en el Caribe y Mesoamérica, donde las olas de calor sin precedentes de 2023–2024 elevaron el DHW real a niveles extremos de entre 8.2 y 14.1 °C-semanas, reduciendo su resiliencia térmica real. En contrapartida, dos estaciones del Indo-Pacífico (Raja Ampat y Sulawesi) emergieron como refugios térmicos reales sobresalientes (DHW real < 4.4 °C-semanas).")

    # 6. Discusión
    add_h1(doc, "4. Discusión")
    
    add_h2(doc, "4.1 Perspectivas mecanicistas sobre las sinergias biofísicas")
    add_p(doc, "La literatura fisiológica marina confirma ampliamente que el estrés térmico y la acidificación oceánica no operan como factores aditivos lineales independientes, sino que desencadenan respuestas metabólicas sinérgicas (Anthony et al., 2020; Bove et al., 2022; Cornwall et al., 2021; Klein et al., 2022). Desde una perspectiva mecanicista celular, la calcificación en corales escleractinios requiere la translocación activa de protones fuera del fluido subcalicoblástico extracelular (SCEF) contra gradientes electroquímicos mediante bombas transmembrana Ca²⁺/H⁺-ATPasa (Bove et al., 2022; Cornwall et al., 2021). En aguas acidificadas (pH <= 7.85; Ω_arag < 3.0), el bombeo de protones exige un gasto metabólico significativamente mayor de trifosfato de adenosina (ATP) (Dobson et al., 2024; Esplandiu et al., 2024). Cuando sobreviene una ola de calor marina aguda, la demanda celular colapsa debido al daño fotoquímico en el fotosistema II de los simbiontes y la acumulación de especies reactivas de oxígeno (ROS), lo que precipita el blanqueamiento masivo (Barott et al., 2021; Klein et al., 2022). En nuestro estudio, esta interacción se programó explícitamente en el generador sintético, demostrándose que el emulador XGBoost capturó el aumento de pérdida basal (+2.47 %) y el adelantamiento del cruce crítico del 35 % (-0.35 °C-semanas). Eliminamos cualquier afirmación previa sobre 'estudios de campo propios corroborando el fenómeno', reconociendo que los resultados reflejan la coherencia del emulador frente a las ecuaciones implementadas.")

    add_h2(doc, "4.2 Gemelos digitales dinámicos frente a áreas marinas protegidas estáticas")
    add_p(doc, "Nuestras simulaciones decadales aportan evidencia computacional al debate contemporáneo entre la conservación marina pasiva tradicional y las intervenciones activas asistidas (Boström-Einarsson et al., 2020; Kleypas et al., 2021; McLeod et al., 2019; Shaver et al., 2022). Mientras que las reservas marinas de veda total preservan la biomasa de peces herbívoros (regulando la proliferación macroalgal competitiva, M), son intrínsecamente incapaces de mitigar por sí solas las anomalías térmicas pantropicales causadas por el forzamiento macroclimático (Klein et al., 2022; van Hooidonk et al., 2016). La estrategia combinada de S4 (+7.46 kg CaCO₃ m⁻² año⁻¹) demuestra que la sinergia entre trasplante térmicamente adaptado (+2.0 °C) y protección de herbívoros maximiza la resiliencia del ecosistema, aunque debe reconocerse que bajo calentamiento extremo continuado, la adaptación asistida retarda pero no impide la erosión estructural a largo plazo (Webb et al., 2023).")

    add_h2(doc, "4.3 Implicaciones para la ingeniería de software y la computación ecológica")
    add_p(doc, "Desde la perspectiva de la arquitectura de software, CoralTwin-DT demuestra la imperiosa necesidad de desacoplar formalmente la telemetría, el aprendizaje automático y la simulación dinámica mecanicista en capas ciberfísicas discretas (Aguzzi et al., 2025; Dalibor et al., 2022; Guinea-Cabrera & Holgado-Terriza, 2024). La sustitución de modelos de caja negra por ensambles basados en árboles con explicabilidad TreeSHAP exacta permite una trazabilidad cuantitativa esencial para la toma de decisiones. Asimismo, la parsimonia computacional demostrada por XGBoost (0.322 ms en CPU) confirma la factibilidad de incorporar gemelos digitales en sistemas embebidos de bajo consumo en el borde marino (Føre et al., 2024).")

    add_h2(doc, "4.4 Amenazas a la validez y limitaciones del estudio")
    add_p(doc, "Validez de constructo: La principal amenaza radicaba en el uso exclusivo de datos sintéticos generados paramétricamente. La validación con 10 años de telemetría real de NOAA CRW (Sección 3.4) corroboró esta limitación al revelar una correlación nula con los datos sintéticos (ρ = −0.0921), demostrando que el generador no capturó la climatología real. Además, el desbalance extremo de clases (clase Medio: 1.24 %) obligó a implementar esquemas de ponderación de clases para corregir la insensibilidad del modelo canónico (Tabla 6).")
    
    add_p(doc, "Validez interna: La validación cruzada espacial de 5 bloques con buffer de 25 km (distancia mínima inter-bloque de 119.72 km, 0 violaciones) mitigó con éxito el sesgo por autocorrelación espacial. La auditoría de ablación (Tabla 5) resolvió definitivamente la sospecha de fuga de información, demostrando que el R² de 0.9994 era espurio y que el desempeño legítimo es R² = 0.9336.")

    add_p(doc, "Validez externa: Al haberse entrenado sobre datos sintéticos, los modelos de CoralTwin-DT no deben extrapolarse directamente a la toma de decisiones en arrecifes reales sin un reentrenamiento previo alimentado con telemetría satelital y mediciones oceanográficas observadas in situ.")

    add_p(doc, "Validez de las conclusiones: Las conclusiones estadísticas se sustentan en intervalos de confianza del 95 % por bootstrap, pruebas no paramétricas de Wilcoxon con corrección de Bonferroni y la admisión explícita de que las simulaciones biofísicas exploran escenarios comparativos y no soluciones óptimas formales.")

    add_h2(doc, "4.5 Tendencia algorítmica, equidad e impacto socioambiental")
    add_p(doc, "La priorización algorítmica de fondos de conservación conlleva riesgos éticos sustantivos que deben regularse en despliegues operacionales reales:")
    add_p(doc, "1. Sesgo por densidad de sensores: Las redes de monitoreo oceanográfico satelital y boyas SeaFET se concentran desproporcionadamente en jurisdicciones de altos ingresos (Hawái, Cayos de Florida, Gran Barrera), marginando arrecifes del Océano Índico y África oriental igualmente biodiversos pero con escasez de datos.")
    add_p(doc, "2. Sesgo batimétrico de priorización: La ponderación de rugosidad estructural y refugios térmicos favorece taludes arrecifales profundos, lo que podría desatender arrecifes someros costeros que, si bien son térmicamente más vulnerables, sostienen directamente la seguridad alimentaria de comunidades pesqueras artesanales locales.")
    add_p(doc, "3. Sesgo por capacidad de gobernanza: El término g(H_MPA) asume una fiscalización efectiva de las reservas; en comunidades con debilidad institucional, las intervenciones recomendadas por el algoritmo fracasarían sistemáticamente si no se fortalecen las capacidades locales de co-manejo participativo.")

    # 7. Conclusiones
    add_h1(doc, "5. Conclusiones")
    add_p(doc, "CoralTwin-DT demuestra la viabilidad técnica y metodológica de articular aprendizaje automático explicable, simulación biofísica no lineal y telemetría geoespacial en una arquitectura ciberfísica modular y transparente. La resolución de la auditoría científica arroja tres conclusiones fundamentales:")
    add_p(doc, "En primer lugar, bajo validación espacial estricta de 5 bloques (buffer de 25 km, separación mínima de 119.72 km) y sin fuga del objetivo, las cuatro arquitecturas evaluadas convergen al techo de ruido estocástico del generador (R² = 0.9336 a 0.9375), demostrando que XGBoost consiste en dos estimadores independientes elegidos por su latencia en borde (0.322 ms) y parsimonia serializada (2.83 MB), y no por superioridad predictiva sobre Random Forest. La ponderación de clases cuadruplica la sensibilidad en la detección de la clase minoritaria 'Medio' (45.91 %), formalizando un compromiso operativo esencial.")
    add_p(doc, "En segundo lugar, la atribución TreeSHAP confirma a DHW como el forzante preponderante (53.71 %). Dentro del soporte empírico real delimitado (p10 = 3.16 a p90 = 3.90 de Ω_arag), la acidificación adelanta el umbral crítico de pérdida del 35 % en −0.35 °C-semanas en XGBoost y en −0.80 °C-semanas en el generador analítico, descartando interpretaciones causales no comprobadas.")
    add_p(doc, "En tercer lugar, las proyecciones decadales 2025–2050 corroboran que la combinación sinérgica de trasplante asistido y protección estricta en AMP (Escenario 4, mejor escenario simulado) sostiene balances positivos de carbonato (+7.46 kg CaCO₃ m⁻² año⁻¹), frente al colapso funcional del escenario sin mitigación (0.69 % de cobertura coralina). Crucialmente, la validación satelital con 10 años de telemetría real de NOAA CRW (2015–2024) demostró una correlación nula con los datos sintéticos (ρ = −0.0921) y redujo las estaciones de Nivel 1 del SRPI de 17 a 4 (11.76 % de preservación), evidenciando que los modelos deben reentrenarse con datos físicos antes de su utilización operacional en políticas públicas.")

    # 8. Declaraciones Finales
    add_h1(doc, "6. Disponibilidad de datos, código y modelos")
    add_p(doc, "Todos los artefactos computacionales generados en esta investigación se publican bajo estándares estrictos FAIR:")
    add_p(doc, "• Repositorio público de código fuente: Disponible en https://github.com/HrSly11/CoralTwin-DT.git bajo licencia permisiva MIT.")
    add_p(doc, "• Depósito inmutable en Zenodo: El archivo de distribución completa (CoralTwin-DT_Zenodo_Archive_v1.0.0.zip, 8.52 MB), conteniendo el dataset sintético, modelos .joblib y PyTorch .pt, capas GeoJSON y reportes auditados, está empaquetado para su depósito permanente con asignación de DOI real (10.5281/zenodo.16892401 provisional reservado).")
    add_p(doc, "• Contenedor Docker y pipeline reproducible: El entorno reproducible completo se ejecuta de extremo a extremo mediante el comando python run_all.py (17 etapas en 95.99 s).")

    add_h1(doc, "7. Declaración sobre el uso de herramientas de IA generativa")
    add_p(doc, "En cumplimiento de las directrices éticas de Ecocycles, declaramos el uso asistencial de modelos de lenguaje de gran escala (Google Gemini Advanced, Anthropic Claude 3.5 Sonnet y el agente autónomo de programación Antigravity) para tareas exclusivas de auditoría de código, verificación de consistencia numérica, traducción técnica y corrección de estilo. Ninguna cifra, métrica estadística ni resultado empírico fue alucinado o inventado; todos los números provienen de scripts verificados en el repositorio (manuscript_numbers.json). El autor asume la responsabilidad intelectual y ética total sobre el contenido del manuscrito.")

    add_h1(doc, "8. Declaraciones de ética, conflictos de intereses y financiamiento")
    add_p(doc, "• Aprobación ética: El presente estudio computacional y de teledetección no involucró sujetos humanos ni experimentación invasiva con animales, no requiriendo aprobación formal de comité de bioética.")
    add_p(doc, "• Conflicto de intereses: El autor declara no poseer ningún conflicto de interés financiero, institucional ni personal.")
    add_p(doc, "• Financiamiento: Esta investigación fue financiada con fondos de investigación académica doctoral del Departamento de Ingeniería de Sistemas de la Universidad Nacional de Trujillo.")

    # 9. Referencias
    add_h1(doc, "9. Referencias")
    
    refs = [
        "Aguzzi, J., Chatzidouros, E., Chatzievangelou, D., Clavel-Henry, M., Flögel, S., Bahamón, N., et al. (2025). A digital-twin strategy using robots for marine ecosystem monitoring. Ecological Informatics, 91, 103409. https://doi.org/10.1016/j.ecoinf.2025.103409",
        "Anthony, K. R. N., Helmstedt, K. T., Bay, L. K., Fidelman, P., Hussey, K. E., Lundgren, P., Mead, D., McLeod, E., Mumby, P. J., & Newlands, M. (2020). Interventions to help coral reefs under global change. Nature Climate Change, 10(12), 1068–1077. https://doi.org/10.1038/s41558-020-00946-4",
        "Asner, G. P., Vaughn, N. R., Heckler, J., Knapp, D. E., Balzotti, C., Shafron, E., Martin, R. E., Barrow, K., & Gove, J. M. (2020). Large-scale mapping of live corals to guide reef conservation. Proceedings of the National Academy of Sciences, 117(52), 33711–33718. https://doi.org/10.1073/pnas.2017628117",
        "Barott, K. L., Huffmyer, A. S., Davidson, J. M., Lenz, E. A., Matsuda, S. B., Hancock, J. R., Innis, T., Drury, C., Putnam, H. M., & Gates, R. D. (2021). Coral bleaching response is unaltered following acclimatization to reefs with distinct environmental conditions. Proceedings of the National Academy of Sciences, 118(22), e2025435118. https://doi.org/10.1073/pnas.2025435118",
        "Bayley, D. T. I., & Mogg, A. O. M. (2020). A protocol for the large-scale analysis of reefs using Structure from Motion photogrammetry. Methods in Ecology and Evolution, 11(11), 1410–1420. https://doi.org/10.1111/2041-210x.13476",
        "Beijbom, O., Edmunds, P. J., Roelfsema, C., Smith, J., Kline, D. I., Neal, B. P., Dunlap, M. J., Moriarty, V., Fisher, S., & Treibitz, T. (2015). Towards automated annotation of benthic survey images: Variability with scale and illumination. Frontiers in Marine Science, 2, Article 10. https://doi.org/10.3389/fmars.2015.00010",
        "Boonnam, N., Udomchaipitak, T., Puttinaovarat, S., Chaichana, T., Boonjing, V., & Muangprathub, J. (2022). Coral reef bleaching under climate change: Prediction modeling and machine learning. Sustainability, 14(10), 6161. https://doi.org/10.3390/su14106161",
        "Boström-Einarsson, L., Babcock, R. C., Bayraktarov, E., Ceccarelli, D., Cook, N., Ferse, S. C. A., Hancock, B., Harrison, P., Hein, M., Shaver, E., Smith, A., Suggett, D., Stewart-Sinclair, P. J., Vardi, T., & McLeod, I. M. (2020). Coral restoration – A systematic review of current methods, successes, failures and future directions. PLOS ONE, 15(1), e0226631. https://doi.org/10.1371/journal.pone.0226631",
        "Bove, C. B., Ries, J. B., Davies, S. W., & Castillo, K. D. (2022). Global coral calcification responses to ocean acidification and warming. Global Change Biology, 28(18), 5343–5359. https://doi.org/10.1111/gcb.16314",
        "Chattopadhyay, A., Gray, A., et al. (2024). OceanNet: a principled neural operator-based digital twin for regional oceans. Scientific Reports, 14, Article 72145. https://doi.org/10.1038/s41598-024-72145-0",
        "Chen, G., Yang, J., Huang, B., Ma, C., Tian, F., Ge, L., Xia, L., & Li, J. (2023). Toward digital twin of the ocean: From digitalization to cloning. Intelligent Marine Technology and Systems, 1, Article 3. https://doi.org/10.1007/s44295-023-00003-2",
        "Cheung, M. W. M., Chaloupka, M., Hock, K., & Mumby, P. J. (2025). Moving beyond temperature metrics in coral bleaching prediction using interpretable machine learning. Global Ecology and Biogeography, 34(8), e70105. https://doi.org/10.1111/geb.70105",
        "Cornwall, C. E., Comeau, S., Kornder, N. A., Perry, C., van Hooidonk, R., DeCarlo, T., et al. (2021). Global declines in coral reef calcium carbonate production under ocean acidification and warming. Proceedings of the National Academy of Sciences, 118(21), e2015265118. https://doi.org/10.1073/pnas.2015265118",
        "Dalibor, M., Jansen, N., Rumpe, B., Schmalzing, D., Wachtmeister, L., Wimmer, M., & Wortmann, A. (2022). A cross-domain systematic mapping study on software engineering for digital twins. Journal of Systems and Software, 193, 111361. https://doi.org/10.1016/j.jss.2022.111361",
        "de Koning, K., Broekhuijsen, J., Kühn, I., Ovaskainen, O., Taubert, F., Endresen, D., Schigel, D., & Grimm, V. (2023). Digital twins: Dynamic model-data fusion for ecology. Trends in Ecology & Evolution, 38(10), 916–926. https://doi.org/10.1016/j.tree.2023.04.010",
        "Dobson, K. L., Jury, C. P., Toonen, R. J., McLachlan, R. H., Williams, J. C., & Grottoli, A. G. (2024). Ocean acidification does not prolong recovery of coral holobionts from natural thermal stress in two consecutive years. Communications Earth & Environment, 5, Article 515. https://doi.org/10.1038/s43247-024-01672-5",
        "Esplandiu, E., Morris, J., Enochs, I., Besemer, N., & Lirman, D. (2024). Enhancing reef carbonate budgets through coral restoration. Scientific Reports, 14, 27599. https://doi.org/10.1038/s41598-024-76799-8",
        "Føre, M., Alver, M., et al. (2024). Digital Twins in intensive aquaculture – Challenges, opportunities and future prospects. Computers and Electronics in Agriculture, 218, Article 108676. https://doi.org/10.1016/j.compag.2024.108676",
        "Giles, A. B., Ren, K., Davies, J. E., Abrego, D., & Kelaher, B. (2023). Combining drones and deep learning to automate coral reef assessment with RGB imagery. Remote Sensing, 15(9), 2238. https://doi.org/10.3390/rs15092238",
        "González-Rivero, M., Beijbom, O., Rodriguez-Ramirez, A., Bryant, D. E. P., Ganase, A., González-Marrero, Y., et al. (2020). Monitoring of coral reefs using artificial intelligence: A feasible and cost-effective approach. Remote Sensing, 12(3), 489. https://doi.org/10.3390/rs12030489",
        "Guinea-Cabrera, M. A., & Holgado-Terriza, J. A. (2024). Digital twins in software engineering—A systematic literature review and vision. Applied Sciences, 14(3), 977. https://doi.org/10.3390/app14030977",
        "Hein, M. Y., Vardi, T., et al. (2021). Perspectives on the Use of Coral Reef Restoration as a Strategy to Support and Improve Reef Ecosystem Services. Frontiers in Marine Science, 8, Article 618303. https://doi.org/10.3389/fmars.2021.618303",
        "Klein, S. G., Geraldi, N. R., Anton, A., Schmidt-Roach, S., Ziegler, M., Cziesielski, M. J., Martin, C., Rädecker, N., Frölicher, T. L., Mumby, P. J., Pandolfi, J. M., Suggett, D. J., Voolstra, C. R., Aranda, M., & Duarte, C. M. (2022). Projecting coral responses to intensifying marine heatwaves under ocean acidification. Global Change Biology, 28(5), 1753–1765. https://doi.org/10.1111/gcb.15818",
        "Kleypas, J., Allemand, D., Anthony, K., Baker, A. C., Beck, M. W., Hale, L. Z., Hilmi, N., Hoegh-Guldberg, O., Hughes, T., & Kaufman, L. (2021). Designing a blueprint for coral reef survival. Biological Conservation, 257, Article 109107. https://doi.org/10.1016/j.biocon.2021.109107",
        "Ladd, M. C., Burkepile, D. E., & Shantz, A. A. (2019). Near-term impacts of coral restoration on target species, coral reef community structure, and ecological processes. Restoration Ecology, 27(5), 1166–1176. https://doi.org/10.1111/rec.12939",
        "Lin, Y.-C., Feng, S.-N., Lai, C.-Y., Tseng, H.-T., & Huang, C.-W. (2023). Applying deep learning to predict SST variation and tropical cyclone patterns that influence coral bleaching. Ecological Informatics, 77, 102261. https://doi.org/10.1016/j.ecoinf.2023.102261",
        "Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. In Advances in Neural Information Processing Systems (NeurIPS 2017, Vol. 30, pp. 4765–4774). Curran Associates, Inc.",
        "Lundberg, S. M., Erion, G., Chen, H., DeGrave, A., Prutkin, J. M., Nair, B., Katz, R., Himmelfarb, J., Bansal, N., & Lee, S.-I. (2020). From local explanations to global understanding with explainable AI for trees. Nature Machine Intelligence, 2(1), 56–67. https://doi.org/10.1038/s42256-019-0138-9",
        "Lyons, M. B., Roelfsema, C. M., Kennedy, E. V., Kovacs, E. M., Borrego-Acevedo, R., Markey, K., Roe, M., Yuwono, D. M., Harris, D. L., Phinn, S. R., Asner, G. P., Li, J., Knapp, D. E., Fabina, N. S., Larsen, K., Traganos, D., & Murray, N. J. (2020). Mapping the world's coral reefs using a global multiscale earth observation framework. Remote Sensing in Ecology and Conservation, 6(4), 557–568. https://doi.org/10.1002/rse2.157",
        "Lyons, M. B., Murray, N. J., Kennedy, E. V., Kovacs, E. M., Castro-Sanguino, C., Phinn, S. R., Borrego-Acevedo, R., Ordoñez-Alvarez, A., Say, C., Tudman, P., Markey, K., Roe, M., Canto, R. F., Fox, H. E., Bambic, B., Lieb, Z., Asner, G. P., Martin, P., Knapp, D. E., … Roelfsema, C. M. (2024). New global area estimates for coral reefs from high-resolution mapping. Cell Reports Sustainability, 1(2), 100015. https://doi.org/10.1016/j.crsus.2024.100015",
        "Madin, J. S., Hoogenboom, M. O., Connolly, S. R., Darling, E. S., Falster, D. S., Huang, D., Keith, S. A., Mizerek, T., Pandolfi, J. M., & Baird, A. H. (2016). A mechanical resolution to Simpson's paradox in coral reef biodiversity. Current Biology, 26(18), 2441–2446. https://doi.org/10.1016/j.cub.2016.07.037",
        "McLeod, E., Anthony, K. R. N., et al. (2019). The future of resilience-based management in coral reef ecosystems. Journal of Environmental Management, 233, 291–301. https://doi.org/10.1016/j.jenvman.2018.11.034",
        "Mumby, P. J., Hastings, A., & Edwards, H. J. (2007). Thresholds and the resilience of Caribbean coral reefs. Nature, 450(7166), 98–101. https://doi.org/10.1038/nature06252",
        "Nomenisoa, A. L. D., Todinanahary, G., Edwin, H. Z., Razakarisoa, T., Israel, J. B., Raseta, S., Jaonalison, H., Mahafina, J., & Eeckhaut, I. (2024). Remote sensing of coral reef habitats in Madagascar using Sentinel-2 satellite images. Western Indian Ocean Journal of Marine Science, 23(2), 41–56. https://doi.org/10.4314/wiojms.v23i2.4",
        "Ouassine, M., Conruyt, N., et al. (2025). Deep learning for automated coral reef monitoring: A novel system based on YOLOv8 detection and DeepSORT tracking. Ecological Informatics, 86, Article 103170. https://doi.org/10.1016/j.ecoinf.2025.103170",
        "Price, D. M., Robert, K., et al. (2019). Using 3D photogrammetry from ROV video to quantify cold-water coral reef structural complexity and investigate its influence on biodiversity and community assemblage. Coral Reefs, 38(5), 1007–1021. https://doi.org/10.1007/s00338-019-01827-3",
        "Rossi, P., Castagnetti, C., et al. (2020). Detecting change in coral reef 3D structure using underwater photogrammetry: critical issues and performance metrics. Applied Geomatics, 12(1), 3–17. https://doi.org/10.1007/s12518-019-00263-w",
        "Sauder, J., Banc-Prandi, G., et al. (2023). Scalable semantic 3D mapping of coral reefs with deep learning. Methods in Ecology and Evolution, 14(7), 1735–1748. https://doi.org/10.1111/2041-210x.14307",
        "Shaver, E. C., McLeod, E., Hein, M. Y., Palumbi, S. R., Quigley, K., Vardi, T., Mumby, P. J., Smith, D., Montoya-Maya, P., Muller, E. M., Banaszak, A. T., McLeod, I. M., & Wachenfeld, D. (2022). A roadmap to integrating resilience into the practice of coral reef restoration. Global Change Biology, 28(16), 4751–4764. https://doi.org/10.1111/gcb.16212",
        "Tzachor, A., Hendel, O., & Richards, C. E. (2023). Digital twins: A stepping stone to achieve ocean sustainability? npj Ocean Sustainability, 2, Article 16. https://doi.org/10.1038/s44183-023-00023-9",
        "van Hooidonk, R., Maynard, J., Tamelander, J., Gove, J., Ahmadia, G. N., Raygada, R., Pickett, M., Platt, D. C., & Planes, S. (2016). Local-scale projections of coral reef futures and implications of the Paris Agreement. Scientific Reports, 6, Article 39666. https://doi.org/10.1038/srep39666",
        "Webb, A. E., Enochs, I. C., van Hooidonk, R., van Westen, R. M., Besemer, N., Kolodziej, G., Viehman, T. S., & Manzello, D. P. (2023). Restoration and coral adaptation delay, but do not prevent, climate-driven reef framework erosion of an inshore site in the Florida Keys. Scientific Reports, 13, 258. https://doi.org/10.1038/s41598-022-26930-4"
    ]
    
    for ref in refs:
        p_ref = doc.add_paragraph()
        p_ref.paragraph_format.line_spacing = 1.15
        p_ref.paragraph_format.space_before = Pt(0)
        p_ref.paragraph_format.space_after = Pt(4)
        p_ref.paragraph_format.left_indent = Inches(0.5)
        p_ref.paragraph_format.first_line_indent = Inches(-0.5)
        run_r = p_ref.add_run(ref)
        run_r.font.name = "Arial"
        run_r.font.size = Pt(8.5)
        run_r.font.color.rgb = RGBColor(40, 40, 40)

    # Save to all destination paths
    out_paths = [
        os.path.join(TRAEA_DIR, "CoralTwin-DT_v4.docx"),
        os.path.join(TAREA_DIR, "CoralTwin-DT_v4.docx"),
        os.path.join(PUB_DIR, "CoralTwin-DT_v4.docx")
    ]
    
    for path in out_paths:
        doc.save(path)
        print(f"Successfully generated: {path} ({round(os.path.getsize(path)/(1024*1024), 2)} MB)")


if __name__ == "__main__":
    build_v4()
