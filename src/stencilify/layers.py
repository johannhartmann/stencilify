"""Layer mask generation and paint order computation."""

import numpy as np

from stencilify.config import LayerMode, PaintOrder


def build_open_masks(
    label_map: np.ndarray,
    silhouette: np.ndarray,
    palette: list[str],
    mode: LayerMode = LayerMode.KNOCKOUT,
) -> dict[str, np.ndarray]:
    """
    Build binary open masks for each palette color.

    An open mask has 1 where material should be cut out / paint sprayed.

    Two modes are supported:
    - KNOCKOUT: Each pixel belongs to exactly one layer (exclusive masks)
    - OVERLAPPING: Each layer includes all lighter colors (traditional stencil graffiti)

    In overlapping mode, layers are cumulative:
    - Darkest layer (index 0): includes pixels with label >= 0 (all colors)
    - Mid layer (index 1): includes pixels with label >= 1 (mid + light)
    - Lightest layer (index N): includes only pixels with label == N

    This allows traditional stencil painting where each lighter layer is painted
    over the previous darker layers.

    Args:
        label_map: [H, W] array with palette index (0..K-1) per pixel, -1 outside silhouette
        silhouette: [H, W] binary mask (0/1)
        palette: List of HEX color strings in order (sorted dark to light for overlapping)
        mode: Layer generation mode (knockout or overlapping)

    Returns:
        Dict mapping color_hex -> binary mask [H, W] with 0/1 values

    Raises:
        ValueError: If shapes don't match or palette is invalid
    """
    if label_map.shape != silhouette.shape:
        raise ValueError(
            f"Shape mismatch: label_map {label_map.shape} vs silhouette {silhouette.shape}"
        )

    if not palette or len(palette) < 2 or len(palette) > 4:
        raise ValueError(f"Palette must have 2-4 colors, got {len(palette)}")

    h, w = label_map.shape
    open_masks: dict[str, np.ndarray] = {}

    if mode == LayerMode.KNOCKOUT:
        # Knockout mode: each pixel belongs to exactly one layer
        for idx, color_hex in enumerate(palette):
            mask = np.zeros((h, w), dtype=np.uint8)
            mask[label_map == idx] = 1
            mask = mask & silhouette
            open_masks[color_hex] = mask

    elif mode == LayerMode.OVERLAPPING:
        # Overlapping mode: each layer includes all lighter colors
        # Layer 0 (darkest): includes all pixels (0, 1, 2, ...)
        # Layer 1: includes pixels with label >= 1 (1, 2, ...)
        # Layer N (lightest): includes only pixels with label == N
        for idx, color_hex in enumerate(palette):
            mask = np.zeros((h, w), dtype=np.uint8)
            # Include this layer and all lighter layers
            mask[label_map >= idx] = 1
            mask = mask & silhouette
            open_masks[color_hex] = mask

    else:
        raise ValueError(f"Unknown layer mode: {mode}")

    return open_masks


def compute_luminance(color_hex: str) -> float:
    """
    Compute luminance (Y) of a color using standard luma formula.

    Y = 0.299*R + 0.587*G + 0.114*B

    Args:
        color_hex: Color in format "#RRGGBB" or "RRGGBB"

    Returns:
        Luminance value in range [0, 255]

    Raises:
        ValueError: If hex color format is invalid
    """
    # Remove '#' if present
    color_hex = color_hex.lstrip("#")

    if len(color_hex) != 6:
        raise ValueError(f"Invalid HEX color format: {color_hex}")

    try:
        r = int(color_hex[0:2], 16)
        g = int(color_hex[2:4], 16)
        b = int(color_hex[4:6], 16)
    except ValueError as e:
        raise ValueError(f"Invalid HEX color format: {color_hex}") from e

    # Standard luma formula
    luminance = 0.299 * r + 0.587 * g + 0.114 * b

    return luminance


def compute_paint_order(palette: list[str], mode: PaintOrder) -> list[int]:
    """
    Compute paint order indices for palette colors.

    Args:
        palette: List of HEX color strings
        mode: Paint order mode (GIVEN or AUTO)

    Returns:
        List of palette indices in paint order

    Raises:
        ValueError: If palette is invalid
    """
    if not palette or len(palette) < 2 or len(palette) > 4:
        raise ValueError(f"Palette must have 2-4 colors, got {len(palette)}")

    if mode == PaintOrder.GIVEN:
        # Use palette order as-is
        return list(range(len(palette)))

    elif mode == PaintOrder.AUTO:
        # Sort by luminance (dark to light)
        luminances = [(idx, compute_luminance(color)) for idx, color in enumerate(palette)]
        # Sort by luminance ascending (dark first)
        sorted_by_luma = sorted(luminances, key=lambda x: x[1])
        return [idx for idx, _ in sorted_by_luma]

    else:
        raise ValueError(f"Unknown paint order mode: {mode}")


def verify_knockout_property(
    open_masks: dict[str, np.ndarray],
    silhouette: np.ndarray,
) -> bool:
    """
    Verify that the knockout property holds: each pixel in silhouette belongs to exactly one layer.

    Args:
        open_masks: Dict of color -> binary mask
        silhouette: Binary silhouette mask

    Returns:
        True if knockout property holds, False otherwise
    """
    if not open_masks:
        return bool(np.all(silhouette == 0))

    # Sum all masks
    total_mask = np.zeros_like(silhouette, dtype=np.int32)
    for mask in open_masks.values():
        total_mask += mask

    # Should equal silhouette exactly
    return bool(np.array_equal(total_mask, silhouette))
