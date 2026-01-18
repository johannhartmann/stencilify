"""Tests for export functionality."""

from pathlib import Path

import cv2
import numpy as np
import pytest

from stencilify.export import export_png, export_svg_contours, export_svg_potrace


def test_export_png_basic(tmp_path: Path) -> None:
    """Test basic PNG export."""
    # Create simple 100x100 mask
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[25:75, 25:75] = 1  # White square in center

    output_path = tmp_path / "test.png"

    export_png(mask, output_path)

    # Verify file exists
    assert output_path.exists()
    assert output_path.is_file()

    # Read back and verify
    loaded = cv2.imread(str(output_path), cv2.IMREAD_GRAYSCALE)
    assert loaded is not None
    assert loaded.shape == (100, 100)

    # Check that center is white (255) and edges are black (0)
    assert loaded[50, 50] == 255  # Center
    assert loaded[10, 10] == 0  # Corner


def test_export_png_all_white(tmp_path: Path) -> None:
    """Test PNG export with all white mask."""
    mask = np.ones((50, 50), dtype=np.uint8)
    output_path = tmp_path / "all_white.png"

    export_png(mask, output_path)

    assert output_path.exists()

    loaded = cv2.imread(str(output_path), cv2.IMREAD_GRAYSCALE)
    assert np.all(loaded == 255)


def test_export_png_all_black(tmp_path: Path) -> None:
    """Test PNG export with all black mask."""
    mask = np.zeros((50, 50), dtype=np.uint8)
    output_path = tmp_path / "all_black.png"

    export_png(mask, output_path)

    assert output_path.exists()

    loaded = cv2.imread(str(output_path), cv2.IMREAD_GRAYSCALE)
    assert np.all(loaded == 0)


def test_export_png_creates_parent_dirs(tmp_path: Path) -> None:
    """Test that PNG export creates parent directories."""
    output_path = tmp_path / "subdir" / "nested" / "test.png"
    mask = np.zeros((50, 50), dtype=np.uint8)

    export_png(mask, output_path)

    assert output_path.exists()
    assert output_path.parent.exists()


def test_export_png_invalid_shape() -> None:
    """Test error on non-2D mask."""
    mask = np.zeros((50, 50, 3), dtype=np.uint8)
    output_path = Path("test.png")

    with pytest.raises(ValueError, match="must be 2D"):
        export_png(mask, output_path)


def test_export_png_invalid_dtype() -> None:
    """Test error on non-uint8 mask."""
    mask = np.zeros((50, 50), dtype=np.float32)
    output_path = Path("test.png")

    with pytest.raises(ValueError, match="must be uint8"):
        export_png(mask, output_path)


def test_export_png_invalid_values() -> None:
    """Test error on non-binary values."""
    mask = np.full((50, 50), 2, dtype=np.uint8)
    output_path = Path("test.png")

    with pytest.raises(ValueError, match="only 0 or 1"):
        export_png(mask, output_path)


def test_export_svg_contours_basic(tmp_path: Path) -> None:
    """Test basic SVG export with contours."""
    # Create simple mask with a square
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[25:75, 25:75] = 1  # White square

    output_path = tmp_path / "test.svg"
    px_per_mm = 10.0  # 100x100 px = 10x10 mm

    export_svg_contours(mask, output_path, px_per_mm)

    # Verify file exists
    assert output_path.exists()
    assert output_path.is_file()

    # Read and verify SVG content
    svg_content = output_path.read_text()

    # Check for SVG tags
    assert "<svg" in svg_content
    assert "</svg>" in svg_content

    # Check dimensions (100px / 10 px/mm = 10mm)
    assert "10.0mm" in svg_content or "10mm" in svg_content

    # Check viewBox
    assert "viewBox" in svg_content

    # Check for path elements
    assert "<path" in svg_content


def test_export_svg_contours_dimensions(tmp_path: Path) -> None:
    """Test SVG dimensions are correct."""
    # 200x300 px at 10 px/mm = 20x30 mm
    mask = np.zeros((300, 200), dtype=np.uint8)
    mask[50:250, 50:150] = 1

    output_path = tmp_path / "dimensions.svg"
    px_per_mm = 10.0

    export_svg_contours(mask, output_path, px_per_mm)

    svg_content = output_path.read_text()

    # Check width and height
    assert "20.0mm" in svg_content or "20mm" in svg_content  # width
    assert "30.0mm" in svg_content or "30mm" in svg_content  # height


def test_export_svg_contours_circle(tmp_path: Path) -> None:
    """Test SVG export with circular shape."""
    # Create circular mask
    mask = np.zeros((100, 100), dtype=np.uint8)
    cv2.circle(mask, (50, 50), 30, color=1, thickness=-1)

    output_path = tmp_path / "circle.svg"
    px_per_mm = 10.0

    export_svg_contours(mask, output_path, px_per_mm)

    assert output_path.exists()

    svg_content = output_path.read_text()
    assert "<path" in svg_content


def test_export_svg_contours_multiple_shapes(tmp_path: Path) -> None:
    """Test SVG export with multiple shapes."""
    mask = np.zeros((200, 200), dtype=np.uint8)
    # Two separate squares
    mask[20:60, 20:60] = 1
    mask[120:160, 120:160] = 1

    output_path = tmp_path / "multiple.svg"
    px_per_mm = 10.0

    export_svg_contours(mask, output_path, px_per_mm)

    assert output_path.exists()

    svg_content = output_path.read_text()
    # Should have multiple path elements
    assert svg_content.count("<path") >= 2


