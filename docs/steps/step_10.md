# Step 10 — Page layout and registration marks

## Prompt (verbatim)

```
Add page layout and registration marks.

Goal: Place the working-resolution stencil masks onto a page canvas with margins and add registration marks that are identical across all layers.

Requirements:
- Page canvas size is determined by selected page and orientation, minus margins.
- Do not crop the portrait; scale it to fit inside the printable area while preserving aspect ratio.
- Add outer padding such that registration marks are outside the artwork but inside the page.
- Registration marks:
  - 3 marks (default): top-left, top-right, bottom-left within margin area
  - each mark is a circle cutout (open=1) of configurable diameter (default 6mm)
- The same marks must be added to every layer open_mask.

Tasks:
1) Add src/stencilify/layout.py:
   - compute_page_canvas_px(page_mm, px_per_mm) -> (H,W)
   - place_artwork_on_page(open_masks, page_spec, margin_mm, px_per_mm) -> placed_masks
   - add_registration_marks(placed_masks, px_per_mm, diameter_mm=6.0) -> placed_masks
2) Add tests verifying that:
   - artwork fits
   - marks exist at expected approximate positions
   - marks identical across layers

Acceptance:
- Output masks are page-sized.
- Marks consistent layer-to-layer.
```

## Summary of work performed

1. **Implemented layout.py** for page layout and registration marks:
   - `compute_page_canvas_px()`: Compute page canvas size in pixels from dimensions
     * Simple conversion: `(height_px, width_px) = (height_mm * px_per_mm, width_mm * px_per_mm)`
   - `place_artwork_on_page()`: Place artwork on page canvas with margins
     * Handles page size (A4, A3, A2) and orientation (portrait, landscape, auto)
     * AUTO orientation selects based on artwork aspect ratio vs page aspect ratio
     * Scales artwork to fit within printable area (page - margins) while preserving aspect ratio
     * Centers artwork on page canvas
     * Places all layers identically for perfect alignment
     * Returns page-sized masks for all layers
   - `add_registration_marks()`: Add registration marks to all layers
     * Adds 3 circular cutouts (open=1) at top-left, top-right, bottom-left
     * Marks positioned in margin area (centered at margin/2 from edges)
     * Configurable diameter (default 6mm)
     * Uses cv2.circle() with filled circles (thickness=-1)
     * Marks are identical across all layers for precise alignment
   - `RegistrationMark` dataclass:
     * center_px: Center position (x, y) in pixels
     * radius_px: Radius in pixels

2. **Page layout algorithm**:
   - Step 1: Determine effective page orientation
     * AUTO: Compare artwork aspect ratio with page aspect ratio
     * Use landscape if artwork is wider relative to page proportions
   - Step 2: Apply orientation to get page dimensions
     * Portrait: width = base width, height = base height
     * Landscape: width = base height, height = base width
   - Step 3: Validate margins (must be non-negative and not exceed page)
   - Step 4: Compute page canvas size in pixels
   - Step 5: Compute printable area (canvas - margins on all sides)
   - Step 6: Scale artwork to fit printable area
     * scale_w = printable_w / artwork_w
     * scale_h = printable_h / artwork_h
     * scale = min(scale_w, scale_h)  # Preserve aspect ratio
   - Step 7: Compute offset to center artwork
     * offset_x = (canvas_w - scaled_w) / 2
     * offset_y = (canvas_h - scaled_h) / 2
   - Step 8: Resize and place all masks identically

3. **Registration mark placement**:
   - Mark positions (3 marks):
     * Top-left: (margin_mm/2, margin_mm/2) from top-left corner
     * Top-right: (width - margin_mm/2, margin_mm/2) from top-right corner
     * Bottom-left: (margin_mm/2, height - margin_mm/2) from bottom-left corner
   - Mark rendering:
     * Convert diameter to radius in pixels: radius_px = (diameter_mm / 2) * px_per_mm
     * Draw filled circles with cv2.circle(mask, center, radius, color=1, thickness=-1)
     * Minimum radius is 1px (for very small diameters)
   - Consistency: Same marks added to all layers for perfect alignment

4. **Comprehensive tests** (24 new tests, 275 total):
   - test_layout.py (24 tests):
     * Canvas size computation (portrait, landscape)
     * Artwork placement (basic, scaling, centering)
     * Orientation handling (portrait, landscape, auto)
     * Multiple layers (identical placement)
     * Different page sizes (A4, A3)
     * Registration marks (basic, consistency, size)
     * Mark positioning and preservation of non-mark areas
     * Error handling (empty masks, invalid dimensions, invalid margins, etc.)
     * Dataclass validation

## Commands executed

```bash
# Test imports
uv run python -c "from stencilify.layout import compute_page_canvas_px, place_artwork_on_page, add_registration_marks, RegistrationMark"

# Run layout tests
uv run pytest tests/test_layout.py -v

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
33 files already formatted

$ uv run ruff check .
All checks passed!

$ uv run mypy .
Success: no issues found in 33 source files

$ uv run pytest -q
============================= test session starts ==============================
collected 275 items
tests/test_bridges.py .................                                  [  6%]
tests/test_cli.py ...............                                        [ 11%]
tests/test_config.py ...........................                         [ 21%]
tests/test_geometry.py ............                                      [ 25%]
tests/test_imageio.py ...........                                        [ 29%]
tests/test_islands.py ...................                                [ 36%]
tests/test_labeling.py ........................                          [ 45%]
tests/test_layers.py .....................                               [ 53%]
tests/test_layout.py ........................                            [ 61%]
tests/test_locks.py ....................                                 [ 69%]
tests/test_masks.py ..................                                   [ 75%]
tests/test_preview.py ....................                               [ 82%]
tests/test_stencil_opt.py ............................                   [ 93%]
tests/test_superpixels.py ...................                            [100%]

============================== 275 passed in 4.19s ==============================
```

**Result**: PASS ✓

## Files changed (high-level)

**New files:**
- `src/stencilify/layout.py` - Page layout, artwork placement, registration marks
- `tests/test_layout.py` - 24 tests for layout functionality

**No modified dependencies** - Used existing OpenCV, numpy, and geometry module

## Deviations / Decisions

1. **Page canvas size**: Full page size (not minus margins) for canvas dimensions
2. **Printable area**: Page size minus margins on all sides (2*margin per dimension)
3. **Artwork scaling**: Scale to fit printable area using min(scale_w, scale_h) to preserve aspect ratio
4. **Centering**: Artwork centered on full page canvas (not just printable area)
5. **Registration mark positions**: Centered at margin/2 from respective corners
6. **Mark positions**: Top-left, top-right, bottom-left (3 marks as specified)
7. **Mark rendering**: cv2.circle with filled circles (thickness=-1)
8. **Minimum mark radius**: 1 pixel (for very small diameters)
9. **AUTO orientation**: Based on aspect ratio comparison (artwork vs page)
10. **Function parameters**: Explicit parameters for page_size, orientation, margin_mm for flexibility

## Notes / Follow-ups

- All acceptance criteria met:
  - Output masks are page-sized ✓
  - Registration marks consistent layer-to-layer ✓
  - Artwork fits within printable area ✓
  - Marks positioned in margin area ✓
- 275 total tests (24 new), all passing
- Registration marks ensure perfect layer alignment when cutting/printing
- Page layout preserves artwork aspect ratio while maximizing use of printable area
- AUTO orientation intelligently selects best orientation based on artwork shape
- Layout functions are reusable and well-tested for integration into main pipeline
- Ready for Step 11 (next stage of pipeline)
