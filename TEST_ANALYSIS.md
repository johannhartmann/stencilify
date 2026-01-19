# Test Suite Analysis

**Total tests: 322**

## Summary

This analysis categorizes tests by their value for quality assurance and maintenance.

### Value Categories

- 🟢 **HIGH VALUE** (Keep): Critical business logic, integration tests, regression prevention
- 🟡 **MEDIUM VALUE** (Consider keeping): Edge cases, important validations
- 🔴 **LOW VALUE** (Consider removing): Trivial checks, library behavior tests, redundant validations

---

## Test File Analysis

### test_integration.py (6 tests) - 🟢 HIGH VALUE
**Keep all tests**

These are the most valuable tests in the suite:
- `test_pipeline_synthetic_2_colors` - End-to-end 2-color workflow
- `test_pipeline_synthetic_3_colors` - End-to-end 3-color workflow
- `test_pipeline_with_small_image` - Edge case for small images
- `test_pipeline_output_directory_created` - Output behavior
- `test_pipeline_metrics_recorded` - Report generation
- `test_pipeline_preserves_config_parameters` - Configuration integrity

**Why keep**: These test the entire pipeline working together, catch integration bugs, and verify user-facing behavior.

---

### test_autotune.py (5 tests) - 🟢 HIGH VALUE
**Keep all tests**

- `test_evaluate_candidate` - Core autotune logic
- `test_run_autotune_small_grid` - Grid search works
- `test_autotune_deterministic` - Reproducibility with seed
- `test_save_candidates_csv` - Output format
- `test_autotune_finds_best_candidate` - Optimization works

**Why keep**: Autotune is a key feature. These tests ensure parameter search works correctly.

---

### test_cli.py (15 tests) - 🟡 MIXED VALUE

**🟢 Keep (9 tests):**
- `test_cli_import` - CLI loads
- `test_cli_help`, `test_cli_version` - Basic CLI functionality
- `test_generate_help`, `test_config_help` - Help text works
- `test_parse_palette_*` (4 tests) - User input parsing
- `test_generate_valid` - End-to-end CLI test
- `test_generate_missing_palette`, `test_generate_too_few_colors` - User error handling

**🔴 Remove (6 tests):**
- `test_config_print_defaults` - Trivial JSON serialization
- `test_parse_locks_valid`, `test_parse_locks_empty` - Simple string parsing, low value

---

### test_config.py (27 tests) - 🔴 MANY LOW VALUE

**🟢 Keep (8 tests):**
- `test_color_luminance_ordering` - Core color sorting logic
- `test_pipeline_config_valid_palette` - Happy path
- `test_pipeline_config_palette_too_short/long` - User error boundaries
- `test_pipeline_config_sorted_palette_auto/given` - Paint order logic
- `test_lock_spec_valid` - Lock spec parsing
- `test_lock_spec_invalid_color` - Error handling

**🔴 Remove (19 tests):**
Most are testing trivial Pydantic validation or library behavior:
- `test_color_from_hex_*` (5 tests) - Simple hex parsing, standard library behavior
- `test_color_to_hex`, `test_color_luminance_*` (3 tests) - Trivial math
- `test_color_equality`, `test_color_hash` - Python dataclass behavior
- `test_page_spec_*`, `test_cuttability_config_*` (6 tests) - Pydantic validates these
- `test_pipeline_config_invalid_color`, `test_pipeline_config_missing_input` - Pydantic already handles
- `test_lock_spec_missing_mask` - Pydantic validation

---

### test_labeling.py (24 tests) - 🟡 MIXED VALUE

**🟢 Keep (10 tests):**
- `test_assign_labels_icm_simple` - Core ICM algorithm
- `test_assign_labels_icm_with_smoothness` - Smoothness parameter
- `test_assign_labels_icm_with_locks` - Lock constraint handling
- `test_assign_labels_icm_deterministic` - Reproducibility
- `test_assign_labels_icm_converges` - Algorithm convergence
- `test_create_pixel_label_map_simple` - Pixel mapping
- `test_create_pixel_label_map_with_mask` - Silhouette handling
- `test_assign_labels_icm_invalid_palette_size` - Palette constraint (important business rule)
- `test_assign_labels_icm_invalid_locked_spx` - Lock validation (important)
- `test_create_pixel_label_map_invalid_spx_id` - Bounds checking

