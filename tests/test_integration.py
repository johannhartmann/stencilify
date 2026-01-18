"""Integration tests for end-to-end pipeline."""

import json
from pathlib import Path

import numpy as np
from PIL import Image

from stencilify.config import CuttabilityConfig, ExportConfig, PageSpec, PipelineConfig
from stencilify.pipeline import run_pipeline


def create_synthetic_portrait(width: int, height: int) -> np.ndarray:
    """
    Create a synthetic RGBA portrait for testing.

    Args:
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        RGBA image array [H, W, 4]
    """
    # Create RGBA array
    rgba = np.zeros((height, width, 4), dtype=np.uint8)

    # Create a simple portrait-like shape
    # Head (circle)
    cy, cx = height // 3, width // 2
    radius = min(width, height) // 4

    y, x = np.ogrid[:height, :width]
    dist_from_center = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    head_mask = dist_from_center <= radius

    # Body (rectangle)
    body_top = cy + radius
    body_bottom = min(height, body_top + radius * 2)
    body_left = cx - radius // 2
    body_right = cx + radius // 2

    body_mask = np.zeros((height, width), dtype=bool)
    body_mask[body_top:body_bottom, body_left:body_right] = True

    # Combine
    portrait_mask = head_mask | body_mask

    # Create color gradient (dark at bottom, light at top)
    gradient = np.linspace(50, 200, height).astype(np.uint8)
    gradient_rgb = np.repeat(gradient[:, np.newaxis], width, axis=1)

    # Apply colors
    rgba[portrait_mask, 0] = gradient_rgb[portrait_mask]  # R
    rgba[portrait_mask, 1] = gradient_rgb[portrait_mask]  # G
    rgba[portrait_mask, 2] = gradient_rgb[portrait_mask]  # B
    rgba[portrait_mask, 3] = 255  # Alpha

    return rgba


def test_pipeline_synthetic_2_colors(tmp_path: Path) -> None:
    """Test full pipeline with synthetic portrait and 2-color palette."""
    # Create synthetic portrait
    portrait = create_synthetic_portrait(200, 300)

    # Save to temporary file
    input_path = tmp_path / "input.png"
    Image.fromarray(portrait, mode="RGBA").save(input_path)

    # Output directory
    output_dir = tmp_path / "output"

    # Create configuration
    config = PipelineConfig(
        input_image=input_path,
        palette=["#000000", "#ffffff"],  # Black and white
        export=ExportConfig(output_dir=output_dir),
        seed=42,
    )

    # Run pipeline
    result = run_pipeline(config)

    # Verify result
    assert result.input_image == str(input_path)
    assert result.palette == ["#000000", "#ffffff"]
    assert len(result.layers) == 2

    # Verify output files exist
    assert output_dir.exists()

    # PNG files
    assert (output_dir / "01_000000.png").exists()
    assert (output_dir / "02_ffffff.png").exists()

    # SVG files
    assert (output_dir / "01_000000.svg").exists()
    assert (output_dir / "02_ffffff.svg").exists()

    # Preview
    assert (output_dir / "preview.png").exists()

    # Report
    report_path = output_dir / "report.json"
    assert report_path.exists()

    # Verify report content
    with open(report_path) as f:
        report_data = json.load(f)

    assert report_data["input_image"] == str(input_path)
    assert report_data["palette"] == ["#000000", "#ffffff"]
    assert len(report_data["layers"]) == 2

    # Verify metrics exist
    for layer in report_data["layers"]:
        assert "color" in layer
        assert "before_optimization" in layer
        assert "after_optimization" in layer
        assert "island_fixing" in layer


