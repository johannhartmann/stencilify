"""Autotuning for stencilify parameters."""

import csv
import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from stencilify.bridges import fix_islands
from stencilify.config import PipelineConfig
from stencilify.geometry import mm2_to_pixels2, mm_to_pixels
from stencilify.imageio import load_rgba
from stencilify.islands import find_material_islands
from stencilify.labeling import assign_labels_icm, create_pixel_label_map
from stencilify.layers import build_open_masks
from stencilify.masks import silhouette_from_alpha
from stencilify.stencil_opt import (
    compute_layer_metrics,
    morph_cleanup,
    remove_small_cutouts,
)
from stencilify.superpixels import compute_superpixels

logger = logging.getLogger(__name__)


@dataclass
class CandidateParams:
    """Parameter set for a single autotune candidate."""

    n_segments: int
    smooth_lambda: float
    slic_compactness: float
    cleanup_strength: float


@dataclass
class CandidateResult:
    """Result of evaluating one parameter candidate."""

    params: CandidateParams
    score: float
    palette_error: float
    cutout_components: int
    island_count: int
    contour_complexity: float


@dataclass
class AutotuneResult:
    """Result of autotuning process."""

    best_params: CandidateParams
    best_score: float
    all_candidates: list[CandidateResult] = field(default_factory=list)


def compute_palette_error(
    rgb: np.ndarray,
    label_map: np.ndarray,
    silhouette: np.ndarray,
    palette_hex: list[str],
) -> float:
    """
    Compute mean Lab distance between assigned palette colors and original pixels.

    Args:
        rgb: Original RGB image [H, W, 3]
        label_map: Label map [H, W] with palette indices
        silhouette: Binary silhouette mask [H, W]
        palette_hex: List of palette colors as hex strings

    Returns:
        Mean Lab distance
    """
    from stencilify.config import Color

    # Convert palette to Lab
    palette_colors = [Color.from_hex(hex_str) for hex_str in palette_hex]
    palette_lab = np.array([[c.luminance() * 100, 0, 0] for c in palette_colors])

    # Compute Lab for each pixel in silhouette
    total_error = 0.0
    pixel_count = 0

    foreground_mask = silhouette > 0

    for label_idx, palette_l in enumerate(palette_lab):
        # Get pixels assigned to this label
        label_mask = (label_map == label_idx) & foreground_mask

        if not np.any(label_mask):
            continue

        # Get RGB values for these pixels
        pixel_rgb = rgb[label_mask].astype(float) / 255.0

        # Convert to Lab (simplified: just luminance)
        pixel_l = (
            0.2126 * pixel_rgb[:, 0] + 0.7152 * pixel_rgb[:, 1] + 0.0722 * pixel_rgb[:, 2]
        ) * 100

        # Compute distance in Lab space (just L channel)
        distances = np.abs(pixel_l - palette_l[0])

        total_error += np.sum(distances)
        pixel_count += len(distances)

    if pixel_count == 0:
        return 0.0

    return float(total_error / pixel_count)


def evaluate_candidate(
    params: CandidateParams,
    config: PipelineConfig,
    rgb: np.ndarray,
    alpha: np.ndarray,
    silhouette: np.ndarray,
    px_per_mm: float,
) -> CandidateResult:
    """
    Evaluate a single parameter candidate.

    Args:
        params: Parameter set to evaluate
        config: Pipeline configuration
        rgb: RGB image [H, W, 3]
        alpha: Alpha channel [H, W]
        silhouette: Silhouette mask [H, W]
        px_per_mm: Pixels per millimeter

    Returns:
        CandidateResult with score and metrics
    """
    # Step 1: Compute superpixels with candidate parameters
    spx_result = compute_superpixels(
        rgb,
        silhouette,
        n_segments=params.n_segments,
        compactness=params.slic_compactness,
    )

    spx_labels = spx_result.labels
    adjacency = spx_result.adjacency
    mean_lab = spx_result.mean_lab

    # Step 2: Palette labeling
    sorted_palette = config.get_sorted_palette()
    palette_hex = [color.to_hex() for color in sorted_palette]
    palette_lab = np.array([[color.luminance() * 100, 0, 0] for color in sorted_palette])

    labeling_result = assign_labels_icm(
        mean_lab=mean_lab,
        adjacency=adjacency,
        palette_lab=palette_lab,
        smooth_lambda=params.smooth_lambda,
        locked_spx=None,  # No locks in autotune
        max_iters=10,
        seed=config.seed,
    )

    label_map = create_pixel_label_map(spx_labels, labeling_result.label_per_spx, silhouette)

    # Step 3: Build open masks
    open_masks = build_open_masks(label_map, silhouette, palette_hex)

    # Step 4: Optimize each layer and collect metrics
    min_feature_px = round(config.cuttability.min_feature_mm * px_per_mm * params.cleanup_strength)
    min_cutout_area_px = round(config.cuttability.min_island_area_mm2 * (px_per_mm**2))
    min_island_area_px = round(mm2_to_pixels2(config.cuttability.min_island_area_mm2, dpi=300.0))
    bridge_width_px = round(mm_to_pixels(config.cuttability.bridge_width_mm, dpi=300.0))

    total_cutout_components = 0
    total_island_count = 0
    total_contour_length = 0.0

    for color_hex in palette_hex:
        open_mask = open_masks[color_hex]

        # Morphological cleanup
        cleaned = morph_cleanup(open_mask, min_feature_px=min_feature_px)

        # Remove small cutouts
        no_small_cutouts = remove_small_cutouts(cleaned, min_area_px=min_cutout_area_px)

        # Island detection and fixing
        _ = find_material_islands(no_small_cutouts)

        # Fix islands
        fixed_mask, bridge_report = fix_islands(
            no_small_cutouts,
            min_island_area_px=min_island_area_px,
            bridge_width_px=bridge_width_px,
            max_attempts=3,
        )

        # Compute metrics
        metrics = compute_layer_metrics(fixed_mask)

        total_cutout_components += int(metrics["cutout_component_count"])
        total_island_count += bridge_report.islands_remaining
        total_contour_length += float(metrics["estimated_contour_length_px"])

    # Step 5: Compute palette error
    palette_error = compute_palette_error(rgb, label_map, silhouette, palette_hex)

    # Step 6: Compute score (lower is better)
    # Weights for different components
    w1 = 1.0  # palette_error weight
    w2 = 10.0  # cutout_components weight
    w3 = 100.0  # island_count weight (penalize heavily)
    w4 = 0.001  # contour_complexity weight

    score = (
        w1 * palette_error
        + w2 * total_cutout_components
        + w3 * total_island_count
        + w4 * total_contour_length
    )

    return CandidateResult(
        params=params,
        score=score,
        palette_error=palette_error,
        cutout_components=total_cutout_components,
        island_count=total_island_count,
        contour_complexity=total_contour_length,
    )


