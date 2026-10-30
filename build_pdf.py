#!/usr/bin/env python3
"""
build_pdf.py — Convierte los .md del proyecto SILENT ASHES en PDF.

Uso:
    # activa el entorno primero:  source .venv/bin/activate
    python build_pdf.py                 # construye TODOS los PDFs
    python build_pdf.py manuscrito/acto-1.md
    python build_pdf.py biblia.md -o salida/biblia.pdf

Requisitos (ya instalados en .venv): weasyprint, markdown
"""
import sys
import pathlib
import argparse
import markdown
from weasyprint import HTML

ROOT = pathlib.Path(__file__).parent.resolve()
OUT = ROOT / "pdf"

# Archivos que se construyen cuando no se pasa ninguno en concreto.
DEFAULT_TARGETS = [
    "biblia.md",
    "registro-continuidad.md",
    "manuscrito/acto-1.md",
]

# CSS: dos estilos. "manuscrito" (literario, serif, portada) y "doc" (biblia/registro).
CSS_BASE = """
@page {
    size: A4;
    margin: 2.4cm 2.2cm 2.2cm 2.2cm;
    @bottom-right {
        content: "PÁGINA " counter(page);
        font-family: Georgia, 'Times New Roman', serif;
        font-size: 8pt;
        color: #777;
        letter-spacing: 0.5px;
    }
}
@page :first { @bottom-right { content: ""; } }
html { font-family: Georgia, 'Times New Roman', serif; }
body { color: #1a1a1a; line-height: 1.55; font-size: 11.5pt; text-align: justify; }
h1, h2, h3 { font-weight: bold; text-align: left; line-height: 1.2; }
h1 { font-size: 20pt; margin: 0 0 0.4em; }
h2 { font-size: 15pt; margin: 1.6em 0 0.5em; }
h3 { font-size: 12.5pt; margin: 1.2em 0 0.4em; }
p { margin: 0 0 0.75em; }
em { font-style: italic; }
strong { font-weight: bold; }
ul, ol { margin: 0 0 0.8em 1.1em; }
li { margin-bottom: 0.25em; }
hr { border: none; border-top: 1px solid #ccc; margin: 1.6em 0; }
table { border-collapse: collapse; width: 100%; font-size: 10pt; margin: 0.6em 0 1em; }
th, td { border: 1px solid #ccc; padding: 5px 8px; text-align: left; vertical-align: top; }
th { background: #2b3440; color: #fff; }
blockquote { border-left: 3px solid #c9a227; margin: 1em 0; padding: 0.2em 1em;
             background: #faf7ef; color: #333; font-style: italic; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 9.5pt;
       background: #f2f2f2; padding: 1px 4px; border-radius: 3px; }
pre { background: #f2f2f2; padding: 0.8em; border-radius: 4px; overflow: hidden;
      font-size: 9pt; white-space: pre-wrap; }
"""

# Estilo específico del manuscrito literario.
CSS_MS = """
body { font-size: 12pt; line-height: 1.6; }
/* El separador --- marca cambio de capítulo / salto de escena.
   Los H1 del manuscrito (nombres de POV) se centran como en el original. */
h1 { text-align: center; font-variant: small-caps; letter-spacing: 1px;
     font-size: 17pt; margin: 0.2em 0 1.4em; page-break-before: always; }
h1:first-of-type { page-break-before: avoid; }
/* Portada */
.cover { page-break-after: always; text-align: center; }
.cover .title { font-size: 40pt; letter-spacing: 3px; font-variant: small-caps;
                margin-top: 34vh; font-weight: bold; }
.cover .act { margin-top: 42vh; font-size: 13pt; letter-spacing: 2px; }
/* primera línea de párrafo tras un salto NO sangra; el resto, sí (estilo novela) */
p { text-indent: 1.4em; margin: 0; }
p:first-of-type, h1 + p, h2 + p, h3 + p, hr + p, blockquote + p { text-indent: 0; }
hr { border: none; text-align: center; margin: 1.3em 0; }
hr::after { content: "* * *"; color: #999; letter-spacing: 4px; }
"""

CSS_DOC = """
h1 { border-bottom: 3px solid #c9a227; padding-bottom: 0.2em; }
.meta { color: #666; font-size: 9pt; border-bottom: 1px solid #ddd;
        padding-bottom: 0.6em; margin-bottom: 1.4em; }
"""

MD_EXT = ["tables", "fenced_code", "sane_lists", "attr_list", "md_in_html"]


def render(md_path: pathlib.Path, out_path: pathlib.Path):
    text = md_path.read_text(encoding="utf-8")
    kind = "ms" if "manuscrito" in str(md_path).replace("\\", "/") else "doc"

    # Portada solo para el manuscrito, si la primera línea es un marcador <!--COVER ...-->
    cover_html = ""
    if text.startswith("<!--COVER"):
        first, _, rest = text.partition("-->")
        title = first.replace("<!--COVER", "").strip() or "SILENT ASHES"
        text = rest.lstrip("\n")
        cover_html = (
            f'<div class="cover"><div class="title">{title}</div>'
            f'<div class="act"></div></div>'
        )

    body = markdown.markdown(text, extensions=MD_EXT)
    css = CSS_BASE + (CSS_MS if kind == "ms" else CSS_DOC)
    html = (f"<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>"
            f"<style>{css}</style></head><body>{cover_html}{body}</body></html>")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html, base_url=str(ROOT)).write_pdf(str(out_path))
    size = out_path.stat().st_size
    print(f"  ✓ {md_path.name:28s} -> {out_path.relative_to(ROOT)}  ({size//1024} KB)")


def main():
    ap = argparse.ArgumentParser(description="Construye PDFs de SILENT ASHES.")
    ap.add_argument("targets", nargs="*", help="archivos .md a construir")
    ap.add_argument("-o", "--output", help="ruta de salida (solo con 1 target)")
    args = ap.parse_args()

    targets = args.targets or DEFAULT_TARGETS
    print("Construyendo PDFs…")
    for t in targets:
        md = (ROOT / t).resolve()
        if not md.exists():
            print(f"  ✗ no existe: {t}")
            continue
        if args.output and len(targets) == 1:
            out = (ROOT / args.output).resolve()
        else:
            out = OUT / (md.stem + ".pdf")
        render(md, out)
    print(f"\nListo. PDFs en: {OUT}")


if __name__ == "__main__":
    main()
