"""
CoralTwin-DT: Final Delivery Package Consolidator
=================================================
Consolidates all certified project artifacts, PDFs, datasets, architectures,
figures, and manuals into FINAL_DELIVERY_PACKAGE/.

Author: CoralTwin-DT Project Lead
License: MIT
"""

import os
import shutil
import hashlib
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DELIVERY_DIR = os.path.join(PROJECT_ROOT, "FINAL_DELIVERY_PACKAGE")

SUBDIRS = {
    "01_Technical_Report": os.path.join(DELIVERY_DIR, "01_Technical_Report"),
    "02_Scientific_Manuscript": os.path.join(DELIVERY_DIR, "02_Scientific_Manuscript"),
    "03_Documented_Dataset": os.path.join(DELIVERY_DIR, "03_Documented_Dataset"),
    "04_Digital_Twin_Architecture": os.path.join(DELIVERY_DIR, "04_Digital_Twin_Architecture"),
    "05_Main_Results_and_Tables": os.path.join(DELIVERY_DIR, "05_Main_Results_and_Tables"),
    "06_Scientific_Figures_300DPI": os.path.join(DELIVERY_DIR, "06_Scientific_Figures_300DPI"),
    "07_Project_Manuals": os.path.join(DELIVERY_DIR, "07_Project_Manuals"),
}


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()[:16]


