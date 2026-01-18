# Step 03 — Image I/O and scaling layer

## Prompt (verbatim)

```
Implement the foundational image I/O and scaling layer.

Goal: Load RGBA portraits, derive silhouette from alpha, and rescale to a working resolution suitable for DIN A4–A2 and min_feature_mm.

Requirements:
- Input image is RGBA (alpha present). If not, error with actionable message.
- Compute a working resolution based on page long-edge mm and min_feature_mm:
  work_long_edge_px = clamp(2000, 6000, int(long_edge_mm * (4 / min_feature_mm)))
- Preserve aspect ratio; do not crop.
- Compute px_per_mm_work based on the final working image size and intended page placement (inside margins).
- Create silhouette mask S from alpha threshold (configurable; default 20/255).
- Smooth silhouette with morphology close then open, kernel sizes derived from min_feature_mm.
- Provide debug outputs (in memory, not written yet) for silhouette.

Tasks:
1) Add src/stencilify/imageio.py:
   - load_rgba(path) -> (rgb_uint8[h,w,3], alpha_uint8[h,w])
   - resize_to_working(rgb, alpha, config) -> (rgb_resized, alpha_resized, px_per_mm)
2) Add src/stencilify/masks.py:
   - silhouette_from_alpha(alpha, thresh=20) -> mask01 uint8 0/1
   - morph_smooth(mask01, close_px, open_px) -> mask01
3) Add unit tests using small synthetic images (numpy arrays) to validate:
   - silhouette extraction respects alpha
   - resizing returns consistent px_per_mm values

Acceptance:
- Running `uv run python -c "from stencilify.imageio import ..."` works.
- Tests pass.

No segmentation yet; focus on correct scaling and silhouette.
```

## Summary of work performed

1. **Added scipy dependency** for morphology operations
2. **Implemented imageio.py** with:
   - `load_rgba()`: Load RGBA images with validation
     * Checks for alpha channel presence
     * Converts to RGBA if transparency info available
     * Clear error messages if alpha missing
   - `resize_to_working()`: Smart resolution scaling
     * Formula: work_long_edge_px = clamp(2000, 6000, page_long_edge_mm * 4 / min_feature_mm)
     * Preserves aspect ratio without cropping
     * Uses high-quality Lanczos resampling
     * Computes px_per_mm for subsequent processing
3. **Implemented masks.py** with:
   - `silhouette_from_alpha()`: Extract binary silhouette from alpha
     * Configurable threshold (default 20/255)
     * Returns binary mask (0/1 values)
   - `morph_smooth()`: Morphological smoothing
     * Closing (fills small holes) then opening (removes noise)
     * Circular structuring elements
     * Kernel sizes derived from min_feature_mm
   - `_create_circular_kernel()`: Helper for circular kernels
4. **Comprehensive tests** (29 new tests, 83 total):
   - test_imageio.py: 11 tests covering loading, resizing, validation
   - test_masks.py: 18 tests covering silhouette, morphology, edge cases

## Commands executed

```bash
# Add scipy dependency
uv sync

# Test imports
uv run python -c "from stencilify.imageio import load_rgba, resize_to_working; ..."

# Format code
uv run ruff format .

# Validation sequence
uv run pytest tests/test_imageio.py tests/test_masks.py -v
uv run ruff format --check .
uv run ruff check .
uv run mypy .
uv run pytest -q

# Full validation
uv run ruff format --check . && uv run ruff check . && uv run mypy . && uv run pytest -q
```

## Validation results

```
$ uv run ruff format --check .
15 files already formatted

$ uv run ruff check .
All checks passed!

$ uv run mypy .
Success: no issues found in 15 source files

$ uv run pytest -q
============================= test session starts ==============================
collected 83 items
tests/test_cli.py ...............                                        [ 18%]
tests/test_config.py ...........................                         [ 50%]
tests/test_geometry.py ............                                      [ 65%]
tests/test_imageio.py ...........                                        [ 78%]
tests/test_masks.py ..................                                   [100%]

============================== 83 passed in 3.27s ==============================
```

**Result**: PASS ✓

## Files changed (high-level)

**New files:**
- `src/stencilify/imageio.py` - Image loading and intelligent resolution scaling
- `src/stencilify/masks.py` - Silhouette extraction and morphological smoothing
- `tests/test_imageio.py` - 11 tests for image I/O
- `tests/test_masks.py` - 18 tests for mask operations

**Modified files:**
- `pyproject.toml` - Added scipy>=1.11.0 dependency
- `uv.lock` - Updated with scipy

## Deviations / Decisions

1. **Scipy for morphology**: Chose scipy.ndimage over opencv for lighter weight
2. **Lanczos resampling**: Used PIL's Lanczos for high-quality image resizing
3. **Circular kernels**: Implemented custom circular structuring elements for natural smoothing
4. **Type annotations**: Added type: ignore for scipy (no stubs) and PIL assignments

## Notes / Follow-ups

- All acceptance criteria met: imports work, tests pass, RGBA validation, resolution clamping
- 83 total tests (29 new), all passing
- No segmentation yet (as specified)
- Ready for Step 4 (segmentation/palette quantization)
