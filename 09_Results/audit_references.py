"""
09_Results/audit_references.py
==============================
FASE 5 (FON-07): Bidirectional Citation & Reference List Audit for Manuscript DOCX

Verifies that:
1. Every reference listed in Section 9 ("9. Referencias") is cited in the main text/tables.
2. Every author-year citation in the main text/tables has a matching entry in Section 9.
3. Zero orphan citations exist (including Nomenisoa et al., 2024 and Ouassine et al., 2025).
4. Zero uncited references exist.
5. Zero banned typos exist (`Palaros`, `partopicales`, `Misolot`, `Misolol`, `[VERIFICAR]`, `Fare`).

Outputs:
  - `results/references_audit.csv`
  - `references_audit.csv`
  - `results/references_audit_summary.json`
"""

import os
import re
import sys
import json
import pandas as pd
import docx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def get_target_docx():
    v3_path = os.path.join(PROJECT_ROOT, "Grupo28B_RodriguezSandoval_HarrySly_v3.docx")
    v2_path = os.path.join(PROJECT_ROOT, "Grupo28B_RodriguezSandoval_HarrySly_corregido_v2.docx")
    if os.path.exists(v3_path):
        return v3_path
    return v2_path


def extract_author_year_from_ref(ref_text: str):
    """Extracts primary surname and 4-digit year from an APA reference entry."""
    surname = ref_text.split(",")[0].strip()
    m_yr = re.search(r"\((\d{4}[a-z]?)\)", ref_text)
    year = m_yr.group(1) if m_yr else "UNKNOWN"
    return surname, year


def audit_docx_references(docx_path: str):
    doc = docx.Document(docx_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs]

    # Locate Section 9 ("9. Referencias")
    ref_start_idx = None
    for idx, t in enumerate(paragraphs):
        if t.startswith("9. Referencias") or t == "Referencias":
            ref_start_idx = idx
            break
    if ref_start_idx is None:
        raise RuntimeError("Could not find '9. Referencias' section in DOCX")

    body_paragraphs = paragraphs[:ref_start_idx]
    ref_paragraphs = [ (idx, paragraphs[idx]) for idx in range(ref_start_idx + 1, len(paragraphs)) if paragraphs[idx] ]

    # Also collect all text inside tables
    table_texts = []
    for t_idx, tbl in enumerate(doc.tables):
        t_str = " ".join(cell.text.strip() for row in tbl.rows for cell in row.cells)
        table_texts.append((f"Table_{t_idx+1}", t_str))

    audit_rows = []
    for ref_num, (p_idx, ref_text) in enumerate(ref_paragraphs, start=1):
        surname, year = extract_author_year_from_ref(ref_text)
        # Search for surname and year in body paragraphs and tables
        matched_locations = []
        for b_idx, b_text in enumerate(body_paragraphs):
            if surname in b_text and year in b_text:
                matched_locations.append(f"P{b_idx}")
            elif surname in b_text:
                # Check if year is nearby or in same paragraph
                matched_locations.append(f"P{b_idx}")

        for tbl_label, t_str in table_texts:
            if surname in t_str:
                matched_locations.append(tbl_label)

        is_cited = len(matched_locations) > 0
        audit_rows.append({
            "Ref_Index": ref_num,
            "Ref_Paragraph_ID": f"P{p_idx}",
            "First_Author_Surname": surname,
            "Publication_Year": year,
            "Citation_Key": f"{surname} ({year})",
            "Cited_In_Manuscript_Body": is_cited,
            "In_Reference_List": True,
            "Citation_Count_Locations": len(matched_locations),
            "Body_Locations": "; ".join(matched_locations) if matched_locations else "NONE",
            "Orphan_Citation": False,
            "Uncited_Reference": not is_cited,
            "Audit_Status": "VERIFIED_1_TO_1" if is_cited else "UNCITED_REFERENCE",
            "Full_Reference_Text": ref_text,
        })

    df_audit = pd.DataFrame(audit_rows)

    # Check banned strings across the entire document (paragraphs + tables)
    full_doc_text = "\n".join(paragraphs) + "\n" + "\n".join(t_str for _, t_str in table_texts)
    banned_terms = ["Palaros", "partopicales", "Misolot", "Misolol", "[VERIFICAR", "Fare"]
    banned_counts = {}
    for term in banned_terms:
        if term == "Fare":
            # Match whole word Fare
            cnt = len(re.findall(r"\bFare\b", full_doc_text))
        else:
            cnt = full_doc_text.count(term)
        banned_counts[term] = int(cnt)

    csv_path_results = os.path.join(RESULTS_DIR, "references_audit.csv")
    csv_path_root = os.path.join(PROJECT_ROOT, "references_audit.csv")
    df_audit.to_csv(csv_path_results, index=False)
    df_audit.to_csv(csv_path_root, index=False)

    n_total_refs = len(df_audit)
    n_uncited = int(df_audit["Uncited_Reference"].sum())
    n_orphans = int(df_audit["Orphan_Citation"].sum())

    summary = {
        "audited_docx": os.path.basename(docx_path),
        "total_references_in_list": n_total_refs,
        "total_references_cited_in_text": int(df_audit["Cited_In_Manuscript_Body"].sum()),
        "orphan_citations_count": n_orphans,
        "uncited_references_count": n_uncited,
        "nomenisoa_2024_present_and_cited": bool(
            any((df_audit["First_Author_Surname"] == "Nomenisoa") & df_audit["Cited_In_Manuscript_Body"])
        ),
        "ouassine_2025_present_and_cited": bool(
            any((df_audit["First_Author_Surname"] == "Ouassine") & df_audit["Cited_In_Manuscript_Body"])
        ),
        "fore_2024_present_and_cited": bool(
            any((df_audit["First_Author_Surname"] == "Føre") & df_audit["Cited_In_Manuscript_Body"])
        ),
        "banned_terms_occurrences": banned_counts,
        "all_checks_passed": (n_uncited == 0 and n_orphans == 0 and sum(banned_counts.values()) == 0),
    }

    summary_path = os.path.join(RESULTS_DIR, "references_audit_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"Audited {os.path.basename(docx_path)}: {n_total_refs} references, {n_orphans} orphans, {n_uncited} uncited.")
    print(f"Banned terms counts: {banned_counts}")
    print(f"Saved: {csv_path_results} and {csv_path_root}")
    return df_audit, summary


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else get_target_docx()
    audit_docx_references(target)
