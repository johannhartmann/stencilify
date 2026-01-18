# Step 06 — Layer mask generation and preview composite

## Prompt (verbatim)

```
Implement layer mask generation and a preview composite.

Goal: From label_map_pixels and silhouette, build per-color open masks (binary cutouts), determine paint order, and render a preview image that simulates spraying layers in order.

Definitions:
- open_mask for a layer: 1 means "cut out / spray here".
- Knockout mode: each pixel inside silhouette belongs to exactly one label.

Requirements:
- Generate open_masks: dict[color_hex -> uint8 mask01]
- Paint order:
  - "given": use palette order as provided
  - "auto": sort by palette luminance (dark->light) based on RGB -> Y luma
- Preview:
  - Start with transparent canvas; for each layer in paint order, paint that color where open_mask==1.
  - Output preview RGBA (uint8) sized to working resolution.
- Provide a function to write debug previews to disk (behind a CLI flag later).

Tasks:
1) Add src/stencilify/layers.py:
   - build_open_masks(label_map, silhouette01, palette) -> dict
   - compute_paint_order(palette, mode) -> list
2) Add src/stencilify/preview.py:
   - render_preview(open_masks, palette, paint_order) -> RGBA uint8
3) Add a unit test ensuring knockout property holds and preview has expected pixels.

Acceptance:
- Preview renders without errors for K=2..4.
- Knockout: sum over all open_masks equals silhouette at every pixel.
```

## Summary of work performed

1. **Implemented layers.py** for layer mask generation:
   - `build_open_masks()`: Generate binary masks for each palette color
     * Creates dict mapping color_hex -> binary mask [H, W]
     * Mask has 1 where material should be cut out / paint sprayed
     * Ensures masks are only within silhouette
     * Validates palette size (2-4 colors)
   - `compute_luminance()`: Calculate luminance using standard luma formula
     * Y = 0.299*R + 0.587*G + 0.114*B
     * Used for automatic paint order sorting
   - `compute_paint_order()`: Determine layer painting order
     * GIVEN mode: Use palette order as-is
     * AUTO mode: Sort by luminance (dark to light)
     * Returns list of palette indices in paint order
   - `verify_knockout_property()`: Verify each pixel belongs to exactly one layer
     * Sum of all masks should equal silhouette
     * Ensures no overlaps or gaps

2. **Implemented preview.py** for preview rendering:
   - `hex_to_rgb()`: Convert HEX color strings to RGB tuples
   - `render_preview()`: Composite layers in paint order
     * Start with transparent RGBA canvas
     * Paint each layer in order where open_mask == 1
     * Later layers overwrite earlier ones
     * Returns RGBA image [H, W, 4] as uint8
   - `save_preview()`: Save preview image to disk
     * Validates RGBA format
     * Uses PIL to save as PNG

3. **Knockout property implementation**:
   - Each pixel inside silhouette belongs to exactly one label
   - Open masks are mutually exclusive within silhouette
   - Sum of all open_masks equals silhouette at every pixel
   - Comprehensive validation to catch overlaps or gaps

4. **Paint order modes**:
   - GIVEN: Preserves user-specified palette order
   - AUTO: Sorts dark to light using perceptual luminance
   - Deterministic sorting for reproducibility

5. **Comprehensive tests** (41 new tests, 187 total):
   - test_layers.py (21 tests):
     * Open mask generation with various configurations
     * Knockout property verification
     * Luminance computation
     * Paint order (GIVEN and AUTO modes)
     * Edge cases and error handling
   - test_preview.py (20 tests):
     * Preview rendering with 2-4 colors
     * Paint order effects (later layers overwrite)
     * Transparent background handling
     * Saving to disk
     * Error handling and validation

## Commands executed

```bash
# Test imports
uv run python -c "from stencilify.layers import build_open_masks, compute_paint_order"
uv run python -c "from stencilify.preview import render_preview, save_preview"

# Run layers and preview tests
uv run pytest tests/test_layers.py tests/test_preview.py -v

# Format code
uv run ruff format src/stencilify/preview.py

# Full validation sequence
uv run ruff format --check .
uv run ruff check .
uv run mypy .
uv run pytest -q

# Combined validation
uv run ruff format --check . && uv run ruff check . && uv run mypy . && uv run pytest -q
```

## Validation results

```
$ uv run ruff format --check .
25 files already formatted

$ uv run ruff check .
All checks passed!

$ uv run mypy .
Success: no issues found in 25 source files

$ uv run pytest -q
============================= test session starts ==============================
collected 187 items
tests/test_cli.py ...............                                        [  8%]
tests/test_config.py ...........................                         [ 22%]
tests/test_geometry.py ............                                      [ 28%]
tests/test_imageio.py ...........                                        [ 34%]
tests/test_labeling.py ........................                          [ 47%]
tests/test_layers.py .....................                               [ 58%]
tests/test_locks.py ....................                                 [ 69%]
tests/test_masks.py ..................                                   [ 79%]
tests/test_preview.py ....................                               [ 89%]
tests/test_superpixels.py ...................                            [100%]

============================== 187 passed in 3.87s ==============================
```

**Result**: PASS ✓

## Files changed (high-level)

**New files:**
- `src/stencilify/layers.py` - Layer mask generation, paint order, knockout verification
- `src/stencilify/preview.py` - Preview rendering and saving
- `tests/test_layers.py` - 21 tests for layer mask functionality
- `tests/test_preview.py` - 20 tests for preview rendering

**No modified dependencies** - Used existing numpy and PIL/Pillow

## Deviations / Decisions

1. **Standard luma formula**: Used Y = 0.299*R + 0.587*G + 0.114*B for luminance calculation
2. **Knockout enforcement**: Strictly enforced that each pixel belongs to exactly one layer
3. **Paint order**: Later layers overwrite earlier ones in preview (matches physical stencil behavior)
4. **RGBA output**: Preview uses full RGBA with transparent background for flexibility
5. **Type safety**: Cast numpy bool_ to Python bool for mypy compatibility
6. **Assertions**: Use simple `assert` instead of `assert ... is True` for numpy boolean compatibility
7. **No dithering**: Preview uses solid colors without anti-aliasing (matches stencil output)

## Notes / Follow-ups

- All acceptance criteria met: Open masks generated, knockout property enforced, preview renders for K=2..4
- 187 total tests (41 new), all passing
- Knockout property verification ensures data integrity
- Paint order modes provide flexibility (user-specified or automatic)
- Preview accurately simulates layer compositing
- Save function ready for debug output (can be wired to CLI flag later)
- Ready for Step 7 (next stage of pipeline)