def test_export_svg_contours_empty_mask(tmp_path: Path) -> None:
    """Test SVG export with empty mask (all black)."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    output_path = tmp_path / "empty.svg"
    px_per_mm = 10.0

    export_svg_contours(mask, output_path, px_per_mm)

    assert output_path.exists()

    svg_content = output_path.read_text()
    # Should still be valid SVG even with no paths
    assert "<svg" in svg_content


def test_export_svg_contours_creates_parent_dirs(tmp_path: Path) -> None:
    """Test that SVG export creates parent directories."""
    output_path = tmp_path / "subdir" / "nested" / "test.svg"
    mask = np.zeros((50, 50), dtype=np.uint8)
    mask[10:40, 10:40] = 1

    export_svg_contours(mask, output_path, px_per_mm=10.0)

    assert output_path.exists()
    assert output_path.parent.exists()


def test_export_svg_contours_invalid_shape() -> None:
    """Test error on non-2D mask."""
    mask = np.zeros((50, 50, 3), dtype=np.uint8)
    output_path = Path("test.svg")

    with pytest.raises(ValueError, match="must be 2D"):
        export_svg_contours(mask, output_path, px_per_mm=10.0)


def test_export_svg_contours_invalid_dtype() -> None:
    """Test error on non-uint8 mask."""
    mask = np.zeros((50, 50), dtype=np.float32)
    output_path = Path("test.svg")

    with pytest.raises(ValueError, match="must be uint8"):
        export_svg_contours(mask, output_path, px_per_mm=10.0)


def test_export_svg_contours_invalid_values() -> None:
    """Test error on non-binary values."""
    mask = np.full((50, 50), 2, dtype=np.uint8)
    output_path = Path("test.svg")

    with pytest.raises(ValueError, match="only 0 or 1"):
        export_svg_contours(mask, output_path, px_per_mm=10.0)


def test_export_svg_contours_invalid_px_per_mm() -> None:
    """Test error on invalid px_per_mm."""
    mask = np.zeros((50, 50), dtype=np.uint8)
    output_path = Path("test.svg")

    with pytest.raises(ValueError, match="must be positive"):
        export_svg_contours(mask, output_path, px_per_mm=0.0)

    with pytest.raises(ValueError, match="must be positive"):
        export_svg_contours(mask, output_path, px_per_mm=-1.0)


def test_export_svg_potrace_fallback_no_potrace(tmp_path: Path) -> None:
    """Test potrace fallback when potrace is not available."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[25:75, 25:75] = 1

    output_path = tmp_path / "potrace_fallback.svg"
    px_per_mm = 10.0

    # Use non-existent potrace path to force fallback
    export_svg_potrace(mask, output_path, px_per_mm, potrace_path="nonexistent_potrace")

    # Should still create file via fallback
    assert output_path.exists()

    svg_content = output_path.read_text()
    assert "<svg" in svg_content


def test_export_svg_potrace_with_potrace_if_available(tmp_path: Path) -> None:
    """Test potrace export if potrace is available."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[25:75, 25:75] = 1

    output_path = tmp_path / "potrace.svg"
    px_per_mm = 10.0

    # Try with default potrace path
    export_svg_potrace(mask, output_path, px_per_mm)

    # Should create file either via potrace or fallback
    assert output_path.exists()

    svg_content = output_path.read_text()
    assert "<svg" in svg_content


def test_export_svg_potrace_invalid_shape() -> None:
    """Test error on non-2D mask."""
    mask = np.zeros((50, 50, 3), dtype=np.uint8)
    output_path = Path("test.svg")

    with pytest.raises(ValueError, match="must be 2D"):
        export_svg_potrace(mask, output_path, px_per_mm=10.0)


def test_export_svg_potrace_invalid_dtype() -> None:
    """Test error on non-uint8 mask."""
    mask = np.zeros((50, 50), dtype=np.float32)
    output_path = Path("test.svg")

    with pytest.raises(ValueError, match="must be uint8"):
        export_svg_potrace(mask, output_path, px_per_mm=10.0)


def test_export_svg_potrace_invalid_values() -> None:
    """Test error on non-binary values."""
    mask = np.full((50, 50), 2, dtype=np.uint8)
    output_path = Path("test.svg")

    with pytest.raises(ValueError, match="only 0 or 1"):
        export_svg_potrace(mask, output_path, px_per_mm=10.0)


def test_export_svg_potrace_invalid_px_per_mm() -> None:
    """Test error on invalid px_per_mm."""
    mask = np.zeros((50, 50), dtype=np.uint8)
    output_path = Path("test.svg")

    with pytest.raises(ValueError, match="must be positive"):
        export_svg_potrace(mask, output_path, px_per_mm=0.0)


def test_export_all_formats(tmp_path: Path) -> None:
    """Test exporting to all formats."""
    # Create test mask
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[20:80, 20:80] = 1

    # Export to all formats
    png_path = tmp_path / "layer.png"
    svg_contours_path = tmp_path / "layer_contours.svg"
    svg_potrace_path = tmp_path / "layer_potrace.svg"

    export_png(mask, png_path)
    export_svg_contours(mask, svg_contours_path, px_per_mm=10.0)
    export_svg_potrace(mask, svg_potrace_path, px_per_mm=10.0)

    # Verify all files exist
    assert png_path.exists()
    assert svg_contours_path.exists()
    assert svg_potrace_path.exists()

    # Verify PNG content
    loaded_png = cv2.imread(str(png_path), cv2.IMREAD_GRAYSCALE)
    assert loaded_png is not None

    # Verify SVG content
    assert "<svg" in svg_contours_path.read_text()
    assert "<svg" in svg_potrace_path.read_text()
