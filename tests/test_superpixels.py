"""Tests for superpixel generation and adjacency."""

import numpy as np
import pytest

from stencilify.superpixels import build_adjacency, compute_mean_lab, compute_superpixels


def test_compute_superpixels_basic() -> None:
    """Test basic superpixel computation on a simple image."""
    # Create a simple 20x20 RGB image with two distinct regions
    rgb = np.zeros((20, 20, 3), dtype=np.uint8)
    rgb[:, :10] = [255, 0, 0]  # Left half red
    rgb[:, 10:] = [0, 0, 255]  # Right half blue

    # Full silhouette
    silhouette = np.ones((20, 20), dtype=np.uint8)

    result = compute_superpixels(rgb, silhouette, n_segments=10, compactness=10.0, sigma=0)

    # Check result structure
    assert result.labels.shape == (20, 20)
    assert result.labels.dtype == np.int32
    assert result.count > 0
    assert isinstance(result.adjacency, list)
    assert result.mean_lab.shape == (result.count, 3)

    # Check that labels are in valid range
    assert np.all(result.labels >= -1)
    assert np.all(result.labels < result.count)


def test_compute_superpixels_with_mask() -> None:
    """Test that superpixels are only computed within the mask."""
    # Create image
    rgb = np.full((20, 20, 3), 128, dtype=np.uint8)

    # Circular mask in the center
    y, x = np.ogrid[:20, :20]
    center_y, center_x = 10, 10
    radius = 5
    silhouette = ((x - center_x) ** 2 + (y - center_y) ** 2 <= radius**2).astype(np.uint8)

    result = compute_superpixels(rgb, silhouette, n_segments=5, compactness=10.0, sigma=0)

    # Check that labels outside the mask are -1
    assert np.all(result.labels[silhouette == 0] == -1)

    # Check that there are valid labels inside the mask
    assert np.any(result.labels[silhouette == 1] >= 0)


def test_compute_superpixels_invalid_rgb_dtype() -> None:
    """Test that non-uint8 RGB raises error."""
    rgb = np.zeros((10, 10, 3), dtype=np.float32)
    silhouette = np.ones((10, 10), dtype=np.uint8)

    with pytest.raises(ValueError, match="RGB must be uint8"):
        compute_superpixels(rgb, silhouette)


def test_compute_superpixels_invalid_rgb_shape() -> None:
    """Test that invalid RGB shape raises error."""
    rgb = np.zeros((10, 10), dtype=np.uint8)  # Missing channel dimension
    silhouette = np.ones((10, 10), dtype=np.uint8)

    with pytest.raises(ValueError, match="RGB must be"):
        compute_superpixels(rgb, silhouette)


def test_compute_superpixels_shape_mismatch() -> None:
    """Test that RGB/silhouette shape mismatch raises error."""
    rgb = np.zeros((10, 10, 3), dtype=np.uint8)
    silhouette = np.ones((20, 20), dtype=np.uint8)

    with pytest.raises(ValueError, match="shape mismatch"):
        compute_superpixels(rgb, silhouette)


def test_compute_superpixels_invalid_silhouette_values() -> None:
    """Test that silhouette with non-binary values raises error."""
    rgb = np.zeros((10, 10, 3), dtype=np.uint8)
    silhouette = np.full((10, 10), 2, dtype=np.uint8)

    with pytest.raises(ValueError, match="must contain only 0 or 1"):
        compute_superpixels(rgb, silhouette)


def test_build_adjacency_simple() -> None:
    """Test adjacency building on a simple grid."""
    # Create a simple 4x4 grid with 4 quadrants
    labels = np.array(
        [
            [0, 0, 1, 1],
            [0, 0, 1, 1],
            [2, 2, 3, 3],
            [2, 2, 3, 3],
        ],
        dtype=np.int32,
    )
    silhouette = np.ones((4, 4), dtype=np.uint8)

    edges = build_adjacency(labels, spx_count=4, silhouette=silhouette)

    # Expected adjacencies:
    # 0-1 (horizontal between quadrants)
    # 0-2 (vertical between quadrants)
    # 1-3 (vertical between quadrants)
    # 2-3 (horizontal between quadrants)
    expected_edges = [(0, 1), (0, 2), (1, 3), (2, 3)]

    assert sorted(edges) == expected_edges


