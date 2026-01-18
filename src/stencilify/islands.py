"""Island detection for stencil material support."""

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class IslandStats:
    """Statistics for a single material island.

    Attributes:
        area_px: Area in pixels
        bbox: Bounding box as (x, y, width, height)
        centroid: Centroid as (x, y)
    """

    area_px: int
    bbox: tuple[int, int, int, int]
    centroid: tuple[float, float]


@dataclass
class IslandResult:
    """Result of island detection.

    Attributes:
        island_mask: Binary mask [H, W] with 1 where island material exists
        island_stats: List of statistics for each island
        island_count: Number of islands detected
    """

    island_mask: np.ndarray
    island_stats: list[IslandStats]
    island_count: int


def find_material_islands(open_mask: np.ndarray) -> IslandResult:
    """
    Find material islands that would fall out of the stencil.

    Material islands are connected components of material (1 - open_mask) that
    do NOT touch any border pixel (top, bottom, left, right).

    Args:
        open_mask: Binary mask [H, W] with 0/1 values (1 = cut out / spray)

    Returns:
        IslandResult with island mask and statistics

    Raises:
        ValueError: If open_mask is invalid
    """
    if open_mask.ndim != 2:
        raise ValueError(f"open_mask must be 2D, got shape {open_mask.shape}")

    if open_mask.dtype != np.uint8:
        raise ValueError(f"open_mask must be uint8, got {open_mask.dtype}")

    if not np.all((open_mask == 0) | (open_mask == 1)):
        raise ValueError("open_mask must contain only 0 or 1 values")

    h, w = open_mask.shape

    # Compute material mask (complement of open mask)
    material = 1 - open_mask

    # Convert to uint8 255 for OpenCV
    material_255 = material * 255

    # Find connected components in material
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        material_255, connectivity=8
    )

    # Determine which components touch the border
    touching_border = set()

    # Check background label 0
    touching_border.add(0)

    # Check each component
    for label in range(1, num_labels):
        component_mask = labels == label

        # Check if component touches any border
        if (
            np.any(component_mask[0, :])  # Top edge
            or np.any(component_mask[-1, :])  # Bottom edge
            or np.any(component_mask[:, 0])  # Left edge
            or np.any(component_mask[:, -1])  # Right edge
        ):
            touching_border.add(label)

    # Create island mask (components NOT touching border)
    island_mask = np.zeros((h, w), dtype=np.uint8)
    island_stats_list: list[IslandStats] = []

    for label in range(1, num_labels):
        if label not in touching_border:
            # This is an island
            island_mask[labels == label] = 1

            # Extract stats
            x = stats[label, cv2.CC_STAT_LEFT]
            y = stats[label, cv2.CC_STAT_TOP]
            width = stats[label, cv2.CC_STAT_WIDTH]
            height = stats[label, cv2.CC_STAT_HEIGHT]
            area = stats[label, cv2.CC_STAT_AREA]

            cx, cy = centroids[label]

            island_stats_list.append(
                IslandStats(
                    area_px=int(area),
                    bbox=(int(x), int(y), int(width), int(height)),
                    centroid=(float(cx), float(cy)),
                )
            )

    return IslandResult(
        island_mask=island_mask,
        island_stats=island_stats_list,
        island_count=len(island_stats_list),
    )
