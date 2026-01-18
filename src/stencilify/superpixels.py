"""Superpixel generation and adjacency graph computation."""

from dataclasses import dataclass

import numpy as np
from skimage import color, segmentation


@dataclass
class SuperpixelResult:
    """Result of superpixel computation."""

    labels: np.ndarray  # int32 [H, W], superpixel ID per pixel
    count: int  # Number of superpixels
    adjacency: list[tuple[int, int]]  # Undirected edges (unique)
    mean_lab: np.ndarray  # float [count, 3], mean Lab color per superpixel


def compute_superpixels(
    rgb: np.ndarray,
    silhouette: np.ndarray,
    n_segments: int = 100,
    compactness: float = 10.0,
    sigma: float = 1.0,
) -> SuperpixelResult:
    """
    Compute SLIC superpixels within the silhouette mask.

    Args:
        rgb: RGB image (H, W, 3), uint8
        silhouette: Binary silhouette mask (H, W), uint8 with values 0 or 1
        n_segments: Approximate number of superpixels to generate
        compactness: Balances color proximity and space proximity.
                     Higher values give more weight to space proximity.
        sigma: Width of Gaussian smoothing kernel for pre-processing.
               Zero disables smoothing.

    Returns:
        SuperpixelResult with labels, count, adjacency, and mean Lab colors

    Raises:
        ValueError: If inputs are invalid
    """
    if rgb.dtype != np.uint8:
        raise ValueError(f"RGB must be uint8, got {rgb.dtype}")

    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError(f"RGB must be (H, W, 3), got {rgb.shape}")

    if silhouette.dtype != np.uint8:
        raise ValueError(f"Silhouette must be uint8, got {silhouette.dtype}")

    if silhouette.ndim != 2:
        raise ValueError(f"Silhouette must be 2D, got shape {silhouette.shape}")

    if rgb.shape[:2] != silhouette.shape:
        raise ValueError(
            f"RGB and silhouette shape mismatch: {rgb.shape[:2]} vs {silhouette.shape}"
        )

    if not np.all((silhouette == 0) | (silhouette == 1)):
        raise ValueError("Silhouette must contain only 0 or 1 values")

    # Convert RGB to Lab for more perceptually uniform segmentation
    # Note: skimage expects float RGB in [0, 1]
    rgb_float = rgb.astype(np.float32) / 255.0
    lab = color.rgb2lab(rgb_float)

    # Create a mask for SLIC (True for valid pixels)
    mask = silhouette.astype(bool)

    # Run SLIC superpixel segmentation
    # slic returns 0-indexed labels
    labels = segmentation.slic(
        lab,
        n_segments=n_segments,
        compactness=compactness,
        sigma=sigma,
        mask=mask,
        start_label=0,
        channel_axis=2,
    )

    # Convert to int32 for consistency
    labels = labels.astype(np.int32)

    # Count unique superpixel IDs (excluding -1 which might be background)
    unique_labels = np.unique(labels[mask])
    spx_count = len(unique_labels)

    # Relabel to ensure contiguous IDs from 0 to spx_count-1
    # This is important for indexing into mean_lab array
    relabel_map = {old_id: new_id for new_id, old_id in enumerate(unique_labels)}
    relabeled = np.full_like(labels, -1)
    for old_id, new_id in relabel_map.items():
        relabeled[labels == old_id] = new_id

    # Build adjacency graph
    adjacency = build_adjacency(relabeled, spx_count, silhouette)

    # Compute mean Lab colors
    mean_lab = compute_mean_lab(rgb, relabeled, spx_count)

    return SuperpixelResult(
        labels=relabeled,
        count=spx_count,
        adjacency=adjacency,
        mean_lab=mean_lab,
    )


def build_adjacency(
    spx_labels: np.ndarray,
    spx_count: int,
    silhouette: np.ndarray,
) -> list[tuple[int, int]]:
    """
    Build adjacency graph between superpixels.

    Checks 4-connectivity (up, down, left, right) to find adjacent superpixels.

    Args:
        spx_labels: Superpixel labels (H, W), int32, values in [0, spx_count-1] or -1
        spx_count: Number of superpixels
        silhouette: Binary silhouette mask (H, W), uint8 with values 0 or 1

    Returns:
        List of undirected edges (i, j) where i < j

    Raises:
        ValueError: If inputs are invalid
    """
    if spx_labels.ndim != 2:
        raise ValueError(f"spx_labels must be 2D, got shape {spx_labels.shape}")

    if silhouette.shape != spx_labels.shape:
        raise ValueError(
            f"Shape mismatch: spx_labels {spx_labels.shape} vs silhouette {silhouette.shape}"
        )

    h, w = spx_labels.shape

    # Use a set to collect unique edges
    edges_set: set[tuple[int, int]] = set()

    # Check horizontal adjacency (left-right)
    for y in range(h):
        for x in range(w - 1):
            if silhouette[y, x] == 1 and silhouette[y, x + 1] == 1:
                left_id = spx_labels[y, x]
                right_id = spx_labels[y, x + 1]
                if left_id >= 0 and right_id >= 0 and left_id != right_id:
                    edge = (min(left_id, right_id), max(left_id, right_id))
                    edges_set.add(edge)

    # Check vertical adjacency (up-down)
    for y in range(h - 1):
        for x in range(w):
            if silhouette[y, x] == 1 and silhouette[y + 1, x] == 1:
                top_id = spx_labels[y, x]
                bottom_id = spx_labels[y + 1, x]
                if top_id >= 0 and bottom_id >= 0 and top_id != bottom_id:
                    edge = (min(top_id, bottom_id), max(top_id, bottom_id))
                    edges_set.add(edge)

    return sorted(edges_set)


def compute_mean_lab(
    rgb: np.ndarray,
    spx_labels: np.ndarray,
    spx_count: int,
) -> np.ndarray:
    """
    Compute mean Lab color for each superpixel.

    Args:
        rgb: RGB image (H, W, 3), uint8
        spx_labels: Superpixel labels (H, W), int32, values in [0, spx_count-1] or -1
        spx_count: Number of superpixels

    Returns:
        Mean Lab colors (spx_count, 3), float64

    Raises:
        ValueError: If inputs are invalid
    """
    if rgb.dtype != np.uint8:
        raise ValueError(f"RGB must be uint8, got {rgb.dtype}")

    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError(f"RGB must be (H, W, 3), got {rgb.shape}")

    if spx_labels.ndim != 2:
        raise ValueError(f"spx_labels must be 2D, got shape {spx_labels.shape}")

    if rgb.shape[:2] != spx_labels.shape:
        raise ValueError(
            f"RGB and spx_labels shape mismatch: {rgb.shape[:2]} vs {spx_labels.shape}"
        )

    # Convert RGB to Lab
    rgb_float = rgb.astype(np.float32) / 255.0
    lab = color.rgb2lab(rgb_float)

    # Compute mean Lab for each superpixel
    mean_lab = np.zeros((spx_count, 3), dtype=np.float64)

    for spx_id in range(spx_count):
        mask = spx_labels == spx_id
        if np.any(mask):
            mean_lab[spx_id] = lab[mask].mean(axis=0)

    return mean_lab
