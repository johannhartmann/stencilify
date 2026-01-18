# Step 11 — Exporting to PNG and SVG

## Prompt (verbatim)

```
Implement exporting.

Goal: Export each layer as:
- Binary PNG (white=open/cut, black=material)
- SVG vector suitable for cutter/laser

Backends:
1) contours backend:
   - findContours on open_mask (as 0/255)
   - simplify with approxPolyDP
   - write SVG paths via svgwrite
   - ensure correct scaling to mm using px_per_mm
2) potrace backend (optional):
   - if potrace is installed, call it via subprocess
   - otherwise fallback to contours backend with a warning

Requirements:
- Output filenames include layer index in paint order:
  - 01_colorname.png / .svg
- Add preview export and report.json export hooks (preview already exists).
- Ensure SVG uses a consistent viewBox and units in mm.

Tasks:
1) Add src/stencilify/export.py:
   - export_png(mask01, path)
   - export_svg_contours(mask01, path, px_per_mm)
   - export_svg_potrace(mask01, path, px_per_mm) with fallback
2) Add minimal tests:
   - exporting creates files
   - SVG contains expected tags and dimensions

Acceptance:
- `stencilify generate` can write outputs for a synthetic test case.
```
