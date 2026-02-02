"""Stencil-optimized masking - favors recall over precision."""

import numpy as np
from PIL import Image
import cv2
from scipy.ndimage import binary_dilation, binary_erosion, binary_fill_holes
from skimage.filters import threshold_otsu


def stencil_optimized_masking(rgb: np.ndarray) -> np.ndarray:
    """
    Stencil-optimized subject detection.

    For stencils, we want to err on the side of including more rather than less.
    This version combines multiple strategies and uses OR logic to be more inclusive.
    """
    h, w = rgb.shape[:2]

    # Strategy 1: RGB color distance (more sensitive)
    border_width = max(5, min(h, w) // 40)

    # Sample borders
    top = rgb[0:border_width, :].reshape(-1, 3)
    bottom = rgb[-border_width:, :].reshape(-1, 3)
    left = rgb[:, 0:border_width].reshape(-1, 3)
    right = rgb[:, -border_width:].reshape(-1, 3)

    border_pixels = np.vstack([top, bottom, left, right])
    bg_color = np.median(border_pixels, axis=0)

    # Color distance
    color_diff = np.sqrt(np.sum((rgb.astype(float) - bg_color)**2, axis=2))

    # Use a MORE LENIENT threshold for stencils
    threshold_color = np.percentile(color_diff, 30)  # 30th percentile = keep 70% of pixels
    mask1 = color_diff > threshold_color

    # Strategy 2: Contrast-based detection
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    # Areas with high contrast are likely part of the subject
    # Compute local standard deviation
    blur = cv2.GaussianBlur(gray, (15, 15), 0)
    contrast = cv2.absdiff(gray, blur)

    threshold_contrast = np.percentile(contrast, 50)
    mask2 = contrast > threshold_contrast

    # Strategy 3: Grayscale intensity difference (original method)
    bg_intensity = np.median(border_pixels.mean(axis=1))
    intensity_diff = np.abs(gray.astype(float) - bg_intensity)
    threshold_intensity = max(10, np.std(intensity_diff) * 1.0)
    mask3 = intensity_diff > threshold_intensity

    # Combine masks with OR (inclusive)
    combined = mask1 | mask2 | mask3

    # Morphological operations
    # Light erosion to remove tiny noise
    combined = binary_erosion(combined, iterations=1)

    # Fill holes
    combined = binary_fill_holes(combined)

    # Aggressive dilation to ensure we capture full subject
    combined = binary_dilation(combined, iterations=5)

    # Final fill
    combined = binary_fill_holes(combined)

    alpha = (combined * 255).astype(np.uint8)
    return alpha


def conservative_grabcut(rgb: np.ndarray) -> np.ndarray:
    """
    GrabCut with a more conservative rectangle (larger margin) for better coverage.
    """
    h, w = rgb.shape[:2]

    mask = np.zeros((h, w), np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    # Larger rectangle to ensure we capture the full subject
    margin_h = int(h * 0.05)  # Only 5% margin
    margin_w = int(w * 0.05)
    rect = (margin_w, margin_h, w - 2*margin_w, h - 2*margin_h)

    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    # Run GrabCut with more iterations for better results
    cv2.grabCut(bgr, mask, rect, bgd_model, fgd_model, 8, cv2.GC_INIT_WITH_RECT)

    # Include both definite and probable foreground
    foreground_mask = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)

    # Post-process: dilate to ensure full coverage
    kernel = np.ones((5, 5), np.uint8)
    foreground_mask = cv2.dilate(foreground_mask, kernel, iterations=2)

    return foreground_mask


if __name__ == "__main__":
    img = Image.open("test_images/test_portrait.jpg")
    rgb = np.array(img)

    print("Testing stencil-optimized masking methods...")
    print(f"Image size: {rgb.shape}")
    print(f"Total pixels: {rgb.shape[0] * rgb.shape[1]:,}")

    # Test stencil-optimized method
    print("\n1. Stencil-optimized (high recall)...")
    alpha_stencil = stencil_optimized_masking(rgb)
    pixels = np.sum(alpha_stencil > 0)
    print(f"   Detected {pixels:,} foreground pixels ({pixels / alpha_stencil.size * 100:.1f}%)")

    img_rgba = np.dstack([rgb, alpha_stencil])
    result = Image.fromarray(img_rgba, 'RGBA')
    result.save("test_images/test_portrait_stencil_optimized.png")
    print("   Saved to: test_images/test_portrait_stencil_optimized.png")

    # Test conservative GrabCut
    print("\n2. Conservative GrabCut...")
    alpha_gc = conservative_grabcut(rgb)
    pixels_gc = np.sum(alpha_gc > 0)
    print(f"   Detected {pixels_gc:,} foreground pixels ({pixels_gc / alpha_gc.size * 100:.1f}%)")

    img_rgba_gc = np.dstack([rgb, alpha_gc])
    result_gc = Image.fromarray(img_rgba_gc, 'RGBA')
    result_gc.save("test_images/test_portrait_grabcut_v2.png")
    print("   Saved to: test_images/test_portrait_grabcut_v2.png")

    print("\n=== Comparison ===")
    print(f"  Reference (manual):     269,245 pixels (58.9%)")
    print(f"  Current method:          81,717 pixels (17.9%)")
    print(f"  Improved (precision):    44,258 pixels ( 9.7%)")
    print(f"  Stencil-optimized:      {pixels:7,} pixels ({pixels/456800*100:5.1f}%)")
    print(f"  GrabCut v2:             {pixels_gc:7,} pixels ({pixels_gc/456800*100:5.1f}%)")
