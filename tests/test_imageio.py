"""Tests for image I/O and scaling."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from stencilify.config import CuttabilityConfig, PageSpec, PipelineConfig
from stencilify.geometry import Orientation, PageSize
from stencilify.imageio import load_rgba, resize_to_working


def test_load_rgba_valid(tmp_path: Path) -> None:
    """Test loading a valid RGBA image."""
    # Create a small RGBA test image
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))
    img_path = tmp_path / "test.png"
    img.save(img_path)

    rgb, alpha = load_rgba(img_path)

    assert rgb.shape == (100, 100, 3)
    assert alpha.shape == (100, 100)
    assert rgb.dtype == np.uint8
    assert alpha.dtype == np.uint8
    # Check that RGB is red
    assert np.all(rgb[:, :, 0] == 255)  # R
    assert np.all(rgb[:, :, 1] == 0)  # G
    assert np.all(rgb[:, :, 2] == 0)  # B
    # Check that alpha is opaque
    assert np.all(alpha == 255)


def test_load_rgba_with_transparency(tmp_path: Path) -> None:
    """Test loading an RGBA image with varying alpha values."""
    # Create image with gradient alpha
    img = Image.new("RGBA", (100, 100))
    pixels = img.load()
    for y in range(100):
        for x in range(100):
            alpha_val = int((x / 100.0) * 255)
            pixels[x, y] = (128, 64, 32, alpha_val)  # type: ignore[index]

    img_path = tmp_path / "test_alpha.png"
    img.save(img_path)

    rgb, alpha = load_rgba(img_path)

    assert rgb.shape == (100, 100, 3)
    assert alpha.shape == (100, 100)
    # Check alpha gradient
    assert alpha[0, 0] < alpha[0, 50] < alpha[0, 99]


def test_load_rgba_no_alpha_fails(tmp_path: Path) -> None:
    """Test that loading an RGB image without alpha fails."""
    # Create RGB image
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img_path = tmp_path / "test_rgb.png"
    img.save(img_path)

    with pytest.raises(ValueError, match="must have an alpha channel"):
        load_rgba(img_path)


def test_load_rgba_missing_file() -> None:
    """Test that loading a missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_rgba(Path("/nonexistent/file.png"))


def test_resize_to_working_preserves_aspect_ratio(tmp_path: Path) -> None:
    """Test that resizing preserves aspect ratio."""
    # Create a 200x100 image (2:1 aspect ratio)
    rgb = np.zeros((100, 200, 3), dtype=np.uint8)
    alpha = np.full((100, 200), 255, dtype=np.uint8)

    # Create minimal config
    input_file = tmp_path / "test.png"
    input_file.touch()

    config = PipelineConfig(
        input_image=input_file,
        palette=["#000000", "#ffffff"],
        page=PageSpec(size=PageSize.A4, orientation=Orientation.AUTO),
        cuttability=CuttabilityConfig(min_feature_mm=2.0),
    )

    rgb_resized, alpha_resized, px_per_mm = resize_to_working(rgb, alpha, config)

    # Check that aspect ratio is preserved
    original_aspect = rgb.shape[1] / rgb.shape[0]  # W / H
    resized_aspect = rgb_resized.shape[1] / rgb_resized.shape[0]

    assert abs(original_aspect - resized_aspect) < 0.01  # Within 1%

    # Check shapes match
    assert rgb_resized.shape[:2] == alpha_resized.shape

    # Check that px_per_mm is positive
    assert px_per_mm > 0


def test_resize_to_working_respects_min_feature(tmp_path: Path) -> None:
    """Test that working resolution respects min_feature_mm."""
    rgb = np.zeros((100, 100, 3), dtype=np.uint8)
    alpha = np.full((100, 100), 255, dtype=np.uint8)

    input_file = tmp_path / "test.png"
    input_file.touch()

    # Test with different min_feature_mm values
    for min_feature_mm in [1.0, 2.0, 4.0]:
        config = PipelineConfig(
            input_image=input_file,
            palette=["#000000", "#ffffff"],
            page=PageSpec(size=PageSize.A4, orientation=Orientation.AUTO),
            cuttability=CuttabilityConfig(min_feature_mm=min_feature_mm),
        )

        rgb_resized, alpha_resized, px_per_mm = resize_to_working(rgb, alpha, config)

        # Smaller min_feature_mm should result in higher resolution
        # (more pixels per mm)
        long_edge = max(rgb_resized.shape[0], rgb_resized.shape[1])

        # Resolution should be clamped between 2000 and 6000
        assert 2000 <= long_edge <= 6000


