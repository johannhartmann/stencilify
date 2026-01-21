"""End-to-end stencil generation pipeline."""

import json
import logging
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

from stencilify.autotune import run_autotune, save_candidates_csv
from stencilify.bridges import fix_islands
from stencilify.config import PipelineConfig, VectorBackend
from stencilify.export import export_png, export_svg_contours, export_svg_potrace
from stencilify.geometry import mm2_to_pixels2, mm_to_pixels
from stencilify.imageio import load_rgba
from stencilify.islands import find_material_islands
from stencilify.labeling import assign_labels_icm, create_pixel_label_map
from stencilify.layers import build_open_masks, compute_paint_order
from stencilify.layout import add_registration_marks, place_artwork_on_page
from stencilify.locks import load_lock_mask, map_locks_to_superpixels
from stencilify.masks import silhouette_from_alpha
from stencilify.preview import render_preview
from stencilify.stencil_opt import (
    compute_layer_metrics,
    morph_cleanup,
    remove_small_cutouts,
)
from stencilify.superpixels import compute_superpixels

logger = logging.getLogger(__name__)


@dataclass
class LayerMetrics:
    """Metrics for a single layer."""

    color: str
    # Before optimization
    material_pixels_before: int
    open_pixels_before: int
    contours_count_before: int
    # After optimization
    material_pixels_after: int
    open_pixels_after: int
    contours_count_after: int
    contour_length_after: float
    # Island fixing
    islands_found: int
    islands_filled: int
    bridges_added: int