def test_build_adjacency_with_mask() -> None:
    """Test adjacency with partial mask."""
    # Create labels
    labels = np.array(
        [
            [0, 0, 1, 1],
            [0, 0, 1, 1],
            [2, 2, 3, 3],
            [2, 2, 3, 3],
        ],
        dtype=np.int32,
    )

    # Mask out bottom half
    silhouette = np.zeros((4, 4), dtype=np.uint8)
    silhouette[:2, :] = 1

    edges = build_adjacency(labels, spx_count=4, silhouette=silhouette)

    # Only 0-1 edge should exist (top half only)
    assert edges == [(0, 1)]


def test_build_adjacency_no_adjacency() -> None:
    """Test case with no adjacent superpixels."""
    # Each pixel is its own superpixel with gaps
    labels = np.array(
        [
            [0, -1, 1, -1],
            [-1, -1, -1, -1],
            [2, -1, 3, -1],
            [-1, -1, -1, -1],
        ],
        dtype=np.int32,
    )
    silhouette = (labels >= 0).astype(np.uint8)

    edges = build_adjacency(labels, spx_count=4, silhouette=silhouette)

    # No adjacent superpixels
    assert edges == []


def test_build_adjacency_self_not_included() -> None:
    """Test that self-edges are not included."""
    # All same superpixel
    labels = np.zeros((5, 5), dtype=np.int32)
    silhouette = np.ones((5, 5), dtype=np.uint8)

    edges = build_adjacency(labels, spx_count=1, silhouette=silhouette)

    # No edges (single superpixel)
    assert edges == []


def test_build_adjacency_unique_edges() -> None:
    """Test that edges are unique and undirected."""
    # Create a pattern that could generate duplicate edges
    labels = np.array(
        [
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0],
        ],
        dtype=np.int32,
    )
    silhouette = np.ones((3, 3), dtype=np.uint8)

    edges = build_adjacency(labels, spx_count=2, silhouette=silhouette)

    # Should have only one edge (0, 1), not multiple
    assert edges == [(0, 1)]


def test_compute_mean_lab_simple() -> None:
    """Test mean Lab computation on simple colors."""
    # Create image with two regions
    rgb = np.zeros((10, 10, 3), dtype=np.uint8)
    rgb[:, :5] = [255, 0, 0]  # Red
    rgb[:, 5:] = [0, 0, 255]  # Blue

    # Create corresponding labels
    labels = np.zeros((10, 10), dtype=np.int32)
    labels[:, :5] = 0
    labels[:, 5:] = 1

    mean_lab = compute_mean_lab(rgb, labels, spx_count=2)

    # Check shape
    assert mean_lab.shape == (2, 3)

    # Check that Lab values are reasonable
    # Red: high L, positive a, low b
    # Blue: lower L, negative a, negative b
    assert mean_lab[0, 0] > mean_lab[1, 0]  # Red has higher L than blue
    assert mean_lab[0, 1] > 0  # Red has positive a
    assert mean_lab[1, 2] < 0  # Blue has negative b


def test_compute_mean_lab_single_pixel_superpixel() -> None:
    """Test mean Lab for single-pixel superpixels."""
    # Create a small image
    rgb = np.array(
        [
            [[255, 0, 0], [0, 255, 0]],
            [[0, 0, 255], [255, 255, 0]],
        ],
        dtype=np.uint8,
    )

    # Each pixel is its own superpixel
    labels = np.array(
        [
            [0, 1],
            [2, 3],
        ],
        dtype=np.int32,
    )

    mean_lab = compute_mean_lab(rgb, labels, spx_count=4)

    # Each superpixel has only one pixel, so mean should equal that pixel's Lab
    assert mean_lab.shape == (4, 3)
    # All values should be valid Lab values
    assert np.all(np.isfinite(mean_lab))


