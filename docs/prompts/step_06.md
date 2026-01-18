# Step 06 Prompt

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
