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
