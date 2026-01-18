# Step 13 Prompt: Autotuning Mode

Add an autotuning mode.

Goal: When --autotune is enabled, search over a small parameter grid and select the best candidate according to a scoring function.

Parameters to tune (example grid; keep modest):
- n_segments: [800, 1200, 1800, 2500]
- smooth_lambda: [5, 10, 20]
- slic_compactness: [10, 15, 20]
- cleanup_strength multiplier for morphology: [0.8, 1.0, 1.2]

Score function (lower is better):
score = w1 * palette_error + w2 * cutout_components + w3 * island_count + w4 * contour_complexity
Where:
- palette_error: mean Lab distance between assigned palette color and original pixel Lab within silhouette
- cutout_components: sum across layers after cleanup
- island_count: sum across layers after bridges/fill
- contour_complexity: approximate total contour length or number of contour points

Requirements:
- Use deterministic randomness via seed.
- Save the best run config into report.json.
- Optionally save a "candidates.csv" with all candidate metrics.

Tasks:
- Implement src/stencilify/autotune.py
- Integrate with pipeline so that non-autotune uses config defaults, autotune overrides.
- Add at least one test ensuring autotune returns a candidate and is deterministic.

Acceptance:
- Autotune runs in reasonable time for medium images (don't overdo the grid).
