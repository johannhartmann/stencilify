"""Stencil cuttability optimization for layer masks."""

import cv2
import numpy as np


def morph_cleanup(open_mask: np.ndarray, min_feature_px: int) -> np.ndarray:
    """
    Clean up open mask using morphological operations to smooth jagged edges.

    Performs closing (fill small holes) followed by opening (remove small protrusions).
    Kernel size is proportional to min_feature_px.

    Args:
        open_mask: Binary mask [H, W] with 0/1 values (1 = cut out / spray)
        min_feature_px: Minimum feature size in pixels

    Returns:
        Cleaned binary mask [H, W] with 0/1 values

    Raises:
        ValueError: If open_mask is invalid
    """
    if open_mask.ndim != 2:
        raise ValueError(f"open_mask must be 2D, got shape {open_mask.shape}")

    if open_mask.dtype != np.uint8:
        raise ValueError(f"open_mask must be uint8, got {open_mask.dtype}")

    if not np.all((open_mask == 0) | (open_mask == 1)):
        raise ValueError("open_mask must contain only 0 or 1 values")

    # Convert to uint8 255 for OpenCV (0 or 255)
    mask = open_mask * 255

    # Kernel size: use min_feature_px as base, ensure odd
    kernel_size = max(3, int(min_feature_px) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))

    # Close: fill small holes
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Open: remove small protrusions
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # Convert back to 0/1
    result = (mask > 127).astype(np.uint8)

    return result


def remove_small_cutouts(open_mask: np.ndarray, min_area_px: int) -> np.ndarray:
    """
    Remove small disconnected cutouts (connected components) from open mask.

    Args:
        open_mask: Binary mask [H, W] with 0/1 values (1 = cut out / spray)
        min_area_px: Minimum area in pixels for a cutout to be kept

    Returns:
        Filtered binary mask [H, W] with 0/1 values

    Raises:
        ValueError: If open_mask is invalid
    """
    if open_mask.ndim != 2:
        raise ValueError(f"open_mask must be 2D, got shape {open_mask.shape}")

    if open_mask.dtype != np.uint8:
        raise ValueError(f"open_mask must be uint8, got {open_mask.dtype}")

    if not np.all((open_mask == 0) | (open_mask == 1)):
        raise ValueError("open_mask must contain only 0 or 1 values")

    # Convert to uint8 255 for OpenCV
    mask = open_mask * 255

    # Find connected components
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)

    # Create output mask
    result = np.zeros_like(open_mask)

    # Keep components with area >= min_area_px
    # Label 0 is background, so start from 1
    for label in range(1, num_labels):
        area = stats[label, cv2.CC_STAT_AREA]
        if area >= min_area_px:
            result[labels == label] = 1

    return result


def compute_layer_metrics(open_mask: np.ndarray) -> dict[str, int | float]:
    """
    Compute metrics for an open mask layer.

    Args:
        open_mask: Binary mask [H, W] with 0/1 values (1 = cut out / spray)

    Returns:
        Dict with metrics:
        - cutout_component_count: Number of disconnected cutout regions
        - smallest_component_area_px: Area of smallest component (0 if none)
        - total_open_area_px: Total area where mask == 1
        - estimated_contour_length_px: Approximate contour perimeter

    Raises:
        ValueError: If open_mask is invalid
    """
    if open_mask.ndim != 2:
        raise ValueError(f"open_mask must be 2D, got shape {open_mask.shape}")

    if open_mask.dtype != np.uint8:
        raise ValueError(f"open_mask must be uint8, got {open_mask.dtype}")

    if not np.all((open_mask == 0) | (open_mask == 1)):
        raise ValueError("open_mask must contain only 0 or 1 values")

    # Convert to uint8 255 for OpenCV
    mask = open_mask * 255

    # Total open area
    total_open_area_px = int(np.sum(open_mask))

    # Find connected components
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)

    # Count components (excluding background label 0)
    cutout_component_count = num_labels - 1

    # Find smallest component area
    smallest_component_area_px = 0
    if cutout_component_count > 0:
        areas = [stats[label, cv2.CC_STAT_AREA] for label in range(1, num_labels)]
        smallest_component_area_px = int(min(areas))

    # Estimate contour length using findContours
    contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    estimated_contour_length_px = sum(cv2.arcLength(contour, closed=True) for contour in contours)

    return {
        "cutout_component_count": cutout_component_count,
        "smallest_component_area_px": smallest_component_area_px,
        "total_open_area_px": total_open_area_px,
        "estimated_contour_length_px": float(estimated_contour_length_px),
    }
