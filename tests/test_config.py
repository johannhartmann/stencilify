"""Tests for configuration models."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from stencilify.config import (
    Color,
    CuttabilityConfig,
    LockSpec,
    PageSpec,
    PaintOrder,
    PipelineConfig,
)
from stencilify.geometry import Orientation, PageSize


def test_color_from_hex_with_hash() -> None:
    """Test parsing hex color with # prefix."""
    color = Color.from_hex("#FF0000")
    assert color.r == 255
    assert color.g == 0
    assert color.b == 0


def test_color_from_hex_without_hash() -> None:
    """Test parsing hex color without # prefix."""
    color = Color.from_hex("00FF00")
    assert color.r == 0
    assert color.g == 255
    assert color.b == 0


def test_color_from_hex_lowercase() -> None:
    """Test parsing lowercase hex color."""
    color = Color.from_hex("#0000ff")
    assert color.r == 0
    assert color.g == 0
    assert color.b == 255


def test_color_from_hex_invalid() -> None:
    """Test that invalid hex raises ValueError."""
    with pytest.raises(ValueError, match="Invalid hex color"):
        Color.from_hex("#GGGGGG")


def test_color_from_hex_wrong_length() -> None:
    """Test that wrong length hex raises ValueError."""
    with pytest.raises(ValueError, match="Invalid hex color"):
        Color.from_hex("#FF")


def test_color_to_hex() -> None:
    """Test converting color back to hex."""
    color = Color(255, 128, 0)
    assert color.to_hex() == "#ff8000"


def test_color_luminance_black() -> None:
    """Test luminance of black is 0."""
    color = Color(0, 0, 0)
    assert color.luminance() == 0.0


def test_color_luminance_white() -> None:
    """Test luminance of white is 1."""
    color = Color(255, 255, 255)
    assert color.luminance() == 1.0


def test_color_luminance_ordering() -> None:
    """Test that darker colors have lower luminance."""
    black = Color(0, 0, 0)
    gray = Color(128, 128, 128)
    white = Color(255, 255, 255)

    assert black.luminance() < gray.luminance() < white.luminance()


def test_color_equality() -> None:
    """Test color equality."""
    c1 = Color(255, 0, 0)
    c2 = Color(255, 0, 0)
    c3 = Color(0, 255, 0)

    assert c1 == c2
    assert c1 != c3


def test_color_hash() -> None:
    """Test that colors can be used in sets."""
    c1 = Color(255, 0, 0)
    c2 = Color(255, 0, 0)
    c3 = Color(0, 255, 0)

    color_set = {c1, c2, c3}
    assert len(color_set) == 2  # c1 and c2 are the same


def test_page_spec_defaults() -> None:
    """Test PageSpec default values."""
    spec = PageSpec()
    assert spec.size == PageSize.A4
    assert spec.orientation == Orientation.AUTO
    assert spec.margin_mm == 10.0


def test_page_spec_custom() -> None:
    """Test PageSpec with custom values."""
    spec = PageSpec(size=PageSize.A3, orientation=Orientation.LANDSCAPE, margin_mm=5.0)
    assert spec.size == PageSize.A3
    assert spec.orientation == Orientation.LANDSCAPE
    assert spec.margin_mm == 5.0


def test_page_spec_negative_margin() -> None:
    """Test that negative margins are rejected."""
    with pytest.raises(ValidationError):
        PageSpec(margin_mm=-1.0)


def test_cuttability_config_defaults() -> None:
    """Test CuttabilityConfig default values."""
    config = CuttabilityConfig()
    assert config.min_feature_mm == 2.0
    assert config.min_island_area_mm2 == 25.0
    assert config.bridge_width_mm == 1.0


def test_cuttability_config_zero_bridge() -> None:
    """Test that bridge width can be zero (disables bridges)."""
    config = CuttabilityConfig(bridge_width_mm=0.0)
    assert config.bridge_width_mm == 0.0


def test_cuttability_config_negative_min_feature() -> None:
    """Test that negative min feature is rejected."""
    with pytest.raises(ValidationError):
        CuttabilityConfig(min_feature_mm=-1.0)


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


def test_pipeline_config_invalid_color(tmp_path: Path) -> None:
    """Test that invalid color in palette fails."""
    input_file = tmp_path / "input.png"
    input_file.touch()

    with pytest.raises(ValidationError, match="Invalid palette color"):
        PipelineConfig(
            input_image=input_file,
            palette=["#000000", "not-a-color"],
        )


def test_pipeline_config_missing_input() -> None:
    """Test that missing input file fails."""
    with pytest.raises(ValidationError, match="does not exist"):
        PipelineConfig(
            input_image=Path("/nonexistent/file.png"),
            palette=["#000000", "#ffffff"],
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


def test_lock_spec_missing_mask() -> None:
    """Test LockSpec with missing mask file."""
    with pytest.raises(ValidationError, match="does not exist"):
        LockSpec(color="#ff0000", mask_path=Path("/nonexistent/mask.png"))
