#!/usr/bin/env python3
"""
Fusiona 'SILENT ASHES v2' (DOCX nativo del autor) con nuestro Capitulo 3,
conservando el estilo del autor y aplicando una jerarquia de titulos navegable:
  - Title    -> portada (SILENT ASHES)
  - Heading 1 -> inicios de ACTO/CAPITULO
  - Heading 2 -> cada POV
"""
import re
import docx
from docx import Document
from copy import deepcopy

SRC = "entrada/silent-ashes-v2.docx"
OUT = "docx/SILENT-ASHES-v2-fusion.docx"

POV = {"SETH", "ELOY", "ADORAL", "HOPE", "MAGNUS", "ILIANA",
       "DARIUS", "BRON", "YIEL", "BRON Y YIEL", "SETH E ILIANA", "ELOY Y HOPE"}

d = Document(SRC)

# --- Paso 1: reasignar estilos del documento del autor ---
# Subtitle (actos/capitulos) -> Heading 1 ; Heading 1 (POV) -> Heading 2
# POV suelto en 'normal' (titulo perdido) -> Heading 2
promoted = 0
for p in d.paragraphs:
    name = p.style.name
    txt = p.text.strip()
    if name == "Subtitle":
        if txt:  # solo los subtitulos con texto (actos/capitulos); vacios -> normal
            p.style = d.styles["Heading 1"]
        else:
            p.style = d.styles["Normal"]
    elif name == "Heading 1":
        p.style = d.styles["Heading 2"]  # POV
    elif name == "normal" and txt in POV:
        p.style = d.styles["Heading 2"]  # ILIANA perdido, u otros
        promoted += 1

print(f"POV sueltos promovidos a Heading 2: {promoted}")

# --- Paso 2: anexar nuestro Capitulo 3 desde el markdown ---
with open("manuscrito/capitulo-3.md", encoding="utf-8") as f:
    lines = f.read().splitlines()

# Mapa de titulos de capitulo del md a formato del autor
# El primer '# ' es el rotulo de capitulo; el resto son POV.
def add_para(text, style):
    para = d.add_paragraph(text)
    para.style = d.styles[style]
    return para

# salto de pagina antes del nuevo capitulo
from docx.enum.text import WD_BREAK
d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

# Encabezado de capitulo (Heading 1), replicando tu estilo:
# "ACTO I." en un parrafo, y "TERCER CAPITULO." + subtitulo con salto
# de linea interno en el mismo parrafo (como "PRIMER CAPITULO. / AQUEL...").
add_para("ACTO I.", "Heading 1")
h = d.add_paragraph()
h.style = d.styles["Heading 1"]
r = h.add_run("TERCER CAPITULO.")
r.add_break()  # salto de linea interno
h.add_run("CENIZA Y CORONA.")

first_h1_seen = False
for ln in lines:
    s = ln.strip()
    if s.startswith("<!--"):
        continue
    if s.startswith("# "):
        title = s[2:].strip()
        if not first_h1_seen:
            # este es el rotulo "ACTO I * Capitulo 3 ..." del md -> ya lo pusimos arriba
            first_h1_seen = True
            continue
        # es un POV -> Heading 2
        add_para(title.upper(), "Heading 2")
        continue
    if s == "---":
        # separador de escena: parrafo con guiones, estilo del autor
        add_para("* * *", "Normal")
        continue
    if s == "":
        continue
    add_para(s, "Normal")

d.save(OUT)
print("Guardado:", OUT)

# --- Verificacion: listar jerarquia final ---
d2 = Document(OUT)
print("\n=== Jerarquia final (Title/Heading 1/Heading 2) ===")
for p in d2.paragraphs:
    if p.style.name in ("Title", "Heading 1", "Heading 2"):
        t = p.text.strip()
        if t:
            print(f"  {p.style.name:10s} | {t[:55]}")