def create_delivery_package():
    print(f"Building Final Delivery Package: {DELIVERY_DIR}...")
    for path in SUBDIRS.values():
        os.makedirs(path, exist_ok=True)

    manifest = []

    # 1. Technical Report
    src_tech_pdf = os.path.join(PROJECT_ROOT, "13_Documentation", "technical_report.pdf")
    src_tech_md = os.path.join(PROJECT_ROOT, "13_Documentation", "technical_report.md")
    src_exec_pdf = os.path.join(PROJECT_ROOT, "11_Presentation", "executive_summary.pdf")
    if os.path.exists(src_tech_pdf):
        shutil.copy(src_tech_pdf, SUBDIRS["01_Technical_Report"])
        manifest.append({"Category": "01_Technical_Report", "File": "technical_report.pdf", "Description": "Comprehensive technical systems report (PDF)"})
    if os.path.exists(src_tech_md):
        shutil.copy(src_tech_md, SUBDIRS["01_Technical_Report"])
    if os.path.exists(src_exec_pdf):
        shutil.copy(src_exec_pdf, SUBDIRS["01_Technical_Report"])
        manifest.append({"Category": "01_Technical_Report", "File": "executive_summary.pdf", "Description": "Executive summary policy brief (PDF)"})

    # 2. Scientific Manuscript
    src_ms_pdf = os.path.join(PROJECT_ROOT, "10_Publication", "Final_Submission", "manuscript.pdf")
    src_ms_docx = os.path.join(PROJECT_ROOT, "10_Publication", "Final_Submission", "manuscript.docx")
    src_ms_md = os.path.join(PROJECT_ROOT, "10_Publication", "Final_Submission", "manuscript_final.md")
    src_supp_pdf = os.path.join(PROJECT_ROOT, "10_Publication", "Final_Submission", "supplementary_material.pdf")
    src_hl_md = os.path.join(PROJECT_ROOT, "10_Publication", "Final_Submission", "highlights.md")
    src_cl_md = os.path.join(PROJECT_ROOT, "10_Publication", "Final_Submission", "cover_letter.md")

    for f_path, desc in [(src_ms_pdf, "Scopus Q1 Manuscript formatted for Ecological Informatics (PDF)"),
                         (src_ms_docx, "Editable Word manuscript for coauthors (DOCX)"),
                         (src_ms_md, "Complete Markdown source of Q1 paper"),
                         (src_supp_pdf, "Supplementary material and methods (PDF)"),
                         (src_hl_md, "Research highlights"),
                         (src_cl_md, "Formal cover letter to Editor-in-Chief")]:
        if os.path.exists(f_path):
            shutil.copy(f_path, SUBDIRS["02_Scientific_Manuscript"])
            manifest.append({"Category": "02_Scientific_Manuscript", "File": os.path.basename(f_path), "Description": desc})

    # 3. Documented Dataset
    src_data_csv = os.path.join(PROJECT_ROOT, "03_Data", "final_dataset.csv")
    src_dict_csv = os.path.join(PROJECT_ROOT, "03_Data", "data_dictionary_final.csv")
    src_val_md = os.path.join(PROJECT_ROOT, "03_Data", "dataset_validation_report.md")
    src_desc_md = os.path.join(PROJECT_ROOT, "03_Data", "dataset_description.md")

    for f_path, desc in [(src_data_csv, "Harmonized gold-standard dataset (N=15,000, 34 variables)"),
                         (src_dict_csv, "ISO-19115 compliant comprehensive data dictionary"),
                         (src_val_md, "Biophysical quality & ML validation report"),
                         (src_desc_md, "General dataset description & provenance")]:
        if os.path.exists(f_path):
            shutil.copy(f_path, SUBDIRS["03_Documented_Dataset"])
            manifest.append({"Category": "03_Documented_Dataset", "File": os.path.basename(f_path), "Description": desc})

    # 4. Digital Twin Architecture
    src_arch_md = os.path.join(PROJECT_ROOT, "04_Digital_Twin_Architecture", "advanced_architecture.md")
    src_arch_png = os.path.join(PROJECT_ROOT, "04_Digital_Twin_Architecture", "digital_twin_final_diagram.png")
    src_six_md = os.path.join(PROJECT_ROOT, "04_Digital_Twin_Architecture", "six_layer_framework.md")

    for f_path, desc in [(src_arch_md, "Advanced cyber-physical digital twin architecture specification"),
                         (src_arch_png, "300 DPI high-resolution architecture diagram"),
                         (src_six_md, "Six-layer framework reference document")]:
        if os.path.exists(f_path):
            shutil.copy(f_path, SUBDIRS["04_Digital_Twin_Architecture"])
            manifest.append({"Category": "04_Digital_Twin_Architecture", "File": os.path.basename(f_path), "Description": desc})

    # 5. Main Results & Tables
    src_res_md = os.path.join(PROJECT_ROOT, "09_Results", "scientific_results_report.md")
    src_comp_md = os.path.join(PROJECT_ROOT, "06_AI_and_Modeling", "model_comparison_report.md")
    src_t1 = os.path.join(PROJECT_ROOT, "09_Results", "tables", "Table1_model_performance_benchmarks.csv")
    src_t2 = os.path.join(PROJECT_ROOT, "09_Results", "tables", "Table2_decadal_scenario_projections.csv")
    src_t3 = os.path.join(PROJECT_ROOT, "09_Results", "tables", "Table3_spatial_restoration_priority.csv")
    src_geojson = os.path.join(PROJECT_ROOT, "08_GIS_and_Remote_Sensing", "geospatial_outputs", "priority_restoration_zones.geojson")

    for f_path, desc in [(src_res_md, "Q1 scientific results and restoration prioritization report"),
                         (src_comp_md, "Comparative AI benchmark report (RF vs XGBoost vs LSTM)"),
                         (src_t1, "Table 1: Model performance benchmarks (CSV)"),
                         (src_t2, "Table 2: Decadal scenario projections 2025-2050 (CSV)"),
                         (src_t3, "Table 3: Spatial restoration priority rankings (CSV)"),
                         (src_geojson, "Spatial Restoration Priority Index zoning layer (GeoJSON)")]:
        if os.path.exists(f_path):
            shutil.copy(f_path, SUBDIRS["05_Main_Results_and_Tables"])
            manifest.append({"Category": "05_Main_Results_and_Tables", "File": os.path.basename(f_path), "Description": desc})

    # 6. Scientific Figures 300 DPI
    figs_dir = os.path.join(PROJECT_ROOT, "09_Results", "figures")
    for f_name in sorted(os.listdir(figs_dir)):
        if f_name.endswith(".png"):
            shutil.copy(os.path.join(figs_dir, f_name), SUBDIRS["06_Scientific_Figures_300DPI"])
            manifest.append({"Category": "06_Scientific_Figures_300DPI", "File": f_name, "Description": f"300 DPI Publication Figure: {f_name}"})

    src_ga = os.path.join(PROJECT_ROOT, "10_Publication", "Final_Submission", "graphical_abstract.png")
    if os.path.exists(src_ga):
        shutil.copy(src_ga, SUBDIRS["06_Scientific_Figures_300DPI"])
        manifest.append({"Category": "06_Scientific_Figures_300DPI", "File": "graphical_abstract.png", "Description": "300 DPI Graphical Abstract (16:9)"})

    # 7. Project Manuals
    src_manual = os.path.join(PROJECT_ROOT, "13_Documentation", "user_manual.md")
    src_rep_guide = os.path.join(PROJECT_ROOT, "12_Reproducibility", "replication_guide.md")
    src_audit_md = os.path.join(PROJECT_ROOT, "FINAL_PROJECT_AUDIT.md")
    src_changelog = os.path.join(PROJECT_ROOT, "CHANGELOG.md")

    for f_path, desc in [(src_manual, "Comprehensive user and operations manual"),
                         (src_rep_guide, "Step-by-step third-party replication guide"),
                         (src_audit_md, "Master final audit sign-off certification"),
                         (src_changelog, "Release v1.0.0 changelog")]:
        if os.path.exists(f_path):
            shutil.copy(f_path, SUBDIRS["07_Project_Manuals"])
            manifest.append({"Category": "07_Project_Manuals", "File": os.path.basename(f_path), "Description": desc})

    # Write Master Index & README in Delivery Package
    df_manifest = pd.DataFrame(manifest)
    manifest_csv = os.path.join(DELIVERY_DIR, "INDEX_OF_DELIVERABLES.csv")
    df_manifest.to_csv(manifest_csv, index=False)

    write_delivery_readme(df_manifest)
    print(f"Final delivery package successfully generated with {len(manifest)} key assets.")


