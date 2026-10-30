#!/usr/bin/env python3
"""
build_docx.py — Convierte los .md del proyecto SILENT ASHES en .docx (Word).

Uso:
    source .venv/bin/activate
    python build_docx.py                  # construye todos (biblia, registro, acto-1)
    python build_docx.py manuscrito/acto-1.md

Pensado sobre todo para el manuscrito: produce un .docx limpio, editable en Word,
con portada, capítulos que empiezan en página nueva y separadores de escena.
Las tablas de la biblia/registro se vuelcan como tablas de Word.

Requisitos (en .venv): python-docx
"""
import re
import sys
import pathlib
import argparse
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = pathlib.Path(__file__).parent.resolve()
OUT = ROOT / "docx"
DEFAULT_TARGETS = ["biblia.md", "registro-continuidad.md", "manuscrito/acto-1.md"]

GOLD = RGBColor(0xC9, 0xA2, 0x27)


def add_page_break(doc):
    doc.add_page_break()


def set_cell_bg(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def add_runs_with_inline(paragraph, text):
    """Procesa **negrita**, *cursiva* y `código` mínimos para una línea."""
    # patrón simple: **x**  *x*  `x`
    pos = 0
    pattern = re.compile(r"(\*\*.+?\*\*|\*.+?\*|`.+?`)")
    for m in pattern.finditer(text):
        if m.start() > pos:
            paragraph.add_run(text[pos:m.start()])
        token = m.group(0)
        if token.startswith("**"):
            r = paragraph.add_run(token[2:-2]); r.bold = True
        elif token.startswith("`"):
            r = paragraph.add_run(token[1:-1]); r.font.name = "Consolas"
        else:
            r = paragraph.add_run(token[1:-1]); r.italic = True
        pos = m.end()
    if pos < len(text):
        paragraph.add_run(text[pos:])


def strip_inline(text):
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)  # quita html como <div>, <strong>
    return text


def build_manuscript(md_text, out_path):
    doc = Document()

    # Estilo base tipo novela
    normal = doc.styles["Normal"]
    normal.font.name = "Georgia"
    normal.font.size = Pt(12)
    pf = normal.paragraph_format
    pf.line_spacing = 1.5
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.first_line_indent = Inches(0.3)
    pf.space_after = Pt(0)

    lines = md_text.splitlines()

    # Portada
    if lines and lines[0].startswith("<!--COVER"):
        title = lines[0].replace("<!--COVER", "").replace("-->", "").strip() or "SILENT ASHES"
        lines = lines[1:]
        for _ in range(10):
            doc.add_paragraph()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(title.upper())
        r.bold = True
        r.font.size = Pt(34)
        p.paragraph_format.first_line_indent = Inches(0)
        add_page_break(doc)

    first_h1_seen = False
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("# "):
            # Capítulo / POV: página nueva (salvo el primero) y centrado en versalitas
            if first_h1_seen:
                add_page_break(doc)
            first_h1_seen = True
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Inches(0)
            p.paragraph_format.space_before = Pt(18)
            p.paragraph_format.space_after = Pt(24)
            r = p.add_run(strip_inline(line[2:]).upper())
            r.bold = True
            r.font.size = Pt(16)
        elif line.strip() == "---":
            p = doc.add_paragraph("* * *")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Inches(0)
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(10)
        else:
            p = doc.add_paragraph()
            # Formato de novela aplicado EXPLÍCITAMENTE en cada párrafo
            # (no se confía en la herencia del estilo, que python-docx no
            # propaga de forma fiable). Sangría de primera línea + un pequeño
            # espacio posterior para que narración y diálogos "respiren".
            pf2 = p.paragraph_format
            pf2.first_line_indent = Inches(0.3)
            pf2.space_after = Pt(6)
            pf2.line_spacing = 1.5
            pf2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            add_runs_with_inline(p, line)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    print(f"  ✓ {out_path.name}  ({out_path.stat().st_size//1024} KB)")


def build_doc(md_text, out_path):
    """Para biblia/registro: encabezados, listas, tablas y citas."""
    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)

    lines = md_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        s = line.strip()
        if not s:
            i += 1
            continue
        # Tabla markdown
        if s.startswith("|") and i + 1 < len(lines) and lines[i+1].strip() and set(lines[i+1].strip()) <= set("|-: "):
            header = [c.strip() for c in s.strip("|").split("|")]
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            table = doc.add_table(rows=1, cols=len(header))
            try:
                table.style = "Table Grid"
            except Exception:
                pass
            for k, h in enumerate(header):
                cell = table.rows[0].cells[k]
                cell.text = ""
                run = cell.paragraphs[0].add_run(strip_inline(h))
                run.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                set_cell_bg(cell, "2B3440")
            for row in rows:
                cells = table.add_row().cells
                for k, val in enumerate(row[:len(header)]):
                    cells[k].text = ""
                    add_runs_with_inline(cells[k].paragraphs[0], val)
            doc.add_paragraph()
            i = j
            continue
        if s.startswith("#"):
            level = len(s) - len(s.lstrip("#"))
            text = strip_inline(s.lstrip("#").strip())
            # Evitamos doc.add_heading (lookup de estilos extremadamente lento
            # en este entorno); construimos el encabezado a mano.
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14 if level <= 2 else 8)
            p.paragraph_format.space_after = Pt(4)
            r = p.add_run(text)
            r.bold = True
            r.font.size = Pt({1: 20, 2: 15, 3: 13}.get(level, 12))
            if level <= 2:
                r.font.color.rgb = RGBColor(0x20, 0x28, 0x33)
            i += 1
            continue
        if s.startswith(">"):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            r = p.add_run(strip_inline(s.lstrip(">").strip()))
            r.italic = True
            i += 1
            continue
        if s.startswith("- ") or s.startswith("* "):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            p.add_run("•  ")
            add_runs_with_inline(p, s[2:])
            i += 1
            continue
        if re.match(r"^\d+\. ", s):
            num = re.match(r"^(\d+)\.", s).group(1)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            p.add_run(f"{num}.  ")
            add_runs_with_inline(p, re.sub(r"^\d+\.\s*", "", s))
            i += 1
            continue
        if s == "---":
            i += 1
            continue
        p = doc.add_paragraph()
        add_runs_with_inline(p, strip_inline(s) if s.startswith("<") else s)
        i += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    print(f"  ✓ {out_path.name}  ({out_path.stat().st_size//1024} KB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="*")
    args = ap.parse_args()
    targets = args.targets or DEFAULT_TARGETS
    print("Construyendo DOCX…")
    for t in targets:
        md = (ROOT / t).resolve()
        if not md.exists():
            print(f"  ✗ no existe: {t}")
            continue
        text = md.read_text(encoding="utf-8")
        out = OUT / (md.stem + ".docx")
        if "manuscrito" in str(md).replace("\\", "/"):
            build_manuscript(text, out)
        else:
            build_doc(text, out)
    print(f"\nListo. DOCX en: {OUT}")


if __name__ == "__main__":
    main()
