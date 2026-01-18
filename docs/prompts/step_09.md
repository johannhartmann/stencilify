# Step 09 Prompt

```
Implement island fixing: fill small islands, add bridges for large ones.

Goal: Ensure the physical stencil stays in one piece.

Policy:
- For each material island:
  - if area_px < min_island_area_px: fill it (convert that material island to open area, i.e., set open_mask=1 there)
  - else if bridge_width_mm > 0: add a bridge (a strip of material) connecting island to supported material

Bridge algorithm (practical):
1) Compute a distance transform over supported material to find nearest support for each island pixel.
2) For each large island:
   - pick the island pixel with minimal distance to support
   - find its nearest support pixel (use distance transform labeling if available; otherwise approximate by searching within a radius)
   - draw a thick line (bridge) between them in MATERIAL space:
       set open_mask=0 along the line with thickness bridge_width_px
3) Recompute islands once after bridges; if islands remain, add up to max_bridge_attempts per island.

Requirements:
- Use OpenCV distanceTransform where possible.
- bridge_width_px = round(bridge_width_mm * px_per_mm)
- Provide a cap on attempts and log warnings if unresolved.

Tasks:
1) Add src/stencilify/bridges.py:
   - fix_islands(open_mask01, min_island_area_px, bridge_width_px, max_attempts=3) -> (open_mask01, BridgeReport)
2) Add tests on synthetic ring shapes where bridges resolve islands.

Acceptance:
- Rings become connected material after bridging OR get filled if below threshold.
- BridgeReport records how many bridges were added and where.
```
