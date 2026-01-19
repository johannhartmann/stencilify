"""Configuration models for the stencilify pipeline."""

import re
from enum import Enum
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

from stencilify.geometry import Orientation, PageSize


class Color:
    """RGB color representation."""

    def __init__(self, r: int, g: int, b: int) -> None:
        """
        Create a color from RGB values.

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
        """
        self.r = r
        self.g = g
        self.b = b

    @classmethod
    def from_hex(cls, hex_string: str) -> "Color":
        """
        Parse a hex color string.

        Args:
            hex_string: Hex color like #RRGGBB or RRGGBB

        Returns:
            Color instance

        Raises:
            ValueError: If the hex string is invalid
        """
        hex_string = hex_string.strip()
        if hex_string.startswith("#"):
            hex_string = hex_string[1:]

        if not re.match(r"^[0-9A-Fa-f]{6}$", hex_string):
            raise ValueError(f"Invalid hex color: #{hex_string}. Expected format: #RRGGBB")

        r = int(hex_string[0:2], 16)
        g = int(hex_string[2:4], 16)
        b = int(hex_string[4:6], 16)

        return cls(r, g, b)

    def to_hex(self) -> str:
        """
        Convert color to hex string.

        Returns:
            Hex string like #RRGGBB
        """
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def luminance(self) -> float:
        """
        Calculate relative luminance (ITU-R BT.709).

        Returns:
            Luminance value in range [0, 1]
        """
        # ITU-R BT.709 coefficients
        return 0.2126 * (self.r / 255.0) + 0.7152 * (self.g / 255.0) + 0.0722 * (self.b / 255.0)

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, Color):
            return False
        return self.r == other.r and self.g == other.g and self.b == other.b

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.r, self.g, self.b))

    def __repr__(self) -> str:
        """String representation."""
        return f"Color({self.to_hex()})"


class PaintOrder(str, Enum):
    """Paint order for layers."""

    AUTO = "auto"
    GIVEN = "given"


class VectorBackend(str, Enum):
    """Vector export backend."""

    CONTOURS = "contours"
    POTRACE = "potrace"


class LockSpec(BaseModel):
    """Specification for locked layer (pre-existing mask)."""

    color: str = Field(..., description="Hex color for this locked layer")
    mask_path: Path = Field(..., description="Path to binary mask PNG")

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Validate hex color format."""
        # Will raise ValueError if invalid
        Color.from_hex(v)
        return v

    @field_validator("mask_path")
    @classmethod
    def validate_mask_path(cls, v: Path) -> Path:
        """Validate mask path exists."""
        if not v.exists():
            raise ValueError(f"Mask file does not exist: {v}")
        if not v.is_file():
            raise ValueError(f"Mask path is not a file: {v}")
        return v


class PageSpec(BaseModel):
    """Page size and layout configuration."""

    size: PageSize = Field(default=PageSize.A4, description="Page size (A4, A3, A2)")
    orientation: Orientation = Field(
        default=Orientation.AUTO,
        description="Page orientation (portrait, landscape, auto)",
    )
    margin_mm: Annotated[float, Field(ge=0.0)] = Field(
        default=10.0,
        description="Margin in millimeters (applied to all edges)",
    )


class ExportConfig(BaseModel):
    """Export and output configuration."""

    vector_backend: VectorBackend = Field(
        default=VectorBackend.CONTOURS,
        description="Vector export backend (contours, potrace)",
    )
    output_dir: Path = Field(
        default=Path("out"),
        description="Output directory for generated files",
    )


class AutotuneConfig(BaseModel):
    """Autotune configuration."""

    enabled: bool = Field(default=False, description="Enable autotune mode")
    # Future: Add specific autotune parameters here


class CuttabilityConfig(BaseModel):
    """Cuttability optimization parameters."""

    min_feature_mm: Annotated[float, Field(gt=0.0)] = Field(
        default=2.0,
        description="Minimum feature size in millimeters",
    )
    min_island_area_mm2: Annotated[float, Field(ge=0.0)] = Field(
        default=25.0,
        description="Minimum island area in square millimeters (0 disables island removal)",
    )
    bridge_width_mm: Annotated[float, Field(ge=0.0)] = Field(
        default=1.0,
        description="Bridge width in millimeters (0 disables bridges)",
    )


class PipelineConfig(BaseModel):
    """Complete pipeline configuration."""

    # Input/output
    input_image: Path = Field(..., description="Path to input RGBA image")
    export: ExportConfig = Field(
        default_factory=ExportConfig,
        description="Export configuration",
    )

    # Palette
    palette: list[str] = Field(
        ...,
        min_length=2,
        max_length=4,
        description="Palette colors as hex strings (#RRGGBB)",
    )
    paint_order: PaintOrder = Field(
        default=PaintOrder.AUTO,
        description="Paint order: auto (sort by luminance) or given",
    )

    # Page layout
    page: PageSpec = Field(
        default_factory=PageSpec,
        description="Page size and layout",
    )

    # Cuttability
    cuttability: CuttabilityConfig = Field(
        default_factory=CuttabilityConfig,
        description="Cuttability optimization parameters",
    )

    # Locks (optional pre-existing masks)
    locks: list[LockSpec] = Field(
        default_factory=list,
        description="Locked layers (pre-existing masks)",
    )

    # Autotune
    autotune: AutotuneConfig = Field(
        default_factory=AutotuneConfig,
        description="Autotune configuration",
    )

    # Random seed
    seed: int | None = Field(
        default=None,
        description="Random seed for deterministic results",
    )

    # Compute device
    device: str = Field(
        default="cpu",
        description="Compute device: cpu, cuda, or auto",
    )

    @field_validator("device")
    @classmethod
    def validate_device(cls, v: str) -> str:
        """Validate device is one of cpu, cuda, or auto."""
        v_lower = v.lower()
        if v_lower not in ("cpu", "cuda", "auto"):
            raise ValueError(
                f"Invalid device '{v}'. Must be one of: cpu, cuda, auto"
            )
        return v_lower

    @field_validator("palette")
    @classmethod
    def validate_palette_colors(cls, v: list[str]) -> list[str]:
        """Validate all palette colors are valid hex."""
        for color_str in v:
            try:
                Color.from_hex(color_str)
            except ValueError as e:
                raise ValueError(f"Invalid palette color '{color_str}': {e}") from e
        return v

    @field_validator("input_image")
    @classmethod
    def validate_input_exists(cls, v: Path) -> Path:
        """Validate input image exists."""
        if not v.exists():
            raise ValueError(f"Input image does not exist: {v}")
        if not v.is_file():
            raise ValueError(f"Input path is not a file: {v}")
        return v

    @model_validator(mode="after")
    def validate_palette_length(self) -> "PipelineConfig":
        """Validate palette has 2-4 colors."""
        if not (2 <= len(self.palette) <= 4):
            raise ValueError(
                f"Palette must contain 2-4 colors, got {len(self.palette)}. "
                f"Please provide between 2 and 4 hex colors."
            )
        return self

    def get_sorted_palette(self) -> list[Color]:
        """
        Get palette colors sorted according to paint_order.

        Returns:
            List of Color objects, sorted dark to light if paint_order is AUTO
        """
        colors = [Color.from_hex(hex_str) for hex_str in self.palette]

        if self.paint_order == PaintOrder.AUTO:
            # Sort by luminance: darkest first (ascending luminance)
            colors.sort(key=lambda c: c.luminance())

        return colors
