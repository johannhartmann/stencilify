"""Tests for mask generation and morphology operations."""

import numpy as np
import pytest

from stencilify.masks import morph_smooth, silhouette_from_alpha


def test_silhouette_from_alpha_basic() -> None:
    """Test basic silhouette extraction."""
    # Create alpha channel with clear foreground/background
    alpha = np.zeros((10, 10), dtype=np.uint8)
    alpha[3:7, 3:7] = 255  # Opaque square in center

    mask = silhouette_from_alpha(alpha, threshold=20)

    assert mask.shape == (10, 10)
    assert mask.dtype == np.uint8
    assert np.all((mask == 0) | (mask == 1))

    # Check that center is foreground (1) and edges are background (0)
    assert np.all(mask[3:7, 3:7] == 1)
    assert np.all(mask[0:3, :] == 0)
    assert np.all(mask[7:, :] == 0)


def test_silhouette_from_alpha_threshold() -> None:
    """Test that threshold works correctly."""
    # Create alpha with gradient
    alpha = np.arange(0, 256, dtype=np.uint8).reshape(16, 16)

    # Test with different thresholds
    mask_low = silhouette_from_alpha(alpha, threshold=50)
    mask_high = silhouette_from_alpha(alpha, threshold=200)

    # Low threshold should have more foreground pixels
    assert np.sum(mask_low) > np.sum(mask_high)

    # Check specific values
    assert mask_low[0, 0] == 0  # alpha=0, below threshold
    assert mask_low[-1, -1] == 1  # alpha=255, above threshold
    assert mask_high[-1, -1] == 1  # alpha=255, above threshold


def test_silhouette_from_alpha_default_threshold() -> None:
    """Test default threshold of 20."""
    alpha = np.full((10, 10), 25, dtype=np.uint8)
    mask = silhouette_from_alpha(alpha)  # Default threshold=20

    # All pixels should be foreground (25 > 20)
    assert np.all(mask == 1)

    alpha_low = np.full((10, 10), 15, dtype=np.uint8)
    mask_low = silhouette_from_alpha(alpha_low)

    # All pixels should be background (15 <= 20)
    assert np.all(mask_low == 0)


def test_silhouette_from_alpha_invalid_dtype() -> None:
    """Test that non-uint8 alpha raises ValueError."""
    alpha = np.zeros((10, 10), dtype=np.float32)

    with pytest.raises(ValueError, match="must be uint8"):
        silhouette_from_alpha(alpha)


def test_silhouette_from_alpha_invalid_shape() -> None:
    """Test that non-2D alpha raises ValueError."""
    alpha = np.zeros((10, 10, 3), dtype=np.uint8)

    with pytest.raises(ValueError, match="must be 2D"):
        silhouette_from_alpha(alpha)


def test_silhouette_from_alpha_invalid_threshold() -> None:
    """Test that invalid threshold raises ValueError."""
    alpha = np.zeros((10, 10), dtype=np.uint8)

    with pytest.raises(ValueError, match="Threshold must be in"):
        silhouette_from_alpha(alpha, threshold=-1)

    with pytest.raises(ValueError, match="Threshold must be in"):
        silhouette_from_alpha(alpha, threshold=256)


