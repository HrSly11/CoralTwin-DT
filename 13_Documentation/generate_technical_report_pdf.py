"""
CoralTwin-DT: Technical Report PDF Generator
============================================
Compiles technical_report.md into technical_report.pdf.
"""

import os
from fpdf import FPDF

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MD_PATH = os.path.join(BASE_DIR, "technical_report.md")
PDF_PATH = os.path.join(BASE_DIR, "technical_report.pdf")


class TechPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(27, 73, 101)
        self.cell(0, 8, "CoralTwin-DT | Technical Architecture & Systems Engineering Report", 0, 1, "R")
        self.line(10, 15, 200, 15)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")


def render_pdf():
    print(f"Generating Technical Report PDF: {PDF_PATH}...")
    pdf = TechPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    with open(MD_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        l = line.strip().encode("latin-1", "replace").decode("latin-1")
        if not l:
            pdf.ln(2)
            continue

        if l.startswith("# "):
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(27, 73, 101)
            pdf.multi_cell(0, 7, l[2:])
            pdf.ln(2)
        elif l.startswith("## "):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(43, 108, 176)
            pdf.multi_cell(0, 6, l[3:])
            pdf.ln(1)
        elif l.startswith("### "):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 30, 30)
            pdf.multi_cell(0, 5, l[4:])
            pdf.ln(1)
        else:
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(0, 4.8, l)
            pdf.ln(1)

    pdf.output(PDF_PATH)
    print("Technical Report PDF created.")


if __name__ == "__main__":
    render_pdf()
