"""Tests for layer mask generation and paint order."""

import numpy as np
import pytest

from stencilify.config import PaintOrder
from stencilify.layers import (
    build_open_masks,
    compute_luminance,
    compute_paint_order,
    verify_knockout_property,
)


def test_build_open_masks_simple() -> None:
    """Test basic open mask generation."""
    # 4x4 label map with 2 colors
    label_map = np.array(
        [
            [0, 0, 1, 1],
            [0, 0, 1, 1],
            [0, 0, 1, 1],
            [0, 0, 1, 1],
        ],
        dtype=np.int32,
    )

    silhouette = np.ones((4, 4), dtype=np.uint8)
    palette = ["#000000", "#FFFFFF"]

    open_masks = build_open_masks(label_map, silhouette, palette)

    # Should have 2 masks
    assert len(open_masks) == 2
    assert "#000000" in open_masks
    assert "#FFFFFF" in open_masks

    # Check shapes
    assert open_masks["#000000"].shape == (4, 4)
    assert open_masks["#FFFFFF"].shape == (4, 4)

    # Check values
    assert np.sum(open_masks["#000000"]) == 8  # Left half
    assert np.sum(open_masks["#FFFFFF"]) == 8  # Right half


def test_build_open_masks_with_silhouette() -> None:
    """Test that open masks respect silhouette."""
    label_map = np.array(
        [
            [0, 0, -1, -1],
            [0, 0, -1, -1],
            [1, 1, -1, -1],
            [1, 1, -1, -1],
        ],
        dtype=np.int32,
    )

    silhouette = np.array(
        [
            [1, 1, 0, 0],
            [1, 1, 0, 0],
            [1, 1, 0, 0],
            [1, 1, 0, 0],
        ],
        dtype=np.uint8,
    )

    palette = ["#000000", "#FFFFFF"]

    open_masks = build_open_masks(label_map, silhouette, palette)

    # Masks should only be 1 inside silhouette
    assert np.all(open_masks["#000000"][:, 2:] == 0)
    assert np.all(open_masks["#FFFFFF"][:, 2:] == 0)

    # Check sums
    assert np.sum(open_masks["#000000"]) == 4  # Top-left quadrant
    assert np.sum(open_masks["#FFFFFF"]) == 4  # Bottom-left quadrant


def test_build_open_masks_knockout_property() -> None:
    """Test that knockout property holds (each pixel in exactly one layer)."""
    label_map = np.array(
        [
            [0, 1, 2],
            [0, 1, 2],
            [0, 1, 2],
        ],
        dtype=np.int32,
    )

    silhouette = np.ones((3, 3), dtype=np.uint8)
    palette = ["#000000", "#808080", "#FFFFFF"]

    open_masks = build_open_masks(label_map, silhouette, palette)

    # Sum all masks
    total = np.zeros_like(silhouette, dtype=np.int32)
    for mask in open_masks.values():
        total += mask

    # Should equal silhouette
    assert np.array_equal(total, silhouette)


def test_build_open_masks_shape_mismatch() -> None:
    """Test that shape mismatch raises error."""
    label_map = np.zeros((4, 4), dtype=np.int32)
    silhouette = np.ones((5, 5), dtype=np.uint8)
    palette = ["#000000", "#FFFFFF"]

    with pytest.raises(ValueError, match="Shape mismatch"):
        build_open_masks(label_map, silhouette, palette)


def test_build_open_masks_invalid_palette_size() -> None:
    """Test that invalid palette size raises error."""
    label_map = np.zeros((4, 4), dtype=np.int32)
    silhouette = np.ones((4, 4), dtype=np.uint8)

    # Only 1 color
    with pytest.raises(ValueError, match="2-4 colors"):
        build_open_masks(label_map, silhouette, ["#000000"])

    # 5 colors
    with pytest.raises(ValueError, match="2-4 colors"):
        build_open_masks(
            label_map,
            silhouette,
            ["#000000", "#404040", "#808080", "#C0C0C0", "#FFFFFF"],
        )


def test_compute_luminance_basic() -> None:
    """Test luminance computation for basic colors."""
    # Black
    assert compute_luminance("#000000") == 0.0

    # White
    assert compute_luminance("#FFFFFF") == 255.0

    # Pure red: 0.299 * 255
    red_luma = 0.299 * 255
    assert abs(compute_luminance("#FF0000") - red_luma) < 0.01

    # Pure green: 0.587 * 255
    green_luma = 0.587 * 255
    assert abs(compute_luminance("#00FF00") - green_luma) < 0.01

    # Pure blue: 0.114 * 255
    blue_luma = 0.114 * 255
    assert abs(compute_luminance("#0000FF") - blue_luma) < 0.01


def test_compute_luminance_gray() -> None:
    """Test luminance for gray colors."""
    # Middle gray
    gray_luma = 0.299 * 128 + 0.587 * 128 + 0.114 * 128
    assert abs(compute_luminance("#808080") - gray_luma) < 0.01


def test_compute_luminance_without_hash() -> None:
    """Test luminance computation without # prefix."""
    assert compute_luminance("000000") == 0.0
    assert compute_luminance("FFFFFF") == 255.0


