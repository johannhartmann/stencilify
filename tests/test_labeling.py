"""Tests for palette-constrained labeling."""

import numpy as np
import pytest

from stencilify.labeling import (
    assign_labels_icm,
    create_pixel_label_map,
)


def test_assign_labels_icm_simple() -> None:
    """Test ICM labeling on simple case with clear separation."""
    # Two superpixels with very different colors
    mean_lab = np.array(
        [
            [20.0, 0.0, 0.0],  # Dark (close to black)
            [80.0, 0.0, 0.0],  # Light (close to white)
        ],
        dtype=np.float32,
    )

    # No adjacency (independent)
    adjacency: list[tuple[int, int]] = []

    # Black and white palette
    palette_lab = np.array(
        [
            [0.0, 0.0, 0.0],  # Black
            [100.0, 0.0, 0.0],  # White
        ],
        dtype=np.float32,
    )

    result = assign_labels_icm(mean_lab, adjacency, palette_lab)

    # Should assign 0 (black) to dark, 1 (white) to light
    assert result.label_per_spx[0] == 0
    assert result.label_per_spx[1] == 1
    assert result.energy >= 0


def test_assign_labels_icm_with_smoothness() -> None:
    """Test that smoothness term encourages adjacent superpixels to have same label."""
    # Three superpixels in a line, middle is ambiguous
    mean_lab = np.array(
        [
            [20.0, 0.0, 0.0],  # Dark
            [50.0, 0.0, 0.0],  # Medium (ambiguous)
            [20.0, 0.0, 0.0],  # Dark
        ],
        dtype=np.float32,
    )

    # Linear adjacency: 0-1-2
    adjacency = [(0, 1), (1, 2)]

    # Black and white palette
    palette_lab = np.array(
        [
            [0.0, 0.0, 0.0],  # Black
            [100.0, 0.0, 0.0],  # White
        ],
        dtype=np.float32,
    )

    # With high smoothness weight, middle should match neighbors
    result = assign_labels_icm(mean_lab, adjacency, palette_lab, smooth_lambda=100.0)

    # All should be black (smoothness dominates)
    assert result.label_per_spx[0] == 0
    assert result.label_per_spx[1] == 0
    assert result.label_per_spx[2] == 0


def test_assign_labels_icm_with_locks() -> None:
    """Test that locked superpixels maintain their assigned labels."""
    # Two superpixels
    mean_lab = np.array(
        [
            [80.0, 0.0, 0.0],  # Light (would naturally be white)
            [20.0, 0.0, 0.0],  # Dark (would naturally be black)
        ],
        dtype=np.float32,
    )

    adjacency: list[tuple[int, int]] = []

    palette_lab = np.array(
        [
            [0.0, 0.0, 0.0],  # Black
            [100.0, 0.0, 0.0],  # White
        ],
        dtype=np.float32,
    )

    # Lock first superpixel to black (against its natural assignment)
    locked_spx = {0: 0}

    result = assign_labels_icm(mean_lab, adjacency, palette_lab, locked_spx=locked_spx)

    # First should be locked to black, second should naturally be black too
    assert result.label_per_spx[0] == 0  # Locked
    assert result.label_per_spx[1] == 0  # Natural (20 is closer to 0 than to 100)


def test_assign_labels_icm_deterministic() -> None:
    """Test that ICM produces deterministic results."""
    mean_lab = np.array(
        [
            [30.0, 10.0, -5.0],
            [50.0, -5.0, 10.0],
            [70.0, 5.0, -10.0],
        ],
        dtype=np.float32,
    )

    adjacency = [(0, 1), (1, 2)]

    palette_lab = np.array(
        [
            [20.0, 0.0, 0.0],
            [80.0, 0.0, 0.0],
        ],
        dtype=np.float32,
    )

    result1 = assign_labels_icm(mean_lab, adjacency, palette_lab, seed=42)
    result2 = assign_labels_icm(mean_lab, adjacency, palette_lab, seed=42)

    assert np.array_equal(result1.label_per_spx, result2.label_per_spx)
    assert result1.energy == result2.energy


