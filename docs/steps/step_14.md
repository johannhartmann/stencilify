# Step 14: Optional GPU Capability

Add optional GPU acceleration without making it a hard dependency.

## Goal

Make it possible to use GPU where it's easy (e.g., color conversion, blurs) while keeping CPU as default and ensuring the project runs without GPU packages installed.

## Requirements

- GPU packages (torch, kornia) are **optional dependencies**
- Install with: `uv sync --extra gpu`
- Project works perfectly without GPU packages
- Graceful fallback from CUDA to CPU when GPU not available
- Add `--device` CLI flag (cpu, cuda, auto)
- Log which device is being used
- Document what operations stay on CPU and why

## Implementation

### 1. Optional Dependencies

Added `gpu` optional dependency group in `pyproject.toml`:

```toml
[project.optional-dependencies]
gpu = [
    "torch>=2.0.0",
    "kornia>=0.7.0",
]
```

### 2. Compute Backend (`src/stencilify/compute.py`)

Created device adapter with graceful fallback:

- `Device` enum: CPU, CUDA, AUTO
- `get_device()`: Device selection with fallback logic
- `bilateral_filter()`: Edge-preserving smoothing (GPU/CPU)
- `gaussian_blur()`: Gaussian blurring (GPU/CPU)
- `rgb_to_lab_batch()`: Batch color space conversion (GPU/CPU)

All functions include:
- Try/except blocks for GPU operations
- Automatic fallback to CPU implementations
- Logging for device selection and fallbacks

### 3. Configuration

- Added `device` field to `PipelineConfig` (default: "cpu")
- Added validator to ensure device is one of: cpu, cuda, auto
- Device is validated and normalized to lowercase

### 4. CLI Integration

- Added `--device` flag to `generate` command
- Options: cpu (default), cuda, auto
- Case-insensitive input
- Device is passed through configuration to pipeline

### 5. Pipeline Integration

- Pipeline detects and logs device at startup
- Device information available for future optimizations
- Current pipeline operations remain on CPU (see below)

### 6. Testing

Added 12 comprehensive tests in `tests/test_compute.py`:

- Device enum and selection
- Bilateral filter on CPU (RGB and grayscale)
- Gaussian blur on CPU (RGB and grayscale)
- Edge preservation and smoothing properties
- Different parameter configurations
- All tests pass without GPU packages installed

### 7. Documentation

Updated `README.md` with:

- GPU installation instructions
- Device flag usage examples
- Explanation of CPU-only operations
- GPU acceleration benefits and limitations

## Operations on CPU vs GPU

### GPU-Accelerated (Optional)

When `--device cuda` or `--device auto` with CUDA available:

- **Bilateral filtering**: Edge-preserving smoothing (kornia.filters.bilateral_blur)
- **Gaussian blurring**: Standard blurring (kornia.filters.gaussian_blur2d)
- **Batch color conversion**: RGB to Lab conversion (kornia.color.rgb_to_lab)

### CPU-Only (Always)

These operations remain on CPU regardless of device setting:

- **SLIC superpixels**: Complex scikit-image implementation, CPU-optimized
- **Connected components**: OpenCV cv2.connectedComponents, CPU-optimized
- **Contour extraction**: OpenCV cv2.findContours, CPU-optimized
- **Morphological operations**: OpenCV operations, CPU-optimized

**Rationale**: These operations have complex dependencies and highly-optimized CPU implementations. The overhead of GPU transfer would likely negate any performance benefits.

## Usage

### CPU (Default)

```bash
stencilify generate input.png --palette #000000,#ffffff
```

### Explicit CUDA

```bash
stencilify generate input.png --palette #000000,#ffffff --device cuda
```

Falls back to CPU if CUDA unavailable or GPU packages not installed.

### Auto-detect

```bash
stencilify generate input.png --palette #000000,#ffffff --device auto
```

Automatically uses CUDA if available, otherwise CPU.

## Files Changed

- `pyproject.toml`: Added gpu optional dependencies
- `src/stencilify/compute.py`: New device adapter module
- `src/stencilify/config.py`: Added device field and validator
- `src/stencilify/cli.py`: Added --device flag
- `src/stencilify/pipeline.py`: Added device detection and logging
- `tests/test_compute.py`: New tests for compute module
- `README.md`: Added GPU documentation

## Test Results

- **322 tests pass** (310 existing + 12 new)
- All tests pass **without GPU packages installed**
- Graceful fallback verified
- mypy: ✓ No type errors
- ruff: ✓ No linting errors

## Acceptance Criteria

✓ GPU packages are optional, not required
✓ Project installs and runs without GPU packages
✓ `--device` CLI flag added (cpu, cuda, auto)
✓ Device detection logs which device is being used
✓ Graceful fallback from CUDA to CPU
✓ CPU-only operations documented with rationale
✓ Comprehensive tests added
✓ README updated with GPU instructions
✓ All existing tests still pass

## Notes

- GPU acceleration is infrastructure for future optimizations
- Current pipeline doesn't actively use GPU-accelerated operations
- The compute functions are available for preprocessing or future features
- CUDA device selection is validated at runtime (not config validation)
