"""Palette-constrained labeling using ICM optimization."""

from dataclasses import dataclass

import numpy as np
from skimage import color


@dataclass
class LabelingResult:
    """Result of palette-constrained labeling.

    Attributes:
        label_map_pixels: [H, W] array with palette index (0..K-1) per pixel, -1 outside silhouette
        label_per_spx: [spx_count] array with palette index per superpixel
        energy: Final energy value
    """

    label_map_pixels: np.ndarray
    label_per_spx: np.ndarray
    energy: float


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """
    Convert HEX color string to RGB tuple.

    Args:
        hex_color: Color in format "#RRGGBB" or "RRGGBB"

    Returns:
        Tuple of (R, G, B) values in range [0, 255]

    Raises:
        ValueError: If hex_color format is invalid
    """
    # Remove '#' if present
    hex_color = hex_color.lstrip("#")

    if len(hex_color) != 6:
        raise ValueError(f"Invalid HEX color format: {hex_color}. Expected 6 characters.")

    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
    except ValueError as e:
        raise ValueError(f"Invalid HEX color format: {hex_color}") from e

    return (r, g, b)


def rgb_to_lab(rgb: tuple[int, int, int] | np.ndarray) -> np.ndarray:
    """
    Convert RGB color to Lab color space.

    Args:
        rgb: Either tuple of (R, G, B) in [0, 255] or numpy array

    Returns:
        Lab color as numpy array [L, a, b]
    """
    if isinstance(rgb, tuple):
        rgb_array = np.array([[[rgb[0], rgb[1], rgb[2]]]], dtype=np.uint8)
    else:
        if rgb.dtype != np.uint8:
            raise ValueError("RGB array must be uint8")
        rgb_array = rgb.reshape(1, 1, 3) if rgb.ndim == 1 else rgb

    # Convert using scikit-image (expects shape [..., 3] with RGB in [0, 255])
    lab: np.ndarray = color.rgb2lab(rgb_array)

    # Return as 1D array if input was single color
    if isinstance(rgb, tuple) or (isinstance(rgb, np.ndarray) and rgb.ndim == 1):
        return lab[0, 0, :]

    return lab


def hex_to_lab(hex_color: str) -> np.ndarray:
    """
    Convert HEX color directly to Lab color space.

    Args:
        hex_color: Color in format "#RRGGBB" or "RRGGBB"

    Returns:
        Lab color as numpy array [L, a, b]
    """
    rgb = hex_to_rgb(hex_color)
    return rgb_to_lab(rgb)