def test_assign_labels_icm_converges() -> None:
    """Test that ICM converges (doesn't oscillate)."""
    # Create scenario where convergence is important
    mean_lab = np.random.RandomState(42).randn(10, 3).astype(np.float32) * 20 + 50

    # Ring adjacency
    adjacency = [(i, (i + 1) % 10) for i in range(10)]

    palette_lab = np.array(
        [
            [30.0, 0.0, 0.0],
            [70.0, 0.0, 0.0],
        ],
        dtype=np.float32,
    )

    result = assign_labels_icm(mean_lab, adjacency, palette_lab, max_iters=100)

    # Should produce valid labels
    assert np.all(result.label_per_spx >= 0)
    assert np.all(result.label_per_spx < 2)
    assert result.energy >= 0
def test_assign_labels_icm_invalid_palette_size() -> None:
    """Test that palette with < 2 or > 4 colors raises error."""
    mean_lab = np.array([[50.0, 0.0, 0.0]], dtype=np.float32)
    adjacency: list[tuple[int, int]] = []

    # Only 1 color
    palette_lab = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)
    with pytest.raises(ValueError, match="2-4 colors"):
        assign_labels_icm(mean_lab, adjacency, palette_lab)

    # 5 colors
    palette_lab = np.array(
        [[0.0, 0.0, 0.0], [25.0, 0.0, 0.0], [50.0, 0.0, 0.0], [75.0, 0.0, 0.0], [100.0, 0.0, 0.0]],
        dtype=np.float32,
    )
    with pytest.raises(ValueError, match="2-4 colors"):
        assign_labels_icm(mean_lab, adjacency, palette_lab)
def test_assign_labels_icm_invalid_locked_spx() -> None:
    """Test that invalid locked superpixel raises error."""
    mean_lab = np.array([[50.0, 0.0, 0.0]], dtype=np.float32)
    adjacency: list[tuple[int, int]] = []
    palette_lab = np.array([[0.0, 0.0, 0.0], [100.0, 0.0, 0.0]], dtype=np.float32)

    # Out of range superpixel ID
    with pytest.raises(ValueError, match="out of range"):
        assign_labels_icm(mean_lab, adjacency, palette_lab, locked_spx={5: 0})

    # Out of range label
    with pytest.raises(ValueError, match="out of range"):
        assign_labels_icm(mean_lab, adjacency, palette_lab, locked_spx={0: 5})


def test_create_pixel_label_map_simple() -> None:
    """Test creating pixel label map from superpixel labels."""
    # 4x4 image with 4 superpixels (quadrants)
    spx_labels = np.array(
        [
            [0, 0, 1, 1],
            [0, 0, 1, 1],
            [2, 2, 3, 3],
            [2, 2, 3, 3],
        ],
        dtype=np.int32,
    )

    silhouette = np.ones((4, 4), dtype=np.uint8)

    # Assign labels: 0->0, 1->1, 2->0, 3->1 (checkerboard pattern)
    label_per_spx = np.array([0, 1, 0, 1], dtype=np.int32)

    label_map = create_pixel_label_map(spx_labels, label_per_spx, silhouette)

    # Check shape
    assert label_map.shape == (4, 4)

    # Check values
    assert label_map[0, 0] == 0  # Superpixel 0 -> label 0
    assert label_map[0, 2] == 1  # Superpixel 1 -> label 1
    assert label_map[2, 0] == 0  # Superpixel 2 -> label 0
    assert label_map[2, 2] == 1  # Superpixel 3 -> label 1


def test_create_pixel_label_map_with_mask() -> None:
    """Test that pixels outside silhouette are set to -1."""
    spx_labels = np.array(
        [
            [0, 0, -1, -1],
            [0, 0, -1, -1],
            [-1, -1, -1, -1],
            [-1, -1, -1, -1],
        ],
        dtype=np.int32,
    )

    silhouette = np.array(
        [
            [1, 1, 0, 0],
            [1, 1, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )

    label_per_spx = np.array([1], dtype=np.int32)

    label_map = create_pixel_label_map(spx_labels, label_per_spx, silhouette)

    # Inside silhouette should have label 1
    assert label_map[0, 0] == 1
    assert label_map[1, 1] == 1

    # Outside silhouette should have -1
    assert label_map[0, 2] == -1
    assert label_map[2, 0] == -1
def test_create_pixel_label_map_invalid_spx_id() -> None:
    """Test that out-of-range superpixel ID raises error."""
    spx_labels = np.array([[0, 5]], dtype=np.int32)  # 5 is out of range
    silhouette = np.ones((1, 2), dtype=np.uint8)
    label_per_spx = np.array([0], dtype=np.int32)  # Only 1 superpixel

    with pytest.raises(ValueError, match="exceeds"):
        create_pixel_label_map(spx_labels, label_per_spx, silhouette)
