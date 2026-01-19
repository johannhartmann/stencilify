"""Tests for geometry utilities."""


from stencilify.geometry import (
    Orientation,
    PageSize,
    get_page_dimensions,
    mm_to_pixels,
    pixels_to_mm,
)


def test_a4_dimensions() -> None:
    """Test A4 dimensions are correct."""
    from stencilify.geometry import PAGE_SIZES_MM

    a4 = PAGE_SIZES_MM[PageSize.A4]
    assert a4.width_mm == 210.0
    assert a4.height_mm == 297.0


def test_get_page_dimensions_portrait() -> None:
    """Test page dimensions in portrait orientation."""
    dims = get_page_dimensions(PageSize.A4, Orientation.PORTRAIT, margin_mm=0.0)
    assert dims.width_mm == 210.0
    assert dims.height_mm == 297.0


def test_get_page_dimensions_landscape() -> None:
    """Test page dimensions in landscape orientation."""
    dims = get_page_dimensions(PageSize.A4, Orientation.LANDSCAPE, margin_mm=0.0)
    assert dims.width_mm == 297.0
    assert dims.height_mm == 210.0


def test_get_page_dimensions_with_margin() -> None:
    """Test page dimensions with margins."""
    dims = get_page_dimensions(PageSize.A4, Orientation.PORTRAIT, margin_mm=10.0)
    # 210 - (2 * 10) = 190
    # 297 - (2 * 10) = 277
    assert dims.width_mm == 190.0
    assert dims.height_mm == 277.0
def test_mm_to_pixels_300dpi() -> None:
    """Test millimeter to pixel conversion at 300 DPI."""
    # 25.4mm = 1 inch = 300 pixels at 300 DPI
    pixels = mm_to_pixels(25.4, dpi=300.0)
    assert pixels == 300
def test_mm_to_pixels_roundtrip() -> None:
    """Test that conversion roundtrips correctly."""
    original_mm = 100.0
    pixels = mm_to_pixels(original_mm, dpi=300.0)
    back_to_mm = pixels_to_mm(pixels, dpi=300.0)
    assert abs(back_to_mm - original_mm) < 0.1
