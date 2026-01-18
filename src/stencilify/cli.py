"""Command-line interface for stencilify."""

import json
import sys
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from stencilify.config import (
    AutotuneConfig,
    CuttabilityConfig,
    ExportConfig,
    LockSpec,
    PageSpec,
    PaintOrder,
    PipelineConfig,
    VectorBackend,
)
from stencilify.constants import __version__
from stencilify.geometry import Orientation, PageSize
from stencilify.logging import get_logger, setup_logging

app = typer.Typer(
    name="stencilify",
    help="Convert RGBA portrait images into palette-constrained stencil layers.",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"stencilify version {__version__}")
        raise typer.Exit()


def parse_palette(palette_values: list[str]) -> list[str]:
    """
    Parse palette from CLI arguments.

    Supports both repeated --palette entries and comma-separated strings.

    Args:
        palette_values: List of palette arguments

    Returns:
        Flattened list of palette color strings
    """
    colors: list[str] = []
    for value in palette_values:
        # Support comma-separated values
        if "," in value:
            colors.extend(v.strip() for v in value.split(","))
        else:
            colors.append(value.strip())
    return colors


def parse_locks(lock_values: list[str]) -> list[LockSpec]:
    """
    Parse lock specifications from CLI arguments.

    Format: COLOR=PATH where COLOR is hex and PATH is path to mask.

    Args:
        lock_values: List of lock arguments in format COLOR=PATH

    Returns:
        List of LockSpec objects

    Raises:
        typer.BadParameter: If lock format is invalid
    """
    locks = []
    for lock_str in lock_values:
        if "=" not in lock_str:
            raise typer.BadParameter(
                f"Invalid lock format: '{lock_str}'. Expected format: COLOR=PATH"
            )

        color, path_str = lock_str.split("=", 1)
        color = color.strip()
        path = Path(path_str.strip())

        try:
            locks.append(LockSpec(color=color, mask_path=path))
        except ValidationError as e:
            raise typer.BadParameter(f"Invalid lock '{lock_str}': {e}") from e

    return locks


