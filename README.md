# Stencilify

Convert RGBA portrait images into palette-constrained stencil layers suitable for cutting plotters and laser cutters.

## Overview

Stencilify takes an input image and generates **cut masks** for each color in your palette. Each mask represents a physical stencil layer:

- **White pixels = open (cut through)** - These areas will be painted
- **Black pixels = material (keep)** - These areas remain as material

The masks are designed to be **cuttable**: small features are removed, disconnected islands are fixed with bridges, and registration marks ensure perfect alignment across layers.

### Paint Order and White Undercoat Strategy

When painting with stencils, you typically work **dark to light**. For the brightest colors (white, light yellow), use a **white undercoat strategy**:

1. Paint a white base layer first (separate stencil)
2. Then paint your bright color on top

This technique prevents dark paper from showing through and ensures vibrant, opaque colors. Stencilify automatically orders layers by luminance when `--paint-order auto` is used.

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

### Quick Start

Check your system setup:

```bash
stencilify doctor
```

### Basic Examples

#### 2-Color Stencil (High Contrast)

Perfect for bold, graphic designs:

```bash
stencilify generate portrait.png \
  --palette #000000 \
  --palette #ffffff
```

**Output**: 2 layers (black, white)
**Paint order**: Black first, then white on top

#### 3-Color Stencil (Shadow/Midtone/Highlight)

Best for portraits with depth:

```bash
stencilify generate portrait.png \
  --palette #000000 \
  --palette #666666 \
  --palette #ffffff
```

**Output**: 3 layers (black, gray, white)
**Paint order**: Black → Gray → White

#### 4-Color Stencil (Full Tonal Range)

Maximum detail and smooth gradients:

```bash
stencilify generate portrait.png \
  --palette #000000 \
  --palette #555555 \
  --palette #aaaaaa \
  --palette #ffffff
```

**Output**: 4 layers with smooth tonal transitions
**Paint order**: Darkest to lightest (auto-sorted by luminance)

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

### Lock Masks (Manual Layer Control)

Sometimes you want manual control over specific layers. Lock masks let you provide pre-made stencils for certain colors:

```bash
# Create a manual background layer, let stencilify handle foreground
stencilify generate portrait.png \
  --palette #000000,#ffffff \
  --lock "#000000=my_background.png"
```

**Lock mask workflow**:

1. Create a binary PNG mask in any editor (GIMP, Photoshop, etc.)
2. White = cut, Black = keep (same as output masks)
3. Must match input image dimensions
4. Lock it with `--lock COLOR=PATH`

**Use cases**:
- Manual backgrounds or borders
- Preserve specific details that autotune misses
- Artistic control over specific layers
- Import stencils from other sources

See `examples/how_to_make_lock_masks.md` for detailed workflow.

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

## Troubleshooting

### Common Issues and Solutions

#### Problem: Tiny details are getting cut

**Symptoms**: Small features disappear, fine lines are removed

**Solution**: Decrease `--min-feature-mm`

```bash
# Default is 2.0mm, try smaller values
stencilify generate input.png --palette ... --min-feature-mm 1.5
```

#### Problem: Floating disconnected pieces

**Symptoms**: Small islands that will fall out when cut

**Solution**: Increase `--min-island-area-mm2` to remove them

```bash
# Default is 25mm², increase to remove more islands
stencilify generate input.png --palette ... --min-island-area-mm2 50.0
```

Or adjust `--bridge-width-mm` to connect them:

```bash
# Default is 1.0mm, increase for wider bridges
stencilify generate input.png --palette ... --bridge-width-mm 1.5
```

#### Problem: Output doesn't match image colors well

**Symptoms**: Wrong colors assigned to regions, poor color accuracy

**Solution**: Enable `--autotune` to search for better parameters

```bash
stencilify generate input.png --palette ... --autotune
```

Autotune tests 108 parameter combinations and picks the best one based on color accuracy, cutout complexity, and island count.

#### Problem: Cut paths are too complex

**Symptoms**: Cutting takes forever, jagged edges

**Solution**: Use potrace backend for smoother vectors

```bash
stencilify generate input.png --palette ... --vector-backend potrace
```

Requires `potrace` installed: `apt-get install potrace` or `brew install potrace`

#### Problem: Need reproducible results

**Solution**: Set a random seed

```bash
stencilify generate input.png --palette ... --seed 42
```

### Parameter Tuning Guide

| Parameter              | Lower Value                          | Higher Value                        |
| ---------------------- | ------------------------------------ | ----------------------------------- |
| `--min-feature-mm`     | Keep more detail, harder to cut      | Remove detail, easier to cut        |
| `--min-island-area-mm2`| Keep small islands (needs bridges)   | Remove small islands                |
| `--bridge-width-mm`    | Thin bridges, more delicate          | Wide bridges, more structural       |
| `--margin-mm`          | Less margin, larger artwork          | More margin, smaller artwork        |

**Pro tip**: Start with defaults, then adjust one parameter at a time while examining the output.

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
