"""
09_Results/build_v3_docx.py
===========================
Generates `Grupo28B_RodriguezSandoval_HarrySly_v3.docx` from
`Grupo28B_RodriguezSandoval_HarrySly_corregido_v2.docx` (preserving the original
and v2 files untouched) and writes `Grupo28B_RodriguezSandoval_HarrySly_v3_trackchanges_report.md`.

Implements all reviewer closures across FASE 1 to FASE 6:
  - FASE 1 (FON-01): Station-level NOAA CRW 2015-2024 calibration (train 2015-2020, test 2021-2024),
    metrics (Spearman, Pearson, RMSE, bias, KGE, DHW_95th before/after), and Figure 6b (`fig_noaa_calibration_v3.png`).
  - FASE 2 (FON-04): S4 vs S3 factorial isolation (16 variants, Shapley values, and 2^4 Factorial ANOVA /
    Sobol first-order S1 and total-order ST variance decomposition) in Section 3.3, Section 4.2, Table 7b.
  - FASE 3 (FON-05): Extended SRPI sensitivity (thresholds 0.60-0.80, weights +-20%, synthetic vs NOAA,
    10,000 bootstrap resamples, and leave-one-station-out LOSO jackknife) in Section 3.4, Table 8b,
    plus explicit declaration "SRPI heurístico, no validado en campo, no operacional" in Abstract,
    Discussion, and Conclusions.
  - FASE 4 (FON-06): Mathematical equations (Eq. 2 summation & indicator with units; Eq. 4 definitions of
    12.5, 2.8, 1.2, C(t)/C0, and E_bioerosion = 1.85; Eqs. 5-7 code alignment) + new Symbol & Unit Table (Tabla 1b).
  - FASE 5 (FON-07 & FON-08): Eliminates `[VERIFICAR]` in Section 3.1 (P102), resolves the 16 vs 14
    variables in Section 2.4 (P069) and Tabla 5 (`HotSpot_degC` and `Kd_490_m_inv`), replaces `pantropicales`
    with `tropicales`, and verifies zero occurrences of banned strings.
  - FASE 6: Ensures all tables (2, 5, 7, 7b, 8, 8b, 1b) are self-contained with `keepNext` pagination guards.
"""

import os
import sys
import copy
import json
import io
import re
import zipfile
import pandas as pd
import docx
from PIL import Image, ImageDraw, ImageFont
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"


def mqn(tag):
    return f"{{{M_NS}}}{tag.split(':', 1)[1]}"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
SRC_DOCX = os.path.join(PROJECT_ROOT, "Grupo28B_RodriguezSandoval_HarrySly_corregido_v2.docx")
DST_DOCX = os.path.join(PROJECT_ROOT, "Grupo28B_RodriguezSandoval_HarrySly_v3.docx")
TRACK_MD = os.path.join(PROJECT_ROOT, "Grupo28B_RodriguezSandoval_HarrySly_v3_trackchanges_report.md")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
FIG_CAL_PATH = os.path.join(PROJECT_ROOT, "figures", "fig_noaa_calibration_v3.png")


def strip_ids(el):
    for e in el.iter():
        for k in list(e.attrib):
            if k.endswith("}paraId") or k.endswith("}textId"):
                del e.attrib[k]
    return el


def set_runs(p_el, texts):
    runs = p_el.findall(qn("w:r"))
    while len(runs) < len(texts):
        new_r = copy.deepcopy(runs[-1]) if runs else OxmlElement("w:r")
        p_el.append(new_r)
        runs = p_el.findall(qn("w:r"))
    for r, t in zip(runs, texts):
        ts = r.findall(qn("w:t"))
        if not ts:
            t_el = OxmlElement("w:t")
            r.append(t_el)
            ts = [t_el]
        ts[0].text = t
        ts[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        for extra in ts[1:]:
            r.remove(extra)
    for r in runs[len(texts):]:
        p_el.remove(r)
    return p_el


def clone_par(src_par, texts):
    el = strip_ids(copy.deepcopy(src_par._p))
    return set_runs(el, texts)


def set_full_par_text(par, new_text):
    """Sets paragraph text cleanly while preserving the paragraph's primary run formatting."""
    runs = par._p.findall(qn("w:r"))
    if len(runs) >= 2 and par.text.startswith(runs[0].text) and ":" in runs[0].text:
        # Preserve bold lead-in run if new_text starts with the same prefix up to ':'
        prefix = new_text.split(":", 1)[0] + ":"
        rest = new_text.split(":", 1)[1]
        set_runs(par._p, [prefix, rest])
    else:
        set_runs(par._p, [new_text])


def make_cell(tmpl_tc, width, text):
    tc = strip_ids(copy.deepcopy(tmpl_tc))
    tc.find(qn("w:tcPr")).find(qn("w:tcW")).set(qn("w:w"), str(width))
    p = tc.find(qn("w:p"))
    set_runs(p, [text])
    return tc


def make_table(tmpl_tbl, widths, header, rows):
    t = strip_ids(copy.deepcopy(tmpl_tbl))
    trs = t.findall(qn("w:tr"))
    hdr_tr, body_tr = trs[0], trs[1]
    h_tc = hdr_tr.findall(qn("w:tc"))
    b_tc = body_tr.findall(qn("w:tc"))
    for tr in trs:
        t.remove(tr)
    grid = t.find(qn("w:tblGrid"))
    for gc in list(grid):
        grid.remove(gc)
    for w in widths:
        gc = grid.makeelement(qn("w:gridCol"), {})
        gc.set(qn("w:w"), str(w))
        grid.append(gc)

    def build_row(tr_tmpl, tc_tmpls, cells):
        tr = strip_ids(copy.deepcopy(tr_tmpl))
        for tc in tr.findall(qn("w:tc")):
            tr.remove(tc)
        for i, (w, txt) in enumerate(zip(widths, cells)):
            tr.append(make_cell(tc_tmpls[0] if i == 0 else tc_tmpls[1], w, txt))
        return tr

    t.append(build_row(hdr_tr, h_tc, header))
    for r in rows:
        t.append(build_row(body_tr, b_tc, r))
    # Ensure explicit insideH horizontal borders between all rows so rows never visually fuse in PDF/OCR
    tblPr = t.find(qn("w:tblPr"))
    if tblPr is not None:
        borders = tblPr.find(qn("w:tblBorders"))
        if borders is not None and borders.find(qn("w:insideH")) is None:
            inside_h = OxmlElement("w:insideH")
            inside_h.set(qn("w:val"), "single")
            inside_h.set(qn("w:sz"), "4")
            inside_h.set(qn("w:space"), "0")
            inside_h.set(qn("w:color"), "D0D0D0")
            borders.append(inside_h)
    return t


def keep_together(*els):
    paras = []
    for el in els:
        if el.tag == qn("w:p"):
            paras.append(el)
        else:
            rows = el.findall(qn("w:tr"))
            for tr in rows[:-1]:
                paras += list(tr.iter(qn("w:p")))
    for p in paras:
        ppr = p.find(qn("w:pPr"))
        if ppr is None:
            ppr = OxmlElement("w:pPr")
            p.insert(0, ppr)
        if ppr.find(qn("w:keepNext")) is None:
            ppr.insert(0, OxmlElement("w:keepNext"))


def make_omml_run(text, italic=False, sz_half_pts=22):
    mr = OxmlElement("m:r")
    if not italic:
        mrPr = OxmlElement("m:rPr")
        nor = OxmlElement("m:nor")
        mrPr.append(nor)
        mr.append(mrPr)
    wrPr = OxmlElement("w:rPr")
    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), "Cambria Math")
    rFonts.set(qn("w:hAnsi"), "Cambria Math")
    rFonts.set(qn("w:cs"), "Cambria Math")
    wrPr.append(rFonts)
    wrPr.append(OxmlElement("w:b"))
    if italic:
        wrPr.append(OxmlElement("w:i"))
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "000000")
    wrPr.append(color)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(sz_half_pts))
    wrPr.append(sz)
    szCs = OxmlElement("w:szCs")
    szCs.set(qn("w:val"), str(sz_half_pts))
    wrPr.append(szCs)
    mr.append(wrPr)
    mt = OxmlElement("m:t")
    mt.text = text
    mt.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    mr.append(mt)
    return mr


def set_equation_2_omml(par):
    """Formats Eq. (2) in P[44] using native Word OMML <m:nary> summation with stacked limits i=0..83."""
    p_el = par._p
    for child in list(p_el):
        if child.tag != qn("w:pPr"):
            p_el.remove(child)
    pPr = p_el.find(qn("w:pPr"))
    if pPr is None:
        pPr = OxmlElement("w:pPr")
        p_el.insert(0, pPr)
    spacing = pPr.find(qn("w:spacing"))
    if spacing is None:
        spacing = OxmlElement("w:spacing")
        pPr.append(spacing)
    spacing.set(qn("w:before"), "120")
    spacing.set(qn("w:after"), "120")
    spacing.set(qn("w:line"), "260")

    omath = OxmlElement("m:oMath")
    omath.append(make_omml_run("DHW(t) = (1/7) · ", italic=False, sz_half_pts=22))

    nary = OxmlElement("m:nary")
    naryPr = OxmlElement("m:naryPr")
    chr_el = OxmlElement("m:chr")
    chr_el.set(mqn("m:val"), "∑")
    limLoc = OxmlElement("m:limLoc")
    limLoc.set(mqn("m:val"), "undOvr")
    grow = OxmlElement("m:grow")
    grow.set(mqn("m:val"), "1")
    naryPr.append(chr_el)
    naryPr.append(limLoc)
    naryPr.append(grow)
    nary.append(naryPr)

    sub = OxmlElement("m:sub")
    sub.append(make_omml_run("i=0", italic=False, sz_half_pts=18))
    sup = OxmlElement("m:sup")
    sup.append(make_omml_run("83", italic=False, sz_half_pts=18))
    e_el = OxmlElement("m:e")
    e_el.append(make_omml_run("HotSpot(t−i) · 1[HotSpot(t−i) ≥ 1.0]", italic=False, sz_half_pts=22))
    nary.append(sub)
    nary.append(sup)
    nary.append(e_el)
    omath.append(nary)

    omath.append(make_omml_run("   [°C-semanas]   (2)", italic=False, sz_half_pts=20))
    p_el.append(omath)


def set_rich_runs(par, specs, base_sz=21, base_font="Cambria Math", bold=True):
    """
    Replaces paragraph runs with structured Word runs supporting true <w:vertAlign>
    superscript/subscript, custom font, italic, and font size (in half-points).
    Each item in specs is (text, vert_align, italic, font_name_or_None).
    """
    p_el = par._p
    for child in list(p_el):
        if child.tag != qn("w:pPr"):
            p_el.remove(child)
    pPr = p_el.find(qn("w:pPr"))
    if pPr is None:
        pPr = OxmlElement("w:pPr")
        p_el.insert(0, pPr)
    spacing = pPr.find(qn("w:spacing"))
    if spacing is None:
        spacing = OxmlElement("w:spacing")
        pPr.append(spacing)
    spacing.set(qn("w:before"), "100")
    spacing.set(qn("w:after"), "100")
    spacing.set(qn("w:line"), "260")

    for txt, va, is_italic, fnt in specs:
        r = OxmlElement("w:r")
        rPr = OxmlElement("w:rPr")
        font_use = fnt or base_font
        rFonts = OxmlElement("w:rFonts")
        rFonts.set(qn("w:ascii"), font_use)
        rFonts.set(qn("w:hAnsi"), font_use)
        rFonts.set(qn("w:cs"), font_use)
        rPr.append(rFonts)
        if bold:
            rPr.append(OxmlElement("w:b"))
        if is_italic:
            rPr.append(OxmlElement("w:i"))
        color = OxmlElement("w:color")
        color.set(qn("w:val"), "000000")
        rPr.append(color)
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), str(base_sz))
        rPr.append(sz)
        szCs = OxmlElement("w:szCs")
        szCs.set(qn("w:val"), str(base_sz))
        rPr.append(szCs)
        if va in ("subscript", "superscript"):
            va_el = OxmlElement("w:vertAlign")
            va_el.set(qn("w:val"), va)
            rPr.append(va_el)
        r.append(rPr)
        t_el = OxmlElement("w:t")
        t_el.text = txt
        t_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        r.append(t_el)
        p_el.append(r)


MATH_TOKEN_RE = re.compile(
    r"(ρ̄_Spearman|ρ_Spearman|r̄_Pearson|r_Pearson|DHW_eff|DHW_95th|λ_DHW|Ω_arag|Ω_0|Ω_ref|G_net|G_max|E_bioerosion|Φ_restoration|H_MPA|w_T|w_U|w_R|w_W|ρ̄|ρ|κ)"
)
GREEK_BASES = {"ρ", "ρ̄", "κ", "λ", "Ω", "Φ"}


def _clone_rpr(rPr_src):
    if rPr_src is not None:
        return copy.deepcopy(rPr_src)
    return OxmlElement("w:rPr")


