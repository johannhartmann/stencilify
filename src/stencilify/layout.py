"""Page layout and registration marks."""

from dataclasses import dataclass

import cv2
import numpy as np

from stencilify.geometry import PAGE_SIZES_MM, Dimensions, Orientation, PageSize


@dataclass
class RegistrationMark:
    """Information about a registration mark.

    Attributes:
        center_px: Center position (x, y) in pixels
        radius_px: Radius in pixels
    """

    center_px: tuple[int, int]
    radius_px: int


def compute_page_canvas_px(page_mm: Dimensions, px_per_mm: float) -> tuple[int, int]:
    """
    Compute page canvas size in pixels.

    Args:
        page_mm: Page dimensions in millimeters
        px_per_mm: Pixels per millimeter

    Returns:
        Tuple of (height, width) in pixels
    """
    height_px = round(page_mm.height_mm * px_per_mm)
    width_px = round(page_mm.width_mm * px_per_mm)
    return (height_px, width_px)


def place_artwork_on_page(
    open_masks: dict[str, np.ndarray],
    page_size: PageSize,
    orientation: Orientation,
    margin_mm: float,
    px_per_mm: float,
) -> dict[str, np.ndarray]:
    """
    Place artwork on page canvas with margins.

    Scales artwork to fit within printable area (page - margins) while preserving
    aspect ratio. Centers artwork on page. All layers are placed identically.

    Args:
        open_masks: Dictionary of layer name -> open_mask (binary uint8)
        page_size: Page size (A4, A3, A2)
        orientation: Page orientation (portrait, landscape, or auto)
        margin_mm: Margin in millimeters (applied to all edges)
        px_per_mm: Pixels per millimeter

    Returns:
        Dictionary of layer name -> placed open_mask on page canvas

    Raises:
        ValueError: If inputs are invalid or margins too large
    """
    if not open_masks:
        raise ValueError("open_masks cannot be empty")

    # Get dimensions of first mask (all should be same size)
    first_mask = next(iter(open_masks.values()))
    if first_mask.ndim != 2:
        raise ValueError(f"Masks must be 2D, got shape {first_mask.shape}")
    if first_mask.dtype != np.uint8:
        raise ValueError(f"Masks must be uint8, got {first_mask.dtype}")

    artwork_h, artwork_w = first_mask.shape

    # Verify all masks have same dimensions
    for name, mask in open_masks.items():
        if mask.shape != (artwork_h, artwork_w):
            raise ValueError(
                f"All masks must have same dimensions. "
                f"Expected {(artwork_h, artwork_w)}, got {mask.shape} for layer '{name}'"
            )

    # Get page dimensions
    base_dims = PAGE_SIZES_MM[page_size]

    # Determine orientation (AUTO based on artwork aspect ratio)
    if orientation == Orientation.AUTO:
        artwork_aspect = artwork_w / artwork_h
        page_aspect = base_dims.width_mm / base_dims.height_mm
        # Use landscape if artwork is wider than page
        if artwork_aspect > page_aspect:
            effective_orientation = Orientation.LANDSCAPE
        else:
            effective_orientation = Orientation.PORTRAIT
    else:
        effective_orientation = orientation

    # Apply orientation to get page dimensions
    if effective_orientation == Orientation.LANDSCAPE:
        page_dims = Dimensions(width_mm=base_dims.height_mm, height_mm=base_dims.width_mm)
    else:
        page_dims = base_dims

    # Validate margins
    if margin_mm < 0:
        raise ValueError(f"margin_mm must be non-negative, got {margin_mm}")
    if margin_mm * 2 >= page_dims.width_mm or margin_mm * 2 >= page_dims.height_mm:
        raise ValueError(
            f"Margins ({margin_mm}mm) are too large for {page_size.value} "
            f"({page_dims.width_mm}x{page_dims.height_mm}mm)"
        )

    # Compute page canvas size
    canvas_h, canvas_w = compute_page_canvas_px(page_dims, px_per_mm)

    # Compute printable area (page - margins)
    margin_px = round(margin_mm * px_per_mm)
    printable_w = canvas_w - 2 * margin_px
    printable_h = canvas_h - 2 * margin_px

    if printable_w <= 0 or printable_h <= 0:
        raise ValueError("Margins too large, no printable area remaining")

    # Scale artwork to fit within printable area while preserving aspect ratio
    scale_w = printable_w / artwork_w
    scale_h = printable_h / artwork_h
    scale = min(scale_w, scale_h)

    scaled_w = round(artwork_w * scale)
    scaled_h = round(artwork_h * scale)

    # Compute offset to center artwork on page
    offset_x = (canvas_w - scaled_w) // 2
    offset_y = (canvas_h - scaled_h) // 2

    # Place all masks on page canvas
    placed_masks: dict[str, np.ndarray] = {}

    for name, mask in open_masks.items():
        # Create page canvas (all open = 1 by default)
        canvas = np.ones((canvas_h, canvas_w), dtype=np.uint8)

        # Resize mask to scaled size
        scaled_mask = cv2.resize(
            mask,
            (scaled_w, scaled_h),
            interpolation=cv2.INTER_NEAREST,
        )

        # Place scaled mask on canvas
        canvas[offset_y : offset_y + scaled_h, offset_x : offset_x + scaled_w] = scaled_mask

        placed_masks[name] = canvas

    return placed_masks


