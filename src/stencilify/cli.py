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
    device: Annotated[
        str,
        typer.Option(
            "--device",
            help="Compute device: cpu (default), cuda, or auto",
            case_sensitive=False,
        ),
    ] = "cpu",
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
            device=device,
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
            device="cpu",
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


@app.command()
def doctor() -> None:
    """
    Check system setup and dependencies.

    Verifies that all required dependencies are working and reports
    on optional features (GPU, potrace).
    """
    import platform
    import shutil
    import subprocess

    import cv2
    import numpy as np
    import skimage
    from PIL import Image

    skimage_version = skimage.__version__  # type: ignore[attr-defined]

    typer.echo("=" * 60)
    typer.echo("Stencilify System Check")
    typer.echo("=" * 60)
    typer.echo()

    # Python and platform info
    typer.echo("📋 System Information")
    typer.echo(f"  Python version: {platform.python_version()}")
    typer.echo(f"  Platform: {platform.system()} {platform.release()}")
    typer.echo(f"  Stencilify version: {__version__}")
    typer.echo()

    # Required dependencies
    typer.echo("✓ Required Dependencies")
    typer.echo(f"  OpenCV: {cv2.__version__}")
    typer.echo(f"  Pillow: {Image.__version__}")
    typer.echo(f"  NumPy: {np.__version__}")
    typer.echo(f"  scikit-image: {skimage_version}")
    typer.echo()

    # Test OpenCV basic operations
    typer.echo("🔧 Testing OpenCV...")
    try:
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        _ = cv2.cvtColor(test_img, cv2.COLOR_RGB2GRAY)
        contours, _ = cv2.findContours(
            np.zeros((100, 100), dtype=np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        typer.echo("  ✓ OpenCV basic operations working")
    except Exception as e:
        typer.echo(f"  ✗ OpenCV error: {e}", err=True)
    typer.echo()

    # GPU availability
    typer.echo("🎮 GPU Acceleration (Optional)")
    try:
        import torch  # type: ignore[import-not-found]

        typer.echo(f"  PyTorch: {torch.__version__}")
        if torch.cuda.is_available():
            typer.echo(f"  CUDA available: Yes (Device: {torch.cuda.get_device_name(0)})")
            typer.echo(f"  CUDA version: {torch.version.cuda}")
        else:
            typer.echo("  CUDA available: No")

        try:
            import kornia  # type: ignore[import-not-found]

            typer.echo(f"  Kornia: {kornia.__version__}")
        except ImportError:
            typer.echo("  Kornia: Not installed")

        typer.echo()
        typer.echo("  Use --device cuda or --device auto to enable GPU acceleration")
    except ImportError:
        typer.echo("  PyTorch: Not installed")
        typer.echo("  GPU acceleration unavailable (CPU only)")
        typer.echo()
        typer.echo("  To enable GPU: uv sync --extra gpu")
    typer.echo()

    # Potrace availability
    typer.echo("🎨 Vector Backends")
    typer.echo("  Contours (OpenCV): ✓ Available")

    potrace_path = shutil.which("potrace")
    if potrace_path:
        try:
            result = subprocess.run(
                ["potrace", "--version"], capture_output=True, text=True, timeout=5
            )
            version_line = result.stdout.split("\n")[0] if result.stdout else "Unknown"
            typer.echo(f"  Potrace: ✓ Available ({version_line})")
            typer.echo(f"    Path: {potrace_path}")
        except Exception as e:
            typer.echo(f"  Potrace: Found but error running: {e}")
    else:
        typer.echo("  Potrace: Not installed (optional)")
        typer.echo("    Install: apt-get install potrace  or  brew install potrace")
    typer.echo()

    # Summary
    typer.echo("=" * 60)
    typer.echo("Summary")
    typer.echo("=" * 60)

    all_good = True
    try:
        # Check if we can import all critical modules
        from stencilify.pipeline import run_pipeline  # noqa: F401

        typer.echo("✓ All required dependencies are working")
    except Exception as e:
        typer.echo(f"✗ Dependency error: {e}", err=True)
        all_good = False

    if all_good:
        typer.echo("✓ System is ready to use stencilify")
        typer.echo()
        typer.echo("Next steps:")
        typer.echo("  1. Prepare an RGBA portrait image")
        typer.echo("  2. Run: stencilify generate input.png --palette #000000 --palette #ffffff")
        typer.echo("  3. Check the output in the 'out/' directory")
        typer.echo()
        typer.echo("See examples/ folder for more recipes and guides")
    else:
        typer.echo()
        typer.echo("Please fix the errors above before using stencilify")
        raise typer.Exit(code=1)


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
