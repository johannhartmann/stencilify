"""Image I/O and scaling utilities."""

from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from stencilify.config import PipelineConfig
from stencilify.geometry import get_page_dimensions


def auto_detect_subject(rgb: np.ndarray) -> np.ndarray:
    """
    Automatically detect the subject in an RGB image and create an alpha mask.

    Uses a combination of strategies:
    1. Corner-based background detection
    2. Threshold-based segmentation (for uniform backgrounds)
    3. Morphological operations to clean up the mask

    Args:
        rgb: RGB image array of shape (H, W, 3), uint8

    Returns:
        Alpha mask of shape (H, W), uint8 (0=transparent, 255=opaque)
    """
    from scipy.ndimage import binary_dilation, binary_erosion, binary_fill_holes

    h, w = rgb.shape[:2]

    # Convert to grayscale for analysis
    gray = np.mean(rgb, axis=2).astype(np.uint8)

    # Strategy 1: Corner-based background detection
    # Sample corners to detect background color
    corner_size = max(10, min(h, w) // 20)  # At least 10px, or 5% of image
    corners = [
        gray[0:corner_size, 0:corner_size],  # Top-left
        gray[0:corner_size, -corner_size:],  # Top-right
        gray[-corner_size:, 0:corner_size],  # Bottom-left
        gray[-corner_size:, -corner_size:],  # Bottom-right
    ]

    # Estimate background intensity from corners
    corner_values = np.concatenate([c.flatten() for c in corners])
    bg_intensity = np.median(corner_values)
    bg_std = np.std(corner_values)

    # Create initial mask based on similarity to background
    # Pixels similar to background are marked as background (0)
    intensity_diff = np.abs(gray.astype(float) - bg_intensity)

    # More lenient threshold to capture more of the subject
    threshold = max(15, bg_std * 1.5)  # Lower threshold

    # Initial foreground mask (True = foreground/subject)
    foreground = intensity_diff > threshold

    # Strategy 2: Morphological cleanup
    # Remove small noise in background
    foreground = binary_erosion(foreground, iterations=1)

    # Fill holes in foreground (important for capturing full subject)
    foreground = binary_fill_holes(foreground)

    # Dilate to recover edges and ensure full coverage
    foreground = binary_dilation(foreground, iterations=3)

    # Convert to uint8 alpha channel
    alpha = (foreground * 255).astype(np.uint8)

    return alpha


def load_rgba(image_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """
    Load an RGBA image from disk, or convert RGB to RGBA with automatic subject detection.

    For images without an alpha channel (RGB, L, etc.), this function automatically
    detects the subject and creates a silhouette mask by analyzing the background.

    Args:
        image_path: Path to the input image

    Returns:
        Tuple of (rgb, alpha) where:
        - rgb: uint8 array of shape (H, W, 3)
        - alpha: uint8 array of shape (H, W)

    Raises:
        FileNotFoundError: If the image file does not exist
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Load image with Pillow
    img = Image.open(image_path)

    # Convert to RGBA if not already
    if img.mode == "RGBA":
        # Already has alpha channel
        img_array = np.array(img, dtype=np.uint8)
        rgb = img_array[:, :, :3]
        alpha = img_array[:, :, 3]
    elif "transparency" in img.info:
        # Has transparency info, convert to RGBA
        img = img.convert("RGBA")  # type: ignore[assignment]
        img_array = np.array(img, dtype=np.uint8)
        rgb = img_array[:, :, :3]
        alpha = img_array[:, :, 3]
    else:
        # No alpha channel - automatically detect subject
        # First convert to RGB if needed (handles grayscale, etc.)
        img_rgb = img.convert("RGB")  # type: ignore[assignment]
        rgb = np.array(img_rgb, dtype=np.uint8)

        # Automatically detect subject and create alpha mask
        alpha = auto_detect_subject(rgb)

    return rgb, alpha


def resize_to_working(
    rgb: np.ndarray,
    alpha: np.ndarray,
    config: PipelineConfig,
) -> tuple[np.ndarray, np.ndarray, float]:
    """
    Resize image to working resolution based on page size and min_feature_mm.

    Computes a working resolution that balances detail preservation with performance:
    - work_long_edge_px = clamp(2000, 6000, int(long_edge_mm * (4 / min_feature_mm)))
    - Preserves aspect ratio without cropping
    - Computes px_per_mm based on final working size and page dimensions

    Args:
        rgb: Input RGB image (H, W, 3), uint8
        alpha: Input alpha channel (H, W), uint8
        config: Pipeline configuration with page and cuttability settings

    Returns:
        Tuple of (rgb_resized, alpha_resized, px_per_mm) where:
        - rgb_resized: Resized RGB image (H', W', 3), uint8
        - alpha_resized: Resized alpha channel (H', W'), uint8
        - px_per_mm: Pixels per millimeter in the working resolution

    Raises:
        ValueError: If input dimensions are invalid
    """
    if rgb.shape[0] == 0 or rgb.shape[1] == 0:
        raise ValueError(f"Invalid input dimensions: {rgb.shape}")

    if rgb.shape[:2] != alpha.shape:
        raise ValueError(f"RGB and alpha shape mismatch: {rgb.shape[:2]} vs {alpha.shape}")

    # Get page dimensions (with margins applied)
    page_dims = get_page_dimensions(
        config.page.size,
        config.page.orientation,
        config.page.margin_mm,
    )

    # Determine the long edge of the page
    page_long_edge_mm = max(page_dims.width_mm, page_dims.height_mm)

    # Compute working resolution based on min_feature_mm
    # Formula: work_long_edge_px = long_edge_mm * (4 / min_feature_mm)
    min_feature_mm = config.cuttability.min_feature_mm
    target_long_edge_px = int(page_long_edge_mm * (4.0 / min_feature_mm))

    # Clamp to reasonable range
    work_long_edge_px = max(2000, min(6000, target_long_edge_px))

    # Get input dimensions
    input_h, input_w = rgb.shape[:2]
    input_long_edge = max(input_h, input_w)
    input_short_edge = min(input_h, input_w)

    # Compute target dimensions preserving aspect ratio
    aspect_ratio = input_short_edge / input_long_edge

    if input_w >= input_h:
        # Width is the long edge
        target_w = work_long_edge_px
        target_h = int(target_w * aspect_ratio)
    else:
        # Height is the long edge
        target_h = work_long_edge_px
        target_w = int(target_h * aspect_ratio)

    # Resize using Pillow (high-quality Lanczos resampling)
    rgb_pil = Image.fromarray(rgb, mode="RGB")
    alpha_pil = Image.fromarray(alpha, mode="L")

    rgb_resized_pil = rgb_pil.resize(
        (target_w, target_h),
        resample=Image.Resampling.LANCZOS,
    )
    alpha_resized_pil = alpha_pil.resize(
        (target_w, target_h),
        resample=Image.Resampling.LANCZOS,
    )

    # Convert back to numpy
    rgb_resized = np.array(rgb_resized_pil, dtype=np.uint8)
    alpha_resized = np.array(alpha_resized_pil, dtype=np.uint8)

    # Compute px_per_mm based on the final working size
    # The working image will be scaled to fit within the page dimensions
    resized_long_edge = max(target_h, target_w)
    px_per_mm = resized_long_edge / page_long_edge_mm

    return rgb_resized, alpha_resized, px_per_mm