def run_autotune(config: PipelineConfig, px_per_mm: float) -> AutotuneResult:
    """
    Run autotuning to find best parameters.

    Args:
        config: Pipeline configuration
        px_per_mm: Pixels per millimeter

    Returns:
        AutotuneResult with best parameters and all candidates
    """
    logger.info("=" * 60)
    logger.info("Starting autotuning")
    logger.info("=" * 60)

    # Load image once
    rgb, alpha = load_rgba(config.input_image)
    silhouette = silhouette_from_alpha(alpha)

    logger.info(f"Image size: {rgb.shape[1]}x{rgb.shape[0]} pixels")

    # Define parameter grid (modest for reasonable execution time)
    n_segments_grid = [800, 1200, 1800, 2500]
    smooth_lambda_grid = [5.0, 10.0, 20.0]
    slic_compactness_grid = [10.0, 15.0, 20.0]
    cleanup_strength_grid = [0.8, 1.0, 1.2]

    # Generate all combinations
    all_candidates: list[CandidateResult] = []
    total_combinations = (
        len(n_segments_grid)
        * len(smooth_lambda_grid)
        * len(slic_compactness_grid)
        * len(cleanup_strength_grid)
    )

    logger.info(f"Evaluating {total_combinations} parameter combinations")

    candidate_idx = 0

    for n_segments in n_segments_grid:
        for smooth_lambda in smooth_lambda_grid:
            for slic_compactness in slic_compactness_grid:
                for cleanup_strength in cleanup_strength_grid:
                    candidate_idx += 1

                    params = CandidateParams(
                        n_segments=n_segments,
                        smooth_lambda=smooth_lambda,
                        slic_compactness=slic_compactness,
                        cleanup_strength=cleanup_strength,
                    )

                    logger.info(
                        f"Candidate {candidate_idx}/{total_combinations}: "
                        f"n_segments={n_segments}, lambda={smooth_lambda}, "
                        f"compactness={slic_compactness}, cleanup={cleanup_strength}"
                    )

                    result = evaluate_candidate(params, config, rgb, alpha, silhouette, px_per_mm)

                    logger.info(
                        f"  Score: {result.score:.2f} "
                        f"(palette_error={result.palette_error:.2f}, "
                        f"cutouts={result.cutout_components}, "
                        f"islands={result.island_count}, "
                        f"contour_len={result.contour_complexity:.0f})"
                    )

                    all_candidates.append(result)

    # Find best candidate (lowest score)
    best_result = min(all_candidates, key=lambda r: r.score)

    logger.info("=" * 60)
    logger.info(f"Best candidate: score={best_result.score:.2f}")
    logger.info(f"  n_segments: {best_result.params.n_segments}")
    logger.info(f"  smooth_lambda: {best_result.params.smooth_lambda}")
    logger.info(f"  slic_compactness: {best_result.params.slic_compactness}")
    logger.info(f"  cleanup_strength: {best_result.params.cleanup_strength}")
    logger.info("=" * 60)

    return AutotuneResult(
        best_params=best_result.params,
        best_score=best_result.score,
        all_candidates=all_candidates,
    )


def save_candidates_csv(candidates: list[CandidateResult], output_path: Path) -> None:
    """
    Save all candidates to CSV file.

    Args:
        candidates: List of candidate results
        output_path: Path to CSV file
    """
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(
            [
                "n_segments",
                "smooth_lambda",
                "slic_compactness",
                "cleanup_strength",
                "score",
                "palette_error",
                "cutout_components",
                "island_count",
                "contour_complexity",
            ]
        )

        # Data rows
        for candidate in candidates:
            writer.writerow(
                [
                    candidate.params.n_segments,
                    candidate.params.smooth_lambda,
                    candidate.params.slic_compactness,
                    candidate.params.cleanup_strength,
                    candidate.score,
                    candidate.palette_error,
                    candidate.cutout_components,
                    candidate.island_count,
                    candidate.contour_complexity,
                ]
            )

    logger.info(f"Saved candidates to {output_path}")
