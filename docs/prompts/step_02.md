# Step 02 — Configuration system and CLI options

## Prompt (verbatim)

```
Extend the stencilify project.

Goal: Implement a robust configuration system and CLI options for the stencil pipeline.

Requirements:
- Use pydantic models for configuration and validation.
- Support page sizes A4, A3, A2 with mm dimensions and both portrait/landscape.
- Inputs:
  - --input (path to RGBA image)
  - --outdir (output folder)
  - --palette (2–4 colors; accept repeated --palette entries or a comma-separated string)
  - --page (A4|A3|A2)
  - --orientation (portrait|landscape|auto)
  - --margin-mm (float)
  - --min-feature-mm (float)
  - --min-island-area-mm2 (float)
  - --bridge-width-mm (float; 0 disables bridges)
  - --paint-order (auto|given) where auto sorts by palette luminance (dark->light)
  - --locks (optional: mapping color->mask file; allow multiple --lock COLOR=PATH)
  - --vector-backend (contours|potrace)
  - --autotune (flag)
  - --seed (int)

Tasks:
1) Create src/stencilify/config.py with pydantic models:
   - PageSpec, PipelineConfig, LockSpec, ExportConfig, AutotuneConfig
2) Create src/stencilify/geometry.py for unit conversions and page constants.
3) Implement palette parsing (HEX like #RRGGBB).
4) Implement CLI parsing with Typer, producing a validated PipelineConfig instance.
5) Add `stencilify config --print-defaults` to print a JSON config example.

Acceptance:
- `uv run stencilify generate --help` shows all options.
- Invalid palette length (<2 or >4) fails with a clear message.
- Page sizing functions return usable width/height in mm.

Do not implement the image pipeline yet; just config + parsing + validation + utilities + tests.
```
