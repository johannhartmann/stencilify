"""Tests for geometry utilities."""

import pytest

from stencilify.geometry import (
    Dimensions,
    Orientation,
    PageSize,
    get_page_dimensions,
    mm2_to_pixels2,
    mm_to_pixels,
    pixels_to_mm,
)


def test_page_sizes_defined() -> None:
    """Test that all page sizes have defined dimensions."""
    from stencilify.geometry import PAGE_SIZES_MM

    assert PageSize.A4 in PAGE_SIZES_MM
    assert PageSize.A3 in PAGE_SIZES_MM
    assert PageSize.A2 in PAGE_SIZES_MM


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


def test_get_page_dimensions_margin_too_large() -> None:
    """Test that excessive margins raise an error."""
    with pytest.raises(ValueError, match="Margins.*too large"):
        get_page_dimensions(PageSize.A4, Orientation.PORTRAIT, margin_mm=200.0)


def test_mm_to_pixels_300dpi() -> None:
    """Test millimeter to pixel conversion at 300 DPI."""
    # 25.4mm = 1 inch = 300 pixels at 300 DPI
    pixels = mm_to_pixels(25.4, dpi=300.0)
    assert pixels == 300


def test_mm_to_pixels_600dpi() -> None:
    """Test millimeter to pixel conversion at 600 DPI."""
    # 25.4mm = 1 inch = 600 pixels at 600 DPI
    pixels = mm_to_pixels(25.4, dpi=600.0)
    assert pixels == 600


def test_pixels_to_mm_300dpi() -> None:
    """Test pixel to millimeter conversion at 300 DPI."""
    mm = pixels_to_mm(300, dpi=300.0)
    assert abs(mm - 25.4) < 0.01


def test_mm_to_pixels_roundtrip() -> None:
    """Test that conversion roundtrips correctly."""
    original_mm = 100.0
    pixels = mm_to_pixels(original_mm, dpi=300.0)
    back_to_mm = pixels_to_mm(pixels, dpi=300.0)
    assert abs(back_to_mm - original_mm) < 0.1


def test_mm2_to_pixels2() -> None:
    """Test area conversion from mm² to pixels²."""
    # 1mm² at 300 DPI
    dpi = 300.0
    mm2 = 1.0
    pixels_per_mm = dpi / 25.4
    expected = pixels_per_mm**2

    result = mm2_to_pixels2(mm2, dpi=dpi)
    assert abs(result - expected) < 0.01


def test_dimensions_immutable() -> None:
    """Test that Dimensions is immutable (frozen dataclass)."""
    dims = Dimensions(width_mm=100.0, height_mm=200.0)
    with pytest.raises(AttributeError):
        dims.width_mm = 150.0  # type: ignore[misc]