@app.command()
def generate(
    input_image: Annotated[
        Path,
        typer.Argument(
            help="Path to input RGBA image",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    outdir: Annotated[
        Path,
        typer.Option(
            "--outdir",
            "-o",
            help="Output directory for generated files",
        ),
    ] = Path("out"),
    palette: Annotated[
        list[str] | None,
        typer.Option(
            "--palette",
            "-p",
            help=(
                "Palette color in hex (#RRGGBB). Repeat for multiple colors or use comma-separated."
            ),
        ),
    ] = None,
    page: Annotated[
        PageSize,
        typer.Option(
            "--page",
            help="Page size",
            case_sensitive=False,
        ),
    ] = PageSize.A4,
    orientation: Annotated[
        Orientation,
        typer.Option(
            "--orientation",
            help="Page orientation",
            case_sensitive=False,
        ),
    ] = Orientation.AUTO,
    margin_mm: Annotated[
        float,
        typer.Option(
            "--margin-mm",
            help="Page margin in millimeters (applied to all edges)",
        ),
    ] = 10.0,
    min_feature_mm: Annotated[
        float,
        typer.Option(
            "--min-feature-mm",
            help="Minimum feature size in millimeters",
        ),
    ] = 2.0,
    min_island_area_mm2: Annotated[
        float,
        typer.Option(
            "--min-island-area-mm2",
            help="Minimum island area in square millimeters (0 disables island removal)",
        ),
    ] = 25.0,
    bridge_width_mm: Annotated[
        float,
        typer.Option(
            "--bridge-width-mm",
            help="Bridge width in millimeters (0 disables bridges)",
        ),
    ] = 1.0,
    paint_order: Annotated[
        str,
        typer.Option(
            "--paint-order",
            help="Paint order: auto (sort by luminance, dark to light) or given",
        ),
    ] = "auto",
    lock: Annotated[
        list[str] | None,
        typer.Option(
            "--lock",
            help=(
                "Lock a layer to a pre-existing mask. Format: COLOR=PATH. "
                "Repeat for multiple locks."
            ),
        ),
    ] = None,
    vector_backend: Annotated[
        str,
        typer.Option(
            "--vector-backend",
            help="Vector export backend",
        ),
    ] = "contours",
    autotune: Annotated[
        bool,
        typer.Option(
            "--autotune",
            help="Enable autotune mode",
        ),
    ] = False,
    seed: Annotated[
        int | None,
        typer.Option(
            "--seed",
            help="Random seed for deterministic results",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable verbose output (DEBUG level)",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress all but error messages",
        ),
    ] = False,
) -> None:
    """
    Generate stencil layers from an input image.

    Creates binary PNG masks and vector SVG files for each layer,
    with registration marks, preview composite, and report.json.

    Example:
        stencilify generate input.png --palette #000000 --palette #ffffff --page A4
    """
    # Setup logging
    setup_logging(verbose=verbose, quiet=quiet)
    logger = get_logger()

    # Parse palette
    palette_colors = parse_palette(palette or [])
    if not palette_colors:
        typer.echo("Error: No palette colors specified. Use --palette COLOR.", err=True)
        typer.echo(
            "Example: stencilify generate input.png --palette #000000 --palette #ffffff",
            err=True,
        )
        raise typer.Exit(code=1)

    # Parse locks
    try:
        lock_specs = parse_locks(lock or [])
    except typer.BadParameter as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e

    # Build configuration
    try:
        config = PipelineConfig(
            input_image=input_image,
            export=ExportConfig(
                output_dir=outdir,
                vector_backend=VectorBackend(vector_backend),
            ),
            palette=palette_colors,
            paint_order=PaintOrder(paint_order),
            page=PageSpec(
                size=page,
                orientation=orientation,
                margin_mm=margin_mm,
            ),
            cuttability=CuttabilityConfig(
                min_feature_mm=min_feature_mm,
                min_island_area_mm2=min_island_area_mm2,
                bridge_width_mm=bridge_width_mm,
            ),
            locks=lock_specs,
            autotune=AutotuneConfig(enabled=autotune),
            seed=seed,
        )
    except ValidationError as e:
        typer.echo(f"Configuration error:\n{e}", err=True)
        raise typer.Exit(code=1) from e

    # Log configuration summary
    logger.info(f"Input: {config.input_image}")
    logger.info(f"Output: {config.export.output_dir}")
    logger.info(f"Palette: {len(config.palette)} colors - {', '.join(config.palette)}")
    logger.info(f"Page: {config.page.size.value} ({config.page.orientation.value})")
    logger.info(f"Paint order: {config.paint_order}")

    if config.seed is not None:
        logger.info(f"Random seed: {config.seed}")

    # Run pipeline
    try:
        from stencilify.pipeline import run_pipeline

        result = run_pipeline(config)

        # Report warnings
        if result.warnings:
            logger.warning(f"\nPipeline completed with {len(result.warnings)} warning(s):")
            for warning in result.warnings:
                logger.warning(f"  - {warning}")

        # Success
        typer.echo(f"\n✓ Successfully generated {len(result.layers)} stencil layers")
        typer.echo(f"  Output directory: {config.export.output_dir}")
        typer.echo(f"  Report: {config.export.output_dir / 'report.json'}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise typer.Exit(code=1) from e
    except ValueError as e:
        logger.error(f"Pipeline error: {e}")
        raise typer.Exit(code=1) from e
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise typer.Exit(code=1) from e


@app.command()
def config(
    print_defaults: Annotated[
        bool,
        typer.Option(
            "--print-defaults",
            help="Print default configuration as JSON",
        ),
    ] = False,
) -> None:
    """
    Show or export configuration.

    Use --print-defaults to see a JSON representation of default configuration values.
    """
    if print_defaults:
        # Create a sample configuration with defaults (bypass validation for example)
        sample_config = PipelineConfig.model_construct(
            input_image=Path("input.png"),
            palette=["#000000", "#808080", "#ffffff"],
            export=ExportConfig(output_dir=Path("out"), vector_backend=VectorBackend.CONTOURS),
            paint_order=PaintOrder.AUTO,
            page=PageSpec(),
            cuttability=CuttabilityConfig(),
            locks=[],
            autotune=AutotuneConfig(),
            seed=None,
        )

        # Export as JSON
        config_dict = sample_config.model_dump(mode="json")
        # Convert Path objects to strings for JSON serialization
        config_dict["input_image"] = str(config_dict["input_image"])
        config_dict["export"]["output_dir"] = str(config_dict["export"]["output_dir"])

        typer.echo(json.dumps(config_dict, indent=2))
    else:
        typer.echo("Use --print-defaults to see default configuration")


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            help="Show version and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """
    Stencilify: Convert RGBA images into stencil layers.

    Generates 2-4 stencil layers suitable for cutting plotters and laser cutters,
    with binary PNG masks, vector SVG output, registration marks, and cuttability
    optimization.
    """
    pass


def cli_main() -> int:
    """Entry point for the CLI."""
    try:
        app()
        return 0
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(cli_main())
