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

## Summary of work performed

1. **Switched from Click to Typer** as requested in the prompt
2. **Added Pydantic models** for configuration:
   - `Color`: RGB color with hex parsing and luminance calculation
   - `PaintOrder`, `VectorBackend`: String enums for options
   - `PageSpec`: Page size, orientation, margins
   - `CuttabilityConfig`: Feature sizes, island handling, bridges
   - `ExportConfig`: Vector backend and output directory
   - `AutotuneConfig`: Autotune settings
   - `LockSpec`: Color-to-mask mapping for pre-existing layers
   - `PipelineConfig`: Complete pipeline configuration with validation
3. **Created geometry.py** with:
   - `PageSize`, `Orientation` enums
   - `Dimensions` dataclass for page dimensions
   - Page size constants (A4, A3, A2) in millimeters
   - Unit conversion functions (mm ↔ pixels, mm² ↔ pixels²)
4. **Implemented comprehensive CLI** with all required options:
   - `generate` command with 15+ options (palette, page, orientation, margins, etc.)
   - `config --print-defaults` command to show JSON configuration
   - Palette parsing (repeated --palette or comma-separated)
   - Lock parsing (--lock COLOR=PATH format)
   - Full validation with pydantic models
5. **Created comprehensive tests** (54 tests total):
   - `test_geometry.py`: 12 tests for page sizes and unit conversions
   - `test_config.py`: 27 tests for color parsing, config validation, palette sorting
   - `test_cli.py`: 15 tests for CLI commands and parsing functions

## Commands executed

```bash
# Add pydantic and typer dependencies, sync
uv sync

# Create test input image for validation
uv run python -c "from PIL import Image; ..."

# Test CLI commands
uv run stencilify --help
uv run stencilify generate --help
uv run stencilify config --print-defaults
uv run stencilify generate test_input.png --palette="#000000" --palette="#ffffff"

# Format code
uv run ruff format .
uv run ruff format src/stencilify/cli.py

# Validation sequence
uv run ruff format --check .
uv run ruff check .
uv run mypy .
uv run pytest -v
uv run pytest -q

# Full validation
uv run ruff format --check . && uv run ruff check . && uv run mypy . && uv run pytest -q
```

## Validation results

```
$ uv run ruff format --check .
11 files already formatted

$ uv run ruff check .
All checks passed!

$ uv run mypy .
Success: no issues found in 11 source files

$ uv run pytest -q
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/user/stencilify
configfile: pyproject.toml
testpaths: tests
collected 54 items

tests/test_cli.py ...............                                        [ 27%]
tests/test_config.py ...........................                         [ 77%]
tests/test_geometry.py ............                                      [100%]

============================== 54 passed in 0.62s ==============================
```

**Result**: PASS ✓

## Files changed (high-level)

**New files:**
- `src/stencilify/config.py` - Pydantic models for configuration (Color, PageSpec, PipelineConfig, etc.)
- `src/stencilify/geometry.py` - Page sizes and unit conversions
- `tests/test_config.py` - 27 tests for configuration models
- `tests/test_geometry.py` - 12 tests for geometry utilities

**Modified files:**
- `pyproject.toml` - Replaced click with typer, added pydantic; updated entry point
- `src/stencilify/cli.py` - Complete rewrite using Typer with all CLI options
- `tests/test_cli.py` - Updated and expanded tests (15 tests)

## Deviations / Decisions

1. **Click → Typer**: Switched from Click to Typer as explicitly requested in prompt
   - Documented in docs/decisions.md as a requirement change from Step 1
2. **Enums for string constants**: Used `str, Enum` pattern for PaintOrder and VectorBackend
   - Required by Pydantic for proper validation
3. **Color class**: Implemented custom Color class instead of using Pydantic model
   - Allows for luminance calculations and sorting
   - Used in validation but not stored in config (strings stored instead)
4. **List defaults**: Used `None` instead of `[]` for list defaults to avoid B006 linting error
   - Handle with `palette or []` and `lock or []` in function body
5. **model_construct for defaults**: Used `PipelineConfig.model_construct()` for config --print-defaults
   - Bypasses validation since sample "input.png" doesn't exist

## Notes / Follow-ups

- All CLI options implemented as requested
- Palette validation enforces 2-4 colors with clear error messages
- Page sizing functions return usable width/height in mm
- Config can be printed as JSON for documentation/reference
- CLI is ready for pipeline implementation in subsequent steps
- 54 tests passing, 100% validation success
