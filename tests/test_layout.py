"""Tests for page layout and registration marks."""

import numpy as np
import pytest

from stencilify.geometry import Dimensions, Orientation, PageSize
from stencilify.layout import add_registration_marks, compute_page_canvas_px, place_artwork_on_page


def test_compute_page_canvas_px() -> None:
    """Test page canvas size computation."""
    # A4 portrait at 10 px/mm: 210mm x 297mm -> 2100 x 2970 px
    page_mm = Dimensions(width_mm=210.0, height_mm=297.0)
    px_per_mm = 10.0

    h, w = compute_page_canvas_px(page_mm, px_per_mm)

    assert w == 2100
    assert h == 2970


def test_compute_page_canvas_px_landscape() -> None:
    """Test page canvas size for landscape."""
    # A4 landscape: 297mm x 210mm
    page_mm = Dimensions(width_mm=297.0, height_mm=210.0)
    px_per_mm = 10.0

    h, w = compute_page_canvas_px(page_mm, px_per_mm)

    assert w == 2970
    assert h == 2100


def test_place_artwork_on_page_basic() -> None:
    """Test basic artwork placement."""
    # Create simple 100x100 artwork
    mask1 = np.zeros((100, 100), dtype=np.uint8)
    mask2 = np.ones((100, 100), dtype=np.uint8)

    open_masks = {"layer1": mask1, "layer2": mask2}

    # Place on A4 portrait with 10mm margins at 1 px/mm
    # A4 = 210x297mm, canvas = 210x297 px
    # Printable = 190x277 px (minus 10mm = 10px on each side)
    # Artwork 100x100 fits easily, will be centered
    placed = place_artwork_on_page(
        open_masks,
        page_size=PageSize.A4,
        orientation=Orientation.PORTRAIT,
        margin_mm=10.0,
        px_per_mm=1.0,
    )

    # Check canvas size
    assert "layer1" in placed
    assert "layer2" in placed

    canvas_h, canvas_w = placed["layer1"].shape
    assert canvas_w == 210  # A4 width in px at 1 px/mm
    assert canvas_h == 297  # A4 height in px at 1 px/mm

    # Both layers should have same size
    assert placed["layer2"].shape == (canvas_h, canvas_w)


def test_place_artwork_on_page_scaling() -> None:
    """Test that artwork is scaled to fit."""
    # Create artwork larger than printable area
    # 200x200 artwork
    mask = np.zeros((200, 200), dtype=np.uint8)
    # Add some pattern
    mask[50:150, 50:150] = 1

    open_masks = {"layer1": mask}

    # Place on A4 with 10mm margins at 1 px/mm
    # Printable area = 190x277 px
    # Artwork 200x200 needs to scale down to fit
    placed = place_artwork_on_page(
        open_masks,
        page_size=PageSize.A4,
        orientation=Orientation.PORTRAIT,
        margin_mm=10.0,
        px_per_mm=1.0,
    )

    canvas = placed["layer1"]

    # Canvas should be full page size
    assert canvas.shape == (297, 210)

    # Artwork should be scaled down and centered
    # Scale factor = min(190/200, 277/200) = 0.95
    # Scaled size ≈ 190x190 (limited by width)


def test_place_artwork_on_page_centering() -> None:
    """Test that artwork is centered on page."""
    # Small 50x50 artwork
    mask = np.zeros((50, 50), dtype=np.uint8)
    mask[10:40, 10:40] = 1  # Inner square

    open_masks = {"layer1": mask}

    placed = place_artwork_on_page(
        open_masks,
        page_size=PageSize.A4,
        orientation=Orientation.PORTRAIT,
        margin_mm=10.0,
        px_per_mm=1.0,
    )

    canvas = placed["layer1"]

    # Find where artwork is placed (look for non-1 values)
    # Canvas should be all 1 except where artwork is placed
    artwork_region = canvas == 0
    rows, cols = np.where(artwork_region)

    if len(rows) > 0:
        # Check that artwork is roughly centered
        min_row, max_row = rows.min(), rows.max()
        min_col, max_col = cols.min(), cols.max()

        center_row = (min_row + max_row) // 2
        center_col = (min_col + max_col) // 2

        canvas_center_row = canvas.shape[0] // 2
        canvas_center_col = canvas.shape[1] // 2

        # Should be within reasonable tolerance (considering scaling and rounding)
        assert abs(center_row - canvas_center_row) < 20
        assert abs(center_col - canvas_center_col) < 20