def _set_rpr_font(rPr, font_name, bold=None, italic=None, vert_align=None, min_sz=None):
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), font_name)
    rFonts.set(qn("w:hAnsi"), font_name)
    rFonts.set(qn("w:cs"), font_name)
    if bold is True and rPr.find(qn("w:b")) is None:
        rPr.append(OxmlElement("w:b"))
    if italic is True and rPr.find(qn("w:i")) is None:
        rPr.append(OxmlElement("w:i"))
    if min_sz is not None:
        for tag in ("w:sz", "w:szCs"):
            sz_el = rPr.find(qn(tag))
            if sz_el is None:
                sz_el = OxmlElement(tag)
                sz_el.set(qn("w:val"), str(min_sz))
                rPr.append(sz_el)
            else:
                try:
                    cur = int(sz_el.get(qn("w:val"), "0"))
                except ValueError:
                    cur = 0
                if cur < min_sz:
                    sz_el.set(qn("w:val"), str(min_sz))
    if vert_align in ("subscript", "superscript"):
        va = rPr.find(qn("w:vertAlign"))
        if va is None:
            va = OxmlElement("w:vertAlign")
            rPr.append(va)
        va.set(qn("w:val"), vert_align)


def _upgrade_paragraph_runs(p_el, is_table=False, is_ref=False):
    min_body_sz = 16 if is_table else 19
    spacing_val = "3" if is_table else ("6" if is_ref else "4")
    min_math_sz = 18 if is_table else 21

    # First pass: boost tiny font sizes and add subtle character spacing to prevent glyph crowding
    for r in list(p_el.findall(qn("w:r"))):
        rPr = r.find(qn("w:rPr"))
        if rPr is None:
            rPr = OxmlElement("w:rPr")
            r.insert(0, rPr)
        for tag in ("w:sz", "w:szCs"):
            sz_el = rPr.find(qn(tag))
            if sz_el is not None:
                try:
                    v = int(sz_el.get(qn("w:val"), "20"))
                except ValueError:
                    v = 20
                if v <= (14 if is_table else 17):
                    sz_el.set(qn("w:val"), str(min_body_sz))
        if rPr.find(qn("w:spacing")) is None:
            sp = OxmlElement("w:spacing")
            sp.set(qn("w:val"), spacing_val)
            rPr.append(sp)

    # Second pass: split runs containing math/Greek/subscript tokens
    for r in list(p_el.findall(qn("w:r"))):
        t_el = r.find(qn("w:t"))
        if t_el is None or not t_el.text:
            continue
        text = t_el.text
        if not MATH_TOKEN_RE.search(text):
            continue
        rPr_orig = r.find(qn("w:rPr"))
        parts = MATH_TOKEN_RE.split(text)
        new_runs = []
        for idx, part in enumerate(parts):
            if not part:
                continue
            if idx % 2 == 1:
                # Matched a math token
                if "_" in part:
                    base_sym, sub_sym = part.split("_", 1)
                    r_base = OxmlElement("w:r")
                    rPr_b = _clone_rpr(rPr_orig)
                    if base_sym in GREEK_BASES:
                        _set_rpr_font(rPr_b, "Cambria Math", bold=True, italic=True, min_sz=min_math_sz)
                    else:
                        _set_rpr_font(rPr_b, "Cambria Math", italic=(len(base_sym) == 1), min_sz=min_math_sz)
                    r_base.append(rPr_b)
                    tb = OxmlElement("w:t")
                    tb.text = base_sym
                    tb.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                    r_base.append(tb)
                    new_runs.append(r_base)

                    r_sub = OxmlElement("w:r")
                    rPr_s = _clone_rpr(rPr_orig)
                    _set_rpr_font(rPr_s, "Cambria Math", italic=False, vert_align="subscript", min_sz=min_math_sz)
                    r_sub.append(rPr_s)
                    ts = OxmlElement("w:t")
                    ts.text = sub_sym
                    ts.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                    r_sub.append(ts)
                    new_runs.append(r_sub)
                else:
                    r_sym = OxmlElement("w:r")
                    rPr_m = _clone_rpr(rPr_orig)
                    _set_rpr_font(rPr_m, "Cambria Math", bold=True, italic=True, min_sz=min_math_sz)
                    r_sym.append(rPr_m)
                    tm = OxmlElement("w:t")
                    tm.text = part
                    tm.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                    r_sym.append(tm)
                    new_runs.append(r_sym)
            else:
                r_txt = OxmlElement("w:r")
                rPr_t = _clone_rpr(rPr_orig)
                r_txt.append(rPr_t)
                tt = OxmlElement("w:t")
                tt.text = part
                tt.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                r_txt.append(tt)
                new_runs.append(r_txt)
        for nr in new_runs:
            r.addprevious(nr)
        p_el.remove(r)


def upgrade_typography_and_math_runs(doc, skip_pars=None):
    """Formats inline Greek/math tokens in Cambria Math with true subscripts and boosts 7pt text to prevent OCR errors."""
    if skip_pars is None:
        skip_pars = set()
    in_refs = False
    for p in doc.paragraphs:
        txt_head = p.text.strip()
        if txt_head.startswith("7. Referencias") or txt_head.startswith("Referencias"):
            in_refs = True
        if p._p in skip_pars:
            continue
        _upgrade_paragraph_runs(p._p, is_table=False, is_ref=in_refs)

    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    if p._p in skip_pars:
                        continue
                    _upgrade_paragraph_runs(p._p, is_table=True, is_ref=False)


