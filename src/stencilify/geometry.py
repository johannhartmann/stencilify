"""Geometry utilities for page sizes and unit conversions."""

from dataclasses import dataclass
from enum import Enum


class PageSize(str, Enum):
    """Standard page sizes."""

    A4 = "A4"
    A3 = "A3"
    A2 = "A2"


class Orientation(str, Enum):
    """Page orientation."""

    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"
    AUTO = "auto"


@dataclass(frozen=True)
class Dimensions:
    """Page dimensions in millimeters."""

    width_mm: float
    height_mm: float


# ISO 216 A-series dimensions in millimeters (portrait orientation)
PAGE_SIZES_MM: dict[PageSize, Dimensions] = {
    PageSize.A4: Dimensions(width_mm=210.0, height_mm=297.0),
    PageSize.A3: Dimensions(width_mm=297.0, height_mm=420.0),
    PageSize.A2: Dimensions(width_mm=420.0, height_mm=594.0),
}


def get_page_dimensions(
    page_size: PageSize,
    orientation: Orientation,
    margin_mm: float = 0.0,
) -> Dimensions:
    """
    Get page dimensions with optional margins applied.

    Args:
        page_size: The page size (A4, A3, A2)
        orientation: Portrait, landscape, or auto
        margin_mm: Margin to subtract from each edge (total 2x per dimension)

    Returns:
        Dimensions with margins applied

    Raises:
        ValueError: If margins are too large for the page size
    """
    base = PAGE_SIZES_MM[page_size]

    # Apply orientation
    if orientation == Orientation.LANDSCAPE:
        width, height = base.height_mm, base.width_mm
    else:
        # Portrait or auto (will be determined later based on image aspect ratio)
        width, height = base.width_mm, base.height_mm

    # Apply margins (margin is subtracted from both sides)
    usable_width = width - (2 * margin_mm)
    usable_height = height - (2 * margin_mm)

    if usable_width <= 0 or usable_height <= 0:
        raise ValueError(
            f"Margins ({margin_mm}mm) are too large for {page_size.value} ({width}x{height}mm)"
        )

    return Dimensions(width_mm=usable_width, height_mm=usable_height)


def mm_to_pixels(mm: float, dpi: float = 300.0) -> int:
    """
    Convert millimeters to pixels at given DPI.

    Args:
        mm: Distance in millimeters
        dpi: Dots per inch (default: 300)

    Returns:
        Distance in pixels (rounded to nearest integer)
    """
    inches = mm / 25.4
    return round(inches * dpi)


def pixels_to_mm(pixels: int, dpi: float = 300.0) -> float:
    """
    Convert pixels to millimeters at given DPI.

    Args:
        pixels: Distance in pixels
        dpi: Dots per inch (default: 300)

    Returns:
        Distance in millimeters
    """
    inches = pixels / dpi
    return inches * 25.4


def mm2_to_pixels2(mm2: float, dpi: float = 300.0) -> float:
    """
    Convert square millimeters to square pixels.

    Args:
        mm2: Area in square millimeters
        dpi: Dots per inch (default: 300)

    Returns:
        Area in square pixels
    """
    pixels_per_mm = dpi / 25.4
    return mm2 * (pixels_per_mm**2)
