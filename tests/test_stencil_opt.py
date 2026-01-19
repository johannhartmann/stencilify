"""Tests for stencil cuttability optimization."""

import numpy as np

from stencilify.stencil_opt import (
    compute_layer_metrics,
    morph_cleanup,
    remove_small_cutouts,
)


def test_morph_cleanup_simple() -> None:
    """Test basic morphological cleanup."""
    # Create mask with small noise
    mask = np.array(
        [
            [0, 0, 0, 0, 0],
            [0, 1, 1, 1, 0],
            [0, 1, 1, 1, 0],
            [0, 1, 1, 1, 0],
            [0, 0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )

    cleaned = morph_cleanup(mask, min_feature_px=3)

    # Should remain similar (already clean)
    assert cleaned.shape == mask.shape
    assert cleaned.dtype == np.uint8
    assert np.sum(cleaned) > 0


def test_morph_cleanup_removes_noise() -> None:
    """Test that cleanup removes small noise."""
    # Create mask with single pixel noise
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[5, 5] = 1  # Single isolated pixel

    cleaned = morph_cleanup(mask, min_feature_px=3)

    # Single pixel should be removed by opening
    assert np.sum(cleaned) == 0


def test_morph_cleanup_fills_holes() -> None:
    """Test that cleanup fills small holes."""
    # Create mask with small hole in center
    mask = np.ones((10, 10), dtype=np.uint8)
    mask[5, 5] = 0  # Single pixel hole

    cleaned = morph_cleanup(mask, min_feature_px=3)

    # Hole should be filled by closing
    assert cleaned[5, 5] == 1


def test_morph_cleanup_smooths_edges() -> None:
    """Test that cleanup smooths jagged edges."""
    # Create jagged edge
    mask = np.array(
        [
            [0, 0, 0, 0, 0, 0],
            [0, 1, 0, 1, 0, 0],
            [0, 1, 1, 1, 0, 0],
            [0, 1, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )

    cleaned = morph_cleanup(mask, min_feature_px=3)

    # Should smooth out the jagged edges
    assert cleaned.shape == mask.shape
    assert np.sum(cleaned) > 0


def test_morph_cleanup_different_sizes() -> None:
    """Test cleanup with different kernel sizes."""
    mask = np.ones((20, 20), dtype=np.uint8)
    mask[10, 10] = 0

    # Small kernel
    cleaned_small = morph_cleanup(mask, min_feature_px=2)
    assert cleaned_small[10, 10] == 1  # Should fill

    # Large kernel
    cleaned_large = morph_cleanup(mask, min_feature_px=10)
    assert cleaned_large[10, 10] == 1  # Should still fill
def test_remove_small_cutouts_simple() -> None:
    """Test basic small cutout removal."""
    # Create mask with one large and one small component
    mask = np.zeros((10, 10), dtype=np.uint8)
    # Large component (left)
    mask[2:8, 1:4] = 1
    # Small component (right)
    mask[5, 7] = 1

    filtered = remove_small_cutouts(mask, min_area_px=10)

    # Large component should remain
    assert np.sum(filtered[:, :4]) > 0
    # Small component should be removed
    assert filtered[5, 7] == 0


def test_remove_small_cutouts_all_large() -> None:
    """Test that all large components are kept."""
    mask = np.zeros((10, 10), dtype=np.uint8)
    # Two large components
    mask[1:4, 1:4] = 1  # 9 pixels
    mask[6:9, 6:9] = 1  # 9 pixels

    filtered = remove_small_cutouts(mask, min_area_px=5)

    # Both should be kept
    assert np.sum(filtered) == 18


def test_remove_small_cutouts_all_small() -> None:
    """Test that all small components are removed."""
    mask = np.zeros((10, 10), dtype=np.uint8)
    # Several small components
    mask[1, 1] = 1
    mask[3, 3] = 1
    mask[5, 5] = 1

    filtered = remove_small_cutouts(mask, min_area_px=10)

    # All should be removed
    assert np.sum(filtered) == 0


def test_remove_small_cutouts_threshold() -> None:
    """Test cutout removal at exact threshold."""
    mask = np.zeros((10, 10), dtype=np.uint8)
    # Component with exactly 5 pixels
    mask[2:4, 2:4] = 1  # 4 pixels
    mask[4, 2] = 1  # 1 more pixel = 5 total

    # At threshold, should be kept
    filtered_keep = remove_small_cutouts(mask, min_area_px=5)
    assert np.sum(filtered_keep) == 5

    # Above threshold, should be removed
    filtered_remove = remove_small_cutouts(mask, min_area_px=6)
    assert np.sum(filtered_remove) == 0


def test_remove_small_cutouts_connected_components() -> None:
    """Test that connectivity is properly detected."""
    mask = np.array(
        [
            [1, 0, 1, 0, 0],
            [1, 0, 1, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 1, 1, 0],
            [0, 0, 1, 1, 0],
        ],
        dtype=np.uint8,
    )

    filtered = remove_small_cutouts(mask, min_area_px=3)

    # Components: top-left (2px), top-right (2px), bottom-right (4px)
    # Only bottom-right (4px) >= 3 should remain
    assert np.sum(filtered[:2, :]) == 0  # Top removed
    assert np.sum(filtered[3:, 2:4]) == 4  # Bottom kept
def test_compute_layer_metrics_simple() -> None:
    """Test basic metrics computation."""
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[2:5, 2:5] = 1  # 3x3 square = 9 pixels

    metrics = compute_layer_metrics(mask)

    assert metrics["cutout_component_count"] == 1
    assert metrics["smallest_component_area_px"] == 9
    assert metrics["total_open_area_px"] == 9
    assert metrics["estimated_contour_length_px"] > 0


def test_compute_layer_metrics_multiple_components() -> None:
    """Test metrics with multiple components."""
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[1:3, 1:3] = 1  # 4 pixels
    mask[6:9, 6:9] = 1  # 9 pixels

    metrics = compute_layer_metrics(mask)

    assert metrics["cutout_component_count"] == 2
    assert metrics["smallest_component_area_px"] == 4
    assert metrics["total_open_area_px"] == 13
    assert metrics["estimated_contour_length_px"] > 0
def test_compute_layer_metrics_contour_length() -> None:
    """Test that contour length is reasonable."""
    # Square should have contour ~ 4 * side_length
    mask = np.zeros((20, 20), dtype=np.uint8)
    mask[5:15, 5:15] = 1  # 10x10 square

    metrics = compute_layer_metrics(mask)

    # Contour should be approximately 40 pixels (perimeter of 10x10 square)
    # Allow some tolerance for pixel approximation
    assert 35 < metrics["estimated_contour_length_px"] < 45
def test_pipeline_morph_then_remove() -> None:
    """Test full cleanup pipeline: morph + remove small cutouts."""
    # Create noisy mask
    mask = np.zeros((20, 20), dtype=np.uint8)
    # Large main region with hole
    mask[5:15, 5:15] = 1
    mask[10, 10] = 0  # Small hole
    # Small isolated noise
    mask[2, 2] = 1
    mask[17, 17] = 1

    # Step 1: Morphological cleanup (fill hole, remove noise)
    cleaned = morph_cleanup(mask, min_feature_px=3)

    # Step 2: Remove remaining small components
    final = remove_small_cutouts(cleaned, min_area_px=10)

    # Verify: hole should be filled, noise removed
    assert final[10, 10] == 1  # Hole filled
    # Main region should remain
    assert np.sum(final) > 80  # Most of the 10x10 region

    # Compute metrics
    metrics = compute_layer_metrics(final)
    assert metrics["cutout_component_count"] >= 1
    assert metrics["total_open_area_px"] > 80
