"""
CoralTwin-DT: Automated Scientific Manuscript Formatter (PDF Only)
==================================================================
Compiles manuscript.md into a publication-formatted PDF document.
Note: Direct .docx generation/modification is strictly disabled to preserve
existing Word documents untouched.

Author: CoralTwin-DT Publication Lead
License: MIT
"""

import os
from fpdf import FPDF

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANUSCRIPT_MD = os.path.join(BASE_DIR, "manuscript", "manuscript.md")
PDF_OUT = os.path.join(BASE_DIR, "manuscript", "article.pdf")


class PDFReport(FPDF):
    def header(self):
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "Global Change Biology | CoralTwin-DT Research Consortium", 0, 1, "R")

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")


def generate_pdf():
    print(f"Generating formatted PDF: {PDF_OUT}...")
    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)

    with open(MANUSCRIPT_MD, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line_str = line.strip().encode("latin-1", "replace").decode("latin-1")
        if not line_str:
            pdf.ln(2)
            continue

        if line_str.startswith("# "):
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(27, 73, 101)
            pdf.multi_cell(0, 7, line_str[2:])
            pdf.ln(2)
        elif line_str.startswith("## "):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(43, 108, 176)
            pdf.multi_cell(0, 6, line_str[3:])
            pdf.ln(1)
        elif line_str.startswith("### "):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 5, line_str[4:])
            pdf.ln(1)
        else:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(0, 4.5, line_str)
            pdf.ln(1)

    pdf.output(PDF_OUT)
    print("PDF successfully generated (DOCX files left untouched).")


if __name__ == "__main__":
    generate_pdf()
