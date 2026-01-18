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