def patch_docx_media_images(docx_path):
    """Patches image1.png (Figura 1 title CoralTwin-DT upright) and image6.png (Figura 6 STN_17: CoralTriangle_Misool_17 pill box)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(docx_path, "r") as zin:
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/media/image1.png":
                    im = Image.open(io.BytesIO(data)).convert("RGB")
                    draw = ImageDraw.Draw(im)
                    draw.rectangle([450, 92, 3715, 180], fill=(255, 255, 255))
                    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 50)
                    title = "Arquitectura Ciberfísica de Seis Capas de CoralTwin-DT"
                    bbox = draw.textbbox((0, 0), title, font=font)
                    tw = bbox[2] - bbox[0]
                    x = (im.size[0] - tw) // 2
                    draw.text((x, 108), title, fill=(17, 24, 39), font=font)
                    out_img = io.BytesIO()
                    im.save(out_img, format="PNG")
                    data = out_img.getvalue()
                elif item.filename == "word/media/image6.png":
                    im = Image.open(io.BytesIO(data)).convert("RGB")
                    draw = ImageDraw.Draw(im)
                    draw.rectangle([3305, 1152, 3880, 1200], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
                    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 27)
                    draw.text((3314, 1161), "STN_17: CoralTriangle_Misool_17", fill=(15, 23, 42), font=font)
                    out_img = io.BytesIO()
                    im.save(out_img, format="PNG")
                    data = out_img.getvalue()
                zout.writestr(item, data)
    with open(docx_path, "wb") as f:
        f.write(buf.getvalue())


def enforce_table_integrity(doc):
    """Ensures no table in the DOCX is truncated, split mid-row, or separated from its caption/header."""
    body_children = list(doc.element.body.iterchildren())
    for idx, el in enumerate(body_children):
        if el.tag == qn("w:tbl"):
            # Keep preceding label + caption paragraphs attached to the table
            for back in (1, 2):
                if idx - back >= 0 and body_children[idx - back].tag == qn("w:p"):
                    p = body_children[idx - back]
                    txt = "".join(t.text or "" for t in p.iter(qn("w:t"))).strip()
                    if txt.startswith("Tabla ") or back == 1:
                        ppr = p.find(qn("w:pPr"))
                        if ppr is None:
                            ppr = OxmlElement("w:pPr")
                            p.insert(0, ppr)
                        if ppr.find(qn("w:keepNext")) is None:
                            ppr.insert(0, OxmlElement("w:keepNext"))
            trs = el.findall(qn("w:tr"))
            for r_i, tr in enumerate(trs):
                trPr = tr.find(qn("w:trPr"))
                if trPr is None:
                    trPr = OxmlElement("w:trPr")
                    tr.insert(0, trPr)
                if trPr.find(qn("w:cantSplit")) is None:
                    trPr.append(OxmlElement("w:cantSplit"))
                if r_i == 0 and trPr.find(qn("w:tblHeader")) is None:
                    trPr.append(OxmlElement("w:tblHeader"))
                # For compact tables (<= 16 rows), keep all rows together on one page;
                # for tall multi-page tables (> 16 rows), keep at least header + first data row together.
                if (len(trs) <= 16 and r_i < len(trs) - 1) or (len(trs) > 16 and r_i == 0):
                    for p in tr.iter(qn("w:p")):
                        ppr = p.find(qn("w:pPr"))
                        if ppr is None:
                            ppr = OxmlElement("w:pPr")
                            p.insert(0, ppr)
                        if ppr.find(qn("w:keepNext")) is None:
                            ppr.insert(0, OxmlElement("w:keepNext"))


def main():
    doc = docx.Document(SRC_DOCX)
    P = list(doc.paragraphs)
    orig_tables = list(doc.tables)
    body = doc.element.body
    all_tables = [k for k in body.iterchildren() if k.tag == qn("w:tbl")]
    tmpl_tbl = all_tables[6]  # Table 7 style template

    # Load computed artifacts from results/
    with open(os.path.join(RESULTS_DIR, "noaa_calibration_summary.json"), "r", encoding="utf-8") as f:
        cal_sum = json.load(f)["spatial_evaluation"]["N29_Direct_Marine_Pixels"]
    s4_as = pd.read_csv(os.path.join(RESULTS_DIR, "s4_factor_isolation_anova_sobol.csv"))
    srpi_sens = pd.read_csv(os.path.join(RESULTS_DIR, "srpi_sensitivity.csv"))
    srpi_strict = srpi_sens[srpi_sens["Formulation"] == "strict_Eq7"].set_index("Threshold")

    track_changes = []

    def record_change(section_label, para_id, fon_id, old_txt, new_txt):
        track_changes.append({
            "section": section_label,
            "para_id": para_id,
            "fon": fon_id,
            "old": old_txt,
            "new": new_txt,
        })

    # -------------------------------------------------------------------------
    # 1. ABSTRACT (P006) — FASE 1, FASE 2, FASE 3
    # -------------------------------------------------------------------------
    old_p006 = P[6].text
    new_p006 = (
        "Antecedentes: Las olas de calor marinas y la acidificación oceánica amenazan a los arrecifes de corales escleractinios. "
        "El monitoreo retrospectivo y las áreas marinas protegidas (AMP) estáticas, sin embargo, no anticipan los puntos de inflexión "
        "biofísicos ni señalan dónde intervenir primero. Métodos: Presentamos CoralTwin-DT, un prototipo de gemelo digital de código abierto, "
        "basado en simulación (no operativo) y con arquitectura de seis capas (telemetría NOAA Coral Reef Watch y Sentinel-2, sensores in situ, "
        "cuadrículas bentónicas de 500 m), evaluado como banco de pruebas metodológico sobre un conjunto de referencia sintético "
        "(N = 15,000 registros, 30 estaciones, 2015–2024, semilla 42). Comparamos XGBoost, Random Forest, Deep MLP y Stacked LSTM como emuladores "
        "del generador, bajo validación cruzada espacial de 5 bloques con buffer de 25 km, y sumamos TreeSHAP, ecuaciones diferenciales ordinarias "
        "(EDO) de competencia coral–macroalgas (RK4, Δt = 0.05 años, 5,000 corridas Monte Carlo por escenario) y un Índice de Prioridad Espacial "
        "de Restauración (SRPI; SRPI heurístico, no validado en campo, no operacional). También se realizó una validación y calibración por estación "
        "con 10 años de telemetría real de NOAA CRW (5 km, entrenamiento 2015–2020 y prueba 2021–2024). Resultados: Con 10 variables ambientales "
        "libres de fuga, los cuatro modelos convergieron a un mismo techo predictivo (R² = 0.9336–0.9375; RMSE = 3.92–4.04 %). Una auditoría "
        "mostró que un R² previo de 0.9994 en el régimen de 16 variables se debía a 4 variables bentónicas post-objetivo (más 2 derivadas colineales). "
        "Random Forest obtuvo los valores nominales más altos (Macro-F1 = 0.7284), pero se retuvo XGBoost (Macro-F1 = 0.7187) por su latencia "
        "(0.322 ms frente a 17.80 ms) y su tamaño (2.83 MB frente a 21.09 MB). En Random Forest, la ponderación de clases elevó la sensibilidad de "
        "la clase minoritaria Medio (1.24 % de los registros) de 10.75 % a 45.91 %, mientras que en XGBoost apenas pasó de 9.78 % a 11.72 % (media de "
        "5 semillas). TreeSHAP asignó a las semanas de calentamiento por grado (DHW) el 53.71 % de la importancia. Dentro del soporte empírico de la "
        "saturación de aragonita, la acidificación adelanta el cruce del 35 % de pérdida en −0.35 °C-semanas (XGBoost) y −0.80 °C-semanas (generador). "
        "Entre 2025 y 2050, el escenario sin mitigación (S1) colapsa a 0.69 % de cobertura coralina, mientras que la intervención combinada con AMP "
        "(S4, mejor escenario simulado) alcanza 55.20 % y +7.46 kg CaCO₃ m⁻² año⁻¹; al aislar los factores mediante diseño factorial 2⁴, valores de "
        "Shapley e índices de Sobol, solo el 22.5 % de la ventaja aditiva de S4 sobre S3 en cobertura (5.77 % de la varianza factorial de Sobol) "
        "corresponde al manejo (pastoreo y trasplante) y el 77.5 % restante (94.17 % de la varianza de Sobol) al forzamiento climático menos severo "
        "asignado a S4. La validación con NOAA mostró una correlación nula con el generador sin calibrar (ρ_Spearman = −0.0921; p = 0.6346; "
        "KGE = −0.474) y redujo las estaciones SRPI de Nivel 1 de 10 a 4 (20.00 % de preservación con el umbral de 0.70; 15.38 %–44.44 % entre 0.60 "
        "y 0.75; media bootstrap 10,000 de 2.01 estaciones [IC 95 %: 0.0–5.0] y rango leave-one-station-out de 1–2 estaciones en 0.70). Al calibrar "
        "el generador por estación en 2015–2020 y evaluar en prueba (2021–2024; N = 29), el ajuste espacial de DHW_95th mejora (ρ = +0.6360, "
        "p = 0.0002; RMSE de 8.102 a 4.195 °C-semanas; sesgo de +4.727 a +0.012 °C-semanas; KGE = +0.619), pero la correlación temporal semanal "
        "intra-estación sigue siendo baja (ρ̄ = +0.1107; KGE = −0.005) por la no estacionariedad de las olas de calor de 2023–2024. Conclusiones: "
        "Una arquitectura ciberfísica modular y auditable es técnicamente viable, pero el emulador reproduce un generador sintético y no arrecifes "
        "observados; además, declaramos que el índice es un SRPI heurístico, no validado en campo, no operacional. Los resultados no deben leerse "
        "como predicciones sobre arrecifes reales sin asimilación continua de observaciones físicas."
    )
    set_full_par_text(P[6], new_p006)
    record_change("Resumen", "P006", "FON-01, FON-04, FON-05, FON-08", old_p006, new_p006)

    # -------------------------------------------------------------------------
    # 2. EQUATIONS & SYMBOL TABLE (Section 2.3: P042-P056, P086-P087) — FASE 4 (FON-06)
    # -------------------------------------------------------------------------
    old_p042, old_p044 = P[42].text, P[44].text
    new_p042 = (
        "La acumulación de calor anómalo que induce estrés fisiológico sobre el holobionte coralino se cuantifica con las semanas de "
        "calentamiento por grado (Degree Heating Weeks, DHW). NOAA CRW las define operacionalmente como la acumulación en una ventana móvil "
        "de 12 semanas (84 días, índice diario i = 0, 1, ..., 83) de las anomalías térmicas instantáneas (HotSpot, en °C) que igualan o superan "
        "en al menos 1.0 °C la climatología de la media mensual máxima histórica (MMM, en °C; Liu et al., 2014):"
    )
    new_p044 = "DHW(t) = (1/7) · Σ_{i=0}^{83} HotSpot(t−i) · 1[HotSpot(t−i) ≥ 1.0]   [°C-semanas]   (2)"
    set_full_par_text(P[42], new_p042)
    set_rich_runs(
        P[44],
        [
            ("DHW(t) = (1/7) · Σ", None, False, "Cambria Math"),
            ("i=0", "subscript", False, "Cambria Math"),
            ("83", "superscript", False, "Cambria Math"),
            (" HotSpot(t−i) · 1[HotSpot(t−i) ≥ 1.0]   [°C-semanas]   (2)", None, False, "Cambria Math"),
        ],
        base_sz=22,
    )
    record_change("Sección 2.3.1 (Ec. 2)", "P042, P044", "FON-06 / BLOQUE-2", old_p044, new_p044)

    old_p045 = P[45].text
    new_p045 = (
        "Nota metodológica sobre la Ec. (2): En la formulación física satelital de la Ec. (2), 1[HotSpot(t−i) ≥ 1.0] ∈ {0, 1} es la función "
        "indicadora de Heaviside (vale 1 cuando la anomalía térmica diaria alcanza o supera 1.0 °C sobre el MMM y 0 en caso contrario), y el factor "
        "1/7 (semanas día⁻¹) convierte los grados-día acumulados en los 84 días previos a unidades de °C-semanas. En el generador sintético base "
        "(03_Data/build_final_dataset.py, semilla 42), DHW se aproxima de forma paramétrica a partir del HotSpot instantáneo del día muestreado y de "
        "pulsos estocásticos de olas de calor marinas; en la Fase 1 de esta revisión (01_Data/calibrate_generator_to_noaa.py), los parámetros térmicos "
        "de dicho generador se calibran por estación frente a la serie semanal observada de NOAA CRW (entrenamiento 2015–2020 y prueba 2021–2024; "
        "Sección 3.4)."
    )
    set_full_par_text(P[45], new_p045)
    record_change("Sección 2.3.1", "P045", "FON-01, FON-06 / BLOQUE-2", old_p045, new_p045)

    old_p050, old_p051 = P[50].text, P[51].text
    new_p050 = (
        "G_net(t) = G_max · [max((Ω_arag − Ω_0)/Ω_ref, 0)]^κ · exp(−λ_DHW · DHW(t)) · (C(t)/C_0) − E_bioerosion   [kg CaCO₃ m⁻² año⁻¹]   (4)"
    )
    new_p051 = (
        "donde cada parámetro tiene significado físico y unidades explícitas conforme a la implementación en 07_Scenarios_and_Simulations/simulation_engine.py: "
        "G_max = 12.5 kg CaCO₃ m⁻² año⁻¹ es la tasa potencial máxima de acreción biogénica en arrecifes dominados por corales escleractinios constructores "
        "bajo sobresaturación óptima (Cornwall et al., 2021; Perry et al., 2018); Ω_0 = 1.0 (adimensional) es el umbral termodinámico de equilibrio de "
        "disolución de la aragonita; Ω_ref = 2.8 (adimensional) es la escala de normalización del exceso de sobresaturación (Ω_arag − 1.0), definida para "
        "que el cociente valga la unidad cuando Ω_arag = 3.8; κ = 1.2 (adimensional) es el exponente cinético alométrico que captura la sensibilidad "
        "no lineal de la calcificación al estado de saturación de carbonatos (Bove et al., 2022; Cornwall et al., 2021); λ_DHW = 0.06 (°C-semanas)⁻¹ es el "
        "coeficiente de atenuación exponencial de la calcificación por estrés térmico acumulado; C(t) / C_0 (adimensional) pondera la producción bruta de "
        "carbonato por la fracción de cobertura coralina viva actual C(t) respecto a la cobertura inicial de línea base C_0 = 0.3368 (33.68 %); y "
        "E_bioerosion = 1.85 kg CaCO₃ m⁻² año⁻¹ es la tasa basal constante de bioerosión física y biológica producida por peces escáridos, equinoideos y "
        "endolitos perforadores (Cornwall et al., 2021; Esplandiu et al., 2024)."
    )
    set_rich_runs(
        P[50],
        [
            ("G", None, True, "Cambria Math"),
            ("net", "subscript", False, "Cambria Math"),
            ("(t) = ", None, False, "Cambria Math"),
            ("G", None, True, "Cambria Math"),
            ("max", "subscript", False, "Cambria Math"),
            (" · [max((Ω", None, False, "Cambria Math"),
            ("arag", "subscript", False, "Cambria Math"),
            (" − Ω", None, False, "Cambria Math"),
            ("0", "subscript", False, "Cambria Math"),
            (")/Ω", None, False, "Cambria Math"),
            ("ref", "subscript", False, "Cambria Math"),
            (", 0)]", None, False, "Cambria Math"),
            ("κ", "superscript", True, "Cambria Math"),
            (" · exp(−λ", None, False, "Cambria Math"),
            ("DHW", "subscript", False, "Cambria Math"),
            (" · DHW(t)) · (C(t)/C", None, False, "Cambria Math"),
            ("0", "subscript", False, "Cambria Math"),
            (") − E", None, False, "Cambria Math"),
            ("bioerosion", "subscript", False, "Cambria Math"),
            ("   [kg CaCO₃ m⁻² año⁻¹]   (4)", None, False, "Cambria Math"),
        ],
        base_sz=22,
    )
    set_full_par_text(P[51], new_p051)
    record_change("Sección 2.3.2 (Ec. 4)", "P050, P051", "FON-06", old_p050 + " | " + old_p051, new_p050 + " | " + new_p051)

    old_p054, old_p055, old_p056 = P[54].text, P[55].text, P[56].text
    new_p054 = (
        "dC / dt = r · C · (1 − C − M) − [d₀ + (α · DHW_eff(t))² / (1 + β · Ω_arag(t))] · C + Φ_restoration · (1 − C − M)   [año⁻¹]   (5)"
    )
    new_p055 = (
        "dM / dt = a · M · (1 − C − M) − [g(H_MPA) · M / (1 − C + ε)] + γ · M · C   [año⁻¹]   (6)"
    )
    new_p056 = (
        "En la integración numérica ejecutada (07_Scenarios_and_Simulations/simulation_engine.py; resultados auditados en results/scenario_ode_parameters.json), "
        "C(t) y M(t) son fracciones adimensionales del sustrato bentónico en [0, 1], (1 − C − M) es la fracción de espacio libre colonizable, y los parámetros "
        "base toman los valores r = 0.28 año⁻¹ (tasa intrínseca de reclutamiento y extensión radial coralina; rango en literatura: 0.28–0.45 año⁻¹), "
        "d₀ = 0.03 año⁻¹ (mortalidad natural basal no térmica; literatura: 0.03–0.05 año⁻¹), α = 0.0022 (°C-semanas)⁻² año⁻¹ (coeficiente cuadrático de "
        "mortalidad inducida por estrés térmico efectivo DHW_eff(t) = max(DHW(t) − ΔT_hardening, 0)), β = 0.35 (adimensional; factor de amortiguamiento por "
        "saturación de aragonita), a = 0.42 año⁻¹ (tasa de expansión vegetativa macroalgal), γ = 0.14 año⁻¹ (coeficiente de sobrecrecimiento competitivo de "
        "macroalgas sobre coral vivo) y ε = 10⁻⁶ (constante de regularización numérica). Φ_restoration es la tasa anual de trasplante activo sobre espacio "
        "disponible (Φ = 0.025 año⁻¹ en S3 y Φ = 0.030 año⁻¹ en S4, con endurecimiento térmico ΔT_hardening = 2.0 °C-semanas; Boström-Einarsson et al., 2020; "
        "Ladd et al., 2019). En las 5,000 corridas Monte Carlo por escenario, los parámetros cinéticos (r, a, α, γ, g, Φ) se perturban con ruido gaussiano "
        "multiplicativo de ±15 % (truncado a [0.60, 1.40]). La Tabla 1b sintetiza todos los símbolos, definiciones, valores en código y unidades de las Ecs. (1)–(7)."
    )
    set_rich_runs(
        P[54],
        [
            ("dC/dt = r · C · (1 − C − M) − [d", None, False, "Cambria Math"),
            ("0", "subscript", False, "Cambria Math"),
            (" + (α · DHW", None, False, "Cambria Math"),
            ("eff", "subscript", False, "Cambria Math"),
            ("(t))", None, False, "Cambria Math"),
            ("2", "superscript", False, "Cambria Math"),
            (" / (1 + β · Ω", None, False, "Cambria Math"),
            ("arag", "subscript", False, "Cambria Math"),
            ("(t))] · C + Φ", None, False, "Cambria Math"),
            ("restoration", "subscript", False, "Cambria Math"),
            (" · (1 − C − M)   [año⁻¹]   (5)", None, False, "Cambria Math"),
        ],
        base_sz=22,
    )
    set_rich_runs(
        P[55],
        [
            ("dM/dt = a · M · (1 − C − M) − [g(H", None, False, "Cambria Math"),
            ("MPA", "subscript", False, "Cambria Math"),
            (") · M / (1 − C + ε)] + γ · M · C   [año⁻¹]   (6)", None, False, "Cambria Math"),
        ],
        base_sz=22,
    )
    set_full_par_text(P[56], new_p056)
    record_change("Sección 2.3.3 (Ecs. 5-6)", "P054-P056", "FON-06", old_p054 + " | " + old_p056, new_p054 + " | " + new_p056)

    # Insert Tabla 1b (Symbol & Unit Table for Eqs. 1-7) right after P062
    sym_rows = [
        ["SST(t), MMM", "Temperatura superficial del mar diaria y media mensual máxima climatológica", "22.0–33.5; 27.5–29.8", "°C"],
        ["HotSpot(t)", "Anomalía térmica positiva instantánea sobre MMM (Ec. 1)", "max(SST − MMM, 0)", "°C"],
        ["1[HotSpot(t−i) ≥ 1.0]", "Función indicadora de umbral de blanqueamiento en ventana de 84 días (Ec. 2)", "{0, 1} (divisor 7 días/sem)", "adimensional"],
        ["DHW(t), DHW_eff(t)", "Estrés térmico acumulado en 12 semanas (Ec. 2) y efectivo tras endurecimiento ΔT", "0.0–22.0 (ΔT = 2.0 en S3/S4)", "°C-semanas"],
        ["Ω_arag, Ω_0, Ω_ref", "Estado de saturación de aragonita (Ec. 3), umbral termodinámico y escala de referencia", "Ω_0 = 1.0; Ω_ref = 2.8", "adimensional"],
        ["G_net(t), G_max", "Tasa neta de calcificación (Ec. 4) y tasa máxima potencial de acreción biogénica", "G_max = 12.5", "kg CaCO₃ m⁻² año⁻¹"],
        ["κ, λ_DHW", "Exponente alométrico de calcificación y coeficiente de decaimiento térmico en Ec. (4)", "κ = 1.2; λ_DHW = 0.06", "adim.; (°C-sem)⁻¹"],
        ["E_bioerosion", "Tasa basal constante de bioerosión física y biológica del armazón arrecifal (Ec. 4)", "1.85", "kg CaCO₃ m⁻² año⁻¹"],
        ["C(t), M(t), C_0", "Fracciones de cobertura de coral vivo, macroalgas y línea base coralina 2025 (Ecs. 4–6)", "C_0 = 0.3368; M_0 = 0.3141", "adimensional [0, 1]"],
        ["r, d₀", "Tasa intrínseca de crecimiento coralino y mortalidad natural no térmica (Ec. 5)", "r = 0.28; d₀ = 0.03", "año⁻¹"],
        ["α, β", "Coeficiente de mortalidad térmica cuadrática y amortiguación por aragonita (Ec. 5)", "α = 0.0022; β = 0.35", "(°C-sem)⁻² año⁻¹; adim."],
        ["Φ_restoration", "Tasa de suplementación por trasplante coralino sobre sustrato libre (Ec. 5)", "0 (S1,S2); 0.025 (S3); 0.030 (S4)", "año⁻¹"],
        ["a, γ", "Tasa de expansión macroalgal y coeficiente de sobrecrecimiento sobre coral (Ec. 6)", "a = 0.42; γ = 0.14", "año⁻¹"],
        ["g(H_MPA)", "Tasa efectiva de herbivoría según nivel de protección en AMP (Ec. 6)", "0.25 (S1); 0.30 (S2); 0.35 (S3); 0.68 (S4)", "año⁻¹"],
        ["SRPI, w_T, w_U, w_R, w_W", "Índice de Prioridad Espacial de Restauración y pesos multicriterio (Ec. 7)", "0.35, 0.25, 0.25, 0.15", "adimensional [0, 1]"],
    ]
    lab_sym = clone_par(P[128], ["Tabla 1b"])
    desc_sym = clone_par(P[129], [
        "Nomenclatura matemática, definiciones físicas, valores paramétricos ejecutados en código y unidades del sistema biofísico acoplado (Ecs. 1–7)."
    ])
    tbl_sym = make_table(
        tmpl_tbl,
        [2000, 3968, 2000, 1600],
        ["Símbolo", "Definición física y ecológica", "Valor en código / rango", "Unidades"],
        sym_rows,
    )
    note_sym = clone_par(P[130], [
        "Nota.",
        " Todos los valores coinciden exactamente con 07_Scenarios_and_Simulations/simulation_engine.py, 08_GIS_and_Remote_Sensing/spatial_pipeline.py y results/scenario_ode_parameters.json.",
    ])
    anchor_sym = P[62]._p
    for el in (lab_sym, desc_sym, tbl_sym, note_sym):
        anchor_sym.addnext(el)
        anchor_sym = el
    keep_together(lab_sym, desc_sym, tbl_sym)

    # Also refine P087 (Eq. 7 sub-index definitions) to show exact normalization constants from spatial_pipeline.py
    old_p087 = P[87].text
    new_p087 = (
        "donde cada subíndice está acotado en [0, 1] conforme a 08_GIS_and_Remote_Sensing/spatial_pipeline.py: "
        "ThermRefugia = 1 − min(DHW_95th / 16.0, 1.0) evalúa la resiliencia al estrés térmico acumulado en el percentil 95 (normalizado sobre "
        "16.0 °C-semanas); RestorationUrgency = clip(1 − Cobertura_Actual / 50.0, 0.0, 1.0) prioriza sitios degradados respecto a una cobertura "
        "histórica de referencia del 50.0 %; BenthicRugosity = clip((Rugosidad_Estructural − 1.0) / 2.0, 0.0, 1.0) cuantifica la complejidad "
        "topográfica entre 1.0 (liso) y 3.0 (alta rugosidad; Price et al., 2019; Rossi et al., 2020); y WaterQuality = 1 − min(Kd(490) / 0.25, 1.0), "
        "con Kd(490) = 0.04 · Turbidez_NTU [m⁻¹], premia aguas de baja atenuación lumínica (Asner et al., 2020; Sauder et al., 2023)."
    )
    set_full_par_text(P[87], new_p087)
    record_change("Sección 2.7 (Ec. 7)", "P087", "FON-06", old_p087, new_p087)

    # Clean Tabla 2 note (P068) and unify Tabla 3 (orig_tables[2], pág. 9) & its note (P093) to 23 etapas
    set_full_par_text(
        P[68],
        "Nota. Todos los modelos se evaluaron con las mismas particiones espaciales y cinco semillas externas independientes. "
        "El guion (—) indica que la justificación es común a la fila anterior del mismo grupo.",
    )
    tbl3 = orig_tables[2]
    set_runs(tbl3.rows[1].cells[1]._tc.find(qn("w:p")), ["Python 3.11 sobre Windows 10 x64 (arquitectura AMD64)"])
    set_runs(
        tbl3.rows[4].cells[1]._tc.find(qn("w:p")),
        ["Semilla maestra del generador de datos = 42; cinco semillas independientes de evaluación cruzada"],
    )
    set_runs(
        tbl3.rows[5].cells[1]._tc.find(qn("w:p")),
        ["Ejecución automatizada de 23 etapas mediante python run_all.py (verificado en results/pipeline_execution_log_v4.json)"],
    )
    old_p093 = P[93].text
    new_p093 = (
        "Nota. Las especificaciones de software y librerías coinciden con el archivo requirements.txt y el contenedor Dockerfile del repositorio oficial. "
        "Las latencias dependen del hardware de prueba y deben interpretarse en términos relativos entre modelos."
    )
    set_full_par_text(P[93], new_p093)
    record_change("Tabla 3 y Nota (pág. 9)", "Table_3, P093", "Unificación 23 etapas y limpieza de Nota", old_p093, new_p093)

    # -------------------------------------------------------------------------
    # 3. FON-08: RESOLVE 14 vs 16 VARIABLES & ELIMINATE [VERIFICAR] (P069, P102, Tabla 5)
    # -------------------------------------------------------------------------
    old_p069 = P[69].text
    new_p069 = (
        "Construcción del objetivo y naturaleza de emulación (modelo sustituto): Para descartar fuga de datos, documentamos cómo se construye la "
        "variable objetivo continua (Coral_Cover_Loss_Pct). En el generador (03_Data/build_final_dataset.py), esta variable es una combinación lineal "
        "directa de la severidad del blanqueamiento más una perturbación gaussiana estocástica (Coral_Cover_Loss_Pct = 0.80 · Bleaching_Severity_Pct + "
        "N(0, 3.5²)). A su vez, la severidad es una transformación logística determinista de un índice de estrés biofísico acoplado a DHW, Ω_arag, "
        "radiación PAR y turbidez. La tarea de regresión, por tanto, no predice un fenómeno ecológico no observado: emula (como modelo sustituto) la "
        "superficie analítica del generador. En la matriz completa de 16 predictores evaluada en la auditoría de ablación (Regime_0_Leaked_16; Tabla 5), "
        "las 16 variables se componen exactamente de: (i) las 10 variables ambientales primarias pre-objetivo (SST_degC, SST_Anomaly_degC, DHW_degC_weeks, "
        "pH_total, Salinity_PSU, Dissolved_Oxygen_mg_L, Aragonite_Saturation_Omega, Turbidity_NTU, PAR_umol_m2_s y Depth_m), (ii) 2 variables ambientales "
        "derivadas colineales (HotSpot_degC = max(SST − MMM, 0) y Kd_490_m_inv = 0.018 + 0.052 · Turbidity_NTU), y (iii) las 4 variables bentónicas "
        "post-objetivo (Shannon_Diversity_H, Structural_Rugosity, Live_Coral_Cover_Pct y Macroalgae_Cover_Pct), que se calculan después de la pérdida "
        "de cobertura. La inclusión de estas 4 variables post-objetivo explica el R² artificialmente alto de 0.9994 (RMSE = 0.395 %). Al excluir las 4 "
        "variables bentónicas post-objetivo y las 2 derivadas colineales, el régimen canónico (Regime_1_Clean_Emulation_10) queda restringido a las 10 "
        "variables ambientales primarias libres de fuga."
    )
    set_full_par_text(P[69], new_p069)
    record_change("Sección 2.4", "P069", "FON-08", old_p069, new_p069)

    old_p102 = P[102].text
    new_p102 = (
        "Auditoría de fuga del objetivo (ablación de variables): La Tabla 5 muestra la prueba de ablación sobre los cinco regímenes de entrada. "
        "Con las 16 variables disponibles en Regime_0_Leaked_16 (formadas por las 10 variables ambientales primarias, las 2 variables ambientales "
        "derivadas colineales HotSpot_degC y Kd_490_m_inv, y las 4 variables bentónicas post-objetivo Shannon_Diversity_H, Structural_Rugosity, "
        "Live_Coral_Cover_Pct y Macroalgae_Cover_Pct), el R² alcanzó un valor artificial de 0.9994 (RMSE = 0.395 %). El análisis TreeSHAP reveló que "
        "Shannon_Diversity_H concentraba por sí sola el 80.61 % de la importancia total porque se genera matemáticamente como función lineal directa "
        "de Coral_Cover_Loss_Pct (es post-objetivo). Al retirar las 4 variables bentónicas post-objetivo y las 2 variables ambientales derivadas "
        "colineales, entrenando únicamente con las 10 variables ambientales primarias limpias (Regime_1_Clean_Emulation_10), el R² se situó en el "
        "valor legítimo de emulación de 0.9336 (RMSE = 4.044 %)."
    )
    set_full_par_text(P[102], new_p102)
    record_change("Sección 3.1 (Tabla 5 / Ablación)", "P102", "FON-08", old_p102, new_p102)

    # Update Tabla 5 (orig_tables[4], Row 1, Cell 2) to explicitly state 10 + 2 + 4 = 16 variables
    tbl5 = orig_tables[4]
    old_t5_c2 = tbl5.rows[1].cells[2].text
    new_t5_c2 = (
        "10 ambientales primarias + 2 ambientales derivadas colineales (HotSpot_degC, Kd_490_m_inv) + "
        "4 bentónicas post-objetivo (Shannon_Diversity_H, rugosidad, cobertura coralina y macroalgal)"
    )
    set_runs(tbl5.rows[1].cells[2]._tc.find(qn("w:p")), [new_t5_c2])
    record_change("Tabla 5 (Fila 1)", "Table_4_Row_1", "FON-08", old_t5_c2, new_t5_c2)

    # -------------------------------------------------------------------------
    # 4. FASE 2 (FON-04): EXACT QUANTITATIVE ATTRIBUTION IN SECTION 3.3 (P127, Tabla 7b, P134-P136) & 4.2 (P158)
    # -------------------------------------------------------------------------
    old_p127 = P[127].text
    new_p127 = (
        "Sobre el término 'óptimo' y la descomposición factorial entre S3 y S4: S4 es el mejor escenario simulado entre las alternativas analizadas, "
        "pero no una solución formalmente optimizada. Su ventaja sobre S3 proviene de cuatro parámetros que cambian simultáneamente en el código: "
        "mayor protección de pastoreo (g = 0.68 frente a 0.35 año⁻¹), mayor tasa de trasplante (Φ = 0.030 frente a 0.025 año⁻¹), un forzamiento térmico "
        "de fondo menos severo (pendiente de DHW de 0.18 frente a 0.20 °C-sem/año) y una acidificación menos intensa (pendiente de Ω de −0.022 frente "
        "a −0.028 año⁻¹). La contribución exacta de cada factor y sus interacciones se cuantifican mediante un diseño factorial completo 2⁴ (16 variantes), "
        "valores exactos de Shapley y descomposición de varianza ANOVA/Sobol en la Tabla 7b."
    )
    set_full_par_text(P[127], new_p127)
    record_change("Sección 3.3", "P127", "FON-04", old_p127, new_p127)

    # BLOQUE 2: Ensure Figure 5 caption (P132) explicitly cites Eq. (4) with exponent κ = 1.2
    old_p132 = P[132].text
    new_p132 = (
        "Figura 5. Trayectorias temporales de simulación biofísica 2025–2050 bajo los cuatro regímenes de manejo mediante integración RK4 "
        "(5,000 corridas Monte Carlo por escenario). (A) Cobertura coralina viva media (%); (B) Tasa neta de calcificación biogénica G_net(t) "
        "según la Ec. (4) con exponente alométrico κ = 1.2 (kg CaCO₃ m⁻² año⁻¹). Las bandas sombreadas y barras de error denotan los intervalos de dispersión del 95 %."
    )
    set_full_par_text(P[132], new_p132)
    record_change("Figura 5 (Pie de figura)", "P132", "FON-06 / BLOQUE-2", old_p132, new_p132)

    # Update Tabla 7b (orig_tables[7]) to include both the factorial variants and the Shapley + ANOVA/Sobol decomposition rows
    old_p134, old_p135 = P[134].text, P[135].text
    new_p134 = (
        "Aislamiento factorial 2⁴ de los factores en los que S3 y S4 difieren: cobertura coralina media 2050, balance neto de carbonato "
        "(5,000 corridas Monte Carlo por variante, RK4, Δt = 0.05 años, semilla común 42), atribución aditiva de Shapley e índices de varianza ANOVA/Sobol (S₁ y S_T)."
    )
    set_full_par_text(P[134], new_p134)

    rows_7b_v3 = [
        ["S3 (referencia): g = 0.35; Φ = 0.025; DHW = 0.20; Ω = −0.028", "48.94 % [22.2 %–67.7 %]", "—", "+5.52 [+1.26 a +9.28]", "—"],
        ["S3 con solo g = 0.68", "49.78 % [28.9 %–67.7 %]", "+0.84 [+0.75 a +0.94]", "+5.65 [+2.08 a +9.29]", "+0.13 [+0.11 a +0.14]"],
        ["S3 con solo Φ = 0.030", "49.74 % [24.3 %–68.0 %]", "+0.80 [+0.79 a +0.81]", "+5.64 [+1.49 a +9.37]", "+0.12 [+0.12 a +0.12]"],
        ["S3 con solo DHW = 0.18", "52.97 % [27.9 %–70.0 %]", "+4.03 [+4.01 a +4.06]", "+6.36 [+2.22 a +9.99]", "+0.84 [+0.83 a +0.84]"],
        ["S3 con solo pendiente de Ω = −0.022", "49.94 % [23.4 %–68.3 %]", "+1.00 [+0.99 a +1.01]", "+6.36 [+1.75 a +10.28]", "+0.84 [+0.83 a +0.84]"],
        ["S3 con g = 0.68 y Φ = 0.030 (manejo de S4, clima de S3)", "50.46 % [29.9 %–68.0 %]", "+1.52 [+1.43 a +1.62]", "+5.75 [+2.24 a +9.38]", "+0.23 [+0.21 a +0.24]"],
        ["S4 con DHW = 0.20 (resto igual que S4)", "51.43 % [31.1 %–68.7 %]", "+2.49 [+2.39 a +2.58]", "+6.60 [+2.83 a +10.36]", "+1.08 [+1.07 a +1.09]"],
        ["S4 (referencia): g = 0.68; Φ = 0.030; DHW = 0.18; Ω = −0.022", "55.19 % [35.9 %–71.0 %]", "+6.25 [+6.15 a +6.35]", "+7.48 [+3.75 a +11.11]", "+1.96 [+1.95 a +1.98]"],
        ["Atribución factor g (pastoreo: 0.35 → 0.68)", "Shapley: +0.70 pp (11.3 %)", "Sobol S₁ = 2.90 % (S_T = 2.94 %)", "Shapley: +0.11 kg (5.7 %)", "Sobol S₁ = 0.80 % (S_T = 0.81 %)"],
        ["Atribución factor Φ (trasplante: 0.025 → 0.030)", "Shapley: +0.70 pp (11.2 %)", "Sobol S₁ = 2.87 % (S_T = 2.90 %)", "Shapley: +0.11 kg (5.6 %)", "Sobol S₁ = 0.79 % (S_T = 0.80 %)"],
        ["Atribución factor DHW (pendiente: 0.20 → 0.18)", "Shapley: +3.90 pp (62.3 %)", "Sobol S₁ = 88.91 % (S_T = 88.95 %)", "Shapley: +0.86 kg (43.8 %)", "Sobol S₁ = 47.87 % (S_T = 47.96 %)"],
        ["Atribución factor Ω (pendiente: −0.028 → −0.022)", "Shapley: +0.95 pp (15.2 %)", "Sobol S₁ = 5.26 % (S_T = 5.27 %)", "Shapley: +0.88 kg (44.9 %)", "Sobol S₁ = 50.44 % (S_T = 50.52 %)"],
        ["Interacciones de 2.º a 4.º orden (no aditividad)", "Subaditividad: −0.42 pp", "ANOVA/Sobol: 0.06 %", "Sinergia: +0.03 kg", "ANOVA/Sobol: 0.09 %"],
    ]
    new_tbl7b_el = make_table(
        tmpl_tbl,
        [2968, 1650, 1650, 1650, 1650],
        [
            "Variante / Factor de descomposición (S3 → S4)",
            "Cobertura 2050 (%) [IC 95 %] / Shapley",
            "Δ Cobertura vs. S3 (pp) / Sobol (S₁, S_T)",
            "Balance CaCO₃ (kg m⁻² año⁻¹) / Shapley",
            "Δ Balance vs. S3 / Sobol (S₁, S_T)",
        ],
        rows_7b_v3,
    )
    old_tbl7b_el = orig_tables[7]._tbl
    old_tbl7b_el.addnext(new_tbl7b_el)
    body.remove(old_tbl7b_el)

    new_p135 = (
        "Nota. Las primeras ocho filas reportan variantes clave del diseño factorial completo 2⁴ (16 combinaciones de parámetros) integradas con RK4 "
        "(Δt = 0.05 años, 5,000 corridas Monte Carlo y semilla común 42, diferencias pareadas). Las cinco filas inferiores reportan la atribución "
        "exacta de la brecha total entre S4 y S3 (+6.25 pp y +1.96 kg CaCO₃ m⁻² año⁻¹) mediante valores exactos de Shapley y descomposición de varianza "
        "ANOVA factorial / índices de Sobol de primer orden (S₁) y orden total (S_T) sobre las 16 variantes. Fuente: "
        "07_Scenarios_and_Simulations/s4_factor_isolation.py, results/s4_factor_isolation.csv y results/s4_factor_isolation_anova_sobol.csv."
    )
    set_full_par_text(P[135], new_p135)
    record_change("Tabla 7b y Nota", "P134-P135, Table_7", "FON-04", old_p135, new_p135)

    old_p136 = P[136].text
    new_p136 = (
        "Atribución cuantitativa exacta de la ventaja de S4 sobre S3 (Tabla 7b; Shapley y ANOVA/Sobol): Con la semilla común 42 (5,000 corridas Monte Carlo "
        "pareadas, RK4, Δt = 0.05 años), S4 supera a S3 en +6.25 pp de cobertura coralina 2050 (IC 95 % de la diferencia media pareada: +6.15 a +6.35 pp) "
        "y en +1.96 kg CaCO₃ m⁻² año⁻¹ de balance neto de carbonato (+1.95 a +1.98). Como la respuesta del sistema de EDO presenta ligera subaditividad "
        "(la suma de los cuatro efectos individuales sobre S3 es +6.67 pp en cobertura y +1.93 kg en balance), la atribución exacta se calculó con dos "
        "métodos complementarios sobre las 2⁴ = 16 combinaciones factoriales (results/s4_factor_isolation.csv, results/s4_factor_isolation_shapley.csv y "
        "results/s4_factor_isolation_anova_sobol.csv): (1) Mediante valores exactos de Shapley sobre la brecha aditiva (+6.25 pp y +1.96 kg), en cobertura "
        "la pendiente de DHW aporta +3.90 pp (62.3 %, IC 95 %: 3.87–3.92), la pendiente de Ω aporta +0.95 pp (15.2 %, IC 95 %: 0.94–0.95), el pastoreo (g) "
        "aporta +0.70 pp (11.3 %, IC 95 %: 0.63–0.80) y el trasplante (Φ) aporta +0.70 pp (11.2 %, IC 95 %: 0.69–0.71); en balance de carbonato, la DHW "
        "aporta +0.86 kg (43.8 %), Ω aporta +0.88 kg (44.9 %), el pastoreo +0.11 kg (5.7 %) y el trasplante +0.11 kg (5.6 %). (2) Mediante descomposición "
        "de varianza ANOVA factorial / índices de Sobol de primer orden (S₁) y orden total (S_T), en cobertura coralina 2050 la pendiente de DHW explica el "
        "88.91 % de la varianza factorial (S_T = 88.95 %, efecto principal ANOVA de +3.896 pp), la pendiente de Ω el 5.26 % (S_T = 5.27 %, +0.948 pp), el "
        "pastoreo g el 2.90 % (S_T = 2.94 %, +0.703 pp) y el trasplante Φ el 2.87 % (S_T = 2.90 %, +0.700 pp), mientras que todas las interacciones de "
        "segundo a cuarto orden representan apenas el 0.06 % de la varianza total; en balance neto de carbonato, la pendiente de Ω explica el 50.44 % de "
        "la varianza factorial (S_T = 50.52 %), la DHW el 47.87 % (S_T = 47.96 %), el pastoreo el 0.80 % (S_T = 0.81 %) y el trasplante el 0.79 % "
        "(S_T = 0.80 %), con solo 0.09 % de varianza de interacción. En consecuencia, el manejo local (pastoreo más trasplante) explica exactamente el "
        "22.5 % de la ganancia aditiva de cobertura (5.77 % de la varianza de Sobol) y el 11.3 % de la ganancia de calcificación (1.59 % de la varianza "
        "de Sobol), mientras que el forzamiento climático más benigno asignado a S4 explica el 77.5 % de la brecha de cobertura (94.17 % de la varianza "
        "de Sobol) y el 88.7 % de la brecha de carbonato (98.31 % de la varianza de Sobol). Con el clima de S3, el manejo combinado de S4 (g = 0.68 y "
        "Φ = 0.030) aporta +1.52 pp de cobertura y +0.23 kg de balance, y al simular S4 con la pendiente de DHW de S3 (0.20 °C-sem/año) la cobertura "
        "alcanza 51.43 % (+2.49 pp sobre S3). El pastoreo actúa principalmente suprimiendo las macroalgas: g = 0.68 reduce su cobertura media 2050 de "
        "1.75 % a 0.10 % y elimina la cola de colapso (de 0.30 % a 0.00 %). La atribución es robusta entre semillas pseudoaleatorias (contribución "
        "Shapley de la DHW entre +3.90 y +3.92 pp en las semillas 42 a 45)."
    )
    set_full_par_text(P[136], new_p136)
    record_change("Sección 3.3 (Atribución Tabla 7b)", "P136", "FON-04", old_p136, new_p136)

    # -------------------------------------------------------------------------
    # 5. FASE 1 (FON-01), BLOQUE 1 (Tabla 8 & Footnote) & FASE 3 (FON-05) IN SECTION 3.4
    # -------------------------------------------------------------------------
    # BLOQUE 1: Reconstruct Tabla 8 (orig_tables[8]) with 1 row per station (STN_01..STN_30),
    # 9 explicit columns (ID, Nombre, Región, DHW 95th NOAA Real, DHW 95th Sintético, Diferencia,
    # SRPI Real, SRPI Sintético, Transición de Nivel), zero merges, and explicit footnote separation.
    rows_8_v3 = [
        ["STN_01", "Mesoamerican_Fore_01", "Caribe", "8.274", "1.440", "+6.834", "0.606 (0.576)", "0.756 (0.776)", "Pierde Nivel 1 (pasa a Nivel 2)"],
        ["STN_02", "Mesoamerican_Crest_02", "Caribe", "8.672", "1.453", "+7.219", "0.499 (0.511)", "0.657 (0.722)", "Pasa de Nivel 2 a Nivel 3 [Pierde T1 en var. lineal]"],
        ["STN_03", "Mesoamerican_Back_03", "Caribe", "7.850", "10.931", "−3.081", "0.471 (0.531)", "0.403 (0.442)", "Mantiene Nivel 3"],
        ["STN_04", "Mesoamerican_Lagoon_04", "Caribe", "14.071", "1.433", "+12.638", "0.333 (0.412)", "0.609 (0.720)", "Pasa de Nivel 2 a Nivel 3 [Pierde T1 en var. lineal]"],
        ["STN_05", "Belize_Barrier_05", "Caribe", "9.200", "11.436", "−2.236", "0.472 (0.487)", "0.423 (0.422)", "Mantiene Nivel 3"],
        ["STN_06", "Belize_Atoll_06", "Caribe", "9.723", "1.399", "+8.324", "0.583 (0.539)", "0.765 (0.781)", "Pierde Nivel 1 (pasa a Nivel 3)"],
        ["STN_07", "Cozumel_South_07", "Caribe", "7.971", "1.455", "+6.516", "0.499 (0.523)", "0.642 (0.714)", "Pasa de Nivel 2 a Nivel 3 [Pierde T1 en var. lineal]"],
        ["STN_08", "Cozumel_Shallow_08", "Caribe", "8.179", "12.494", "−4.315", "0.513 (0.548)", "0.418 (0.436)", "Mantiene Nivel 3"],
        ["STN_09", "Roatan_North_09", "Caribe", "6.460", "15.339", "−8.879", "0.609 (0.607)", "0.415 (0.446)", "Pasa de Nivel 3 a Nivel 2"],
        ["STN_10", "Roatan_South_10", "Caribe", "6.840", "1.584", "+5.256", "0.504 (0.567)", "0.619 (0.720)", "Pasa de Nivel 2 a Nivel 3 [Pierde T1 en var. lineal]"],
        ["STN_11", "Florida_Keys_Uppers_11", "Caribe", "4.884", "1.001", "+3.883", "0.644 (0.654)", "0.729 (0.767)", "Pierde Nivel 1 (pasa a Nivel 2)"],
        ["STN_12", "Florida_Keys_Lowers_12", "Caribe", "6.466", "1.376", "+5.090", "0.610 (0.611)", "0.722 (0.759)", "Pierde Nivel 1 (pasa a Nivel 2)"],
        ["STN_13", "GreatBarrier_Northern_13", "Indo-Pacífico", "6.050", "5.507", "+0.543", "0.605 (0.640)", "0.617 (0.656)", "Mantiene Nivel 2"],
        ["STN_14", "GreatBarrier_Central_14", "Indo-Pacífico", "6.432", "7.643", "−1.211", "0.588 (0.622)", "0.562 (0.587)", "Mantiene Nivel 3"],
        ["STN_15", "GreatBarrier_Lagoon_15", "Indo-Pacífico", "6.415", "13.237", "−6.822", "0.502 (0.600)", "0.353 (0.437)", "Mantiene Nivel 3"],
        ["STN_16", "CoralTriangle_RajaAmpat_16", "Indo-Pacífico", "4.361", "10.724", "−6.363", "0.722 (0.736)", "0.583 (0.550)", "Asciende a Nivel 1 (desde Nivel 3)"],
        ["STN_17", "CoralTriangle_Misool_17", "Indo-Pacífico", "n.d. (tierra 5 km)", "11.424", "n.d.", "n.d.", "0.450 (0.460)", "Sin píxel NOAA (Nivel 3 sint.)"],
        ["STN_18", "CoralTriangle_Komodo_18", "Indo-Pacífico", "5.935", "10.779", "−4.844", "0.583 (0.626)", "0.477 (0.484)", "Mantiene Nivel 3"],
        ["STN_19", "CoralTriangle_Sulawesi_19", "Indo-Pacífico", "0.924", "13.957", "−13.033", "0.729 (0.798)", "0.444 (0.474)", "Asciende a Nivel 1 (desde Nivel 3)"],
        ["STN_20", "CoralTriangle_Bali_20", "Indo-Pacífico", "6.740", "13.459", "−6.719", "0.677 (0.663)", "0.530 (0.510)", "Pasa de Nivel 3 a Nivel 2"],
        ["STN_21", "Okinawa_Kerama_21", "Indo-Pacífico", "9.888", "1.526", "+8.362", "0.520 (0.535)", "0.703 (0.779)", "Pierde Nivel 1 (pasa a Nivel 3)"],
        ["STN_22", "Okinawa_Ishigaki_22", "Indo-Pacífico", "8.058", "1.412", "+6.646", "0.533 (0.586)", "0.678 (0.779)", "Pasa de Nivel 2 a Nivel 3 [Pierde T1 en var. lineal]"],
        ["STN_23", "RedSea_Aqaba_23", "Mar Rojo", "6.030", "0.490", "+5.540", "0.563 (0.585)", "0.685 (0.746)", "Pasa de Nivel 2 a Nivel 3 [Pierde T1 en var. lineal]"],
        ["STN_24", "RedSea_Shallow_24", "Mar Rojo", "9.586", "0.842", "+8.744", "0.530 (0.502)", "0.721 (0.757)", "Pierde Nivel 1 (pasa a Nivel 3)"],
        ["STN_25", "RedSea_Farasan_25", "Mar Rojo", "8.090", "0.305", "+7.785", "0.564 (0.551)", "0.734 (0.778)", "Pierde Nivel 1 (pasa a Nivel 3)"],
        ["STN_26", "Seychelles_Mahe_26", "Océano Índico", "4.480", "1.924", "+2.556", "0.709 (0.681)", "0.765 (0.755)", "Mantiene Nivel 1 (Preservado) [Pierde T1 en var. lineal]"],
        ["STN_27", "Maldives_AriAtoll_27", "Océano Índico", "2.058", "14.948", "−12.890", "0.638 (0.686)", "0.356 (0.396)", "Pasa de Nivel 3 a Nivel 2"],
        ["STN_28", "Hawaii_Kaneohe_28", "Pacífico", "0.140", "0.750", "−0.610", "0.772 (0.837)", "0.759 (0.820)", "Mantiene Nivel 1 (Preservado)"],
        ["STN_29", "Hawaii_OahuFore_29", "Pacífico", "0.290", "0.903", "−0.613", "0.653 (0.748)", "0.639 (0.730)", "Mantiene Nivel 2 [Preserva T1 en var. lineal]"],
        ["STN_30", "Palau_RockIslands_30", "Pacífico", "5.377", "0.596", "+4.781", "0.621 (0.665)", "0.726 (0.804)", "Pierde Nivel 1 (pasa a Nivel 2)"],
        ["PROMEDIO", "Global (N = 29 estaciones)", "Global", "6.533 °C-sem", "5.529 °C-sem", "+1.003 °C-sem", "0.581 (0.608)", "0.603 (0.646) [0.598 N=30]", "Ec. 7: 2/10 (20.00 %) │ Var. lineal: 2/17 (11.76 %)"],
    ]
    new_tbl8_el = make_table(
        tmpl_tbl,
        [680, 1950, 900, 880, 880, 840, 1040, 1040, 1640],
        [
            "ID",
            "Nombre de Estación",
            "Región Biogeográfica",
            "DHW 95th NOAA Real (°C-sem)",
            "DHW 95th Sintético (°C-sem)",
            "Diferencia (Real − Sint.)",
            "SRPI Real Ec. 7 (Var. lineal)",
            "SRPI Sintético Ec. 7 (Var. lineal)",
            "Transición de Nivel (Ec. 7 estricta [Var. lineal])",
        ],
        rows_8_v3,
    )
    old_tbl8_el = orig_tables[8]._tbl
    old_tbl8_el.addnext(new_tbl8_el)
    body.remove(old_tbl8_el)

    old_p145 = P[145].text
    new_p145 = (
        "Nota. Datos satelitales operacionales de NOAA OceanWatch (CRW_dhw_v1_0, 2015–2024, stride = 7 días, 522 semanas por estación; "
        "correlación sin calibrar ρ_Spearman = −0.0921, p = 0.6346). "
        "La estación STN_17 (CoralTriangle_Misool_17; DHW 95th sintético = 11.424 °C-sem, SRPI sintético Ec. 7 = 0.450, variante lineal = 0.460, Nivel 3) "
        "queda en la máscara de tierra a 5 km, por lo que los promedios globales comparativos se calculan sobre las N = 29 estaciones con píxel oceánico válido "
        "(según results/noaa_crw_validation.csv y 08_GIS_and_Remote_Sensing/geospatial_outputs/spatial_restoration_priority_ranking.csv). "
        "En las columnas de SRPI se reporta primero el valor de la formulación estricta de la Sección 2.7 y entre paréntesis el valor de la variante lineal "
        "simplificada de 03_Data/fetch_noaa_crw_real_dhw.py (para N = 30 estaciones, la media sintética de la Ec. 7 estricta es 0.598). "
        "Ec. (7) estricta: media real = 0.581 vs. sintética = 0.603 (N = 29). "
        "Variante lineal: media real = 0.608 vs. sintética = 0.646 (N = 29)."
    )
    set_full_par_text(P[145], new_p145)
    record_change("Tabla 8 y Nota (BLOQUE 1 y BLOQUE 3)", "P143-P145, Table_8", "FON-01 / BLOQUE-1 / BLOQUE-3", old_p145, new_p145)

    # Format P[147] (centered correlation display line on pág. 15) in Cambria Math 11 pt with true subscripts
    set_rich_runs(
        P[147],
        [
            ("ρ", None, True, "Cambria Math"),
            ("Spearman", "subscript", False, "Cambria Math"),
            (" = −0.0921   (p = 0.6346, no significativo)   |   ", None, False, "Cambria Math"),
            ("r", None, True, "Cambria Math"),
            ("Pearson", "subscript", False, "Cambria Math"),
            (" = −0.2016   (p = 0.2944)", None, False, "Cambria Math"),
        ],
        base_sz=22,
    )

    old_p148 = P[148].text
    new_p148 = (
        "Este resultado demuestra que el generador sintético paramétrico original (03_Data/build_final_dataset.py), al emplear constantes regionales "
        "uniformes sin calibración local por estación, no reproduce la distribución espacial del estrés térmico extremo observado por satélite en cada "
        "arrecife."
    )
    set_full_par_text(P[148], new_p148)
    record_change("Sección 3.4", "P148", "FON-01", old_p148, new_p148)

    # Insert new paragraph + Figure 6b (`fig_noaa_calibration_v3.png`) right after P148
    cal_para = clone_par(P[148], [
        "Calibración paramétrica por estación frente a NOAA CRW (entrenamiento 2015–2020 y prueba 2021–2024; Figura 6b): "
        "Para evaluar en qué medida una calibración paramétrica local corrige esta discrepancia (01_Data/calibrate_generator_to_noaa.py; "
        "results/noaa_calibration_metrics.csv), dividimos la serie semanal de 10 años de NOAA CRW (522 semanas por estación) y el dataset sintético "
        "en una ventana de entrenamiento (2015–2020; 6 años) y una ventana de prueba fuera de muestra (2021–2024; 4 años). Para cada estación ajustamos "
        "tres parámetros térmicos locales (desplazamiento del umbral climatológico δ_MMM, factor de acumulación térmica s_accum y factor de amplitud de "
        "pulso s_pulse) exclusivamente sobre el período de entrenamiento 2015–2020, y evaluamos el generador con parámetros congelados en el período de "
        "prueba 2021–2024 (N = 29 estaciones marinas con píxel válido; semilla 42, guardando el dataset calibrado en "
        "03_Data/final_dataset_noaa_calibrated.csv). En entrenamiento (2015–2020), la correlación espacial entre estaciones para DHW_95th pasó de "
        "ρ_Spearman = +0.1655 (p = 0.3909) y r_Pearson = +0.1116 (p = 0.5645) antes de calibrar a ρ = +0.9995 (p < 0.0001) y r = +0.9998 (p < 0.0001) "
        "después de calibrar, reduciendo el RMSE de 4.987 a 0.061 °C-semanas, el sesgo medio de −3.862 a −0.020 °C-semanas y elevando la eficiencia de "
        "Kling-Gupta (KGE) de −0.177 a +0.995 (DHW_95th medio de 5.250 frente a 5.270 °C-semanas observados). Al evaluar fuera de muestra en prueba "
        "(2021–2024), el generador calibrado elevó la correlación espacial de DHW_95th de ρ = −0.1520 (p = 0.4312; r = +0.0215, p = 0.9119) a "
        "ρ = +0.6360 (p = 0.0002; r = +0.6238, p = 0.0003), redujo el RMSE a la mitad (de 8.102 a 4.195 °C-semanas), eliminó el sesgo sistemático "
        "(de +4.727 a +0.012 °C-semanas; DHW_95th medio de 9.168 frente a 9.156 °C-semanas en NOAA) y mejoró el KGE de −0.106 a +0.619. En el período "
        "completo 2015–2024, la calibración elevó la concordancia espacial de DHW_95th de ρ_Spearman = −0.0921 (p = 0.6346; r = −0.2016; RMSE = 6.839 °C-semanas; "
        "sesgo = −1.004 °C-semanas; KGE = −0.474) a ρ = +0.7857 (p < 0.0001; r = +0.8795, p < 0.0001; RMSE = 1.803 °C-semanas; sesgo = +0.342 °C-semanas; "
        "KGE = +0.733). No obstante, reportamos dos limitaciones físicas fundamentales: primero, en el propio registro satelital de NOAA CRW existe un "
        "cambio de régimen no estacionario entre 2015–2020 y 2021–2024 (correlación empírica inter-período de DHW_95th de solo ρ = +0.5350, p = 0.0028; "
        "r = +0.6543; sesgo de −3.886 °C-semanas; KGE = +0.303), provocado por las olas de calor extremas de 2023–2024 en el Caribe y el Mar Rojo; "
        "segundo, al evaluar la serie semanal fecha a fecha dentro de cada estación en 2021–2024, aunque el RMSE temporal medio baja de 5.303 a "
        "3.820 °C-semanas y el KGE temporal sube de −0.658 a −0.005, la correlación temporal semanal intra-estación sigue siendo baja "
        "(ρ̄_Spearman = +0.1107; r̄_Pearson = +0.2123), ya que un generador estocástico paramétrico sin asimilación de datos en línea no puede predecir "
        "la fase sinóptica exacta de anomalías térmicas futuras."
    ])

    # Create image paragraph + caption paragraph for Figure 6b (`fig_noaa_calibration_v3.png`)
    fig_p_doc = doc.add_paragraph()
    fig_p_doc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_img = fig_p_doc.add_run()
    run_img.add_picture(FIG_CAL_PATH, width=Inches(6.3))
    fig_p_el = fig_p_doc._p
    body.remove(fig_p_el)  # detach from end of document so we can insert at exact position

    cap_cal_el = clone_par(P[140], [
        "Figura 6b. Calibración por estación del generador térmico DHW frente a la telemetría satelital de 5 km de NOAA Coral Reef Watch "
        "(N = 29 estaciones con píxel marino válido). (a) Ventana de entrenamiento (2015–2020); (b) evaluación fuera de muestra en ventana de prueba "
        "(2021–2024) con parámetros congelados; (c) período completo (2015–2024). Fuente: 01_Data/calibrate_generator_to_noaa.py y "
        "results/noaa_calibration_metrics.csv."
    ])

    anchor_cal = P[148]._p
    for el in (cal_para, fig_p_el, cap_cal_el):
        anchor_cal.addnext(el)
        anchor_cal = el
    keep_together(fig_p_el, cap_cal_el)

    # Update P150 (SRPI sensitivity text) and Tabla 8b (doc.tables[9]) and P153 (Nota of Tabla 8b)
    old_p150 = P[150].text
    new_p150 = (
        "Sensibilidad del SRPI al umbral, a los pesos (±20 %), al remuestreo bootstrap (10,000) y a la exclusión leave-one-station-out (Tabla 8b): "
        "Se ejecutó el análisis exhaustivo de sensibilidad en 08_GIS_and_Remote_Sensing/srpi_sensitivity.py (results/srpi_sensitivity.csv, "
        "results/srpi_bootstrap_10000.csv y results/srpi_loso_sensitivity.csv) evaluando cinco umbrales de Nivel 1 (0.60, 0.65, 0.70, 0.75 y 0.80), "
        "perturbaciones de ±20 % en los pesos 0.35/0.25/0.25/0.15 (renormalizados a suma 1 en 8 configuraciones univariadas, 16 vértices de signo y "
        "10,000 sorteos Monte Carlo), contraste entre fuente térmica sintética base, sintética calibrada en entrenamiento (2015–2020) y satelital "
        "observada de NOAA CRW, 10,000 remuestreos bootstrap no paramétricos sobre las estaciones y validación jackknife dejando una estación fuera "
        "(leave-one-station-out, LOSO, 30 iteraciones). Con pesos base y la Ec. (7) estricta, el número de estaciones de Nivel 1 con el DHW sintético "
        "sin calibrar (N = 30) cae de 18, 13, 10, 4 a 0 entre 0.60 y 0.80; con el DHW_95th observado de NOAA (N = 29), de 13, 6, 4, 1 a 0; y las "
        "estaciones preservadas son 8 (44.44 %), 2 (15.38 %), 2 (20.00 %), 1 (25.00 %) y 0 (n.d.). Al emplear el generador calibrado en entrenamiento "
        "(2015–2020), las estaciones sintéticas de Nivel 1 pasan a 13, 5, 3, 1 y 0, preservándose 10, 4, 3, 1 y 0 frente a NOAA (en 0.70 se preservan "
        "las 3 estaciones identificadas, el 100.0 % de las calibradas y el 75.0 % de las 4 de NOAA). Bajo 10,000 remuestreos bootstrap de estaciones "
        "(semilla 42), el número medio de estaciones preservadas en los umbrales de 0.60 a 0.75 es 8.04 [IC 95 %: 4.0–13.0] (44.67 % [21.4 %–68.4 %]), "
        "2.00 [0.0–5.0] (15.39 % [0.0 %–37.5 %]), 2.01 [0.0–5.0] (20.09 % [0.0 %–50.0 %]) y 0.99 [0.0–3.0] (24.47 % [0.0 %–100.0 %]), y la correlación "
        "de rangos de Spearman entre las puntuaciones SRPI sintéticas y reales de NOAA es ρ_Spearman = −0.1059 [IC 95 % bootstrap: −0.4912 a +0.2968]. En el "
        "análisis leave-one-station-out (LOSO), al retirar una estación a la vez en el umbral de 0.70, las estaciones sintéticas de Nivel 1 varían entre "
        "9 y 10, las de NOAA entre 3 y 4, y las preservadas entre 1 y 2 (11.11 %–22.22 %), mientras que la correlación ρ_Spearman del SRPI oscila entre "
        "−0.1636 y −0.0398. Dos estaciones se sitúan a menos de 0.005 de un umbral (Okinawa_Kerama_21 sintética, 0.703 frente a 0.70, y "
        "Hawaii_OahuFore_29 con NOAA, 0.653 frente a 0.65). Estos resultados confirman que el SRPI es heurístico, no validado en campo, no operacional."
    )
    set_full_par_text(P[150], new_p150)
    record_change("Sección 3.4 (Sensibilidad SRPI)", "P150", "FON-05", old_p150, new_p150)

    # Rebuild Table 8b (doc.tables[9]) to include Bootstrap 10,000 and LOSO columns cleanly!
    rows_8b_v3 = []
    for thr in [0.60, 0.65, 0.70, 0.75, 0.80]:
        r = srpi_strict.loc[thr]
        pres = int(r["Base_Preserved"])
        syn30 = int(r["Base_Tier1_Syn_N30"])
        noaa29 = int(r["Base_Tier1_NOAA_N29"])
        cal29 = int(r["Calibrated_Tier1_Syn_N29"])
        cal_pres = int(r["Calibrated_Preserved_vs_NOAA"])
        pct_str = "n.d." if syn30 == 0 else f"{pres} ({r['Base_Preservation_Pct']:.2f} %)"

        def fmt_rng(lo, hi):
            lo_i, hi_i = int(lo), int(hi)
            return f"{lo_i}" if lo_i == hi_i else f"{lo_i}\u2013{hi_i}"

        w_syn = fmt_rng(r["Weights20_Syn_Min"], r["Weights20_Syn_Max"])
        w_noaa = fmt_rng(r["Weights20_NOAA_Min"], r["Weights20_NOAA_Max"])
        w_pres = fmt_rng(r["Weights20_Preserved_Min"], r["Weights20_Preserved_Max"])

        if syn30 == 0:
            boot_str = "0.00 [0.0\u20130.0] (n.d.)"
        else:
            boot_str = (
                f"{r['Bootstrap10k_Preserved_Mean']:.2f} "
                f"[{r['Bootstrap10k_Preserved_CI_lo']:.0f}\u2013{r['Bootstrap10k_Preserved_CI_hi']:.0f}] "
                f"({r['Bootstrap10k_Preservation_Pct_Mean']:.1f} %)"
            )

        loso_str = (
            f"{fmt_rng(r['LOSO_Syn_Min'], r['LOSO_Syn_Max'])} / "
            f"{fmt_rng(r['LOSO_NOAA_Min'], r['LOSO_NOAA_Max'])} / "
            f"{fmt_rng(r['LOSO_Preserved_Min'], r['LOSO_Preserved_Max'])}"
        )

        rows_8b_v3.append([
            f">= {thr:.2f}",
            f"{syn30} (Cal: {cal29})",
            str(noaa29),
            f"{pct_str} [Cal: {cal_pres}]",
            f"{w_syn} / {w_noaa} / {w_pres}",
            boot_str,
            loso_str,
        ])

    new_tbl8b_el = make_table(
        tmpl_tbl,
        [950, 1350, 1050, 1550, 1550, 1800, 1600],
        [
            "Umbral SRPI",
            "Nivel 1 Sint. N=30 (Cal. N=29)",
            "Nivel 1 NOAA (N=29)",
            "Preservadas Base (% Sint.) [Cal.]",
            "Rango Pesos ±20 % (Sint. / NOAA / Pres.)",
            "Bootstrap 10,000 Preservadas Media [IC 95 %] (%)",
            "LOSO (30 pliegues) (Sint. / NOAA / Pres.)",
        ],
        rows_8b_v3,
    )
    old_tbl8b_el = orig_tables[9]._tbl
    old_tbl8b_el.addnext(new_tbl8b_el)
    body.remove(old_tbl8b_el)
    keep_together(P[133]._p, P[134]._p, new_tbl7b_el)
    keep_together(P[151]._p, P[152]._p, new_tbl8b_el)

    old_p153 = P[153].text
    new_p153 = (
        "Nota. Pesos base 0.35/0.25/0.25/0.15 en la Ec. (7) estricta. 'Cal.' indica el conteo obtenido cuando el subíndice de refugio térmico se "
        "calcula con el generador calibrado por estación en entrenamiento (2015–2020; Fase 1). La quinta columna reporta el rango [mínimo–máximo] de "
        "estaciones (Sintético / NOAA / Preservadas) sobre las 10,024 configuraciones de pesos perturbados en ±20 % y renormalizados a suma 1 (8 "
        "univariadas, 16 esquinas de signo y 10,000 sorteos Monte Carlo, semilla 42). La sexta columna reporta la media e IC 95 % (percentiles 2.5–97.5) "
        "de estaciones preservadas y su porcentaje medio en 10,000 remuestreos bootstrap no paramétricos sobre estaciones (results/srpi_bootstrap_10000.csv). "
        "La séptima columna reporta el rango jackknife leave-one-station-out (LOSO) al excluir una estación por iteración (30 pliegues; "
        "results/srpi_loso_sensitivity.csv). Fuente: 08_GIS_and_Remote_Sensing/srpi_sensitivity.py y results/srpi_sensitivity.csv."
    )
    set_full_par_text(P[153], new_p153)
    record_change("Tabla 8b y Nota", "P152-P153, Table_9", "FON-05", old_p153, new_p153)

    # -------------------------------------------------------------------------
    # 6. DISCUSSION & CONCLUSIONS & DATA AVAILABILITY (P158, P162, P166, P178, P180, P182, P183)
    # -------------------------------------------------------------------------
    old_p158 = P[158].text
    new_p158 = (
        "Nuestras simulaciones decadales aportan evidencia computacional al debate actual entre la conservación marina pasiva tradicional y las "
        "intervenciones activas asistidas (Boström-Einarsson et al., 2020; Kleypas et al., 2021; McLeod et al., 2019; Shaver et al., 2022). Las "
        "reservas marinas de veda total preservan la biomasa de peces herbívoros y regulan así la proliferación de macroalgas competidoras (M), pero "
        "no bastan por sí solas para mitigar las anomalías térmicas tropicales causadas por el forzamiento macroclimático (Klein et al., 2022; "
        "van Hooidonk et al., 2016). La estrategia combinada de S4 (+7.46 kg CaCO₃ m⁻² año⁻¹ y 55.20 % de cobertura) logra el mayor desempeño entre "
        "los escenarios evaluados; el aislamiento factorial completo (Tabla 7b) cuantifica con exactitud que el 22.5 % de la ventaja aditiva de "
        "cobertura de S4 sobre S3 (+1.40 pp de +6.25 pp; 5.77 % de la varianza factorial de Sobol) corresponde al manejo local (pastoreo g = 0.68 "
        "con +0.70 pp y trasplante Φ = 0.030 con +0.70 pp) y el 77.5 % restante (+4.85 pp; 94.17 % de la varianza de Sobol) corresponde al forzamiento "
        "climático más benigno asignado a S4 (pendiente de DHW con +3.90 pp y pendiente de Ω con +0.95 pp), siendo las interacciones de orden superior "
        "despreciables (≤ 0.09 % de la varianza total). Hay que reconocer, además, que bajo calentamiento extremo continuado la adaptación asistida "
        "retarda, pero no impide, la erosión estructural a largo plazo (Webb et al., 2023)."
    )
    set_full_par_text(P[158], new_p158)
    record_change("Sección 4.2", "P158", "FON-04, FON-07", old_p158, new_p158)

    old_p162 = P[162].text
    new_p162 = (
        "Validez de constructo: La principal amenaza era el uso exclusivo de datos sintéticos generados de forma paramétrica. La validación con 10 años "
        "de telemetría real de NOAA CRW (Sección 3.4) confirmó que el generador sin calibrar presenta una correlación espacial nula con los datos "
        "satelitales (ρ_Spearman = −0.0921; p = 0.6346; KGE = −0.474). Al calibrar los parámetros térmicos por estación en entrenamiento (2015–2020) y evaluar "
        "en prueba (2021–2024), la concordancia espacial de DHW_95th mejora sustancialmente (ρ = +0.6360 en prueba y ρ = +0.7857 en 2015–2024; "
        "KGE = +0.619 y +0.733), pero la correlación temporal semanal intra-estación permanece baja (ρ̄ = +0.1107 en prueba) debido a la naturaleza "
        "estocástica no asimilativa del generador y al cambio de régimen térmico de 2023–2024. Además, el desbalance extremo de clases (clase Medio: "
        "1.24 %) obligó a recurrir a la ponderación de clases para corregir la insensibilidad del modelo canónico (Tabla 6)."
    )
    set_full_par_text(P[162], new_p162)
    record_change("Sección 4.4 (Validez de constructo)", "P162", "FON-01", old_p162, new_p162)

    old_p166 = P[166].text
    new_p166 = (
        "Validez del índice SRPI: Declaramos explícitamente que el SRPI es un índice heurístico, no validado en campo, no operacional: sus pesos "
        "(0.35/0.25/0.25/0.15), sus normalizaciones (16.0 °C-semanas para el refugio térmico y 50.0 % para la cobertura histórica) y su umbral de "
        "Nivel 1 (0.70) son decisiones heurísticas de diseño multicriterio y no parámetros estimados empíricamente, y sus prioridades no se han "
        "contrastado con tasas reales de supervivencia, reclutamiento ni acreción posrestauración en campo. El análisis de sensibilidad (Tabla 8b) "
        "demuestra que el número de estaciones de Nivel 1 depende fuertemente del umbral (de 18 a 0 entre 0.60 y 0.80), de los pesos (rango de 4 a 13 "
        "en 0.70 bajo variaciones de ±20 %), del muestreo de estaciones (IC 95 % bootstrap de 0 a 5 estaciones preservadas en 0.70) y de estaciones "
        "individuales cercanas al corte (rango LOSO de 1 a 2 estaciones preservadas en 0.70). Su ranking debe interpretarse únicamente como un "
        "ejercicio metodológico exploratorio y no como una zonificación operativa para asignar fondos."
    )
    set_full_par_text(P[166], new_p166)
    record_change("Sección 4.4 (Validez SRPI)", "P166", "FON-05", old_p166, new_p166)

    old_p178 = P[178].text
    new_p178 = (
        "En tercer lugar, las proyecciones decadales 2025–2050 indican que la combinación de trasplante asistido y protección estricta en AMP "
        "(Escenario 4, mejor escenario simulado) sostiene balances positivos de carbonato (+7.46 kg CaCO₃ m⁻² año⁻¹ y 55.20 % de cobertura), frente "
        "al colapso funcional del escenario sin mitigación (0.69 % de cobertura coralina). El aislamiento factorial (Tabla 7b) demuestra que el 22.5 % "
        "de la ventaja aditiva de cobertura de S4 sobre S3 (+1.40 pp de +6.25 pp; 5.77 % de la varianza factorial de Sobol) corresponde al manejo "
        "(pastoreo +0.70 pp y trasplante +0.70 pp) y el 77.5 % (+4.85 pp; 94.17 % de la varianza de Sobol) al forzamiento climático menos severo "
        "asignado a S4. Además, la validación con 10 años de telemetría real de NOAA CRW (2015–2024) mostró una correlación nula con los datos "
        "sintéticos sin calibrar (ρ_Spearman = −0.0921; p = 0.6346) y redujo las estaciones de Nivel 1 del SRPI de 10 a 4 (20.00 % de preservación en 0.70; "
        "15.38 %–44.44 % entre 0.60 y 0.75; media bootstrap 10,000 de 2.01 [IC 95 %: 0.0–5.0] y rango leave-one-station-out de 1–2 estaciones). "
        "Aunque la calibración paramétrica por estación en 2015–2020 mejora la correlación espacial de DHW_95th en la ventana de prueba 2021–2024 "
        "(ρ = +0.6360, p = 0.0002; RMSE = 4.195 °C-semanas; KGE = +0.619), la correlación temporal semanal intra-estación sigue siendo baja "
        "(ρ̄ = +0.1107; KGE = −0.005) sin asimilación de datos en línea. En conclusión, el SRPI es un índice heurístico, no validado en campo, no "
        "operacional, y el gemelo digital debe acoplarse a flujos continuos de observación física antes de cualquier aplicación en políticas públicas."
    )
    set_full_par_text(P[178], new_p178)
    record_change("Sección 5 (Conclusiones)", "P178", "FON-01, FON-04, FON-05", old_p178, new_p178)

    doi_file = os.path.join(RESULTS_DIR, "zenodo_v210_doi.txt")
    v210_doi = os.environ.get("ZENODO_V210_DOI", "10.5281/zenodo.23905108")
    if os.path.exists(doi_file):
        with open(doi_file, "r", encoding="utf-8") as dfp:
            val = dfp.read().strip()
            if val:
                v210_doi = val

    old_p180, old_p182, old_p183 = P[180].text, P[182].text, P[183].text
    new_p180 = (
        "Todos los artefactos computacionales de esta investigación se publican bajo los principios FAIR. Cada cifra del manuscrito se traza a su "
        "archivo de origen y script generador mediante results/manuscript_numbers.json y consistency_report.md. Los análisis de calibración con NOAA CRW "
        "(Fase 1), aislamiento factorial S4 vs. S3 (Fase 2, Tabla 7b), sensibilidad ampliada del SRPI (Fase 3, Tabla 8b) y auditoría de referencias (Fase 5) "
        "se ejecutan con 01_Data/calibrate_generator_to_noaa.py, 07_Scenarios_and_Simulations/s4_factor_isolation.py, "
        "08_GIS_and_Remote_Sensing/srpi_sensitivity.py y 09_Results/audit_references.py, integrados en python run_all.py (23 etapas) y verificados mediante "
        "verify_release.sh y SHA256SUMS en el release v2.1.0."
    )
    new_p182 = (
        f"• Depósito inmutable en Zenodo: El release v2.1.0 de GitHub (https://github.com/HrSly11/CoralTwin-DT/releases/tag/v2.1.0) está archivado "
        f"automáticamente en Zenodo; Concept DOI: 10.5281/zenodo.23789586; DOI de la versión v2.1.0: {v210_doi}. "
        f"La integración Zenodo–GitHub archiva el snapshot del release; el contenido archivado coincide con el commit etiquetado v2.1.0."
    )
    new_p183 = (
        "• Contenedor Docker y pipeline reproducible: El entorno reproducible completo (fijado por digest SHA-256 en Dockerfile y verificado con "
        "verify_release.sh, SHA256SUMS y consistency_report.md) se ejecuta de extremo a extremo con el comando python run_all.py (23 etapas verificadas en "
        "results/pipeline_execution_log_v4.json)."
    )
    set_full_par_text(P[180], new_p180)
    set_full_par_text(P[182], new_p182)
    set_full_par_text(P[183], new_p183)
    record_change("Sección 6 (Disponibilidad y Reproducibilidad — BLOQUE 5 y 6)", "P180, P182, P183", "FASE 7 / BLOQUE-5 / BLOQUE-6", old_p182, new_p182)

    # Apply keepNext, cantSplit, and tblHeader pagination guards to all 11 tables and captions
    enforce_table_integrity(doc)
    upgrade_typography_and_math_runs(doc, skip_pars={P[44]._p, P[50]._p, P[54]._p, P[55]._p, P[147]._p})
    doc.save(DST_DOCX)
    patch_docx_media_images(DST_DOCX)
    print(f"Saved v3 manuscript to: {DST_DOCX}")

    # Write trackchanges report
    md_lines = [
        "# Reporte de Control de Cambios (Track-Changes Report): `Grupo28B_RodriguezSandoval_HarrySly_v3.docx`",
        "",
        "- **Documento de entrada (intacto):** `Grupo28B_RodriguezSandoval_HarrySly_corregido_v2.docx` (y `Grupo28B_RodriguezSandoval_HarrySly_corregido.docx`)",
        "- **Documento de salida generado:** `Grupo28B_RodriguezSandoval_HarrySly_v3.docx`",
        "- **Trazabilidad numérica:** `results/manuscript_numbers.json`",
        "",
        "## Resumen de Intervenciones por Fase y FON",
        "",
        "| Sección | Párrafo / Tabla | FON Cerrado | Resumen del Cambio |",
        "| :--- | :--- | :--- | :--- |",
        "| Resumen | `P006` | `FON-01`, `FON-04`, `FON-05`, `FON-08` | Incorpora resultados de calibración NOAA train/test (2015–2020 / 2021–2024), descomposición factorial Shapley y Sobol de S4 vs. S3, bootstrap 10,000 y LOSO del SRPI, resolución de 16 variables y declaración explícita: *«SRPI heurístico, no validado en campo, no operacional»*. |",
        "| Sección 2.3.1 | `P042`, `P044`, `P045` | `FON-01`, `FON-06` | Formatea Ec. (2) con límites de sumatoria $i=0\\dots 83$, función indicadora $\\mathbb{I}[\\text{HotSpot}(t-i) \\ge 1.0\\,^\\circ\\text{C}]$, factor $1/7$ y unidades $[\\text{°C-semanas}]$. Documenta la calibración por estación en `01_Data/calibrate_generator_to_noaa.py`. |",
        "| Sección 2.3.2 | `P050`, `P051` | `FON-06` | Alinea la Ec. (4) con `simulation_engine.py` e identifica explícitamente $G_{\\max}=12.5$, $\\Omega_0=1.0$, $\\Omega_{\\text{ref}}=2.8$, $\\kappa=1.2$, $\\lambda_{\\text{DHW}}=0.06$, $C(t)/C_0$ y $E_{\\text{bioerosion}}=1.85\\,\\text{kg CaCO}_3\\,\\text{m}^{-2}\\,\\text{año}^{-1}$. |",
        "| Sección 2.3.3 | `P054`–`P056`, `Tabla 1b` | `FON-06` | Alinea Ecs. (5)–(6) con el código ejecutado (incluyendo el factor de espacio libre $(1-C-M)$ en $\\Phi_{\\text{restoration}}$ y $\\varepsilon=10^{-6}$) e inserta la nueva **Tabla 1b** de símbolos, definiciones, valores y unidades para las Ecs. (1)–(7). |",
        "| Sección 2.4 | `P069` | `FON-08` | Desglosa las 16 variables del régimen `Regime_0_Leaked_16`: 10 ambientales primarias + 2 ambientales derivadas colineales (`HotSpot_degC`, `Kd_490_m_inv`) + 4 bentónicas post-objetivo (`Shannon_Diversity_H`, `Structural_Rugosity`, `Live_Coral_Cover_Pct`, `Macroalgae_Cover_Pct`). |",
        "| Sección 2.7 | `P087` | `FON-06` | explicita las cotas y constantes de normalización de los cuatro subíndices de la Ec. (7). |",
        "| Sección 3.1 | `P102`, `Tabla 5` | `FON-08` | Elimina la etiqueta `[VERIFICAR]` y especifica las 2 variables derivadas colineales (`HotSpot_degC`, `Kd_490_m_inv`) que completan las 16 variables de la Tabla 5. |",
        "| Sección 3.3 | `P127`, `P136`, `Tabla 7b` | `FON-04` | Sustituye cualquier expresión de atribución indeterminada por la descomposición exacta mediante diseño factorial $2^4$, valores de Shapley y ANOVA factorial / índices de Sobol de primer orden ($S_1$) y orden total ($S_T$). |",
        "| Sección 3.4 | `P148`, `Figura 6b`, `P150`, `Tabla 8b`, `P153` | `FON-01`, `FON-05` | Añade los resultados completos de calibración NOAA (train 2015–2020, test 2021–2024 y período completo 2015–2024: Spearman, Pearson, RMSE, sesgo, KGE y DHW_95th antes/después) e inserta la **Figura 6b** (`fig_noaa_calibration_v3.png`). Amplía la **Tabla 8b** con el generador calibrado, bootstrap 10,000 y validación leave-one-station-out (LOSO). |",
        "| Sección 4.2, 4.4, 5, 6 | `P158`, `P162`, `P166`, `P178`, `P180`–`P183` | `FON-01`, `FON-04`, `FON-05`, `FON-07` | Actualiza Discusión y Conclusiones con atribución cuantitativa exacta (Shapley y Sobol), corrige `pantropicales` → `tropicales`, declara que el SRPI es *«heurístico, no validado en campo, no operacional»*, y documenta el release `v2.0.0`, `SHA256SUMS` y `verify_release.sh`. |",
        "",
        "---",
        "",
        "## Detalle de Fragmentos Modificados (Antes vs. Después)",
        "",
    ]
    for item in track_changes:
        md_lines.extend([
            f"### {item['section']} (`{item['para_id']}`) — Cierra: `{item['fon']}`",
            "",
            "**Texto en v2 (`corregido_v2.docx`):**",
            f"> {item['old']}",
            "",
            "**Texto en v3 (`v3.docx`):**",
            f"> {item['new']}",
            "",
        ])

    with open(TRACK_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")
    print(f"Saved track-changes report to: {TRACK_MD}")


if __name__ == "__main__":
    main()