def assign_labels_icm(
    mean_lab: np.ndarray,
    adjacency: list[tuple[int, int]],
    palette_lab: np.ndarray,
    smooth_lambda: float = 1.0,
    locked_spx: dict[int, int] | None = None,
    max_iters: int = 10,
    seed: int | None = None,
) -> LabelingResult:
    """
    Assign palette labels to superpixels using ICM (Iterated Conditional Modes).

    Minimizes energy: E = sum_i D(i, label_i) + lambda * sum_(i,j) [label_i != label_j]
    where D(i,c) is Euclidean distance in Lab space.

    Args:
        mean_lab: [spx_count, 3] mean Lab color per superpixel
        adjacency: List of (i, j) edges between superpixels
        palette_lab: [K, 3] palette colors in Lab space
        smooth_lambda: Weight for smoothness term (default 1.0)
        locked_spx: Dict mapping superpixel ID to locked palette index (0-based)
        max_iters: Maximum number of ICM iterations (default 10)
        seed: Random seed for deterministic initialization (currently unused, but kept for API)

    Returns:
        LabelingResult with label_per_spx and energy

    Raises:
        ValueError: If inputs have invalid shapes or values
    """
    if mean_lab.ndim != 2 or mean_lab.shape[1] != 3:
        raise ValueError(f"mean_lab must be [spx_count, 3], got {mean_lab.shape}")

    if palette_lab.ndim != 2 or palette_lab.shape[1] != 3:
        raise ValueError(f"palette_lab must be [K, 3], got {palette_lab.shape}")

    spx_count = mean_lab.shape[0]
    num_labels = palette_lab.shape[0]

    if num_labels < 2 or num_labels > 4:
        raise ValueError(f"Palette must have 2-4 colors, got {num_labels}")

    # Build adjacency list for efficient neighbor lookup
    neighbors: list[list[int]] = [[] for _ in range(spx_count)]
    for i, j in adjacency:
        if i < 0 or i >= spx_count or j < 0 or j >= spx_count:
            raise ValueError(f"Invalid adjacency edge: ({i}, {j}) for {spx_count} superpixels")
        neighbors[i].append(j)
        neighbors[j].append(i)

    # Compute data costs: [spx_count, num_labels]
    # D(i, c) = ||mean_lab[i] - palette_lab[c]||^2
    data_costs = np.zeros((spx_count, num_labels), dtype=np.float32)
    for i in range(spx_count):
        for c in range(num_labels):
            diff = mean_lab[i] - palette_lab[c]
            data_costs[i, c] = np.sum(diff * diff)

    # Initialize labels with argmin of data costs
    labels = np.argmin(data_costs, axis=1).astype(np.int32)

    # Apply locks
    locked_dict = locked_spx or {}
    for spx_id, locked_label in locked_dict.items():
        if spx_id < 0 or spx_id >= spx_count:
            raise ValueError(f"Locked superpixel ID {spx_id} out of range [0, {spx_count})")
        if locked_label < 0 or locked_label >= num_labels:
            raise ValueError(
                f"Locked label {locked_label} out of range [0, {num_labels}) "
                f"for superpixel {spx_id}"
            )
        labels[spx_id] = locked_label

    # ICM iterations
    for _ in range(max_iters):
        changed = False

        # Update each superpixel
        for i in range(spx_count):
            # Skip if locked
            if i in locked_dict:
                continue

            # Current label
            current_label = labels[i]

            # Find best label
            best_label = current_label
            best_energy = float("inf")

            for candidate_label in range(num_labels):
                # Data term
                energy = data_costs[i, candidate_label]

                # Smoothness term: count neighbors with different label
                for neighbor in neighbors[i]:
                    if labels[neighbor] != candidate_label:
                        energy += smooth_lambda

                if energy < best_energy:
                    best_energy = energy
                    best_label = candidate_label

            # Update if better
            if best_label != current_label:
                labels[i] = best_label
                changed = True

        # Stop if converged
        if not changed:
            break

    # Compute final energy
    total_energy = 0.0
    for i in range(spx_count):
        total_energy += data_costs[i, labels[i]]
    for i, j in adjacency:
        if labels[i] != labels[j]:
            total_energy += smooth_lambda

    # Create empty label map (will be filled by caller with spx_labels)
    label_map_pixels = np.full((1, 1), -1, dtype=np.int32)

    return LabelingResult(
        label_map_pixels=label_map_pixels,
        label_per_spx=labels,
        energy=total_energy,
    )


def create_pixel_label_map(
    spx_labels: np.ndarray,
    label_per_spx: np.ndarray,
    silhouette: np.ndarray,
) -> np.ndarray:
    """
    Create pixel-level label map from superpixel labels.

    Args:
        spx_labels: [H, W] superpixel ID per pixel (-1 outside silhouette)
        label_per_spx: [spx_count] palette index per superpixel
        silhouette: [H, W] binary mask (0/1)

    Returns:
        [H, W] array with palette index per pixel, -1 outside silhouette

    Raises:
        ValueError: If shapes don't match
    """
    if spx_labels.shape != silhouette.shape:
        raise ValueError(
            f"Shape mismatch: spx_labels {spx_labels.shape} vs silhouette {silhouette.shape}"
        )

    h, w = spx_labels.shape
    label_map = np.full((h, w), -1, dtype=np.int32)

    # For each pixel in silhouette, look up its superpixel's label
    mask = silhouette > 0
    spx_ids = spx_labels[mask]

    # Filter out -1 (outside silhouette in spx_labels)
    valid = spx_ids >= 0
    if np.any(valid):
        valid_spx_ids = spx_ids[valid]
        if np.max(valid_spx_ids) >= len(label_per_spx):
            raise ValueError(
                f"Superpixel ID {np.max(valid_spx_ids)} "
                f"exceeds label_per_spx length {len(label_per_spx)}"
            )

    # Assign labels
    for i in range(h):
        for j in range(w):
            if silhouette[i, j] > 0:
                spx_id = spx_labels[i, j]
                if spx_id >= 0:
                    label_map[i, j] = label_per_spx[spx_id]

    return label_map
