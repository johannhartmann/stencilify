"""Constants for stencilify."""

from pathlib import Path

# Version
__version__ = "0.1.0"

# Default output directory
DEFAULT_OUTPUT_DIR = Path("out")

# Supported paper sizes (in mm)
PAPER_SIZES = {
    "A4": (210, 297),
    "A3": (297, 420),
    "A2": (420, 594),
}

# Layer configuration
MIN_LAYERS = 2
MAX_LAYERS = 4

# Default DPI for output
DEFAULT_DPI = 300

# Minimum feature size (in pixels at DEFAULT_DPI)
MIN_FEATURE_SIZE_MM = 2.0  # 2mm minimum feature size for cutting