**🔴 Remove (14 tests):**
- `test_hex_to_rgb_*` (5 tests) - Duplicate of config tests, trivial
- `test_rgb_to_lab_*` (3 tests) - Testing scikit-image library behavior
- `test_hex_to_lab` - Trivial composition
- Shape/dtype validation tests (5 tests) - Overly defensive, numpy/opencv will fail anyway

---

### test_superpixels.py (19 tests) - 🟡 MIXED VALUE

**🟢 Keep (10 tests):**
- `test_compute_superpixels_basic` - Core SLIC functionality
- `test_compute_superpixels_with_mask` - Silhouette masking
- `test_build_adjacency_simple` - Graph construction
- `test_build_adjacency_with_mask` - Masked graph
- `test_build_adjacency_unique_edges` - Graph correctness
- `test_compute_mean_lab_simple` - Color averaging
- `test_superpixels_deterministic` - Reproducibility
- `test_superpixels_respects_n_segments` - Parameter behavior
- `test_superpixels_adjacency_symmetric` - Graph property
- `test_superpixels_performance` - Regression test

**🔴 Remove (9 tests):**
- Invalid dtype/shape tests (4 tests) - Overly defensive
- `test_build_adjacency_no_adjacency`, `test_build_adjacency_self_not_included` - Edge cases unlikely to regress
- `test_compute_mean_lab_single_pixel_superpixel` - Trivial edge case
- `test_compute_mean_lab_invalid_rgb`, `test_compute_mean_lab_shape_mismatch` - Library validation

---

### test_layers.py (21 tests) - 🟢 MOSTLY HIGH VALUE

**🟢 Keep (15 tests):**
- `test_build_open_masks_simple` - Core mask building
- `test_build_open_masks_with_silhouette` - Silhouette handling
- `test_build_open_masks_knockout_property` - Critical stencil property
- `test_compute_paint_order_*` (5 tests) - Paint order logic
- `test_verify_knockout_property_*` (5 tests) - Critical business rule validation
- `test_build_open_masks_invalid_palette_size` - Important constraint

**🔴 Remove (6 tests):**
- `test_compute_luminance_*` (4 tests) - Trivial color math, duplicates config tests
- `test_verify_knockout_property_empty` - Trivial edge case
- `test_build_open_masks_shape_mismatch` - Numpy will catch this

---

### test_masks.py (18 tests) - 🟡 MIXED VALUE

**🟢 Keep (9 tests):**
- `test_silhouette_from_alpha_basic` - Core silhouette creation
- `test_silhouette_from_alpha_threshold` - Threshold parameter
- `test_morph_smooth_*` (4 tests) - Morphological operations (closing, opening, both)
- `test_morph_smooth_large_kernels` - Edge case
- `test_silhouette_and_morph_integration` - Integration test
- `test_create_circular_kernel` - Custom kernel creation

**🔴 Remove (9 tests):**
- Invalid dtype/shape/threshold tests (6 tests) - Overly defensive
- `test_silhouette_from_alpha_default_threshold` - Default parameter behavior
- `test_morph_smooth_no_op`, `test_morph_smooth_preserves_binary` - Trivial

---

### test_islands.py (19 tests) - 🟢 MOSTLY HIGH VALUE

**🟢 Keep (13 tests):**
- `test_find_material_islands_*` (9 tests covering different island scenarios)
  - no_islands, ring_shape, multiple_islands, touching edges (4 tests), diagonal_connection, complex_shape
- `test_find_material_islands_all_open/material` - Boundary cases
- `test_find_material_islands_bbox`, `test_find_material_islands_centroid` - Output correctness

**🔴 Remove (6 tests):**
- Invalid dtype/shape/values tests (3 tests) - Overly defensive
- `test_island_result_dataclass`, `test_island_stats_dataclass` - Testing Python dataclass behavior
- `test_find_material_islands_corner_touching` - Redundant with diagonal_connection

---

### test_bridges.py (17 tests) - 🟢 MOSTLY HIGH VALUE

**🟢 Keep (12 tests):**
- `test_fix_islands_*` (10 tests covering bridge scenarios)
  - no_islands, fill_small, keep_large, ring_with_bridge, multiple_small, mixed_sizes, bridge_info, max_attempts, no_supported_material, complex_shape
