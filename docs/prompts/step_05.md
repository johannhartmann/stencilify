# Step 05 Prompt

```
Implement palette-constrained labeling over superpixels.

Goal: Assign each superpixel to one of K palette colors (K=2..4), minimizing:
E = sum_i D(i, label_i) + lambda * sum_(i,j in edges) [label_i != label_j]
with optional hard locks that force some pixels/superpixels to a specific label.

Requirements:
- Convert palette colors (HEX) to Lab.
- Data term D(i,c): Euclidean distance between mean_lab[i] and palette_lab[c].
- Smoothness: Potts model with constant penalty lambda.
- Optimization: implement ICM / coordinate descent over superpixel labels:
  - Initialize labels by argmin D(i,c)
  - Iterate N times (configurable, default 10) updating each superpixel to best label given neighbors.
- Locks:
  - CLI can provide --lock "#FFD200"=mask.png
  - Load lock masks; within silhouette; derive which superpixels are locked to which label.
  - If conflicting locks exist, raise a clear error.
- Output:
  - label_map_pixels [H,W] with palette index (0..K-1) within silhouette
  - label_per_spx [spx_count]

Tasks:
1) Add src/stencilify/labeling.py with:
   - hex_to_rgb, rgb_to_lab utilities (or use OpenCV conversion)
   - assign_labels_icm(mean_lab, edges, palette_lab, smooth_lambda, locked_spx, iters, seed)
2) Add src/stencilify/locks.py for loading lock masks and mapping to superpixels.
3) Add tests:
   - With no locks, labels converge to expected simple result.
   - With a lock, forced assignment holds.

Acceptance:
- Deterministic given seed.
- Produces palette index maps limited to silhouette.
```