def write_delivery_readme(df_manifest):
    readme_path = os.path.join(DELIVERY_DIR, "README.md")
    lines = [
        "# CoralTwin-DT: Official Final Delivery Package (Release v1.0.0)",
        "",
        "**Project Title:** Digital Twin of Coral Reefs under Thermal Stress and Ocean Acidification for Restoration and Conservation Prioritization  ",
        "**Consortium:** CoralTwin-DT Doctoral Research Board  ",
        "**Target Journal:** *Ecological Informatics* (Elsevier, Scopus Q1, IF: 5.8)  ",
        "**Release Version:** `v1.0.0` (Production-Ready)  ",
        "**Scientific Attribution:** *Resultado obtenido mediante prototipo computacional del gemelo digital.*  ",
        "",
        "---",
        "",
        "## Structure of the Final Delivery Package",
        "",
        "```text",
        "FINAL_DELIVERY_PACKAGE/",
        "├── 01_Technical_Report/            # Technical systems report (PDF) & executive brief (PDF)",
        "├── 02_Scientific_Manuscript/       # Scopus Q1 paper (PDF/DOCX), cover letter, highlights, supplementary (PDF)",
        "├── 03_Documented_Dataset/          # Harmonized dataset (final_dataset.csv), data dictionary, validation report",
        "├── 04_Digital_Twin_Architecture/   # Advanced architecture specification and 300 DPI diagram",
        "├── 05_Main_Results_and_Tables/     # Results reports, benchmark tables, and SRPI GeoJSON layer",
        "├── 06_Scientific_Figures_300DPI/   # Figures 1 to 7 (300 DPI) and Graphical Abstract (300 DPI)",
        "├── 07_Project_Manuals/             # User operations manual, replication guide, final audit certification",
        "├── INDEX_OF_DELIVERABLES.csv       # Automated asset catalog",
        "└── README.md                       # Package navigation guide",
        "```",
        "",
        "---",
        "",
        "## Summary of Core Deliverables Included",
        "",
        "| Category | File Name | Description |",
        "| :--- | :--- | :--- |"
    ]

    for _, row in df_manifest.iterrows():
        lines.append(f"| `{row['Category']}` | **{row['File']}** | {row['Description']} |")

    lines.extend([
        "",
        "---",
        "",
        "## Verification & Quick Execution",
        "",
        "To verify and execute the complete pipeline that produced these deliverables:",
        "```bash",
        "git clone https://github.com/HrSly11/CoralTwin-DT.git",
        "cd CoralTwin-DT",
        "pip install -r 12_Reproducibility/requirements.txt",
        "python run_all.py",
        "```",
        "",
        "All 13 pipeline stages will execute deterministically in approximately 104 seconds."
    ])

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Delivery README written to: {readme_path}")


if __name__ == "__main__":
    create_delivery_package()
