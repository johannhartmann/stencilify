"""Tests for island detection."""

import numpy as np

from stencilify.islands import find_material_islands


def test_find_material_islands_no_islands() -> None:
    """Test when all material touches border (no islands)."""
    # Open mask with cutout in center
    open_mask = np.array(
        [
            [0, 0, 0, 0, 0],
            [0, 1, 1, 1, 0],
            [0, 1, 1, 1, 0],
            [0, 1, 1, 1, 0],
            [0, 0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )

    result = find_material_islands(open_mask)

    # Material forms a border (touches all edges), so no islands
    assert result.island_count == 0
    assert len(result.island_stats) == 0
    assert np.sum(result.island_mask) == 0


def test_find_material_islands_ring_shape() -> None:
    """Test ring shape creates an island (center material not connected to border)."""
    # Create ring where material ring touches border but center material is an island
    # Material on border, cutout ring, material center
    open_mask = np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 1, 0, 0, 0, 1, 0],
            [0, 1, 0, 0, 0, 1, 0],
            [0, 1, 0, 0, 0, 1, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )

    result = find_material_islands(open_mask)

    # The center material (3x3 square at center) should be an island
    assert result.island_count == 1
    assert len(result.island_stats) == 1

    # Check island stats - center 3x3 region (9 pixels)
    island = result.island_stats[0]
    assert island.area_px == 9
    # Centroid should be at center of 3x3: (3.0, 3.0)
    assert island.centroid == (3.0, 3.0)

    # Check island mask
    assert np.sum(result.island_mask) == 9


def test_find_material_islands_multiple_islands() -> None:
    """Test detection of multiple islands."""
    # Create multiple disconnected material regions not touching border
    open_mask = np.ones((10, 10), dtype=np.uint8)
    # Island 1: 2x2 at (2,2)
    open_mask[2:4, 2:4] = 0
    # Island 2: 1x1 at (6,6)
    open_mask[6, 6] = 0
    # Island 3: 3x1 at (8, 3:6)
    open_mask[8, 3:6] = 0

    result = find_material_islands(open_mask)

    # Should detect 3 islands
    assert result.island_count == 3
    assert len(result.island_stats) == 3

    # Check total island area
    assert np.sum(result.island_mask) == 4 + 1 + 3  # 8 pixels total


def test_find_material_islands_touching_top() -> None:
    """Test that material touching top border is not an island."""
    open_mask = np.ones((5, 5), dtype=np.uint8)
    # Material touching top edge
    open_mask[0:2, 2] = 0

    result = find_material_islands(open_mask)

    # Not an island (touches border)
    assert result.island_count == 0
    assert np.sum(result.island_mask) == 0


def test_find_material_islands_touching_bottom() -> None:
    """Test that material touching bottom border is not an island."""
    open_mask = np.ones((5, 5), dtype=np.uint8)
    # Material touching bottom edge
    open_mask[3:5, 2] = 0

    result = find_material_islands(open_mask)

    # Not an island (touches border)
    assert result.island_count == 0
    assert np.sum(result.island_mask) == 0


def test_find_material_islands_touching_left() -> None:
    """Test that material touching left border is not an island."""
    open_mask = np.ones((5, 5), dtype=np.uint8)
    # Material touching left edge
    open_mask[2, 0:2] = 0

    result = find_material_islands(open_mask)

    # Not an island (touches border)
    assert result.island_count == 0
    assert np.sum(result.island_mask) == 0


def test_find_material_islands_touching_right() -> None:
    """Test that material touching right border is not an island."""
    open_mask = np.ones((5, 5), dtype=np.uint8)
    # Material touching right edge
    open_mask[2, 3:5] = 0

    result = find_material_islands(open_mask)

    # Not an island (touches border)
    assert result.island_count == 0
    assert np.sum(result.island_mask) == 0


def test_find_material_islands_all_open() -> None:
    """Test with all open (no material)."""
    open_mask = np.ones((5, 5), dtype=np.uint8)

    result = find_material_islands(open_mask)

    # No material, so no islands
    assert result.island_count == 0
    assert len(result.island_stats) == 0
    assert np.sum(result.island_mask) == 0


def test_find_material_islands_all_material() -> None:
    """Test with all material (no cutouts)."""
    open_mask = np.zeros((5, 5), dtype=np.uint8)

    result = find_material_islands(open_mask)

    # All material touches border, so no islands
    assert result.island_count == 0
    assert len(result.island_stats) == 0
    assert np.sum(result.island_mask) == 0


def test_find_material_islands_bbox() -> None:
    """Test bounding box calculation."""
    open_mask = np.ones((10, 10), dtype=np.uint8)
    # Create 3x2 island at (3,4)
    open_mask[3:6, 4:6] = 0

    result = find_material_islands(open_mask)

    assert result.island_count == 1
    island = result.island_stats[0]

    # Bbox should be (x=4, y=3, w=2, h=3)
    assert island.bbox == (4, 3, 2, 3)
    assert island.area_px == 6


def test_find_material_islands_centroid() -> None:
    """Test centroid calculation."""
    open_mask = np.ones((10, 10), dtype=np.uint8)
    # Create 2x2 island at (4,4)
    open_mask[4:6, 4:6] = 0

    result = find_material_islands(open_mask)

    assert result.island_count == 1
    island = result.island_stats[0]

    # Centroid should be at center of 2x2 square: (4.5, 4.5)
    assert abs(island.centroid[0] - 4.5) < 0.01
    assert abs(island.centroid[1] - 4.5) < 0.01


def test_find_material_islands_diagonal_connection() -> None:
    """Test that diagonal connection is detected (8-connectivity)."""
    open_mask = np.ones((7, 7), dtype=np.uint8)
    # Create material connected diagonally
    open_mask[2, 2] = 0
    open_mask[3, 3] = 0
    open_mask[4, 4] = 0

    result = find_material_islands(open_mask)

    # Should be one island (diagonally connected)
    assert result.island_count == 1
    assert result.island_stats[0].area_px == 3


def test_find_material_islands_complex_shape() -> None:
    """Test with complex shape."""
    # Create L-shaped island
    open_mask = np.ones((10, 10), dtype=np.uint8)
    # Vertical part
    open_mask[3:7, 3] = 0
    # Horizontal part
    open_mask[6, 3:7] = 0

    result = find_material_islands(open_mask)

    # L-shape is one connected component
    assert result.island_count == 1
    # Vertical: 4 pixels + Horizontal: 4 pixels - overlap: 1 pixel = 7 pixels
    assert result.island_stats[0].area_px == 7