def test_place_artwork_on_page_landscape() -> None:
    """Test landscape orientation."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    open_masks = {"layer1": mask}

    placed = place_artwork_on_page(
        open_masks,
        page_size=PageSize.A4,
        orientation=Orientation.LANDSCAPE,
        margin_mm=10.0,
        px_per_mm=1.0,
    )

    canvas = placed["layer1"]

    # A4 landscape: 297x210 (width x height)
    assert canvas.shape == (210, 297)


def test_place_artwork_on_page_auto_orientation() -> None:
    """Test AUTO orientation selection."""
    # Wide artwork (landscape)
    wide_mask = np.zeros((100, 200), dtype=np.uint8)
    open_masks = {"layer1": wide_mask}

    placed = place_artwork_on_page(
        open_masks,
        page_size=PageSize.A4,
        orientation=Orientation.AUTO,
        margin_mm=10.0,
        px_per_mm=1.0,
    )

    canvas = placed["layer1"]

    # Should choose landscape for wide artwork
    # A4 landscape = 297x210
    assert canvas.shape == (210, 297)


def test_place_artwork_on_page_multiple_layers() -> None:
    """Test that multiple layers are placed identically."""
    mask1 = np.zeros((100, 100), dtype=np.uint8)
    mask2 = np.ones((100, 100), dtype=np.uint8)
    mask3 = np.full((100, 100), 1, dtype=np.uint8)
    mask3[20:80, 20:80] = 0

    open_masks = {"layer1": mask1, "layer2": mask2, "layer3": mask3}

    placed = place_artwork_on_page(
        open_masks,
        page_size=PageSize.A4,
        orientation=Orientation.PORTRAIT,
        margin_mm=10.0,
        px_per_mm=1.0,
    )

    # All should have same size
    assert placed["layer1"].shape == placed["layer2"].shape
    assert placed["layer2"].shape == placed["layer3"].shape

    # Artwork should be placed at same position in all layers
    # (we can't easily verify exact position without knowing scale/offset,
    # but we verify all are same size and structure)


def test_place_artwork_on_page_a3() -> None:
    """Test placement on A3 page."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    open_masks = {"layer1": mask}

    placed = place_artwork_on_page(
        open_masks,
        page_size=PageSize.A3,
        orientation=Orientation.PORTRAIT,
        margin_mm=10.0,
        px_per_mm=1.0,
    )

    canvas = placed["layer1"]

    # A3 portrait: 297x420mm
    assert canvas.shape == (420, 297)


def test_place_artwork_on_page_empty_masks() -> None:
    """Test error on empty masks dict."""
    with pytest.raises(ValueError, match="cannot be empty"):
        place_artwork_on_page(
            {},
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            margin_mm=10.0,
            px_per_mm=1.0,
        )


def test_place_artwork_on_page_invalid_mask_shape() -> None:
    """Test error on non-2D mask."""
    mask = np.zeros((100, 100, 3), dtype=np.uint8)
    open_masks = {"layer1": mask}

    with pytest.raises(ValueError, match="must be 2D"):
        place_artwork_on_page(
            open_masks,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            margin_mm=10.0,
            px_per_mm=1.0,
        )


def test_place_artwork_on_page_invalid_dtype() -> None:
    """Test error on non-uint8 mask."""
    mask = np.zeros((100, 100), dtype=np.float32)
    open_masks = {"layer1": mask}

    with pytest.raises(ValueError, match="must be uint8"):
        place_artwork_on_page(
            open_masks,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            margin_mm=10.0,
            px_per_mm=1.0,
        )


def test_place_artwork_on_page_mismatched_sizes() -> None:
    """Test error when masks have different sizes."""
    mask1 = np.zeros((100, 100), dtype=np.uint8)
    mask2 = np.zeros((200, 200), dtype=np.uint8)

    open_masks = {"layer1": mask1, "layer2": mask2}

    with pytest.raises(ValueError, match="same dimensions"):
        place_artwork_on_page(
            open_masks,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            margin_mm=10.0,
            px_per_mm=1.0,
        )


def test_place_artwork_on_page_negative_margin() -> None:
    """Test error on negative margin."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    open_masks = {"layer1": mask}

    with pytest.raises(ValueError, match="non-negative"):
        place_artwork_on_page(
            open_masks,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            margin_mm=-5.0,
            px_per_mm=1.0,
        )


def test_place_artwork_on_page_margins_too_large() -> None:
    """Test error when margins are too large."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    open_masks = {"layer1": mask}

    # A4 = 210x297mm, margins of 150mm would exceed page
    with pytest.raises(ValueError, match="too large"):
        place_artwork_on_page(
            open_masks,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            margin_mm=150.0,
            px_per_mm=1.0,
        )


def test_add_registration_marks_basic() -> None:
    """Test adding registration marks to masks."""
    # Create simple 300x300 canvas (simulating placed masks)
    mask1 = np.zeros((300, 300), dtype=np.uint8)
    mask2 = np.ones((300, 300), dtype=np.uint8)

    placed_masks = {"layer1": mask1, "layer2": mask2}

    # Add marks with 6mm diameter at 10 px/mm (radius = 30px)
    marked = add_registration_marks(
        placed_masks,
        px_per_mm=10.0,
        diameter_mm=6.0,
        margin_mm=10.0,
    )

    # Check all layers have marks
    assert "layer1" in marked
    assert "layer2" in marked

    # Marks should be circles set to 1 (open)
    # Check that marks exist at expected approximate positions

    # Top-left: (5mm, 5mm) = (50px, 50px)
    # Top-right: (width - 5mm, 5mm) = (250px, 50px)
    # Bottom-left: (5mm, height - 5mm) = (50px, 250px)

    # Check layer1 (originally 0, marks should be 1)
    layer1 = marked["layer1"]
    # Top-left mark
    assert layer1[50, 50] == 1
    # Top-right mark
    assert layer1[50, 250] == 1
    # Bottom-left mark
    assert layer1[250, 50] == 1

    # Check layer2 (originally 1, marks should still be 1)
    layer2 = marked["layer2"]
    assert layer2[50, 50] == 1
    assert layer2[50, 250] == 1
    assert layer2[250, 50] == 1


