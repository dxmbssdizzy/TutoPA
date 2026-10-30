# SILENT ASHES — Proyecto de escritura

Repositorio de trabajo de la novela. Todo el texto vive en **Markdown** (editable, con control de versiones) y los **PDF** se generan a partir de él con un comando.

## Estructura

```
biblia.md                 Documento maestro (worldbuilding, personajes, canon). v0.2
registro-continuidad.md   Bitácora de conflictos y decisiones de coherencia.
manuscrito/
  acto-1.md               Manuscrito, Acto I (Eloy · Hope · Magnus · Seth).
pdf/                       PDFs generados (salida). No editar a mano.
build.sh / build_pdf.py   Herramienta de conversión Markdown → PDF.
```

## Cómo generar los PDF

```bash
./build.sh                      # genera biblia.pdf, registro-continuidad.pdf y acto-1.pdf
./build.sh manuscrito/acto-1.md # genera solo ese
```

La primera vez, `build.sh` crea el entorno `.venv` e instala las dependencias
(WeasyPrint + Markdown) automáticamente. Requiere Python 3.

## Flujo de trabajo sugerido

1. Editar el `.md` correspondiente.
2. `./build.sh` para ver el resultado en PDF.
3. Confirmar los cambios en git / subir a GitHub para leer y respaldar.

## Convenciones del manuscrito (para el conversor)

- La primera línea `<!--COVER Título -->` genera una portada.
- `#` (H1) = capítulo / punto de vista; empieza en página nueva y se centra.
- `---` = salto de escena (se dibuja como `* * *`).
- El resto es prosa normal; el conversor aplica sangría de novela.
