import os
import re
import shutil
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BASE_DIR = Path(r"c:\Users\Harry\Documents\CICLO 8\ING SOFT II\CoralTwin-DT")
MD_PATH = BASE_DIR / "10_Publication" / "final_manuscript" / "manuscript_q1_final.md"
DOCX_PATH = BASE_DIR / "10_Publication" / "final_manuscript" / "manuscript_q1.docx"
PDF_PATH = BASE_DIR / "10_Publication" / "final_manuscript" / "manuscript_q1.pdf"

def clean_latex_math(text):
    replacements = [
        (r'\text{Macro-F1}', 'Macro-F1'),
        (r'\text{RMSE}', 'RMSE'),
        (r'\text{ms/sample}', 'ms/sample'),
        (r'\text{ms}', 'ms'),
        (r'\text{kg CaCO}_3\text{ m}^{-2}\text{ yr}^{-1}', 'kg CaCO₃ m⁻² yr⁻¹'),
        (r'\text{kg CaCO}_3', 'kg CaCO₃'),
        (r'\text{ m}^{-2}\text{ yr}^{-1}', ' m⁻² yr⁻¹'),
        (r'\text{fragments m}^{-2}\text{ yr}^{-1}', 'fragments m⁻² yr⁻¹'),
        (r'\text{yr}^{-1}', 'yr⁻¹'),
        (r'\text{yr}', 'yr'),
        (r'\text{years}', 'years'),
        (r'\text{ m}', ' m'),
        (r'\text{C-weeks}', '°C-weeks'),
        (r'\text{C}', '°C'),
        (r'^\circ\text{C-weeks}', '°C-weeks'),
        (r'^\circ\text{C}', '°C'),
        (r'^\circ', '°'),
        (r'R^2', 'R²'),
        (r'm^{-2}', 'm⁻²'),
        (r'yr^{-1}', 'yr⁻¹'),
        (r'\text{Ca}^{2+}/\text{H}^+\text{-ATPase}', 'Ca²⁺/H⁺-ATPase'),
        (r'\text{Ca}^{2+}', 'Ca²⁺'),
        (r'[\text{Ca}^{2+}]', '[Ca²⁺]'),
        (r'\text{H}^+', 'H⁺'),
        (r'[\text{CO}_3^{2-}]', '[CO₃²⁻]'),
        (r'\text{CO}_3^{2-}', 'CO₃²⁻'),
        (r'\text{-ATPase}', '-ATPase'),
        (r'p\text{CO}_2', 'pCO₂'),
        (r'\Omega_{\text{arag}}', 'Ω_arag'),
        (r'\Omega', 'Ω'),
        (r'K_d(490)', 'Kd(490)'),
        (r'K\'_{\text{sp}}(\text{arag})', 'K\'sp(arag)'),
        (r'\text{HotSpot}', 'HotSpot'),
        (r'\text{ThermRefugia}', 'ThermRefugia'),
        (r'\text{RestoUrgency}', 'RestoUrgency'),
        (r'\text{BenthicRugosity}', 'BenthicRugosity'),
        (r'\text{WaterQuality}', 'WaterQuality'),
        (r'\text{CurrentCover}', 'CurrentCover'),
        (r'\text{HistoricalBaseline}', 'HistoricalBaseline'),
        (r'\text{Rugosity}', 'Rugosity'),
        (r'\text{SRPI}', 'SRPI'),
        (r'\text{MPA}', 'MPA'),
        (r'\text{restoration}', 'restoration'),
        (r'\text{bioerosion}', 'bioerosion'),
        (r'E_{\text{bioerosion}}', 'E_bioerosion'),
        (r'\Phi_{\text{restoration}}', 'Φ_restoration'),
        (r'\Phi', 'Φ'),
        (r'G_{\text{net}}', 'G_net'),
        (r'H_{\text{MPA}}', 'H_MPA'),
        (r'DHW_{95\text{th}}', 'DHW_95th'),
        (r'\mathbb{I}', 'I'),
        (r'\Delta t', 'Δt'),
        (r'\Delta', 'Δ'),
        (r'\approx', '≈'),
        (r'\times', '×'),
        (r'\le', '≤'),
        (r'\ge', '≥'),
        (r'\alpha_{\text{adjusted}}', 'α_adjusted'),
        (r'\alpha', 'α'),
        (r'\beta', 'β'),
        (r'\gamma', 'γ'),
        (r'\eta', 'η'),
        (r'\%', '%'),
        (r'\cdot', '·'),
        (r'\max', 'max'),
        (r'\min', 'min'),
        (r'\exp', 'exp'),
        (r'\sum', '∑'),
        (r'\frac{dC}{dt}', 'dC/dt'),
        (r'\frac{dM}{dt}', 'dM/dt'),
        (r'd_0', 'd₀'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    
    # Generic \text{...}
    text = re.sub(r'\\text\{([^}]+)\}', r'\1', text)
    # Fractions \frac{a}{b} -> (a / b)
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1 / \2)', text)
    # Remove math enclosing $
    text = re.sub(r'\$\$([^$]+)\$\$', r'\1', text)
    text = re.sub(r'\$([^$]+)\$', r'\1', text)
    # Clean remaining single backslashes in math symbols
    text = text.replace('\\', '')
    # Final cleanup of double symbols or leftovers
    text = text.replace('°°C', '°C')
    text = text.replace('CaCO_3', 'CaCO₃')
    text = text.replace('CaCO3', 'CaCO₃')
    text = text.replace('  ', ' ')
    return text

def add_formatted_runs(paragraph, text, default_font="Calibri", default_size=10.5, default_color=None):
    # Split by bold (**...**) and italic (*...*)
    tokens = re.split(r'(\*\*.*?\*\*|\*.*?\*)', text)
    for token in tokens:
        if not token:
            continue
        if token.startswith('**') and token.endswith('**') and len(token) >= 4:
            clean_str = clean_latex_math(token[2:-2])
            run = paragraph.add_run(clean_str)
            run.bold = True
        elif token.startswith('*') and token.endswith('*') and len(token) >= 2:
            clean_str = clean_latex_math(token[1:-1])
            run = paragraph.add_run(clean_str)
            run.italic = True
        else:
            clean_str = clean_latex_math(token)
            run = paragraph.add_run(clean_str)
            
        run.font.name = default_font
        run.font.size = Pt(default_size)
        if default_color:
            run.font.color.rgb = default_color

def set_cell_background(cell, fill_color):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_color)
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def build_clean_docx():
    print(f"Building clean DOCX: {DOCX_PATH}...")
    doc = Document()

    # Set standard margins (1 inch)
    for s in doc.sections:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)

    # Document Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(6)
    run_title = p_title.add_run("CoralTwin-DT: A Cyber-Physical Digital Twin Coupling Machine Learning and Dynamical Biophysics for Coral Reef Restoration Prioritization under Thermal Stress and Ocean Acidification")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(17)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(26, 54, 93)

    # Authors & Target Journal
    p_auth = doc.add_paragraph()
    p_auth.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_auth.paragraph_format.space_after = Pt(14)
    run_auth = p_auth.add_run("CoralTwin-DT Doctoral Research Consortium\nComputational Oceanography & Ecological Informatics Laboratory\nTarget Journal: Ecological Informatics (Elsevier, Scopus Q1) / IEEE Transactions on Cybernetics")
    run_auth.font.name = "Calibri"
    run_auth.font.size = Pt(10)
    run_auth.font.italic = True
    run_auth.font.color.rgb = RGBColor(71, 85, 105)

    with open(MD_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    idx = 0
    in_code_block = False
    
    while idx < len(lines):
        line = lines[idx]
        line_s = line.strip()

        # Handle code blocks / ASCII diagrams
        if line_s.startswith("```"):
            in_code_block = not in_code_block
            idx += 1
            continue

        if in_code_block:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.left_indent = Inches(0.2)
            run = p.add_run(line.rstrip('\n'))
            run.font.name = "Consolas"
            run.font.size = Pt(8.5)
            run.font.color.rgb = RGBColor(30, 41, 59)
            idx += 1
            continue

        if not line_s or line_s == "---":
            idx += 1
            continue

        # Headings
        if line_s.startswith("# "):
            # Already handled title
            idx += 1
            continue
        elif line_s.startswith("## "):
            h_text = clean_latex_math(line_s[3:].strip())
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(h_text)
            run.font.name = "Calibri"
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = RGBColor(43, 108, 176)
            idx += 1
            continue
        elif line_s.startswith("### "):
            h_text = clean_latex_math(line_s[4:].strip())
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(h_text)
            run.font.name = "Calibri"
            run.font.size = Pt(11.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(30, 41, 59)
            idx += 1
            continue
        elif line_s.startswith("#### "):
            h_text = clean_latex_math(line_s[5:].strip())
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(h_text)
            run.font.name = "Calibri"
            run.font.size = Pt(10.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(71, 85, 105)
            idx += 1
            continue

        # Markdown Table Detection
        if line_s.startswith("|"):
            table_lines = []
            while idx < len(lines) and lines[idx].strip().startswith("|"):
                t_line = lines[idx].strip()
                if not re.match(r'^\|[\s\-:]+(\|[\s\-:]+)+\|$', t_line):
                    table_lines.append(t_line)
                idx += 1
                
            if table_lines:
                # Parse cells
                rows_data = []
                for tl in table_lines:
                    cells = [c.strip() for c in tl.split("|")[1:-1]]
                    rows_data.append(cells)
                
                if rows_data:
                    num_rows = len(rows_data)
                    num_cols = max(len(r) for r in rows_data)
                    tbl = doc.add_table(rows=num_rows, cols=num_cols)
                    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                    tbl.autofit = True
                    
                    for r_idx, r_data in enumerate(rows_data):
                        row = tbl.rows[r_idx]
                        is_header = (r_idx == 0)
                        for c_idx in range(min(num_cols, len(r_data))):
                            cell = row.cells[c_idx]
                            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                            set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
                            
                            p_cell = cell.paragraphs[0]
                            p_cell.paragraph_format.space_before = Pt(2)
                            p_cell.paragraph_format.space_after = Pt(2)
                            
                            cell_text = r_data[c_idx]
                            if is_header:
                                set_cell_background(cell, "1A365D")
                                add_formatted_runs(p_cell, cell_text, default_size=9.5, default_color=RGBColor(255, 255, 255))
                                for r in p_cell.runs:
                                    r.bold = True
                            else:
                                if r_idx % 2 == 1:
                                    set_cell_background(cell, "F8FAFC")
                                else:
                                    set_cell_background(cell, "FFFFFF")
                                add_formatted_runs(p_cell, cell_text, default_size=9, default_color=RGBColor(30, 41, 59))
                                
                    p_spacer = doc.add_paragraph()
                    p_spacer.paragraph_format.space_after = Pt(6)
            continue

        # Display Equation ($$ ... $$)
        if line_s.startswith("$$"):
            eq_text = clean_latex_math(line_s)
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(eq_text)
            run.font.name = "Cambria Math"
            run.font.size = Pt(11)
            run.font.italic = True
            run.font.color.rgb = RGBColor(15, 23, 42)
            idx += 1
            continue

        # Bullet lists
        if line_s.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(3)
            add_formatted_runs(p, line_s[2:].strip(), default_font="Calibri", default_size=10.5, default_color=RGBColor(51, 65, 85))
            idx += 1
            continue

        # Numbered lists (e.g. 1. , 2. )
        m_num = re.match(r'^(\d+)\.\s+(.*)', line_s)
        if m_num and not line_s.startswith("1. Introduction"):
            num_prefix = m_num.group(1) + ". "
            rest_text = m_num.group(2)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(3)
            run_num = p.add_run(num_prefix)
            run_num.font.name = "Calibri"
            run_num.font.size = Pt(10.5)
            run_num.bold = True
            run_num.font.color.rgb = RGBColor(30, 41, 59)
            add_formatted_runs(p, rest_text, default_font="Calibri", default_size=10.5, default_color=RGBColor(51, 65, 85))
            idx += 1
            continue

        # Figure/Table captions
        if line_s.startswith("*Figure") or line_s.startswith("*Table"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(8)
            add_formatted_runs(p, line_s, default_font="Calibri", default_size=9.5, default_color=RGBColor(71, 85, 105))
            idx += 1
            continue

        # Regular Paragraph
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.line_spacing = 1.15
        add_formatted_runs(p, line_s, default_font="Calibri", default_size=10.5, default_color=RGBColor(51, 65, 85))
        idx += 1

    doc.save(str(DOCX_PATH))
    print(f"[OK] Clean DOCX successfully created at: {DOCX_PATH}")

    # Copy to all project locations
    targets = [
        Path(r"c:\Users\Harry\Documents\CICLO 8\ING SOFT II\GRUPO28_RodríguezSandoval\ARTICULO_CORALTWIN_Q1.docx"),
        BASE_DIR / "10_Publication" / "Final_Submission" / "manuscript.docx",
        BASE_DIR / "FINAL_DELIVERY_PACKAGE" / "02_Scientific_Manuscript" / "manuscript.docx",
        Path(r"c:\Users\Harry\Documents\CICLO 8\ING SOFT II\PROYECTOS-GEMELOS\CoralTwin-DT\10_Publication\final_manuscript\manuscript_q1.docx")
    ]
    for t in targets:
        if t.parent.exists():
            shutil.copy(DOCX_PATH, t)
            print(f"[OK] Synced to: {t}")

if __name__ == "__main__":
    build_clean_docx()
