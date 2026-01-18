"""Lock mask loading and superpixel mapping."""

from pathlib import Path

import numpy as np
from PIL import Image


def load_lock_mask(mask_path: Path, target_shape: tuple[int, int]) -> np.ndarray:
    """
    Load a lock mask image and resize to target shape.

    Args:
        mask_path: Path to mask image (any format PIL supports)
        target_shape: (height, width) to resize to

    Returns:
        Binary mask [H, W] with values 0 or 1

    Raises:
        ValueError: If mask file doesn't exist or is invalid
        FileNotFoundError: If mask file doesn't exist
    """
    if not mask_path.exists():
        raise FileNotFoundError(f"Lock mask not found: {mask_path}")

    try:
        img = Image.open(mask_path)
    except Exception as e:
        raise ValueError(f"Failed to load lock mask {mask_path}: {e}") from e

    # Convert to grayscale
    img = img.convert("L")  # type: ignore[assignment]

    # Resize to target shape
    h, w = target_shape
    if img.size != (w, h):
        img = img.resize((w, h), Image.Resampling.LANCZOS)  # type: ignore[assignment]

    # Convert to numpy and threshold
    mask_array = np.array(img, dtype=np.uint8)

    # Threshold at 128 to get binary mask
    binary_mask = (mask_array > 128).astype(np.uint8)

    return binary_mask


def map_locks_to_superpixels(
    lock_masks: dict[int, np.ndarray],
    spx_labels: np.ndarray,
    silhouette: np.ndarray,
    overlap_threshold: float = 0.5,
) -> dict[int, int]:
    """
    Map lock masks to superpixels.

    A superpixel is locked to a palette color if >= overlap_threshold of its pixels
    are covered by that color's lock mask.

    Args:
        lock_masks: Dict mapping palette_index -> binary mask [H, W]
        spx_labels: [H, W] superpixel ID per pixel (-1 outside silhouette)
        silhouette: [H, W] binary mask (0/1)
        overlap_threshold: Minimum fraction of superpixel that must overlap (default 0.5)

    Returns:
        Dict mapping superpixel_id -> locked_palette_index

    Raises:
        ValueError: If conflicting locks detected or shapes mismatch
    """
    if spx_labels.shape != silhouette.shape:
        raise ValueError(
            f"Shape mismatch: spx_labels {spx_labels.shape} vs silhouette {silhouette.shape}"
        )

    for palette_idx, mask in lock_masks.items():
        if mask.shape != silhouette.shape:
            raise ValueError(
                f"Lock mask for palette {palette_idx} shape {mask.shape} "
                f"doesn't match silhouette {silhouette.shape}"
            )

    # Find all superpixel IDs
    unique_spx = np.unique(spx_labels)
    unique_spx = unique_spx[unique_spx >= 0]  # Remove -1

    locked_spx: dict[int, int] = {}

    for spx_id in unique_spx:
        spx_mask = (spx_labels == spx_id) & (silhouette > 0)
        spx_pixel_count = np.sum(spx_mask)

        if spx_pixel_count == 0:
            continue

        # Check each palette color's lock mask
        best_palette_idx = None
        best_overlap = 0.0

        for palette_idx, lock_mask in lock_masks.items():
            # Count overlap
            overlap_mask = spx_mask & (lock_mask > 0)
            overlap_count = np.sum(overlap_mask)
            overlap_fraction = overlap_count / spx_pixel_count

            if overlap_fraction >= overlap_threshold:
                if best_palette_idx is not None:
                    # Conflict detected
                    raise ValueError(
                        f"Conflicting locks for superpixel {spx_id}: "
                        f"palette {best_palette_idx} ({best_overlap:.2%}) and "
                        f"palette {palette_idx} ({overlap_fraction:.2%}). "
                        f"Each superpixel can only be locked to one color."
                    )
                best_palette_idx = palette_idx
                best_overlap = overlap_fraction

        if best_palette_idx is not None:
            locked_spx[spx_id] = best_palette_idx

    return locked_spx


def parse_lock_spec(lock_spec: str) -> tuple[str, Path]:
    """
    Parse a lock specification string.

    Args:
        lock_spec: String in format "COLOR=PATH" (e.g., "#FFD200=mask.png")

    Returns:
        Tuple of (color_hex, mask_path)

    Raises:
        ValueError: If format is invalid
    """
    if "=" not in lock_spec:
        raise ValueError(
            f"Invalid lock specification: '{lock_spec}'. Expected format: "
            "'COLOR=PATH' (e.g., '#FFD200=mask.png')"
        )

    parts = lock_spec.split("=", 1)
    if len(parts) != 2:
        raise ValueError(
            f"Invalid lock specification: '{lock_spec}'. Expected format: "
            "'COLOR=PATH' (e.g., '#FFD200=mask.png')"
        )

    color_hex = parts[0].strip()
    mask_path = Path(parts[1].strip())

    # Basic validation of hex color
    if not color_hex.startswith("#"):
        color_hex = "#" + color_hex

    if len(color_hex) != 7:
        raise ValueError(f"Invalid color in lock spec: '{color_hex}'. Expected format: '#RRGGBB'")

    return (color_hex, mask_path)
