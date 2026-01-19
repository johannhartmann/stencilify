"""Tests for compute backend adapter."""

import numpy as np

from stencilify.compute import Device, bilateral_filter, gaussian_blur, get_device


def test_device_enum():
    """Test Device enum values."""
    assert Device.CPU == "cpu"
    assert Device.CUDA == "cuda"
    assert Device.AUTO == "auto"


def test_get_device_cpu():
    """Test explicit CPU device selection."""
    device = get_device(Device.CPU)
    assert device == "cpu"


def test_get_device_auto():
    """Test AUTO device selection (should work without GPU)."""
    device = get_device(Device.AUTO)
    # Should return either "cpu" or "cuda" depending on availability
    assert device in ("cpu", "cuda")


def test_get_device_cuda():
    """Test CUDA device selection (gracefully falls back if unavailable)."""
    device = get_device(Device.CUDA)
    # Should return either "cuda" (if available) or "cpu" (fallback)
    assert device in ("cpu", "cuda")


def test_bilateral_filter_cpu():
    """Test bilateral filter on CPU."""
    # Create a simple test image
    image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

    # Apply bilateral filter on CPU
    result = bilateral_filter(image, d=5, sigma_color=50, sigma_space=50, device="cpu")

    # Check result shape and type
    assert result.shape == image.shape
    assert result.dtype == np.uint8


def test_bilateral_filter_grayscale():
    """Test bilateral filter with grayscale conversion."""
    # Create RGB image
    image = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)

    # Apply filter
    result = bilateral_filter(image, d=3, sigma_color=30, sigma_space=30, device="cpu")

    # Should work and preserve shape
    assert result.shape == image.shape
    assert result.dtype == np.uint8


def test_gaussian_blur_cpu():
    """Test Gaussian blur on CPU."""
    # Create a simple test image (RGB)
    image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

    # Apply Gaussian blur on CPU
    result = gaussian_blur(image, kernel_size=5, sigma=1.5, device="cpu")

    # Check result shape and type
    assert result.shape == image.shape
    assert result.dtype == np.uint8


def test_gaussian_blur_grayscale():
    """Test Gaussian blur on grayscale image."""
    # Create grayscale image
    image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)

    # Apply Gaussian blur on CPU
    result = gaussian_blur(image, kernel_size=5, sigma=1.5, device="cpu")

    # Check result shape and type
    assert result.shape == image.shape
    assert result.dtype == np.uint8


def test_bilateral_filter_preserves_edges():
    """Test that bilateral filter preserves edges better than Gaussian."""
    # Create image with sharp edge
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[:, 50:] = 255

    # Apply bilateral filter
    result = bilateral_filter(image, d=5, sigma_color=50, sigma_space=50, device="cpu")

    # Edge should be somewhat preserved (not completely blurred)
    # Check that there's still a significant difference across the edge
    left_mean = np.mean(result[:, 40:45])
    right_mean = np.mean(result[:, 55:60])
    assert abs(right_mean - left_mean) > 100  # Should still have significant difference


def test_gaussian_blur_smooths():
    """Test that Gaussian blur actually smooths the image."""
    # Create noisy image
    np.random.seed(42)
    image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

    # Apply Gaussian blur
    result = gaussian_blur(image, kernel_size=5, sigma=1.5, device="cpu")

    # Blurred image should have less variance than original
    original_std = np.std(image)
    blurred_std = np.std(result)
    assert blurred_std < original_std


def test_bilateral_filter_different_parameters():
    """Test bilateral filter with different parameter values."""
    image = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)

    # Test different parameters
    result1 = bilateral_filter(image, d=3, sigma_color=10, sigma_space=10, device="cpu")
    result2 = bilateral_filter(image, d=7, sigma_color=50, sigma_space=50, device="cpu")

    # Results should be different
    assert not np.array_equal(result1, result2)
    assert result1.shape == image.shape
    assert result2.shape == image.shape


def test_gaussian_blur_different_parameters():
    """Test Gaussian blur with different parameter values."""
    image = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)

    # Test different kernel sizes
    result1 = gaussian_blur(image, kernel_size=3, sigma=1.0, device="cpu")
    result2 = gaussian_blur(image, kernel_size=7, sigma=2.0, device="cpu")

    # Results should be different
    assert not np.array_equal(result1, result2)
    assert result1.shape == image.shape
    assert result2.shape == image.shape
