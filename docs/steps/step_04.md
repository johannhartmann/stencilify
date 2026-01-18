# Step 04 — Superpixelization and adjacency

## Prompt (verbatim)

```
step 4: Implement superpixelization and adjacency.

Goal: Produce SLIC superpixels within the silhouette mask and compute an adjacency graph between superpixels.

Requirements:
- Use scikit-image SLIC.
- Run SLIC on Lab or RGB, but ensure stable results for portraits.
- Only compute superpixels inside silhouette mask (outside can be ignored).
- Return:
  - spx_labels: int32 [H,W], superpixel id per pixel
  - spx_count: number of superpixels
  - adjacency list: list[tuple[int,int]] edges (undirected, unique)
  - per-superpixel mean color in Lab: mean_lab[spx_count,3]
- Provide config knobs:
  - n_segments (autotune will change later)
  - compactness
  - sigma

Tasks:
1) Add src/stencilify/superpixels.py with:
   - compute_superpixels(rgb, silhouette01, n_segments, compactness, sigma) -> SuperpixelResult
   - build_adjacency(spx_labels, spx_count, silhouette01) -> edges
   - compute_mean_lab(rgb, spx_labels, spx_count) -> mean_lab
2) Add a quick benchmark-safe implementation (avoid Python loops over pixels; use numpy ops).
3) Add unit tests on a small synthetic image with clear regions.

Acceptance:
- Works on small tests quickly.
- No dependency on GPU; pure CPU is fine.

Do not assign palette labels yet.
```

## Summary of work performed

1. **Added scikit-image dependency** for SLIC superpixel segmentation
2. **Implemented superpixels.py** with:
   - `compute_superpixels()`: Main function using scikit-image SLIC
     * Converts RGB to Lab color space for perceptual uniformity
     * Runs SLIC with mask support (only within silhouette)
     * Relabels superpixels to ensure contiguous IDs [0, count-1]
     * Builds adjacency graph
     * Computes mean Lab color per superpixel
   - `build_adjacency()`: 4-connectivity graph building
     * Efficient numpy-based implementation (no pixel loops)
     * Checks horizontal and vertical neighbors
     * Returns unique undirected edges where i < j
   - `compute_mean_lab()`: Per-superpixel mean Lab colors
     * Uses numpy bincount for efficient computation
     * Returns [count, 3] array of mean Lab values
   - `SuperpixelResult` dataclass with labels, count, adjacency, mean_lab
3. **Configuration parameters**:
   - n_segments: Target number of superpixels (default 100)
   - compactness: SLIC compactness parameter (default 10.0)
   - sigma: Gaussian smoothing before SLIC (default 1.0)
4. **Comprehensive tests** (19 new tests, 102 total):
   - Basic superpixel computation
   - Masking (superpixels only within silhouette)
   - Adjacency building with various patterns
   - Mean Lab computation
   - Input validation and error handling
   - Determinism with same parameters
   - Performance testing (< 2s for 100x100 image)
5. **Fixed test issue**: test_superpixels_respects_n_segments
   - Changed from random noise to structured 5x5 grid of color blocks
   - Ensures reliable segmentation for different n_segments values

## Commands executed

```bash
# Add scikit-image dependency
uv sync

# Test imports
uv run python -c "from stencilify.superpixels import compute_superpixels, build_adjacency, compute_mean_lab"

# Run superpixel tests
uv run pytest tests/test_superpixels.py -v
uv run pytest tests/test_superpixels.py::test_superpixels_respects_n_segments -v

# Format code
uv run ruff format tests/test_superpixels.py

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
17 files already formatted

$ uv run ruff check .
All checks passed!

$ uv run mypy .
Success: no issues found in 17 source files

$ uv run pytest -q
============================= test session starts ==============================
collected 102 items
tests/test_cli.py ...............                                        [ 14%]
tests/test_config.py ...........................                         [ 41%]
tests/test_geometry.py ............                                      [ 52%]
tests/test_imageio.py ...........                                        [ 63%]
tests/test_masks.py ..................                                   [ 81%]
tests/test_superpixels.py ...................                            [100%]

============================== 102 passed in 3.72s ==============================
```

**Result**: PASS ✓

## Files changed (high-level)

**New files:**
- `src/stencilify/superpixels.py` - SLIC superpixel segmentation, adjacency building, mean Lab computation
- `tests/test_superpixels.py` - 19 tests for superpixel functionality

**Modified files:**
- `pyproject.toml` - Added scikit-image>=0.22.0 dependency
- `uv.lock` - Updated with scikit-image and dependencies

## Deviations / Decisions

1. **Lab color space**: Used Lab for SLIC to ensure perceptually uniform segmentation
2. **Efficient adjacency**: Implemented numpy-based adjacency building to avoid Python loops
3. **4-connectivity**: Used horizontal/vertical neighbors only (not diagonal)
4. **Test fix**: Changed test_superpixels_respects_n_segments to use structured color grid instead of random noise for reliable segmentation

## Notes / Follow-ups

- All acceptance criteria met: SLIC implementation, adjacency graph, mean Lab colors, config knobs
- 102 total tests (19 new), all passing
- Performance: 100x100 image completes in < 2s
- No GPU dependency (pure CPU implementation)
- Superpixel count is approximate (SLIC may produce fewer than n_segments)
- Ready for Step 5 (palette quantization)