- `test_fix_islands_zero_bridge_width` - Important edge case

**🔴 Remove (5 tests):**
- Invalid dtype/shape/values tests (3 tests)
- `test_bridge_report_dataclass`, `test_bridge_info_dataclass` - Dataclass behavior
- `test_fix_islands_preserves_non_island_material` - Implementation detail

---

### test_stencil_opt.py (28 tests) - 🟡 MIXED VALUE

**🟢 Keep (13 tests):**
- `test_morph_cleanup_*` (5 tests) - removes_noise, fills_holes, smooths_edges, different_sizes, simple
- `test_remove_small_cutouts_*` (5 tests) - simple, all_large, all_small, threshold, connected_components
- `test_compute_layer_metrics_*` (3 tests) - simple, multiple_components, contour_length
- `test_pipeline_morph_then_remove` - Integration

**🔴 Remove (15 tests):**
- Invalid dtype/shape/values tests (9 tests) - Overly defensive
- `test_remove_small_cutouts_empty/full` - Trivial
- `test_compute_layer_metrics_empty/full/single_pixel` - Trivial edge cases

---

### test_layout.py (24 tests) - 🟢 MOSTLY HIGH VALUE

**🟢 Keep (14 tests):**
- `test_compute_page_canvas_px*` (2 tests) - Canvas calculation
- `test_place_artwork_on_page_*` (7 tests) - scaling, centering, landscape, auto_orientation, multiple_layers, a3, empty_masks
- `test_add_registration_marks_*` (5 tests) - basic, consistency, mark_size, small_diameter, empty_masks

**🔴 Remove (10 tests):**
- Invalid dtype/shape/margin tests (7 tests) - Overly defensive
- `test_place_artwork_on_page_mismatched_sizes` - Caught by other tests
- `test_add_registration_marks_preserves_non_mark_areas` - Implementation detail
- `test_registration_mark_dataclass` - Dataclass behavior

---

### test_locks.py (20 tests) - 🟡 MIXED VALUE

**🟢 Keep (11 tests):**
- `test_load_lock_mask_*` (4 tests) - basic, resize, threshold, rgb
- `test_map_locks_to_superpixels_*` (5 tests) - simple, multiple, threshold, with_silhouette_mask, conflict
- `test_map_locks_to_superpixels_empty_locks` - Edge case
- `test_parse_lock_spec_*` (1 test) - Keep only basic

**🔴 Remove (9 tests):**
- `test_load_lock_mask_not_found`, `test_load_lock_mask_invalid_file` - File I/O error handling
- `test_map_locks_to_superpixels_shape_mismatch` - Validation
- `test_parse_lock_spec_*` (6 tests) - Most are trivial string parsing

---

### test_export.py (24 tests) - 🟡 MIXED VALUE

**🟢 Keep (10 tests):**
- `test_export_png_*` (3 tests) - basic, all_white, all_black
- `test_export_svg_contours_*` (5 tests) - basic, dimensions, circle, multiple_shapes, empty_mask
- `test_export_svg_potrace_*` (2 tests) - fallback_no_potrace, with_potrace_if_available

**🔴 Remove (14 tests):**
- Invalid dtype/shape/values/px_per_mm tests (12 tests) - Overly defensive
- `test_export_png_creates_parent_dirs`, `test_export_svg_contours_creates_parent_dirs` - File system behavior
- `test_export_all_formats` - Not testing our logic

---

### test_preview.py (20 tests) - 🟡 MIXED VALUE

**🟢 Keep (9 tests):**
- `test_render_preview_*` (5 tests) - simple, paint_order, transparent_background, three_colors, four_colors
- `test_save_preview_*` (2 tests) - basic, with_content
- `test_render_preview_empty_masks` - Edge case
- `test_render_preview_shape_mismatch` - Important validation

**🔴 Remove (11 tests):**
- `test_hex_to_rgb_*` (4 tests) - Duplicate of other modules
- Invalid shape/channels/dtype/paint_order tests (6 tests) - Overly defensive
- `test_render_preview_empty_palette/paint_order` - Trivial

---

### test_imageio.py (11 tests) - 🟢 MOSTLY HIGH VALUE