def test_resize_to_working_clamps_resolution(tmp_path: Path) -> None:
    """Test that working resolution is clamped to [2000, 6000]."""
    rgb = np.zeros((100, 100, 3), dtype=np.uint8)
    alpha = np.full((100, 100), 255, dtype=np.uint8)

    input_file = tmp_path / "test.png"
    input_file.touch()

    # Test with very small min_feature_mm on large page (should clamp to max)
    config_small = PipelineConfig(
        input_image=input_file,
        palette=["#000000", "#ffffff"],
        page=PageSpec(size=PageSize.A2, orientation=Orientation.LANDSCAPE),
        cuttability=CuttabilityConfig(min_feature_mm=0.3),  # Very small for high res
    )

    rgb_small, _, _ = resize_to_working(rgb, alpha, config_small)
    long_edge_small = max(rgb_small.shape[0], rgb_small.shape[1])

    # Should be clamped to 6000
    assert long_edge_small == 6000

    # Test with very large min_feature_mm (should clamp to min)
    config_large = PipelineConfig(
        input_image=input_file,
        palette=["#000000", "#ffffff"],
        page=PageSpec(size=PageSize.A4, orientation=Orientation.AUTO),
        cuttability=CuttabilityConfig(min_feature_mm=20.0),
    )

    rgb_large, _, _ = resize_to_working(rgb, alpha, config_large)
    long_edge_large = max(rgb_large.shape[0], rgb_large.shape[1])

    # Should be clamped to 2000
    assert long_edge_large == 2000


def test_resize_to_working_different_page_sizes(tmp_path: Path) -> None:
    """Test that different page sizes work correctly."""
    rgb = np.zeros((100, 100, 3), dtype=np.uint8)
    alpha = np.full((100, 100), 255, dtype=np.uint8)

    input_file = tmp_path / "test.png"
    input_file.touch()

    # Test with A2 (largest) to ensure we can reach higher resolutions
    config_a2 = PipelineConfig(
        input_image=input_file,
        palette=["#000000", "#ffffff"],
        page=PageSpec(size=PageSize.A2, orientation=Orientation.PORTRAIT),
        cuttability=CuttabilityConfig(min_feature_mm=1.0),
    )

    rgb_resized, _, px_per_mm = resize_to_working(rgb, alpha, config_a2)
    long_edge = max(rgb_resized.shape[0], rgb_resized.shape[1])

    # A2 with min_feature_mm=1.0 should produce a resolution in valid range
    assert 2000 <= long_edge <= 6000
    # px_per_mm should be positive and reasonable
    assert 2.0 < px_per_mm < 30.0


def test_resize_to_working_invalid_dimensions() -> None:
    """Test that invalid input dimensions raise ValueError."""
    # Zero dimension
    rgb = np.zeros((0, 100, 3), dtype=np.uint8)
    alpha = np.full((0, 100), 255, dtype=np.uint8)

    # Create dummy config (won't be used)
    config = PipelineConfig.model_construct(
        input_image=Path("test.png"),
        palette=["#000000", "#ffffff"],
    )

    with pytest.raises(ValueError, match="Invalid input dimensions"):
        resize_to_working(rgb, alpha, config)


def test_resize_to_working_mismatched_shapes() -> None:
    """Test that mismatched RGB/alpha shapes raise ValueError."""
    rgb = np.zeros((100, 100, 3), dtype=np.uint8)
    alpha = np.full((50, 50), 255, dtype=np.uint8)  # Different size

    config = PipelineConfig.model_construct(
        input_image=Path("test.png"),
        palette=["#000000", "#ffffff"],
    )

    with pytest.raises(ValueError, match="shape mismatch"):
        resize_to_working(rgb, alpha, config)


def test_resize_to_working_returns_uint8() -> None:
    """Test that resized images are uint8."""
    rgb = np.zeros((100, 100, 3), dtype=np.uint8)
    alpha = np.full((100, 100), 255, dtype=np.uint8)

    config = PipelineConfig.model_construct(
        input_image=Path("test.png"),
        palette=["#000000", "#ffffff"],
        page=PageSpec(),
        cuttability=CuttabilityConfig(),
    )

    rgb_resized, alpha_resized, _ = resize_to_working(rgb, alpha, config)

    assert rgb_resized.dtype == np.uint8
    assert alpha_resized.dtype == np.uint8