def add_registration_marks(
    placed_masks: dict[str, np.ndarray],
    px_per_mm: float,
    diameter_mm: float = 6.0,
    margin_mm: float = 10.0,
) -> dict[str, np.ndarray]:
    """
    Add registration marks to all layers.

    Adds 3 circular cutouts (open=1) at top-left, top-right, and bottom-left
    positions in the margin area. Marks are identical across all layers for
    precise alignment.

    Args:
        placed_masks: Dictionary of layer name -> placed open_mask on page canvas
        px_per_mm: Pixels per millimeter
        diameter_mm: Diameter of registration marks in millimeters (default 6mm)
        margin_mm: Margin in millimeters (for positioning marks, default 10mm)

    Returns:
        Dictionary of layer name -> open_mask with registration marks added

    Raises:
        ValueError: If inputs are invalid
    """
    if not placed_masks:
        raise ValueError("placed_masks cannot be empty")

    if diameter_mm <= 0:
        raise ValueError(f"diameter_mm must be positive, got {diameter_mm}")

    if margin_mm <= 0:
        raise ValueError(f"margin_mm must be positive, got {margin_mm}")

    # Get canvas dimensions from first mask
    first_mask = next(iter(placed_masks.values()))
    canvas_h, canvas_w = first_mask.shape

    # Compute mark radius in pixels
    radius_px = round((diameter_mm / 2) * px_per_mm)
    if radius_px < 1:
        radius_px = 1

    # Compute mark positions (centered in margin areas)
    # Top-left
    tl_x = round((margin_mm / 2) * px_per_mm)
    tl_y = round((margin_mm / 2) * px_per_mm)

    # Top-right
    tr_x = canvas_w - round((margin_mm / 2) * px_per_mm)
    tr_y = round((margin_mm / 2) * px_per_mm)

    # Bottom-left
    bl_x = round((margin_mm / 2) * px_per_mm)
    bl_y = canvas_h - round((margin_mm / 2) * px_per_mm)

    mark_positions = [
        RegistrationMark(center_px=(tl_x, tl_y), radius_px=radius_px),
        RegistrationMark(center_px=(tr_x, tr_y), radius_px=radius_px),
        RegistrationMark(center_px=(bl_x, bl_y), radius_px=radius_px),
    ]

    # Add marks to all masks
    marked_masks: dict[str, np.ndarray] = {}

    for name, mask in placed_masks.items():
        # Copy mask to avoid modifying original
        marked_mask = mask.copy()

        # Draw circles (set to 1 = open/cutout)
        for mark in mark_positions:
            cv2.circle(
                marked_mask,
                mark.center_px,
                mark.radius_px,
                color=1,
                thickness=-1,  # Filled circle
            )

        marked_masks[name] = marked_mask

    return marked_masks
