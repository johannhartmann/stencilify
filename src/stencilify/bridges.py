"""Island fixing by filling small islands and adding bridges for large ones."""

from dataclasses import dataclass

import cv2
import numpy as np

from stencilify.islands import find_material_islands


@dataclass
class BridgeInfo:
    """Information about a single bridge.

    Attributes:
        island_id: ID of the island being connected
        start: Starting point (x, y) on the island
        end: Ending point (x, y) on supported material
        width_px: Width of the bridge in pixels
    """

    island_id: int
    start: tuple[int, int]
    end: tuple[int, int]
    width_px: int


@dataclass
class BridgeReport:
    """Report of island fixing operations.

    Attributes:
        islands_filled: Number of small islands filled
        bridges_added: Number of bridges added
        islands_remaining: Number of unresolved islands after fixing
        bridge_info: List of BridgeInfo for each bridge added
    """

    islands_filled: int
    bridges_added: int
    islands_remaining: int
    bridge_info: list[BridgeInfo]


def fix_islands(
    open_mask: np.ndarray,
    min_island_area_px: int,
    bridge_width_px: int,
    max_attempts: int = 3,
) -> tuple[np.ndarray, BridgeReport]:
    """
    Fix material islands by filling small ones and adding bridges for large ones.

    Args:
        open_mask: Binary mask [H, W] with 0/1 values (1 = cut out / spray)
        min_island_area_px: Minimum island area to keep (fill smaller ones)
        bridge_width_px: Width of bridges to add (0 = no bridging)
        max_attempts: Maximum bridge attempts per island (default 3)

    Returns:
        Tuple of (fixed_open_mask, BridgeReport)

    Raises:
        ValueError: If open_mask is invalid
    """
    if open_mask.ndim != 2:
        raise ValueError(f"open_mask must be 2D, got shape {open_mask.shape}")

    if open_mask.dtype != np.uint8:
        raise ValueError(f"open_mask must be uint8, got {open_mask.dtype}")

    if not np.all((open_mask == 0) | (open_mask == 1)):
        raise ValueError("open_mask must contain only 0 or 1 values")

    # Work with a copy
    fixed_mask = open_mask.copy()

    islands_filled = 0
    bridge_info_list: list[BridgeInfo] = []

    # Initial island detection
    island_result = find_material_islands(fixed_mask)

    if island_result.island_count == 0:
        # No islands, nothing to fix
        return fixed_mask, BridgeReport(
            islands_filled=0,
            bridges_added=0,
            islands_remaining=0,
            bridge_info=[],
        )

    # Separate small and large islands
    small_islands = []
    large_islands = []

    for island in island_result.island_stats:
        if island.area_px < min_island_area_px:
            small_islands.append(island)
        else:
            large_islands.append(island)

    # Fill small islands (convert material to open area)
    for island in small_islands:
        # Find pixels belonging to this island
        x, y, w, h = island.bbox
        roi = island_result.island_mask[y : y + h, x : x + w]
        # Set open_mask to 1 where island exists
        fixed_mask[y : y + h, x : x + w][roi > 0] = 1
        islands_filled += 1

    # Add bridges for large islands
    if bridge_width_px > 0 and len(large_islands) > 0:
        # Recompute material and supported regions
        material = 1 - fixed_mask

        # Multiple attempts to bridge all islands
        for _ in range(max_attempts):
            # Recompute islands
            island_result = find_material_islands(fixed_mask)

            if island_result.island_count == 0:
                break

            # Get remaining large islands
            remaining_large = [
                island
                for island in island_result.island_stats
                if island.area_px >= min_island_area_px
            ]

            if len(remaining_large) == 0:
                break

            # For each remaining large island, add one bridge
            for island_idx, island in enumerate(remaining_large):
                # Compute supported material (material that touches border)
                supported_material = material.copy()
                # Remove island pixels from supported material
                supported_material[island_result.island_mask > 0] = 0

                if np.sum(supported_material) == 0:
                    # No supported material, cannot bridge
                    continue

                # Compute distance transform from supported material
                dist_transform = cv2.distanceTransform(
                    (1 - supported_material).astype(np.uint8) * 255,
                    cv2.DIST_L2,
                    5,
                )

                # Find island pixel closest to support
                island_pixels = np.argwhere(
                    (island_result.island_mask > 0)
                    & (
                        island_result.island_mask
                        == island_result.island_mask[
                            int(island.centroid[1]), int(island.centroid[0])
                        ]
                    )
                )

                if len(island_pixels) == 0:
                    continue

                # Get distances for island pixels
                distances = dist_transform[island_pixels[:, 0], island_pixels[:, 1]]
                min_dist_idx = np.argmin(distances)
                closest_island_pixel = island_pixels[min_dist_idx]

                # Find nearest supported pixel
                # Search in a radius around the closest island pixel
                search_radius = int(distances[min_dist_idx]) + 10
                y, x = closest_island_pixel

                # Create search region
                y_min = max(0, y - search_radius)
                y_max = min(supported_material.shape[0], y + search_radius + 1)
                x_min = max(0, x - search_radius)
                x_max = min(supported_material.shape[1], x + search_radius + 1)

                search_region = supported_material[y_min:y_max, x_min:x_max]
                if np.sum(search_region) == 0:
                    continue

                # Find nearest support pixel in region
                support_pixels_rel = np.argwhere(search_region > 0)
                if len(support_pixels_rel) == 0:
                    continue

                # Compute distances from island pixel to support pixels
                support_pixels = support_pixels_rel + np.array([y_min, x_min])
                dists = np.sqrt((support_pixels[:, 0] - y) ** 2 + (support_pixels[:, 1] - x) ** 2)
                nearest_support_idx = np.argmin(dists)
                nearest_support = support_pixels[nearest_support_idx]

                # Draw bridge (thick line in material space)
                # Convert to (x, y) for cv2.line
                start_pt = (int(x), int(y))
                end_pt = (int(nearest_support[1]), int(nearest_support[0]))

                # Draw line on fixed_mask (set to 0 = material)
                cv2.line(
                    fixed_mask,
                    start_pt,
                    end_pt,
                    color=0,
                    thickness=bridge_width_px,
                )

                # Record bridge info
                bridge_info_list.append(
                    BridgeInfo(
                        island_id=island_idx,
                        start=start_pt,
                        end=end_pt,
                        width_px=bridge_width_px,
                    )
                )

                # Update material mask
                material = 1 - fixed_mask

            # After adding bridges for all islands in this attempt, continue to next attempt

    # Final island count
    final_result = find_material_islands(fixed_mask)
    remaining_large = [
        island for island in final_result.island_stats if island.area_px >= min_island_area_px
    ]

    return fixed_mask, BridgeReport(
        islands_filled=islands_filled,
        bridges_added=len(bridge_info_list),
        islands_remaining=len(remaining_large),
        bridge_info=bridge_info_list,
    )