def test_morph_smooth_no_op() -> None:
    """Test that zero kernel sizes don't change the mask."""
    mask = np.array(
        [
            [0, 0, 0, 0, 0],
            [0, 1, 1, 1, 0],
            [0, 1, 1, 1, 0],
            [0, 1, 1, 1, 0],
            [0, 0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )

    smoothed = morph_smooth(mask, close_px=0, open_px=0)

    assert np.array_equal(smoothed, mask)


def test_morph_smooth_closing_fills_holes() -> None:
    """Test that closing fills small holes."""
    # Create mask with a small hole
    mask = np.ones((10, 10), dtype=np.uint8)
    mask[5, 5] = 0  # Single pixel hole

    smoothed = morph_smooth(mask, close_px=2, open_px=0)

    # Hole should be filled
    assert smoothed[5, 5] == 1


def test_morph_smooth_opening_removes_noise() -> None:
    """Test that opening removes small protrusions."""
    # Create mask with noise and larger square
    mask = np.zeros((20, 20), dtype=np.uint8)
    mask[5:15, 5:15] = 1  # Larger solid square (10x10)
    mask[0, 0] = 1  # Single pixel noise

    smoothed = morph_smooth(mask, close_px=0, open_px=2)

    # Noise should be removed
    assert smoothed[0, 0] == 0
    # Main square should remain (center should still be solid)
    assert np.sum(smoothed[8:12, 8:12]) > 0


def test_morph_smooth_close_then_open() -> None:
    """Test that closing is applied before opening."""
    # Create mask with both hole and noise
    mask = np.zeros((20, 20), dtype=np.uint8)
    mask[5:15, 5:15] = 1  # Solid square
    mask[10, 10] = 0  # Hole in the middle
    mask[1, 1] = 1  # Noise outside

    smoothed = morph_smooth(mask, close_px=2, open_px=2)

    # Hole should be filled (by closing)
    assert smoothed[10, 10] == 1
    # Noise should be removed (by opening)
    assert smoothed[1, 1] == 0


def test_morph_smooth_preserves_binary() -> None:
    """Test that smoothing preserves binary nature (0/1 values)."""
    mask = np.random.randint(0, 2, size=(50, 50), dtype=np.uint8)

    smoothed = morph_smooth(mask, close_px=3, open_px=3)

    assert smoothed.dtype == np.uint8
    assert np.all((smoothed == 0) | (smoothed == 1))


def test_morph_smooth_invalid_dtype() -> None:
    """Test that non-uint8 mask raises ValueError."""
    mask = np.zeros((10, 10), dtype=np.float32)

    with pytest.raises(ValueError, match="must be uint8"):
        morph_smooth(mask, close_px=2, open_px=2)


def test_morph_smooth_invalid_shape() -> None:
    """Test that non-2D mask raises ValueError."""
    mask = np.zeros((10, 10, 3), dtype=np.uint8)

    with pytest.raises(ValueError, match="must be 2D"):
        morph_smooth(mask, close_px=2, open_px=2)


def test_morph_smooth_non_binary_values() -> None:
    """Test that non-binary mask values raise ValueError."""
    mask = np.full((10, 10), 2, dtype=np.uint8)

    with pytest.raises(ValueError, match="must contain only 0 or 1"):
        morph_smooth(mask, close_px=2, open_px=2)


def test_morph_smooth_negative_kernel() -> None:
    """Test that negative kernel sizes raise ValueError."""
    mask = np.zeros((10, 10), dtype=np.uint8)

    with pytest.raises(ValueError, match="must be non-negative"):
        morph_smooth(mask, close_px=-1, open_px=2)

    with pytest.raises(ValueError, match="must be non-negative"):
        morph_smooth(mask, close_px=2, open_px=-1)


def test_morph_smooth_large_kernels() -> None:
    """Test that large kernel sizes work correctly."""
    # Create a mask with a solid square
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[25:75, 25:75] = 1

    # Apply aggressive smoothing
    smoothed = morph_smooth(mask, close_px=10, open_px=10)

    assert smoothed.dtype == np.uint8
    assert np.all((smoothed == 0) | (smoothed == 1))
    # Should still have a foreground region
    assert np.sum(smoothed) > 0


def test_silhouette_and_morph_integration() -> None:
    """Test integration of silhouette extraction and morphing."""
    # Create alpha channel with noise
    alpha = np.zeros((50, 50), dtype=np.uint8)
    alpha[10:40, 10:40] = 255  # Main object
    alpha[20, 20] = 0  # Small hole
    alpha[5, 5] = 200  # Noise pixel

    # Extract silhouette
    mask = silhouette_from_alpha(alpha, threshold=20)

    # Apply smoothing
    smoothed = morph_smooth(mask, close_px=3, open_px=3)

    # Check that hole is filled and noise is removed
    assert smoothed[20, 20] == 1  # Hole filled
    assert smoothed[5, 5] == 0  # Noise removed
    assert np.sum(smoothed) > 0  # Still has foreground


def test_create_circular_kernel() -> None:
    """Test circular kernel creation."""
    from stencilify.masks import _create_circular_kernel

    # Test small kernel
    kernel = _create_circular_kernel(1)
    assert kernel.shape == (3, 3)
    assert kernel.dtype == bool

    # Center should be True
    assert kernel[1, 1]

    # Test larger kernel
    kernel_5 = _create_circular_kernel(5)
    assert kernel_5.shape == (11, 11)

    # Should be roughly circular
    # Count True values and compare to expected area
    area = np.sum(kernel_5)
    expected_area = np.pi * 5**2
    assert abs(area - expected_area) < 10  # Within 10 pixels
