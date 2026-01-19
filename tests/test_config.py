"""Tests for configuration models."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from stencilify.config import (
    Color,
    LockSpec,
    PaintOrder,
    PipelineConfig,
)


def test_color_luminance_ordering() -> None:
    """Test that darker colors have lower luminance."""
    black = Color(0, 0, 0)
    gray = Color(128, 128, 128)
    white = Color(255, 255, 255)

    assert black.luminance() < gray.luminance() < white.luminance()
def test_pipeline_config_valid_palette(tmp_path: Path) -> None:
    """Test PipelineConfig with valid 2-color palette."""
    # Create a dummy input file
    input_file = tmp_path / "input.png"
    input_file.touch()

    config = PipelineConfig(
        input_image=input_file,
        palette=["#000000", "#ffffff"],
    )

    assert len(config.palette) == 2
    assert config.palette[0] == "#000000"
    assert config.palette[1] == "#ffffff"


def test_pipeline_config_palette_too_short(tmp_path: Path) -> None:
    """Test that palette with <2 colors fails."""
    input_file = tmp_path / "input.png"
    input_file.touch()

    with pytest.raises(ValidationError, match="at least 2"):
        PipelineConfig(
            input_image=input_file,
            palette=["#000000"],
        )


def test_pipeline_config_palette_too_long(tmp_path: Path) -> None:
    """Test that palette with >4 colors fails."""
    input_file = tmp_path / "input.png"
    input_file.touch()

    with pytest.raises(ValidationError, match="at most 4"):
        PipelineConfig(
            input_image=input_file,
            palette=["#000000", "#111111", "#222222", "#333333", "#444444"],
        )
def test_pipeline_config_sorted_palette_auto(tmp_path: Path) -> None:
    """Test that AUTO paint order sorts palette by luminance."""
    input_file = tmp_path / "input.png"
    input_file.touch()

    config = PipelineConfig(
        input_image=input_file,
        palette=["#ffffff", "#000000", "#808080"],  # White, black, gray
        paint_order=PaintOrder.AUTO,
    )

    sorted_colors = config.get_sorted_palette()
    # Should be sorted dark to light: black, gray, white
    assert sorted_colors[0] == Color.from_hex("#000000")
    assert sorted_colors[1] == Color.from_hex("#808080")
    assert sorted_colors[2] == Color.from_hex("#ffffff")


def test_pipeline_config_sorted_palette_given(tmp_path: Path) -> None:
    """Test that GIVEN paint order preserves order."""
    input_file = tmp_path / "input.png"
    input_file.touch()

    config = PipelineConfig(
        input_image=input_file,
        palette=["#ffffff", "#000000", "#808080"],  # White, black, gray
        paint_order=PaintOrder.GIVEN,
    )

    sorted_colors = config.get_sorted_palette()
    # Should preserve given order
    assert sorted_colors[0] == Color.from_hex("#ffffff")
    assert sorted_colors[1] == Color.from_hex("#000000")
    assert sorted_colors[2] == Color.from_hex("#808080")


def test_lock_spec_valid(tmp_path: Path) -> None:
    """Test LockSpec with valid color and mask."""
    mask_file = tmp_path / "mask.png"
    mask_file.touch()

    lock = LockSpec(color="#ff0000", mask_path=mask_file)
    assert lock.color == "#ff0000"
    assert lock.mask_path == mask_file


def test_lock_spec_invalid_color(tmp_path: Path) -> None:
    """Test LockSpec with invalid color."""
    mask_file = tmp_path / "mask.png"
    mask_file.touch()

    with pytest.raises(ValidationError):
        LockSpec(color="not-a-color", mask_path=mask_file)