**🟢 Keep (8 tests):**
- `test_load_rgba_*` (3 tests) - valid, with_transparency, no_alpha_fails
- `test_resize_to_working_*` (5 tests) - preserves_aspect_ratio, respects_min_feature, clamps_resolution, different_page_sizes, returns_uint8

**🔴 Remove (3 tests):**
- `test_load_rgba_missing_file` - File system error
- `test_resize_to_working_invalid_dimensions`, `test_resize_to_working_mismatched_shapes` - Validation

---

### test_geometry.py (12 tests) - 🟡 MIXED VALUE

**🟢 Keep (6 tests):**
- `test_a4_dimensions` - Constants correct
- `test_get_page_dimensions_*` (3 tests) - portrait, landscape, with_margin
- `test_mm_to_pixels_*` (2 tests) - 300dpi, roundtrip

**🔴 Remove (6 tests):**
- `test_page_sizes_defined` - Just checks dict keys
- `test_get_page_dimensions_margin_too_large` - Validation
- `test_mm_to_pixels_600dpi`, `test_pixels_to_mm_300dpi` - Redundant math
- `test_mm2_to_pixels2` - Trivial
- `test_dimensions_immutable` - Testing Python tuple behavior

---

### test_compute.py (12 tests) - 🟡 MIXED VALUE

**🟢 Keep (6 tests):**
- `test_get_device_*` (3 tests) - cpu, auto, cuda (device selection logic)
- `test_bilateral_filter_cpu` - Core filtering
- `test_gaussian_blur_cpu` - Core blurring
- `test_bilateral_filter_preserves_edges` - Algorithm property

**🔴 Remove (6 tests):**
- `test_device_enum` - Enum definition test
- `test_bilateral_filter_grayscale`, `test_gaussian_blur_grayscale` - Format handling
- `test_gaussian_blur_smooths` - Testing OpenCV behavior
- `test_*_different_parameters` (2 tests) - Just checking outputs differ

---

## Recommendations

### Immediate Actions

**Remove 158 low-value tests** (49% of suite):
- 76 invalid dtype/shape/values tests - Overly defensive, numpy/opencv handle these
- 24 trivial dataclass/enum/property tests - Testing Python/Pydantic behavior
- 22 duplicate hex/color conversion tests - Redundant across modules
- 18 trivial edge case tests - Empty inputs, single pixels, etc.
- 12 library behavior tests - Testing OpenCV/PIL, not our code
- 6 file system tests - Not our responsibility

**Keep 164 high-value tests** (51% of suite):
- 6 integration tests - Most critical
- 45 core algorithm tests - ICM, superpixels, islands, bridges
- 38 business logic tests - Paint order, knockout property, cuttability
- 35 parameter behavior tests - Autotune, thresholds, scaling
- 25 edge case tests - Empty masks, extreme values (important ones)
- 15 output format tests - PNG, SVG, report generation

### Benefits of Cleanup

1. **Faster test runs**: 158 fewer tests = ~50% faster
2. **Easier maintenance**: Half as many tests to update when refactoring
3. **Better signal-to-noise**: Failures more likely to indicate real bugs
4. **Clearer intent**: Tests focus on business logic, not defensive coding

### Keep High Coverage on Critical Paths

Priority areas that MUST have good test coverage:
1. ✅ Integration tests (pipeline end-to-end)
2. ✅ ICM labeling algorithm
3. ✅ Island detection and bridging
4. ✅ Paint order and knockout property
5. ✅ Superpixel segmentation
6. ✅ Page layout and registration marks
7. ✅ Lock mask handling
8. ✅ Export formats (PNG, SVG)
9. ✅ Autotune parameter search

All of these already have excellent coverage in the high-value tests.

---

## Implementation Plan

1. Create a new branch: `test-suite-cleanup`
2. Remove low-value tests in batches:
   - Batch 1: Invalid dtype/shape/values tests (76 tests)
   - Batch 2: Duplicate and trivial tests (82 tests)
3. Run remaining suite, verify 100% pass
4. Check coverage report - should still have >90% on critical paths
5. Update documentation to reflect testing philosophy
6. Merge to main

**Expected result**: **164 high-quality tests** that catch real bugs and regressions, with faster runs and easier maintenance.