def test_pipeline_synthetic_3_colors(tmp_path: Path) -> None:
    """Test full pipeline with 3-color palette."""
    # Create synthetic portrait
    portrait = create_synthetic_portrait(150, 200)

    # Save to temporary file
    input_path = tmp_path / "input.png"
    Image.fromarray(portrait, mode="RGBA").save(input_path)

    # Output directory
    output_dir = tmp_path / "output"

    # Create configuration
    config = PipelineConfig(
        input_image=input_path,
        palette=["#000000", "#808080", "#ffffff"],  # Black, gray, white
        export=ExportConfig(output_dir=output_dir),
        seed=42,
    )

    # Run pipeline
    result = run_pipeline(config)

    # Verify 3 layers
    assert len(result.layers) == 3

    # Verify output files
    assert (output_dir / "01_000000.png").exists()
    assert (output_dir / "02_808080.png").exists()
    assert (output_dir / "03_ffffff.png").exists()


def test_pipeline_with_small_image(tmp_path: Path) -> None:
    """Test pipeline with very small image."""
    # Create small synthetic portrait
    portrait = create_synthetic_portrait(50, 80)

    input_path = tmp_path / "input.png"
    Image.fromarray(portrait, mode="RGBA").save(input_path)

    output_dir = tmp_path / "output"

    config = PipelineConfig(
        input_image=input_path,
        palette=["#000000", "#ffffff"],
        export=ExportConfig(output_dir=output_dir),
        seed=42,
    )

    # Should complete without errors
    result = run_pipeline(config)

    assert len(result.layers) == 2
    assert (output_dir / "report.json").exists()


def test_pipeline_output_directory_created(tmp_path: Path) -> None:
    """Test that output directory is created if it doesn't exist."""
    portrait = create_synthetic_portrait(100, 150)

    input_path = tmp_path / "input.png"
    Image.fromarray(portrait, mode="RGBA").save(input_path)

    # Use nested output directory that doesn't exist
    output_dir = tmp_path / "nested" / "output" / "dir"

    config = PipelineConfig(
        input_image=input_path,
        palette=["#000000", "#ffffff"],
        export=ExportConfig(output_dir=output_dir),
        seed=42,
    )

    _ = run_pipeline(config)

    # Output directory should be created
    assert output_dir.exists()
    assert (output_dir / "report.json").exists()


def test_pipeline_metrics_recorded(tmp_path: Path) -> None:
    """Test that pipeline records metrics properly."""
    portrait = create_synthetic_portrait(100, 150)

    input_path = tmp_path / "input.png"
    Image.fromarray(portrait, mode="RGBA").save(input_path)

    output_dir = tmp_path / "output"

    config = PipelineConfig(
        input_image=input_path,
        palette=["#000000", "#ffffff"],
        export=ExportConfig(output_dir=output_dir),
        seed=42,
    )

    result = run_pipeline(config)

    # Check that metrics are reasonable
    for layer in result.layers:
        assert layer.material_pixels_before >= 0
        assert layer.open_pixels_before >= 0
        assert layer.material_pixels_after >= 0
        assert layer.open_pixels_after >= 0
        assert layer.contours_count_before >= 0
        assert layer.contours_count_after >= 0
        assert layer.islands_found >= 0
        assert layer.islands_filled >= 0
        assert layer.bridges_added >= 0


def test_pipeline_preserves_config_parameters(tmp_path: Path) -> None:
    """Test that pipeline preserves configuration parameters."""
    portrait = create_synthetic_portrait(100, 150)

    input_path = tmp_path / "input.png"
    Image.fromarray(portrait, mode="RGBA").save(input_path)

    output_dir = tmp_path / "output"

    config = PipelineConfig(
        input_image=input_path,
        palette=["#000000", "#ffffff"],
        export=ExportConfig(output_dir=output_dir),
        page=PageSpec(margin_mm=15.0),
        cuttability=CuttabilityConfig(
            min_feature_mm=3.0,
            min_island_area_mm2=30.0,
            bridge_width_mm=2.0,
        ),
        seed=42,
    )

    result = run_pipeline(config)

    # Verify parameters are recorded
    assert result.margin_mm == 15.0
    assert result.min_feature_mm == 3.0
    assert result.min_island_area_mm2 == 30.0
    assert result.bridge_width_mm == 2.0
