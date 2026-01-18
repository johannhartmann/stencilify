# Step 07 — Stencil/cuttability optimization per layer

## Prompt (verbatim)

```
Implement the first stage of stencil/cuttability optimization per layer.

Goal: Given an open_mask01 for a layer, clean it up so it's cuttable:
- Smooth jagged edges
- Remove small disconnected cutouts
- Enforce minimum feature size derived from min_feature_mm and px_per_mm

Requirements:
- Derive pixel thresholds:
  - min_feature_px = round(min_feature_mm * px_per_mm)
  - min_cutout_area_px = round(min_island_area_mm2 * (px_per_mm**2))  [use same knob or add separate knob if needed]
- Perform:
  1) close then open on open_mask (kernel sizes proportional to min_feature_px)
  2) remove small connected components in open_mask (cutouts)
- Provide a metrics function that returns:
  - cutout_component_count
  - smallest_component_area_px
  - total_open_area_px
  - estimated contour length (optional)

Tasks:
1) Add src/stencilify/stencil_opt.py with:
   - morph_cleanup(open_mask01, min_feature_px) -> open_mask01
   - remove_small_cutouts(open_mask01, min_area_px) -> open_mask01
   - compute_layer_metrics(open_mask01) -> dict
2) Implement using OpenCV connectedComponentsWithStats and morphologyEx.
3) Add tests with synthetic masks.

Acceptance:
- Cleaning reduces components in noisy synthetic masks.
- Metrics are stable and documented.
```

## Summary of work performed

1. **Added opencv-python dependency** (version >=4.8.0)
   - Provides morphologyEx for morphological operations
   - Provides connectedComponentsWithStats for component analysis
   - Provides findContours for contour estimation

2. **Implemented stencil_opt.py** with cuttability optimization:
   - `morph_cleanup()`: Morphological smoothing
     * Close operation: Fills small holes in cutouts
     * Open operation: Removes small protrusions and noise
     * Kernel size proportional to min_feature_px
     * Uses elliptical structuring element for smooth results
   - `remove_small_cutouts()`: Connected component filtering
     * Uses OpenCV connectedComponentsWithStats with 8-connectivity
     * Removes components smaller than min_area_px
     * Preserves only cuttable-sized features
   - `compute_layer_metrics()`: Layer quality metrics
     * cutout_component_count: Number of disconnected regions
     * smallest_component_area_px: Size of smallest component
     * total_open_area_px: Total area where mask == 1
     * estimated_contour_length_px: Approximate perimeter using arcLength

3. **Morphological operations**:
   - Closing (dilation then erosion): Fills small holes, connects nearby regions
   - Opening (erosion then dilation): Removes small protrusions, smooths edges
   - Kernel size: max(3, min_feature_px | 1) to ensure odd size
   - Elliptical kernel for natural, isotropic smoothing

4. **Connected component analysis**:
   - 8-connectivity for diagonal connections
   - Background label (0) excluded from counting
   - Area-based filtering preserves large, cuttable features
   - Component statistics used for metrics

5. **Comprehensive tests** (28 new tests, 215 total):
   - test_stencil_opt.py (28 tests):
     * Morphological cleanup (noise removal, hole filling, edge smoothing)
     * Small cutout removal (threshold tests, connectivity)
     * Layer metrics computation (empty, full, multiple components)
     * Full pipeline (morph + remove)
     * Error handling and validation

## Commands executed

```bash
# Add opencv-python dependency
uv sync

# Test imports
uv run python -c "from stencilify.stencil_opt import morph_cleanup, remove_small_cutouts, compute_layer_metrics"

# Run stencil optimization tests
uv run pytest tests/test_stencil_opt.py -v

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
27 files already formatted

$ uv run ruff check .
All checks passed!

$ uv run mypy .
Success: no issues found in 27 source files

$ uv run pytest -q
============================= test session starts ==============================
collected 215 items
tests/test_cli.py ...............                                        [  6%]
tests/test_config.py ...........................                         [ 19%]
tests/test_geometry.py ............                                      [ 25%]
tests/test_imageio.py ...........                                        [ 30%]
tests/test_labeling.py ........................                          [ 41%]
tests/test_layers.py .....................                               [ 51%]
tests/test_locks.py ....................                                 [ 60%]
tests/test_masks.py ..................                                   [ 68%]
tests/test_preview.py ....................                               [ 78%]
tests/test_stencil_opt.py ............................                   [ 91%]
tests/test_superpixels.py ...................                            [100%]

============================== 215 passed in 3.95s ==============================
```

**Result**: PASS ✓

## Files changed (high-level)

**New files:**
- `src/stencilify/stencil_opt.py` - Morphological cleanup, cutout removal, metrics
- `tests/test_stencil_opt.py` - 28 tests for stencil optimization

**Modified files:**
- `pyproject.toml` - Added opencv-python>=4.8.0 dependency
- `uv.lock` - Updated with opencv-python

## Deviations / Decisions

1. **OpenCV for operations**: Used OpenCV instead of scipy for better performance and feature set
2. **Elliptical kernel**: Chose elliptical structuring element for isotropic smoothing
3. **8-connectivity**: Used 8-connectivity (diagonal neighbors) for component analysis
4. **Kernel size formula**: max(3, min_feature_px | 1) ensures odd size and minimum of 3x3
5. **Closing before opening**: Standard order for morphological cleanup (fill then smooth)
6. **Area-based filtering**: Simple area threshold, no shape-based filtering yet
7. **Contour approximation**: CHAIN_APPROX_SIMPLE for efficient contour storage
8. **Single pixel handling**: Allow 0 contour length for degenerate cases

## Notes / Follow-ups

- All acceptance criteria met: Cleaning reduces components, metrics documented
- 215 total tests (28 new), all passing
- Morphological operations effectively smooth edges and remove noise
- Connected component filtering successfully removes small uncuttable features
- Metrics provide useful diagnostics for layer quality
- Pipeline (morph + remove) produces clean, cuttable masks
- Ready for Step 8 (next stage of pipeline)