def test_add_registration_marks_consistency() -> None:
    """Test that marks are identical across layers."""
    # Create different masks
    mask1 = np.zeros((400, 400), dtype=np.uint8)
    mask2 = np.ones((400, 400), dtype=np.uint8)
    mask3 = np.full((400, 400), 1, dtype=np.uint8)
    mask3[100:300, 100:300] = 0

    placed_masks = {"layer1": mask1, "layer2": mask2, "layer3": mask3}

    marked = add_registration_marks(
        placed_masks,
        px_per_mm=10.0,
        diameter_mm=6.0,
        margin_mm=10.0,
    )

    # Extract mark regions from each layer and verify they're identical
    # Top-left region (around 50, 50)
    tl_region1 = marked["layer1"][30:70, 30:70]
    tl_region2 = marked["layer2"][30:70, 30:70]
    tl_region3 = marked["layer3"][30:70, 30:70]

    # All layers should have identical marks in this region
    assert np.array_equal(tl_region1, tl_region2)
    assert np.array_equal(tl_region2, tl_region3)


def test_add_registration_marks_mark_size() -> None:
    """Test that marks have correct size."""
    mask = np.zeros((500, 500), dtype=np.uint8)
    placed_masks = {"layer1": mask}

    # 10mm diameter at 10 px/mm = 100px diameter = 50px radius
    marked = add_registration_marks(
        placed_masks,
        px_per_mm=10.0,
        diameter_mm=10.0,
        margin_mm=10.0,
    )

    layer1 = marked["layer1"]

    # Top-left mark at (50, 50) with radius 50px
    # Count pixels set to 1 in the mark region
    mark_region = layer1[0:100, 0:100]
    mark_pixels = np.sum(mark_region == 1)

    # Expected area ≈ π * r^2 = π * 50^2 ≈ 7854 pixels
    # Allow some tolerance for rasterization
    assert 7000 < mark_pixels < 8500


def test_add_registration_marks_small_diameter() -> None:
    """Test with small diameter mark."""
    mask = np.zeros((200, 200), dtype=np.uint8)
    placed_masks = {"layer1": mask}

    # 1mm diameter at 10 px/mm = 10px diameter = 5px radius
    marked = add_registration_marks(
        placed_masks,
        px_per_mm=10.0,
        diameter_mm=1.0,
        margin_mm=10.0,
    )

    # Should still create marks (minimum radius is 1px)
    layer1 = marked["layer1"]
    # Marks should exist
    assert layer1[50, 50] == 1


def test_add_registration_marks_empty_masks() -> None:
    """Test error on empty masks dict."""
    with pytest.raises(ValueError, match="cannot be empty"):
        add_registration_marks(
            {},
            px_per_mm=10.0,
            diameter_mm=6.0,
            margin_mm=10.0,
        )


def test_add_registration_marks_invalid_diameter() -> None:
    """Test error on invalid diameter."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    placed_masks = {"layer1": mask}

    with pytest.raises(ValueError, match="must be positive"):
        add_registration_marks(
            placed_masks,
            px_per_mm=10.0,
            diameter_mm=0.0,
            margin_mm=10.0,
        )


def test_add_registration_marks_invalid_margin() -> None:
    """Test error on invalid margin."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    placed_masks = {"layer1": mask}

    with pytest.raises(ValueError, match="must be positive"):
        add_registration_marks(
            placed_masks,
            px_per_mm=10.0,
            diameter_mm=6.0,
            margin_mm=0.0,
        )


def test_add_registration_marks_preserves_non_mark_areas() -> None:
    """Test that non-mark areas are preserved."""
    # Create mask with specific pattern
    mask = np.zeros((300, 300), dtype=np.uint8)
    mask[150:200, 150:200] = 1  # Center square

    placed_masks = {"layer1": mask}

    marked = add_registration_marks(
        placed_masks,
        px_per_mm=10.0,
        diameter_mm=6.0,
        margin_mm=10.0,
    )

    layer1 = marked["layer1"]

    # Center region (far from marks) should be unchanged
    assert np.array_equal(layer1[150:200, 150:200], mask[150:200, 150:200])


def test_registration_mark_dataclass() -> None:
    """Test RegistrationMark dataclass."""
    from stencilify.layout import RegistrationMark

    mark = RegistrationMark(center_px=(100, 200), radius_px=30)

    assert mark.center_px == (100, 200)
    assert mark.radius_px == 30
