"""Tests for CLI module."""

from stencilify import cli


def test_cli_import() -> None:
    """Test that CLI module can be imported."""
    assert cli is not None
    assert hasattr(cli, "main")
    assert callable(cli.main)
