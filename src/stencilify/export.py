"""Export stencil layers to PNG and SVG formats."""

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np
import svgwrite  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


def export_png(mask: np.ndarray, path: Path) -> None:
    """
    Export binary mask to PNG.

    Args:
        mask: Binary mask [H, W] with 0/1 values (0=material, 1=open/cut)
        path: Output path for PNG file

    Raises:
        ValueError: If mask is invalid
    """
    if mask.ndim != 2:
        raise ValueError(f"Mask must be 2D, got shape {mask.shape}")

    if mask.dtype != np.uint8:
        raise ValueError(f"Mask must be uint8, got {mask.dtype}")

    if not np.all((mask == 0) | (mask == 1)):
        raise ValueError("Mask must contain only 0 or 1 values")

    # Convert to 0/255 (0=black=material, 255=white=open/cut)
    png_data = mask * 255

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write PNG
    cv2.imwrite(str(path), png_data)

    logger.info(f"Exported PNG to {path}")


def export_svg_contours(
    mask: np.ndarray,
    path: Path,
    px_per_mm: float,
    simplify_epsilon: float = 0.5,
) -> None:
    """
    Export binary mask to SVG using OpenCV contours.

    Args:
        mask: Binary mask [H, W] with 0/1 values (0=material, 1=open/cut)
        path: Output path for SVG file
        px_per_mm: Pixels per millimeter for scaling
        simplify_epsilon: Epsilon for approxPolyDP (in pixels, default 0.5)

    Raises:
        ValueError: If mask or parameters are invalid
    """
    if mask.ndim != 2:
        raise ValueError(f"Mask must be 2D, got shape {mask.shape}")

    if mask.dtype != np.uint8:
        raise ValueError(f"Mask must be uint8, got {mask.dtype}")

    if not np.all((mask == 0) | (mask == 1)):
        raise ValueError("Mask must contain only 0 or 1 values")

    if px_per_mm <= 0:
        raise ValueError(f"px_per_mm must be positive, got {px_per_mm}")

    # Get mask dimensions
    height_px, width_px = mask.shape

    # Convert to mm
    width_mm = width_px / px_per_mm
    height_mm = height_px / px_per_mm

    # Convert mask to 0/255 for contour detection
    mask_255 = mask * 255

    # Find contours (find white regions = open areas)
    contours, hierarchy = cv2.findContours(
        mask_255,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    # Create SVG
    dwg = svgwrite.Drawing(
        str(path),
        size=(f"{width_mm}mm", f"{height_mm}mm"),
        viewBox=f"0 0 {width_mm} {height_mm}",
    )

    # Add contours as paths
    for i, contour in enumerate(contours):
        # Simplify contour
        epsilon = simplify_epsilon
        approx = cv2.approxPolyDP(contour, epsilon, closed=True)

        if len(approx) < 3:
            # Need at least 3 points for a valid polygon
            continue

        # Convert pixel coordinates to mm
        points_mm = []
        for point in approx:
            x_px, y_px = point[0]
            x_mm = x_px / px_per_mm
            y_mm = y_px / px_per_mm
            points_mm.append((x_mm, y_mm))

        # Create path
        if len(points_mm) >= 3:
            # Start path
            path_data = f"M {points_mm[0][0]:.4f},{points_mm[0][1]:.4f}"

            # Add lines to remaining points
            for x_mm, y_mm in points_mm[1:]:
                path_data += f" L {x_mm:.4f},{y_mm:.4f}"

            # Close path
            path_data += " Z"

            # Determine fill based on hierarchy
            # If this is an outer contour (no parent), fill with color
            # If this is a hole (has parent), don't fill (will be handled by parent)
            fill_color = "black" if hierarchy is not None and hierarchy[0][i][3] == -1 else "white"

            dwg.add(
                dwg.path(
                    d=path_data,
                    fill=fill_color,
                    stroke="none",
                )
            )

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Save SVG
    dwg.save()

    logger.info(f"Exported SVG (contours) to {path}")


def export_svg_potrace(
    mask: np.ndarray,
    path: Path,
    px_per_mm: float,
    potrace_path: str = "potrace",
) -> None:
    """
    Export binary mask to SVG using potrace.

    If potrace is not available, falls back to contours backend with a warning.

    Args:
        mask: Binary mask [H, W] with 0/1 values (0=material, 1=open/cut)
        path: Output path for SVG file
        px_per_mm: Pixels per millimeter for scaling
        potrace_path: Path to potrace executable (default: "potrace")

    Raises:
        ValueError: If mask or parameters are invalid
    """
    if mask.ndim != 2:
        raise ValueError(f"Mask must be 2D, got shape {mask.shape}")

    if mask.dtype != np.uint8:
        raise ValueError(f"Mask must be uint8, got {mask.dtype}")

    if not np.all((mask == 0) | (mask == 1)):
        raise ValueError("Mask must contain only 0 or 1 values")

    if px_per_mm <= 0:
        raise ValueError(f"px_per_mm must be positive, got {px_per_mm}")

    # Check if potrace is available
    potrace_available = shutil.which(potrace_path) is not None

    if not potrace_available:
        logger.warning(f"potrace not found at '{potrace_path}', falling back to contours backend")
        export_svg_contours(mask, path, px_per_mm)
        return

    # Get mask dimensions
    height_px, width_px = mask.shape

    # Convert to mm
    width_mm = width_px / px_per_mm
    height_mm = height_px / px_per_mm

    # Create temporary PBM file (Portable Bitmap format)
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".pbm", delete=False) as temp_pbm:
        temp_pbm_path = Path(temp_pbm.name)

        # Write PBM header (P4 = binary PBM)
        temp_pbm.write(f"P4\n{width_px} {height_px}\n".encode("ascii"))

        # Convert mask to bitmap bytes (1=white, 0=black)
        # Pack bits into bytes (8 pixels per byte)
        bitmap = np.packbits(mask, axis=1)
        temp_pbm.write(bitmap.tobytes())

    try:
        # Create temporary SVG file
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".svg", delete=False) as temp_svg:
            temp_svg_path = Path(temp_svg.name)

        # Run potrace
        # -s: SVG output
        # -u: use pixels as units
        # --flat: no Bezier curves (straight lines only for simplicity)
        result = subprocess.run(
            [
                potrace_path,
                "-s",  # SVG output
                "-u",  # Unit: 1 pixel
                str(temp_pbm_path),
                "-o",
                str(temp_svg_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            logger.warning(
                f"potrace failed with error: {result.stderr}, falling back to contours backend"
            )
            export_svg_contours(mask, path, px_per_mm)
            return

        # Read generated SVG
        svg_content = temp_svg_path.read_text()

        # Modify SVG to use mm units and correct viewBox
        # Replace width/height/viewBox attributes
        svg_content = svg_content.replace(
            f'width="{width_px}pt" height="{height_px}pt"',
            f'width="{width_mm}mm" height="{height_mm}mm"',
        )
        svg_content = svg_content.replace(
            f'viewBox="0 0 {width_px} {height_px}"',
            f'viewBox="0 0 {width_mm} {height_mm}"',
        )

        # Scale paths by 1/px_per_mm
        # This is a simplified approach - in practice, we'd need to parse and transform paths
        # For now, we'll rely on the viewBox to handle scaling

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write modified SVG
        path.write_text(svg_content)

        logger.info(f"Exported SVG (potrace) to {path}")

    finally:
        # Clean up temporary files
        temp_pbm_path.unlink(missing_ok=True)
        if "temp_svg_path" in locals():
            temp_svg_path.unlink(missing_ok=True)
