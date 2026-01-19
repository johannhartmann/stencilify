# Stencilify

Convert RGBA portrait images into palette-constrained stencil layers suitable for cutting plotters and laser cutters.

## Features

- **Palette-based layering**: Convert images to 2-4 color layers
- **Superpixel segmentation**: SLIC-based image segmentation for smooth regions
- **ICM optimization**: Iterative Conditional Modes for palette assignment
- **Cuttability optimization**: Morphological cleanup, small cutout removal
- **Island detection and fixing**: Automatic bridging of disconnected regions
- **Page layout**: Place artwork on standard paper sizes (A4, A3, A2)
- **Registration marks**: Automatic alignment marks across layers
- **Export formats**: Binary PNG masks and SVG vectors (contours/potrace)
- **Preview rendering**: Composite preview of final result
- **Autotuning**: Grid search for optimal parameters
- **Optional GPU acceleration**: CUDA support for faster processing

## Installation

### Basic Installation (CPU only)

```bash
uv sync
```

### GPU-Accelerated Installation (Optional)

For optional GPU acceleration on CUDA-capable systems:

```bash
uv sync --extra gpu
```

This installs PyTorch and Kornia for GPU-accelerated operations. GPU acceleration is **not required** - the tool works perfectly fine on CPU alone. The GPU path is used for:

- Bilateral filtering (edge-preserving smoothing)
- Gaussian blurring
- Batch color space conversions

Note: SLIC superpixels, connected components, and contour extraction remain on CPU regardless of the `--device` setting, as they have complex dependencies and well-optimized CPU implementations.

## Usage

### Basic Usage

```bash
# Generate stencils with a 2-color palette
stencilify generate input.png --palette #000000 --palette #ffffff

# 3-color palette
stencilify generate input.png \
  --palette #000000 \
  --palette #808080 \
  --palette #ffffff
```

### Advanced Options

```bash
stencilify generate input.png \
  --palette #000000,#808080,#ffffff \
  --page A4 \
  --orientation landscape \
  --margin-mm 15.0 \
  --min-feature-mm 2.0 \
  --min-island-area-mm2 25.0 \
  --bridge-width-mm 1.0 \
  --paint-order auto \
  --vector-backend contours \
  --device auto \
  --seed 42 \
  --outdir output/
```

### Autotuning

Automatically find the best parameters for your image:

```bash
stencilify generate input.png \
  --palette #000000,#ffffff \
  --autotune
```

Autotuning searches over a parameter grid and selects the best configuration based on a weighted scoring function.

### GPU Acceleration

Use CUDA GPU for faster processing (requires `uv sync --extra gpu`):

```bash
# Explicit CUDA (falls back to CPU if unavailable)
stencilify generate input.png --palette #000000,#ffffff --device cuda

# Auto-detect (uses CUDA if available, otherwise CPU)
stencilify generate input.png --palette #000000,#ffffff --device auto

# Force CPU
stencilify generate input.png --palette #000000,#ffffff --device cpu
```

### Locking Layers

Lock specific layers to pre-existing masks:

```bash
stencilify generate input.png \
  --palette #000000,#ffffff \
  --lock "#000000=dark_layer.png"
```

## Output Files

The tool generates the following files in the output directory:

- `layer_<COLOR>.png` - Binary PNG mask for each layer (white=cut, black=material)
- `layer_<COLOR>.svg` - Vector SVG for each layer
- `preview.png` - Composite preview showing all layers
- `report.json` - Detailed metrics and parameters
- `candidates.csv` - Autotune results (if `--autotune` enabled)

## CLI Options

| Option                    | Description                                          | Default   |
| ------------------------- | ---------------------------------------------------- | --------- |
| `--palette`, `-p`         | Palette color in hex (#RRGGBB), repeat for multiple | Required  |
| `--outdir`, `-o`          | Output directory                                     | `out`     |
| `--page`                  | Page size (A4, A3, A2)                               | `A4`      |
| `--orientation`           | Page orientation (portrait, landscape, auto)         | `auto`    |
| `--margin-mm`             | Page margin in millimeters                           | `10.0`    |
| `--min-feature-mm`        | Minimum feature size in millimeters                  | `2.0`     |
| `--min-island-area-mm2`   | Minimum island area in square millimeters            | `25.0`    |
| `--bridge-width-mm`       | Bridge width in millimeters                          | `1.0`     |
| `--paint-order`           | Paint order: auto (luminance) or given               | `auto`    |
| `--lock`                  | Lock layer to mask (COLOR=PATH)                      | None      |
| `--vector-backend`        | Vector backend (contours, potrace)                   | `contours`|
| `--autotune`              | Enable parameter autotuning                          | `False`   |
| `--device`                | Compute device (cpu, cuda, auto)                     | `cpu`     |
| `--seed`                  | Random seed for deterministic results                | None      |
| `--verbose`, `-v`         | Enable verbose output (DEBUG level)                  | `False`   |
| `--quiet`, `-q`           | Suppress all but error messages                      | `False`   |

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_compute.py -v

# Run with coverage
uv run pytest --cov=stencilify --cov-report=html
```

### Code Quality

```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check

# Type checking
uv run mypy src/
```

## Architecture

The pipeline consists of the following steps:

1. **Load Image**: Load RGBA image and create silhouette from alpha channel
2. **Superpixels**: SLIC superpixel segmentation within silhouette
3. **Labeling**: ICM optimization for palette-constrained labeling
4. **Open Masks**: Build binary masks for each color layer
5. **Optimization**: Morphological cleanup and small cutout removal
6. **Island Fixing**: Detect and fix disconnected regions
7. **Page Layout**: Place artwork on page with registration marks
8. **Preview**: Render composite preview
9. **Export**: Export PNG masks and SVG vectors
10. **Report**: Generate metrics and save report.json

## License

MIT License - See LICENSE file for details.
