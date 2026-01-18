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
