"""Tests for preview rendering."""

from pathlib import Path

import numpy as np
import pytest

from stencilify.preview import render_preview, save_preview


def test_render_preview_simple() -> None:
    """Test basic preview rendering with 2 colors."""
    open_masks = {
        "#000000": np.array([[1, 0], [0, 1]], dtype=np.uint8),
        "#FFFFFF": np.array([[0, 1], [1, 0]], dtype=np.uint8),
    }

    palette = ["#000000", "#FFFFFF"]
    paint_order = [0, 1]

    preview = render_preview(open_masks, palette, paint_order)

    # Check shape
    assert preview.shape == (2, 2, 4)
    assert preview.dtype == np.uint8

    # Check pixel values
    # (0, 0): black
    assert tuple(preview[0, 0]) == (0, 0, 0, 255)
    # (0, 1): white
    assert tuple(preview[0, 1]) == (255, 255, 255, 255)
    # (1, 0): white
    assert tuple(preview[1, 0]) == (255, 255, 255, 255)
    # (1, 1): black
    assert tuple(preview[1, 1]) == (0, 0, 0, 255)


def test_render_preview_paint_order() -> None:
    """Test that paint order affects result (later layers overwrite)."""
    # Both masks cover the same pixel (0, 0)
    open_masks = {
        "#FF0000": np.array([[1, 0], [0, 0]], dtype=np.uint8),
        "#0000FF": np.array([[1, 0], [0, 0]], dtype=np.uint8),
    }

    palette = ["#FF0000", "#0000FF"]

    # Red first, then blue (blue should win)
    paint_order_rb = [0, 1]
    preview_rb = render_preview(open_masks, palette, paint_order_rb)
    assert tuple(preview_rb[0, 0]) == (0, 0, 255, 255)  # Blue

    # Blue first, then red (red should win)
    paint_order_br = [1, 0]
    preview_br = render_preview(open_masks, palette, paint_order_br)
    assert tuple(preview_br[0, 0]) == (255, 0, 0, 255)  # Red


def test_render_preview_transparent_background() -> None:
    """Test that unpainted pixels remain transparent."""
    open_masks = {
        "#FF0000": np.array([[1, 0], [0, 0]], dtype=np.uint8),
    }

    palette = ["#FF0000"]
    paint_order = [0]

    preview = render_preview(open_masks, palette, paint_order)

    # (0, 0) painted red
    assert tuple(preview[0, 0]) == (255, 0, 0, 255)

    # Other pixels transparent
    assert tuple(preview[0, 1]) == (0, 0, 0, 0)
    assert tuple(preview[1, 0]) == (0, 0, 0, 0)
    assert tuple(preview[1, 1]) == (0, 0, 0, 0)


def test_render_preview_three_colors() -> None:
    """Test preview with 3 colors."""
    open_masks = {
        "#FF0000": np.array([[1, 0, 0]], dtype=np.uint8),
        "#00FF00": np.array([[0, 1, 0]], dtype=np.uint8),
        "#0000FF": np.array([[0, 0, 1]], dtype=np.uint8),
    }

    palette = ["#FF0000", "#00FF00", "#0000FF"]
    paint_order = [0, 1, 2]

    preview = render_preview(open_masks, palette, paint_order)

    assert preview.shape == (1, 3, 4)
    assert tuple(preview[0, 0]) == (255, 0, 0, 255)  # Red
    assert tuple(preview[0, 1]) == (0, 255, 0, 255)  # Green
    assert tuple(preview[0, 2]) == (0, 0, 255, 255)  # Blue


def test_render_preview_four_colors() -> None:
    """Test preview with 4 colors."""
    open_masks = {
        "#FF0000": np.array([[1, 0], [0, 0]], dtype=np.uint8),
        "#00FF00": np.array([[0, 1], [0, 0]], dtype=np.uint8),
        "#0000FF": np.array([[0, 0], [1, 0]], dtype=np.uint8),
        "#FFFF00": np.array([[0, 0], [0, 1]], dtype=np.uint8),
    }

    palette = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
    paint_order = [0, 1, 2, 3]

    preview = render_preview(open_masks, palette, paint_order)

    assert preview.shape == (2, 2, 4)
    assert tuple(preview[0, 0]) == (255, 0, 0, 255)  # Red
    assert tuple(preview[0, 1]) == (0, 255, 0, 255)  # Green
    assert tuple(preview[1, 0]) == (0, 0, 255, 255)  # Blue
    assert tuple(preview[1, 1]) == (255, 255, 0, 255)  # Yellow


def test_render_preview_empty_masks() -> None:
    """Test that empty open_masks raises error."""
    with pytest.raises(ValueError, match="cannot be empty"):
        render_preview({}, ["#000000"], [0])
def test_render_preview_shape_mismatch() -> None:
    """Test that mismatched mask shapes raise error."""
    open_masks = {
        "#000000": np.ones((2, 2), dtype=np.uint8),
        "#FFFFFF": np.ones((3, 3), dtype=np.uint8),
    }

    palette = ["#000000", "#FFFFFF"]
    paint_order = [0, 1]

    with pytest.raises(ValueError, match="expected"):
        render_preview(open_masks, palette, paint_order)
def test_save_preview_basic(tmp_path: Path) -> None:
    """Test saving preview to disk."""
    preview = np.zeros((10, 10, 4), dtype=np.uint8)
    preview[:, :, 3] = 255  # Opaque

    output_path = tmp_path / "preview.png"
    save_preview(preview, output_path)

    # Check file exists
    assert output_path.exists()

    # Check file is readable as image
    from PIL import Image

    img = Image.open(output_path)
    assert img.size == (10, 10)
    assert img.mode == "RGBA"


def test_save_preview_with_content(tmp_path: Path) -> None:
    """Test saving preview with colored content."""
    preview = np.zeros((5, 5, 4), dtype=np.uint8)
    # Red square in center
    preview[2, 2] = [255, 0, 0, 255]

    output_path = tmp_path / "preview.png"
    save_preview(preview, output_path)

    # Load and verify
    from PIL import Image

    img = Image.open(output_path)
    pixels = np.array(img)

    assert tuple(pixels[2, 2]) == (255, 0, 0, 255)