def test_compute_luminance_invalid() -> None:
    """Test that invalid hex raises error."""
    with pytest.raises(ValueError, match="Invalid HEX"):
        compute_luminance("#FFF")

    with pytest.raises(ValueError, match="Invalid HEX"):
        compute_luminance("#GGGGGG")


def test_compute_paint_order_given() -> None:
    """Test paint order with GIVEN mode."""
    palette = ["#000000", "#808080", "#FFFFFF"]

    order = compute_paint_order(palette, PaintOrder.GIVEN)

    # Should be [0, 1, 2] (original order)
    assert order == [0, 1, 2]


def test_compute_paint_order_auto() -> None:
    """Test paint order with AUTO mode (dark to light)."""
    # Unsorted palette: white, black, gray
    palette = ["#FFFFFF", "#000000", "#808080"]

    order = compute_paint_order(palette, PaintOrder.AUTO)

    # Should sort dark to light: black (idx 1), gray (idx 2), white (idx 0)
    assert order == [1, 2, 0]


def test_compute_paint_order_auto_sorted() -> None:
    """Test AUTO mode with already-sorted palette."""
    palette = ["#000000", "#808080", "#FFFFFF"]

    order = compute_paint_order(palette, PaintOrder.AUTO)

    # Should be [0, 1, 2] (already sorted dark to light)
    assert order == [0, 1, 2]


def test_compute_paint_order_two_colors() -> None:
    """Test paint order with 2 colors."""
    # White first, black second
    palette = ["#FFFFFF", "#000000"]

    order_given = compute_paint_order(palette, PaintOrder.GIVEN)
    assert order_given == [0, 1]

    order_auto = compute_paint_order(palette, PaintOrder.AUTO)
    assert order_auto == [1, 0]  # Black first, then white


def test_compute_paint_order_four_colors() -> None:
    """Test paint order with 4 colors."""
    palette = ["#FFFFFF", "#000000", "#C0C0C0", "#404040"]

    order = compute_paint_order(palette, PaintOrder.AUTO)

    # Should sort: black (idx 1), dark gray (idx 3), light gray (idx 2), white (idx 0)
    assert order == [1, 3, 2, 0]


def test_compute_paint_order_invalid_palette() -> None:
    """Test that invalid palette raises error."""
    with pytest.raises(ValueError, match="2-4 colors"):
        compute_paint_order(["#000000"], PaintOrder.GIVEN)

    with pytest.raises(ValueError, match="2-4 colors"):
        compute_paint_order(
            ["#000000", "#404040", "#808080", "#C0C0C0", "#FFFFFF"],
            PaintOrder.GIVEN,
        )


def test_verify_knockout_property_simple() -> None:
    """Test knockout property verification."""
    open_masks = {
        "#000000": np.array([[1, 0], [0, 1]], dtype=np.uint8),
        "#FFFFFF": np.array([[0, 1], [1, 0]], dtype=np.uint8),
    }

    silhouette = np.ones((2, 2), dtype=np.uint8)

    assert verify_knockout_property(open_masks, silhouette)


def test_verify_knockout_property_partial_silhouette() -> None:
    """Test knockout with partial silhouette."""
    open_masks = {
        "#000000": np.array([[1, 0], [0, 0]], dtype=np.uint8),
        "#FFFFFF": np.array([[0, 1], [0, 0]], dtype=np.uint8),
    }

    silhouette = np.array([[1, 1], [0, 0]], dtype=np.uint8)

    assert verify_knockout_property(open_masks, silhouette)


def test_verify_knockout_property_violation() -> None:
    """Test knockout property violation (overlap)."""
    open_masks = {
        "#000000": np.array([[1, 1], [0, 0]], dtype=np.uint8),
        "#FFFFFF": np.array([[1, 0], [1, 0]], dtype=np.uint8),
    }

    silhouette = np.ones((2, 2), dtype=np.uint8)

    # Overlap at (0, 0), gap at (1, 1)
    assert not verify_knockout_property(open_masks, silhouette)


def test_verify_knockout_property_gap() -> None:
    """Test knockout property violation (gap)."""
    open_masks = {
        "#000000": np.array([[1, 0], [0, 0]], dtype=np.uint8),
        "#FFFFFF": np.array([[0, 1], [0, 0]], dtype=np.uint8),
    }

    silhouette = np.ones((2, 2), dtype=np.uint8)

    # Gap at (1, 0) and (1, 1)
    assert not verify_knockout_property(open_masks, silhouette)


def test_verify_knockout_property_empty() -> None:
    """Test knockout with empty masks."""
    open_masks: dict[str, np.ndarray] = {}
    silhouette = np.zeros((2, 2), dtype=np.uint8)

    assert verify_knockout_property(open_masks, silhouette)


def test_verify_knockout_property_three_colors() -> None:
    """Test knockout with 3 colors."""
    open_masks = {
        "#000000": np.array([[1, 0, 0], [0, 0, 0]], dtype=np.uint8),
        "#808080": np.array([[0, 1, 0], [0, 0, 0]], dtype=np.uint8),
        "#FFFFFF": np.array([[0, 0, 1], [0, 0, 0]], dtype=np.uint8),
    }

    silhouette = np.array([[1, 1, 1], [0, 0, 0]], dtype=np.uint8)

    assert verify_knockout_property(open_masks, silhouette)
