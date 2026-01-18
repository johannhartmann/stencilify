"""Mask generation and morphology operations."""

import numpy as np
from scipy import ndimage  # type: ignore[import-untyped]


def silhouette_from_alpha(
    alpha: np.ndarray,
    threshold: int = 20,
) -> np.ndarray:
    """
    Create a binary silhouette mask from an alpha channel.

    Args:
        alpha: Alpha channel (H, W), uint8 (0-255)
        threshold: Alpha threshold value (0-255). Pixels with alpha > threshold
                   are considered foreground (value 1). Default: 20

    Returns:
        Binary mask (H, W), uint8 with values 0 or 1

    Raises:
        ValueError: If input is invalid
    """
    if alpha.dtype != np.uint8:
        raise ValueError(f"Alpha must be uint8, got {alpha.dtype}")

    if alpha.ndim != 2:
        raise ValueError(f"Alpha must be 2D, got shape {alpha.shape}")

    if not (0 <= threshold <= 255):
        raise ValueError(f"Threshold must be in [0, 255], got {threshold}")

    # Threshold the alpha channel
    # Values > threshold become 1 (foreground), others become 0 (background)
    mask = (alpha > threshold).astype(np.uint8)

    return mask


def morph_smooth(
    mask: np.ndarray,
    close_px: int,
    open_px: int,
) -> np.ndarray:
    """
    Smooth a binary mask using morphological operations.

    Applies closing followed by opening to:
    - Close small holes and gaps (closing)
    - Remove small protrusions and noise (opening)

    Args:
        mask: Binary mask (H, W), uint8 with values 0 or 1
        close_px: Kernel size for morphological closing (in pixels).
                  Set to 0 to skip closing.
        open_px: Kernel size for morphological opening (in pixels).
                 Set to 0 to skip opening.

    Returns:
        Smoothed binary mask (H, W), uint8 with values 0 or 1

    Raises:
        ValueError: If input is invalid
    """
    if mask.dtype != np.uint8:
        raise ValueError(f"Mask must be uint8, got {mask.dtype}")

    if mask.ndim != 2:
        raise ValueError(f"Mask must be 2D, got shape {mask.shape}")

    if not np.all((mask == 0) | (mask == 1)):
        raise ValueError("Mask must contain only 0 or 1 values")

    if close_px < 0 or open_px < 0:
        raise ValueError("Kernel sizes must be non-negative")

    result = mask.copy()

    # Apply closing (dilation followed by erosion)
    # Closes small holes and gaps
    if close_px > 0:
        # Create circular structuring element
        close_kernel = _create_circular_kernel(close_px)
        result = ndimage.binary_closing(
            result,
            structure=close_kernel,
        ).astype(np.uint8)

    # Apply opening (erosion followed by dilation)
    # Removes small protrusions and noise
    if open_px > 0:
        # Create circular structuring element
        open_kernel = _create_circular_kernel(open_px)
        result = ndimage.binary_opening(
            result,
            structure=open_kernel,
        ).astype(np.uint8)

    return result


def _create_circular_kernel(radius_px: int) -> np.ndarray:
    """
    Create a circular structuring element for morphology operations.

    Args:
        radius_px: Radius of the circular kernel in pixels

    Returns:
        Boolean array representing a circular kernel
    """
    if radius_px <= 0:
        return np.ones((1, 1), dtype=bool)

    # Create a square grid
    y, x = np.ogrid[-radius_px : radius_px + 1, -radius_px : radius_px + 1]

    # Create circular mask
    circle: np.ndarray = x * x + y * y <= radius_px * radius_px

    return circle
