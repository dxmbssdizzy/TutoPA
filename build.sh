#!/usr/bin/env bash
# build.sh — genera los PDFs de SILENT ASHES con un solo comando.
#
#   ./build.sh                      -> construye todos los PDFs (biblia, registro, acto-1)
#   ./build.sh manuscrito/acto-1.md -> construye solo ese archivo
#
# La primera vez crea el entorno .venv e instala dependencias automáticamente.
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Primera ejecución: creando entorno .venv e instalando dependencias…"
  if command -v uv >/dev/null 2>&1; then
    uv venv .venv
    . .venv/bin/activate
    uv pip install weasyprint markdown
  else
    python3 -m venv .venv
    . .venv/bin/activate
    pip install weasyprint markdown
  fi
else
  . .venv/bin/activate
fi

# Asegura que las dependencias de docx también estén
python -c "import docx" 2>/dev/null || { command -v uv >/dev/null 2>&1 && uv pip install python-docx || pip install python-docx; }

echo "== PDF =="
python build_pdf.py "$@"
echo "== DOCX =="
python build_docx.py "$@"
