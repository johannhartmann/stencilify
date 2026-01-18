# Step 07 Prompt

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
