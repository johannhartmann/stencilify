"""Test improved masking strategies."""

import numpy as np
from PIL import Image
import cv2
from scipy.ndimage import binary_dilation, binary_erosion, binary_fill_holes
from skimage.filters import threshold_otsu


def improved_auto_detect_subject(rgb: np.ndarray) -> np.ndarray:
    """
    Improved automatic subject detection using multiple strategies.

    Improvements:
    1. Uses full RGB color information instead of grayscale
    2. Samples entire border instead of just corners
    3. Uses Otsu's method for automatic thresholding
    4. Combines edge detection for refinement
    5. More robust morphological operations
    """
    h, w = rgb.shape[:2]

    # Strategy 1: Border-based background estimation (using RGB color)
    border_width = max(5, min(h, w) // 40)

    # Sample all borders
    top = rgb[0:border_width, :].reshape(-1, 3)
    bottom = rgb[-border_width:, :].reshape(-1, 3)
    left = rgb[:, 0:border_width].reshape(-1, 3)
    right = rgb[:, -border_width:].reshape(-1, 3)

    border_pixels = np.vstack([top, bottom, left, right])

    # Estimate background color (RGB)
    bg_color = np.median(border_pixels, axis=0)

    # Compute color distance for each pixel
    color_diff = np.sqrt(np.sum((rgb.astype(float) - bg_color)**2, axis=2))

    # Strategy 2: Otsu's automatic threshold
    try:
        threshold = threshold_otsu(color_diff)
    except:
        # Fallback if Otsu fails
        threshold = np.mean(color_diff) + np.std(color_diff)

    # Initial foreground mask
    foreground = color_diff > threshold

    # Strategy 3: Edge-based refinement
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    # Dilate edges to create boundary zones
    edge_zones = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=2)

    # Use edges to refine: if a pixel is near an edge and different from background,
    # it's likely part of the subject
    near_edges = edge_zones > 0
    edge_enhanced = foreground | (near_edges & (color_diff > threshold * 0.5))

    # Strategy 4: Morphological cleanup
    # Remove small noise
    cleaned = binary_erosion(edge_enhanced, iterations=2)

    # Fill holes
    cleaned = binary_fill_holes(cleaned)

    # Dilate to recover edges and smooth boundaries
    cleaned = binary_dilation(cleaned, iterations=4)

    # Final fill holes again
    cleaned = binary_fill_holes(cleaned)

    # Convert to uint8 alpha
    alpha = (cleaned * 255).astype(np.uint8)

    return alpha


def grabcut_segmentation(rgb: np.ndarray) -> np.ndarray:
    """
    Use OpenCV's GrabCut algorithm for segmentation.

    GrabCut is an iterative segmentation algorithm that works well
    for separating foreground objects from backgrounds.
    """
    h, w = rgb.shape[:2]

    # Create a mask initialized to probable background
    mask = np.zeros((h, w), np.uint8)

    # Temporary arrays for GrabCut
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    # Define a rectangle around the probable foreground
    # Assume subject is in center 80% of image
    margin_h = int(h * 0.1)
    margin_w = int(w * 0.1)
    rect = (margin_w, margin_h, w - 2*margin_w, h - 2*margin_h)

    # Convert RGB to BGR for OpenCV
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    # Run GrabCut
    cv2.grabCut(bgr, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)

    # Create binary mask (0 and 2 are background, 1 and 3 are foreground)
    foreground_mask = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)

    return foreground_mask


# Test both methods
if __name__ == "__main__":
    # Load test image
    img = Image.open("test_images/test_portrait.jpg")
    rgb = np.array(img)

    print("Testing improved masking methods...")
    print(f"Image size: {rgb.shape}")

    # Test improved method
    print("\n1. Testing improved color-based detection...")
    alpha_improved = improved_auto_detect_subject(rgb)
    foreground_pixels = np.sum(alpha_improved > 0)
    print(f"   Detected {foreground_pixels:,} foreground pixels ({foreground_pixels / alpha_improved.size * 100:.1f}%)")

    # Save result
    img_rgba = np.dstack([rgb, alpha_improved])
    result_img = Image.fromarray(img_rgba, 'RGBA')
    result_img.save("test_images/test_portrait_improved_mask.png")
    print("   Saved to: test_images/test_portrait_improved_mask.png")

    # Test GrabCut
    print("\n2. Testing GrabCut segmentation...")
    alpha_grabcut = grabcut_segmentation(rgb)
    foreground_pixels_gc = np.sum(alpha_grabcut > 0)
    print(f"   Detected {foreground_pixels_gc:,} foreground pixels ({foreground_pixels_gc / alpha_grabcut.size * 100:.1f}%)")

    # Save result
    img_rgba_gc = np.dstack([rgb, alpha_grabcut])
    result_img_gc = Image.fromarray(img_rgba_gc, 'RGBA')
    result_img_gc.save("test_images/test_portrait_grabcut_mask.png")
    print("   Saved to: test_images/test_portrait_grabcut_mask.png")

    print("\nComparison:")
    print(f"  Manual mask:     269,245 pixels (reference)")
    print(f"  Current method:   81,717 pixels (17.9%)")
    print(f"  Improved method: {foreground_pixels:7,} pixels ({foreground_pixels/456800*100:.1f}%)")
    print(f"  GrabCut:         {foreground_pixels_gc:7,} pixels ({foreground_pixels_gc/456800*100:.1f}%)")