@dataclass
class PipelineResult:
    """Result of running the stencil generation pipeline."""

    # Configuration
    input_image: str
    palette: list[str]
    paint_order: str
    page_size: str
    page_orientation: str
    px_per_mm: float

    # Parameters
    margin_mm: float
    min_feature_mm: float
    min_island_area_mm2: float
    bridge_width_mm: float

    # Superpixel parameters
    superpixel_count: int
    superpixel_compactness: float
    smooth_lambda: float = 1.0
    cleanup_strength: float = 1.0

    # Autotune results (if enabled)
    autotune_enabled: bool = False
    autotune_best_score: float | None = None
    autotune_candidates_evaluated: int = 0

    # Per-layer metrics
    layers: list[LayerMetrics] = field(default_factory=list)

    # Warnings
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result_dict = {
            "input_image": self.input_image,
            "palette": self.palette,
            "paint_order": self.paint_order,
            "page": {
                "size": self.page_size,
                "orientation": self.page_orientation,
                "margin_mm": self.margin_mm,
            },
            "resolution": {
                "px_per_mm": self.px_per_mm,
            },
            "parameters": {
                "min_feature_mm": self.min_feature_mm,
                "min_island_area_mm2": self.min_island_area_mm2,
                "bridge_width_mm": self.bridge_width_mm,
                "smooth_lambda": self.smooth_lambda,
                "cleanup_strength": self.cleanup_strength,
            },
            "superpixels": {
                "count": self.superpixel_count,
                "compactness": self.superpixel_compactness,
            },
            "layers": [
                {
                    "color": layer.color,
                    "before_optimization": {
                        "material_pixels": layer.material_pixels_before,
                        "open_pixels": layer.open_pixels_before,
                        "contours": layer.contours_count_before,
                    },
                    "after_optimization": {
                        "material_pixels": layer.material_pixels_after,
                        "open_pixels": layer.open_pixels_after,
                        "contours": layer.contours_count_after,
                        "contour_length": layer.contour_length_after,
                    },
                    "island_fixing": {
                        "islands_found": layer.islands_found,
                        "islands_filled": layer.islands_filled,
                        "bridges_added": layer.bridges_added,
                    },
                }
                for layer in self.layers
            ],
            "warnings": self.warnings,
        }

        # Add autotune info if enabled
        if self.autotune_enabled:
            result_dict["autotune"] = {
                "enabled": True,
                "best_score": self.autotune_best_score,
                "candidates_evaluated": self.autotune_candidates_evaluated,
            }

        return result_dict


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    """
    Run the complete stencil generation pipeline.

    Args:
        config: Pipeline configuration

    Returns:
        PipelineResult with metrics and warnings

    Raises:
        ValueError: On fatal errors
        FileNotFoundError: If input image not found
    """
    logger.info("=" * 60)
    logger.info("Starting stencilify pipeline")
    logger.info("=" * 60)

    # Determine compute device
    from stencilify.compute import Device, get_device

    device_str = get_device(Device(config.device))
    logger.info(f"Compute device: {device_str}")

    # Determine resolution
    px_per_mm = 300.0 / 25.4  # 300 DPI

    # Run autotune if enabled
    if config.autotune.enabled:
        autotune_result = run_autotune(config, px_per_mm)

        # Use best parameters
        n_segments = autotune_result.best_params.n_segments
        compactness = autotune_result.best_params.slic_compactness
        smooth_lambda = autotune_result.best_params.smooth_lambda
        cleanup_strength = autotune_result.best_params.cleanup_strength

        # Save candidates CSV
        candidates_path = config.export.output_dir / "candidates.csv"
        config.export.output_dir.mkdir(parents=True, exist_ok=True)
        save_candidates_csv(autotune_result.all_candidates, candidates_path)

        # Initialize result with autotune info
        result = PipelineResult(
            input_image=str(config.input_image),
            palette=config.palette,
            paint_order=config.paint_order.value,
            page_size=config.page.size.value,
            page_orientation=config.page.orientation.value,
            px_per_mm=px_per_mm,
            margin_mm=config.page.margin_mm,
            min_feature_mm=config.cuttability.min_feature_mm,
            min_island_area_mm2=config.cuttability.min_island_area_mm2,
            bridge_width_mm=config.cuttability.bridge_width_mm,
            superpixel_count=n_segments,
            superpixel_compactness=compactness,
            smooth_lambda=smooth_lambda,
            cleanup_strength=cleanup_strength,
            autotune_enabled=True,
            autotune_best_score=autotune_result.best_score,
            autotune_candidates_evaluated=len(autotune_result.all_candidates),
        )
    else:
        # Use default parameters
        n_segments = 500
        compactness = 10.0
        smooth_lambda = 1.0
        cleanup_strength = 1.0

        result = PipelineResult(
            input_image=str(config.input_image),
            palette=config.palette,
            paint_order=config.paint_order.value,
            page_size=config.page.size.value,
            page_orientation=config.page.orientation.value,
            px_per_mm=px_per_mm,
            margin_mm=config.page.margin_mm,
            min_feature_mm=config.cuttability.min_feature_mm,
            min_island_area_mm2=config.cuttability.min_island_area_mm2,
            bridge_width_mm=config.cuttability.bridge_width_mm,
            superpixel_count=n_segments,
            superpixel_compactness=compactness,
            smooth_lambda=smooth_lambda,
            cleanup_strength=cleanup_strength,
        )

    # Step 1: Load image + working resize + silhouette
    logger.info("Step 1: Loading image and creating silhouette")
    rgb, alpha = load_rgba(config.input_image)
    logger.info(f"  Loaded image: {rgb.shape[1]}x{rgb.shape[0]} pixels")

    # Combine for RGBA
    rgba = np.dstack([rgb, alpha[:, :, np.newaxis]]).astype(np.uint8)

    # Create silhouette from alpha channel
    silhouette = silhouette_from_alpha(alpha)
    foreground_pixels = int(np.sum(silhouette))
    logger.info(f"  Silhouette: {foreground_pixels} foreground pixels")

    # Step 2: Superpixels
    logger.info("Step 2: Computing superpixels")
    logger.info(f"  Using n_segments={n_segments}, compactness={compactness}")

    spx_result = compute_superpixels(
        rgb,
        silhouette,
        n_segments=n_segments,
        compactness=compactness,
    )

    spx_labels = spx_result.labels
    result.superpixel_count = spx_result.count
    logger.info(f"  Created {spx_result.count} superpixels")

    # Use pre-computed adjacency and mean_lab from result
    adjacency = spx_result.adjacency
    mean_lab = spx_result.mean_lab
    logger.info(f"  Computed adjacency: {len(adjacency)} edges")

    # Step 3: Palette labeling (+ locks)
    logger.info("Step 3: Palette-constrained labeling")

    # Get sorted palette
    sorted_palette = config.get_sorted_palette()
    palette_hex = [color.to_hex() for color in sorted_palette]
    logger.info(f"  Palette: {', '.join(palette_hex)}")

    # Convert palette to Lab color space
    palette_lab = np.array([[color.luminance() * 100, 0, 0] for color in sorted_palette])

    # mean_lab is already computed in spx_result above

    # Handle locks
    locked_spx = None
    if config.locks:
        logger.info(f"  Processing {len(config.locks)} lock(s)")
        lock_masks = {}
        for lock_spec in config.locks:
            lock_mask = load_lock_mask(lock_spec.mask_path, target_shape=rgba.shape[:2])
            # Find palette index for this color
            for i, palette_color in enumerate(sorted_palette):
                if palette_color.to_hex().lower() == lock_spec.color.lower():
                    lock_masks[i] = lock_mask
                    break

        locked_spx = map_locks_to_superpixels(lock_masks, spx_labels, silhouette)
        logger.info(f"  Locked {len(locked_spx)} superpixels")

    # Run ICM optimization
    logger.info(f"  Using smooth_lambda={smooth_lambda}")
    labeling_result = assign_labels_icm(
        mean_lab=mean_lab,
        adjacency=adjacency,
        palette_lab=palette_lab,
        smooth_lambda=smooth_lambda,
        locked_spx=locked_spx,
        max_iters=10,
        seed=config.seed,
    )

    logger.info("  ICM optimization complete")
    logger.info(f"  Final energy: {labeling_result.energy:.2f}")

    # Create pixel-level label map from superpixel labels
    label_map = create_pixel_label_map(spx_labels, labeling_result.label_per_spx, silhouette)

    # Step 4: Open masks + paint order
    logger.info("Step 4: Building layer masks")
    logger.info(f"  Layer mode: {config.layer_mode.value}")

    open_masks = build_open_masks(label_map, silhouette, palette_hex, mode=config.layer_mode)
    paint_order_indices = compute_paint_order(palette_hex, config.paint_order)

    logger.info(f"  Created {len(open_masks)} layer masks")
    logger.info(f"  Paint order: {paint_order_indices}")

    # Step 5: Per-layer stencil optimization
    logger.info("Step 5: Stencil optimization per layer")
    logger.info(f"  Using cleanup_strength={cleanup_strength}")

    min_feature_px = round(config.cuttability.min_feature_mm * result.px_per_mm * cleanup_strength)
    min_cutout_area_px = round(config.cuttability.min_island_area_mm2 * (result.px_per_mm**2))
    min_island_area_px = round(mm2_to_pixels2(config.cuttability.min_island_area_mm2, dpi=300.0))
    bridge_width_px = round(mm_to_pixels(config.cuttability.bridge_width_mm, dpi=300.0))

    optimized_masks: dict[str, np.ndarray] = {}

    for idx, color_hex in enumerate(palette_hex):
        logger.info(f"  Layer {idx + 1}/{len(palette_hex)}: {color_hex}")

        open_mask = open_masks[color_hex]

        # Compute metrics before optimization
        metrics_before = compute_layer_metrics(open_mask)
        material_pixels_before = int(np.sum(1 - open_mask))
        open_pixels_before = int(np.sum(open_mask))

        # Morphological cleanup
        cleaned = morph_cleanup(open_mask, min_feature_px=min_feature_px)

        # Remove small cutouts
        no_small_cutouts = remove_small_cutouts(cleaned, min_area_px=min_cutout_area_px)

        # Island detection and fixing
        island_result = find_material_islands(no_small_cutouts)

        logger.info(f"    Found {island_result.island_count} islands")

        # Fix islands
        fixed_mask, bridge_report = fix_islands(
            no_small_cutouts,
            min_island_area_px=min_island_area_px,
            bridge_width_px=bridge_width_px,
            max_attempts=3,
        )

        logger.info(f"    Filled {bridge_report.islands_filled} small islands")
        logger.info(f"    Added {bridge_report.bridges_added} bridges")

        if bridge_report.islands_remaining > 0:
            warning = (
                f"Layer {color_hex}: {bridge_report.islands_remaining} islands remaining "
                f"after optimization"
            )
            result.warnings.append(warning)
            logger.warning(f"    WARNING: {warning}")

        # Compute metrics after optimization
        metrics_after = compute_layer_metrics(fixed_mask)
        material_pixels_after = int(np.sum(1 - fixed_mask))
        open_pixels_after = int(np.sum(fixed_mask))

        # Store metrics
        layer_metrics = LayerMetrics(
            color=color_hex,
            material_pixels_before=material_pixels_before,
            open_pixels_before=open_pixels_before,
            contours_count_before=int(metrics_before["cutout_component_count"]),
            material_pixels_after=material_pixels_after,
            open_pixels_after=open_pixels_after,
            contours_count_after=int(metrics_after["cutout_component_count"]),
            contour_length_after=float(metrics_after["estimated_contour_length_px"]),
            islands_found=island_result.island_count,
            islands_filled=bridge_report.islands_filled,
            bridges_added=bridge_report.bridges_added,
        )
        result.layers.append(layer_metrics)

        optimized_masks[color_hex] = fixed_mask

    # Step 6: Page layout + registration marks
    logger.info("Step 6: Page layout and registration marks")

    placed_masks = place_artwork_on_page(
        optimized_masks,
        page_size=config.page.size,
        orientation=config.page.orientation,
        margin_mm=config.page.margin_mm,
        px_per_mm=result.px_per_mm,
    )

    logger.info(f"  Placed artwork on {config.page.size.value} page")

    marked_masks = add_registration_marks(
        placed_masks,
        px_per_mm=result.px_per_mm,
        diameter_mm=6.0,
        margin_mm=config.page.margin_mm,
    )

    logger.info("  Added registration marks")

    # Step 7: Preview composite
    logger.info("Step 7: Rendering preview")

    preview = render_preview(marked_masks, palette_hex, paint_order_indices)
    logger.info("  Preview rendered")

    # Step 8: Exports (PNG + SVG)
    logger.info("Step 8: Exporting layers")

    output_dir = config.export.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export each layer
    for idx in paint_order_indices:
        color_hex = palette_hex[idx]
        layer_num = idx + 1

        # Clean color name for filename (remove #)
        color_name = color_hex.lstrip("#")
        layer_prefix = f"{layer_num:02d}_{color_name}"

        mask = marked_masks[color_hex]

        # PNG export
        png_path = output_dir / f"{layer_prefix}.png"
        export_png(mask, png_path)
        logger.info(f"  Exported {png_path.name}")

        # SVG export
        svg_path = output_dir / f"{layer_prefix}.svg"

        if config.export.vector_backend == VectorBackend.POTRACE:
            export_svg_potrace(mask, svg_path, px_per_mm=result.px_per_mm)
        else:  # CONTOURS
            export_svg_contours(mask, svg_path, px_per_mm=result.px_per_mm)

        logger.info(f"  Exported {svg_path.name}")

    # Export preview
    preview_path = output_dir / "preview.png"
    preview_pil = Image.fromarray(preview, mode="RGB")
    preview_pil.save(preview_path)
    logger.info(f"  Exported {preview_path.name}")

    # Step 9: Report JSON
    logger.info("Step 9: Writing report")

    report_path = output_dir / "report.json"
    with open(report_path, "w") as f:
        json.dump(result.to_dict(), f, indent=2)

    logger.info(f"  Wrote {report_path.name}")

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully")
    logger.info(f"Output directory: {output_dir}")
    logger.info("=" * 60)

    return result
