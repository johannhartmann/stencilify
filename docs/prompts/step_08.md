# Step 08 Prompt

```
Add island detection for stencil material support.

Goal: Identify "material islands" that would fall out of the stencil: connected components of material (material = 1 - open_mask) that do NOT touch the canvas border.

Requirements:
- For a layer:
  material01 = 1 - open_mask01
- Connected components on material01.
- A component is "supported" if it touches any border pixel (top, bottom, left, right).
- All other components are islands.
- Return:
  - island_mask01 (1 where island material exists)
  - island_stats list: area_px, bbox, centroid

Tasks:
1) Add functions in src/stencilify/islands.py:
   - find_material_islands(open_mask01) -> IslandResult
2) Add tests with small handcrafted masks:
   - a ring shape creates an island
   - a component touching border is not an island

Acceptance:
- Island detection correctly identifies unsupported material.
```
