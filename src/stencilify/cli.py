"""Command-line interface for stencilify."""

import sys
from pathlib import Path

import click

from stencilify.constants import DEFAULT_OUTPUT_DIR, MAX_LAYERS, MIN_LAYERS, __version__
from stencilify.logging import setup_logging


@click.group()
@click.version_option(version=__version__, prog_name="stencilify")
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output (DEBUG level)",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Suppress all but error messages",
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool) -> None:
    """
    Convert RGBA portrait images into palette-constrained stencil layers.

    Generates 2-4 stencil layers suitable for cutting plotters and laser cutters,
    with binary PNG masks, vector SVG output, registration marks, and cuttability
    optimization.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet

    # Setup logging
    setup_logging(verbose=verbose, quiet=quiet)


@cli.command()
@click.argument(
    "input_image",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(path_type=Path),
    default=DEFAULT_OUTPUT_DIR,
    help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
)
@click.option(
    "-n",
    "--num-layers",
    type=click.IntRange(MIN_LAYERS, MAX_LAYERS),
    default=3,
    help=f"Number of stencil layers ({MIN_LAYERS}-{MAX_LAYERS})",
)
@click.option(
    "--paper-size",
    type=click.Choice(["A4", "A3", "A2"], case_sensitive=False),
    default="A4",
    help="Output paper size",
)
@click.option(
    "--seed",
    type=int,
    default=None,
    help="Random seed for deterministic results",
)
@click.pass_context
def generate(
    ctx: click.Context,
    input_image: Path,
    output_dir: Path,
    num_layers: int,
    paper_size: str,
    seed: int | None,
) -> None:
    """
    Generate stencil layers from an input image.

    INPUT_IMAGE: Path to the RGBA portrait image to process.

    Creates binary PNG masks and vector SVG files for each layer,
    with registration marks, preview composite, and report.json.
    """
    click.echo(f"Generating {num_layers} stencil layers from: {input_image}")
    click.echo(f"Output directory: {output_dir}")
    click.echo(f"Paper size: {paper_size}")
    if seed is not None:
        click.echo(f"Random seed: {seed}")

    # TODO: Implement generation logic in subsequent steps
    click.echo("\n[Stub] Generation pipeline not yet implemented")


def main() -> int:
    """Entry point for the CLI."""
    try:
        cli(obj={})
        return 0
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
