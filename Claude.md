# Stencilify Project – Claude Code Tracking Document

## Project Overview

**stencilify** is a Python 3.12 CLI tool that converts RGBA portrait images into 2–4 palette-constrained stencil layers suitable for cutting plotters and laser cutters (DIN A4–A2 output sizes).

Key features:
- Converts input images to binary PNG masks (one per layer)
- Exports vector SVG with contours and optional potrace integration
- Cuttability optimization: minimum feature size enforcement, island fixes, bridge insertion
- Registration marks for multi-layer alignment
- Preview composite rendering
- Generates report.json with metadata
- Optional autotune mode
- Optional GPU acceleration (extras group, never required for correctness)

## Glossary

- **Open mask**: Binary image where white = cut out / spray through, black = material kept
- **Material**: Black regions in the mask; the physical material that remains
- **Knockout**: When a darker layer's features are removed from lighter layers to prevent material overlap
- **Island**: Isolated white region that would fall out when cut
- **Bridge**: Small connecting feature added to anchor islands to the main material
- **Registration marks**: Alignment features added to each layer for precise stacking

## Definition of Done (for each step)

A step is considered DONE when:
1. `ruff format --check .` passes (code is formatted)
2. `ruff check .` passes (no linting errors)
3. `mypy .` passes (type checking clean)
4. `pytest -q` passes (all tests pass)
5. CLI help works for relevant commands (if CLI commands added)
6. Required outputs are produced where specified
7. All changes committed and documented in step log

## Prompt Execution Protocol

For each numbered step prompt (Steps 1–15):

1. **Identify** the step number (NN) and concise title
2. **Record prompt** verbatim into `docs/prompts/step_NN.md`
3. **Create step log** from template: `docs/steps/step_NN.md`
4. **Update status** to IN PROGRESS in both Claude.md and docs/progress.md tables
5. **Implement** the requested changes
6. **Record commands** in `docs/commands.log` (append-only)
7. **Run validation** sequence (see Validation Commands below)
8. **Document results** in `docs/steps/step_NN.md`
9. **Update tables** to DONE + Validation PASS when successful
10. **Do not proceed** to next step until current step is DONE/PASS

If blocked, set status to BLOCKED and document exactly what is missing.

## Validation Commands

Standard validation sequence (run after each step):

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy .
uv run pytest -q
```

Alternative: Use the validation tool:
```bash
uv run python tools/validate.py
```

All commands must pass (exit code 0) before marking a step as DONE.

## Step Checklist (Steps 1–15)

| Step | Title | Status | Validation | Notes | Date |
|------|-------|--------|------------|-------|------|
| 1 | Project initialization and CLI skeleton | DONE | PASS | uv init, CLI stub working, all validations pass | 2026-01-18 |
| 2 | Configuration system and CLI options | DONE | PASS | Pydantic models, Typer CLI, 54 tests pass | 2026-01-18 |
| 3 | Image I/O and scaling layer | DONE | PASS | RGBA loading, resolution scaling, silhouette, 83 tests | 2026-01-18 |
| 4 | Superpixelization and adjacency | DONE | PASS | SLIC superpixels, adjacency graph, 102 tests pass | 2026-01-18 |
| 5 | Palette-constrained labeling over superpixels | DONE | PASS | ICM optimization, locks support, 146 tests pass | 2026-01-18 |
| 6 | Layer mask generation and preview composite | DONE | PASS | Open masks, paint order, knockout property, 187 tests pass | 2026-01-18 |
| 7 | Stencil/cuttability optimization per layer | DONE | PASS | Morphological cleanup, cutout removal, 215 tests pass | 2026-01-18 |
| 8 | Island detection for stencil material support | DONE | PASS | Material island detection, 234 tests pass | 2026-01-18 |
| 9 | Island fixing: fill small islands, add bridges | DONE | PASS | Distance transform bridging, 251 tests pass | 2026-01-18 |
| 10 | | TODO | | | |
| 11 | | TODO | | | |
| 12 | | TODO | | | |
| 13 | | TODO | | | |
| 14 | | TODO | | | |
| 15 | | TODO | | | |
