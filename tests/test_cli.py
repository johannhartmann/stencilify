"""Tests for CLI module."""

from pathlib import Path

from typer.testing import CliRunner

from stencilify import cli
from stencilify.cli import app, parse_palette

runner = CliRunner()


def test_cli_import() -> None:
    """Test that CLI module can be imported."""
    assert cli is not None
    assert hasattr(cli, "cli_main")
    assert callable(cli.cli_main)


def test_cli_help() -> None:
    """Test that --help works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "stencilify" in result.stdout.lower()


def test_cli_version() -> None:
    """Test that --version works."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "stencilify version" in result.stdout.lower()


def test_generate_help() -> None:
    """Test that generate --help works."""
    result = runner.invoke(app, ["generate", "--help"])
    assert result.exit_code == 0
    assert "generate" in result.stdout.lower()
    assert "palette" in result.stdout.lower()


def test_config_help() -> None:
    """Test that config --help works."""
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0
    assert "config" in result.stdout.lower()
def test_parse_palette_single() -> None:
    """Test parsing single palette entry."""
    result = parse_palette(["#000000"])
    assert result == ["#000000"]


def test_parse_palette_multiple() -> None:
    """Test parsing multiple palette entries."""
    result = parse_palette(["#000000", "#ffffff"])
    assert result == ["#000000", "#ffffff"]


def test_parse_palette_comma_separated() -> None:
    """Test parsing comma-separated palette."""
    result = parse_palette(["#000000,#ffffff,#808080"])
    assert result == ["#000000", "#ffffff", "#808080"]


def test_parse_palette_mixed() -> None:
    """Test parsing mixed format (repeated and comma-separated)."""
    result = parse_palette(["#000000,#111111", "#222222"])
    assert result == ["#000000", "#111111", "#222222"]
def test_generate_missing_palette(tmp_path: Path) -> None:
    """Test that generate fails when palette is missing."""
    input_file = tmp_path / "input.png"
    input_file.touch()

    result = runner.invoke(app, ["generate", str(input_file)])
    assert result.exit_code == 1
    output = result.stdout + result.stderr
    assert "No palette colors specified" in output


def test_generate_too_few_colors(tmp_path: Path) -> None:
    """Test that generate fails with too few palette colors."""
    input_file = tmp_path / "input.png"
    input_file.touch()

    result = runner.invoke(app, ["generate", str(input_file), "--palette", "#000000"])
    assert result.exit_code == 1
    output = (result.stdout + result.stderr).lower()
    assert "at least 2" in output


def test_generate_valid(tmp_path: Path) -> None:
    """Test that generate succeeds with valid config."""
    # Create a real synthetic RGBA image
    from PIL import Image

    img = Image.new("RGBA", (100, 100), (128, 128, 128, 255))
    input_file = tmp_path / "input.png"
    img.save(input_file)

    result = runner.invoke(
        app,
        [
            "generate",
            str(input_file),
            "--palette",
            "#000000",
            "--palette",
            "#ffffff",
            "--outdir",
            str(tmp_path / "output"),
        ],
    )
    assert result.exit_code == 0
    assert "Successfully generated" in result.stdout
