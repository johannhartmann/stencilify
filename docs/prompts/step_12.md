# Step 12 Prompt: End-to-end Pipeline Integration

Wire everything into an end-to-end pipeline.

Goal: Implement `stencilify generate` to run the full workflow:
1) load + working resize + silhouette
2) superpixels
3) palette labeling (+ locks)
4) open masks + paint order
5) per-layer stencil optimization (morph + small cutouts + islands + bridges)
6) page layout + registration marks
7) preview composite
8) exports (PNG + SVG)
9) report.json with metrics and warnings

Requirements:
- Create src/stencilify/pipeline.py with a single entry function:
  run_pipeline(config: PipelineConfig) -> PipelineResult
- report.json includes:
  - input file, palette, page, orientation
  - px_per_mm
  - parameters used (including superpixel params)
  - per-layer metrics before/after optimization
  - islands count, bridges count
  - any warnings
- CLI should return non-zero exit code on fatal errors only; otherwise succeed with warnings logged.

Tasks:
- Implement PipelineResult and write JSON.
- Add an integration test using a generated synthetic RGBA portrait + palette to ensure output files are created.

Acceptance:
- `uv run stencilify generate --input ... --palette ... --page A4 --outdir out` completes.