def test_compute_mean_lab_invalid_rgb() -> None:
    """Test that invalid RGB raises error."""
    rgb = np.zeros((10, 10, 3), dtype=np.float32)
    labels = np.zeros((10, 10), dtype=np.int32)

    with pytest.raises(ValueError, match="RGB must be uint8"):
        compute_mean_lab(rgb, labels, spx_count=1)


def test_compute_mean_lab_shape_mismatch() -> None:
    """Test that shape mismatch raises error."""
    rgb = np.zeros((10, 10, 3), dtype=np.uint8)
    labels = np.zeros((20, 20), dtype=np.int32)

    with pytest.raises(ValueError, match="shape mismatch"):
        compute_mean_lab(rgb, labels, spx_count=1)


def test_superpixels_deterministic() -> None:
    """Test that superpixel computation is deterministic with same seed."""
    rgb = np.random.RandomState(42).randint(0, 256, (30, 30, 3), dtype=np.uint8)
    silhouette = np.ones((30, 30), dtype=np.uint8)

    # Compute twice with same parameters
    result1 = compute_superpixels(rgb, silhouette, n_segments=15, compactness=10.0, sigma=1.0)
    result2 = compute_superpixels(rgb, silhouette, n_segments=15, compactness=10.0, sigma=1.0)

    # Should get same results
    assert np.array_equal(result1.labels, result2.labels)
    assert result1.count == result2.count
    assert result1.adjacency == result2.adjacency
    assert np.allclose(result1.mean_lab, result2.mean_lab)


def test_superpixels_respects_n_segments() -> None:
    """Test that n_segments parameter affects superpixel count."""
    # Create a structured image with distinct color blocks (5x5 grid of 10x10 blocks)
    rgb = np.zeros((50, 50, 3), dtype=np.uint8)
    rng = np.random.RandomState(42)
    for i in range(5):
        for j in range(5):
            color = rng.randint(0, 256, 3, dtype=np.uint8)
            rgb[i * 10 : (i + 1) * 10, j * 10 : (j + 1) * 10] = color

    silhouette = np.ones((50, 50), dtype=np.uint8)

    # Small number of segments
    result_small = compute_superpixels(rgb, silhouette, n_segments=10, compactness=10.0, sigma=0)

    # Large number of segments
    result_large = compute_superpixels(rgb, silhouette, n_segments=100, compactness=10.0, sigma=0)

    # More segments should result in more superpixels
    assert result_large.count > result_small.count


def test_superpixels_adjacency_symmetric() -> None:
    """Test that adjacency list is symmetric (i < j)."""
    rgb = np.random.RandomState(42).randint(0, 256, (30, 30, 3), dtype=np.uint8)
    silhouette = np.ones((30, 30), dtype=np.uint8)

    result = compute_superpixels(rgb, silhouette, n_segments=20, compactness=10.0, sigma=0)

    # All edges should have i < j
    for i, j in result.adjacency:
        assert i < j


def test_superpixels_performance() -> None:
    """Test that superpixels computation is reasonably fast on small images."""
    import time

    rgb = np.random.RandomState(42).randint(0, 256, (100, 100, 3), dtype=np.uint8)
    silhouette = np.ones((100, 100), dtype=np.uint8)

    start = time.time()
    result = compute_superpixels(rgb, silhouette, n_segments=50, compactness=10.0, sigma=1.0)
    elapsed = time.time() - start

    # Should complete in reasonable time (< 2 seconds for 100x100 image)
    assert elapsed < 2.0
    assert result.count > 0
