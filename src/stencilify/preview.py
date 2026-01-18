"""Preview rendering for stencil layers."""

from pathlib import Path

import numpy as np
from PIL import Image


def hex_to_rgb(color_hex: str) -> tuple[int, int, int]:
    """
    Convert HEX color to RGB tuple.

    Args:
        color_hex: Color in format "#RRGGBB" or "RRGGBB"

    Returns:
        Tuple of (R, G, B) in range [0, 255]

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

    return (r, g, b)


def render_preview(
    open_masks: dict[str, np.ndarray],
    palette: list[str],
    paint_order: list[int],
) -> np.ndarray:
    """
    Render a preview composite by painting layers in order.

    Starts with a transparent canvas and paints each layer in paint order.
    Where a layer's open_mask is 1, that color is painted.

    Args:
        open_masks: Dict mapping color_hex -> binary mask [H, W]
        palette: List of HEX color strings
        paint_order: List of palette indices in paint order

    Returns:
        RGBA image [H, W, 4] as uint8

    Raises:
        ValueError: If inputs are invalid
    """
    if not open_masks:
        raise ValueError("open_masks cannot be empty")

    if not palette:
        raise ValueError("palette cannot be empty")

    if not paint_order:
        raise ValueError("paint_order cannot be empty")

    # Get dimensions from first mask
    first_mask = next(iter(open_masks.values()))
    h, w = first_mask.shape

    # Verify all masks have same shape
    for color_hex, mask in open_masks.items():
        if mask.shape != (h, w):
            raise ValueError(f"Mask for {color_hex} has shape {mask.shape}, expected {(h, w)}")

    # Create transparent RGBA canvas
    canvas = np.zeros((h, w, 4), dtype=np.uint8)

    # Paint layers in order
    for idx in paint_order:
        if idx < 0 or idx >= len(palette):
            raise ValueError(
                f"Paint order index {idx} out of range for palette of size {len(palette)}"
            )

        color_hex = palette[idx]
        if color_hex not in open_masks:
            raise ValueError(f"Color {color_hex} not found in open_masks")

        mask = open_masks[color_hex]
        r, g, b = hex_to_rgb(color_hex)

        # Paint where mask is 1
        canvas[mask > 0, 0] = r
        canvas[mask > 0, 1] = g
        canvas[mask > 0, 2] = b
        canvas[mask > 0, 3] = 255  # Full opacity

    return canvas


def save_preview(preview: np.ndarray, output_path: Path) -> None:
    """
    Save preview image to disk.

    Args:
        preview: RGBA image [H, W, 4] as uint8
        output_path: Path to save the preview image

    Raises:
        ValueError: If preview format is invalid
    """
    if preview.ndim != 3 or preview.shape[2] != 4:
        raise ValueError(f"Preview must be RGBA [H, W, 4], got shape {preview.shape}")

    if preview.dtype != np.uint8:
        raise ValueError(f"Preview must be uint8, got {preview.dtype}")

    # Convert to PIL Image and save
    img = Image.fromarray(preview, mode="RGBA")
    img.save(output_path)
