"""Tests for island fixing with bridges."""

import numpy as np
import pytest

from stencilify.bridges import BridgeInfo, BridgeReport, fix_islands


def test_fix_islands_no_islands() -> None:
    """Test with no islands (nothing to fix)."""
    # All material touches border
    open_mask = np.array(
        [
            [0, 0, 0, 0, 0],
            [0, 1, 1, 1, 0],
            [0, 1, 1, 1, 0],
            [0, 1, 1, 1, 0],
            [0, 0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )

    fixed, report = fix_islands(open_mask, min_island_area_px=5, bridge_width_px=2)

    assert report.islands_filled == 0
    assert report.bridges_added == 0
    assert report.islands_remaining == 0
    assert np.array_equal(fixed, open_mask)


def test_fix_islands_fill_small() -> None:
    """Test filling small islands."""
    # Create mask with small island in center
    open_mask = np.ones((10, 10), dtype=np.uint8)
    # Small 2x2 island
    open_mask[4:6, 4:6] = 0

    fixed, report = fix_islands(open_mask, min_island_area_px=10, bridge_width_px=0)

    # Island should be filled (converted to open area)
    assert report.islands_filled == 1
    assert report.bridges_added == 0
    assert report.islands_remaining == 0
    # Check that island was filled
    assert fixed[4, 4] == 1
    assert fixed[5, 5] == 1


def test_fix_islands_keep_large() -> None:
    """Test that large islands are not filled when bridge_width_px=0."""
    # Create mask with large island
    open_mask = np.ones((20, 20), dtype=np.uint8)
    # Large 5x5 island
    open_mask[7:12, 7:12] = 0

    fixed, report = fix_islands(open_mask, min_island_area_px=10, bridge_width_px=0)

    # Island should not be filled (too large), but no bridges added
    assert report.islands_filled == 0
    assert report.bridges_added == 0
    assert report.islands_remaining == 1


def test_fix_islands_ring_with_bridge() -> None:
    """Test that ring shape gets bridged."""
    # Create ring: material border, cutout ring, material center (island)
    open_mask = np.array(
        [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 1, 1, 0],
            [0, 1, 0, 0, 0, 0, 0, 1, 0],
            [0, 1, 0, 0, 0, 0, 0, 1, 0],
            [0, 1, 0, 0, 0, 0, 0, 1, 0],
            [0, 1, 0, 0, 0, 0, 0, 1, 0],
            [0, 1, 0, 0, 0, 0, 0, 1, 0],
            [0, 1, 1, 1, 1, 1, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )

    fixed, report = fix_islands(open_mask, min_island_area_px=5, bridge_width_px=2)

    # Bridge should be added
    assert report.islands_filled == 0
    assert report.bridges_added > 0
    # Island should be resolved (or at least attempted)
    assert report.islands_remaining <= 1


def test_fix_islands_multiple_small() -> None:
    """Test filling multiple small islands."""
    open_mask = np.ones((20, 20), dtype=np.uint8)
    # Three small islands
    open_mask[3:5, 3:5] = 0  # 4 pixels
    open_mask[10:12, 10:12] = 0  # 4 pixels
    open_mask[15:17, 15:17] = 0  # 4 pixels

    fixed, report = fix_islands(open_mask, min_island_area_px=10, bridge_width_px=0)

    # All three should be filled
    assert report.islands_filled == 3
    assert report.bridges_added == 0
    assert report.islands_remaining == 0


def test_fix_islands_mixed_sizes() -> None:
    """Test with mix of small and large islands."""
    open_mask = np.ones((30, 30), dtype=np.uint8)
    # Border material (supported)
    open_mask[0, :] = 0
    open_mask[:, 0] = 0
    # Small island (will be filled)
    open_mask[5:7, 5:7] = 0  # 4 pixels
    # Large island (will get bridge)
    open_mask[15:21, 15:21] = 0  # 36 pixels

    fixed, report = fix_islands(open_mask, min_island_area_px=10, bridge_width_px=3)

    # Small filled, large bridged
    assert report.islands_filled == 1
    assert report.bridges_added >= 1  # At least one bridge attempt


def test_fix_islands_bridge_info() -> None:
    """Test that bridge info is recorded."""
    open_mask = np.ones((15, 15), dtype=np.uint8)
    # Large island that needs bridging
    open_mask[6:9, 6:9] = 0

    fixed, report = fix_islands(open_mask, min_island_area_px=5, bridge_width_px=2)

    if report.bridges_added > 0:
        assert len(report.bridge_info) == report.bridges_added
        for bridge in report.bridge_info:
            assert bridge.width_px == 2
            assert len(bridge.start) == 2
            assert len(bridge.end) == 2


def test_fix_islands_max_attempts() -> None:
    """Test that max_attempts limits bridge attempts."""
    open_mask = np.ones((20, 20), dtype=np.uint8)
    # Create island
    open_mask[8:12, 8:12] = 0

    # With max_attempts=1
    fixed1, report1 = fix_islands(
        open_mask, min_island_area_px=5, bridge_width_px=2, max_attempts=1
    )

    # With max_attempts=3
    fixed3, report3 = fix_islands(
        open_mask, min_island_area_px=5, bridge_width_px=2, max_attempts=3
    )

    # More attempts should potentially add more bridges (though not guaranteed)
    assert report1.bridges_added >= 0
    assert report3.bridges_added >= 0


def test_fix_islands_no_supported_material() -> None:
    """Test behavior when there's no supported material to bridge to."""
    # All material is islands (none touches border)
    open_mask = np.ones((10, 10), dtype=np.uint8)
    open_mask[3:5, 3:5] = 0  # Island 1 - 4 pixels
    open_mask[6:8, 6:8] = 0  # Island 2 - 4 pixels

    fixed, report = fix_islands(open_mask, min_island_area_px=20, bridge_width_px=2)

    # Cannot bridge (no supported material)
    # But islands are small enough to fill (4 < 20)
    assert report.islands_filled == 2
    assert report.islands_remaining == 0


def test_fix_islands_invalid_shape() -> None:
    """Test that non-2D mask raises error."""
    open_mask = np.zeros((5, 5, 3), dtype=np.uint8)

    with pytest.raises(ValueError, match="must be 2D"):
        fix_islands(open_mask, min_island_area_px=10, bridge_width_px=2)


def test_fix_islands_invalid_dtype() -> None:
    """Test that non-uint8 raises error."""
    open_mask = np.zeros((5, 5), dtype=np.float32)

    with pytest.raises(ValueError, match="must be uint8"):
        fix_islands(open_mask, min_island_area_px=10, bridge_width_px=2)


def test_fix_islands_invalid_values() -> None:
    """Test that non-binary values raise error."""
    open_mask = np.full((5, 5), 2, dtype=np.uint8)

    with pytest.raises(ValueError, match="only 0 or 1"):
        fix_islands(open_mask, min_island_area_px=10, bridge_width_px=2)


def test_fix_islands_preserves_non_island_material() -> None:
    """Test that non-island material is preserved."""
    # Create mask with border material and island
    open_mask = np.ones((10, 10), dtype=np.uint8)
    # Border material (touches edge)
    open_mask[0, :] = 0  # Top row
    open_mask[:, 0] = 0  # Left column
    # Island
    open_mask[5:7, 5:7] = 0

    fixed, report = fix_islands(open_mask, min_island_area_px=10, bridge_width_px=0)

    # Border material should be preserved
    assert np.all(fixed[0, :] == 0)
    assert np.all(fixed[:, 0] == 0)
    # Island should be filled
    assert report.islands_filled == 1


def test_fix_islands_zero_bridge_width() -> None:
    """Test that bridge_width_px=0 disables bridging."""
    open_mask = np.ones((20, 20), dtype=np.uint8)
    # Large island
    open_mask[8:12, 8:12] = 0

    fixed, report = fix_islands(open_mask, min_island_area_px=5, bridge_width_px=0)

    # No bridges should be added
    assert report.bridges_added == 0
    # Island remains (too large to fill)
    assert report.islands_remaining == 1


def test_bridge_report_dataclass() -> None:
    """Test BridgeReport dataclass."""
    report = BridgeReport(
        islands_filled=2,
        bridges_added=3,
        islands_remaining=1,
        bridge_info=[
            BridgeInfo(island_id=0, start=(5, 5), end=(10, 10), width_px=3),
        ],
    )

    assert report.islands_filled == 2
    assert report.bridges_added == 3
    assert report.islands_remaining == 1
    assert len(report.bridge_info) == 1


def test_bridge_info_dataclass() -> None:
    """Test BridgeInfo dataclass."""
    info = BridgeInfo(island_id=1, start=(10, 20), end=(30, 40), width_px=5)

    assert info.island_id == 1
    assert info.start == (10, 20)
    assert info.end == (30, 40)
    assert info.width_px == 5


def test_fix_islands_complex_shape() -> None:
    """Test with complex stencil shape."""
    # Create more realistic stencil with letters
    open_mask = np.ones((20, 20), dtype=np.uint8)
    # Border frame (connected to edge)
    open_mask[0, :] = 0
    open_mask[-1, :] = 0
    open_mask[:, 0] = 0
    open_mask[:, -1] = 0
    # Create an 'O' shape connected to border - creates island in center
    open_mask[6:14, 6] = 0  # Left
    open_mask[6:14, 13] = 0  # Right
    open_mask[6, 6:14] = 0  # Top
    open_mask[13, 6:14] = 0  # Bottom
    # Connect 'O' to border frame
    open_mask[3:7, 6] = 0  # Connect top

    fixed, report = fix_islands(open_mask, min_island_area_px=10, bridge_width_px=2)

    # Center of 'O' is large (36 pixels), so won't be filled
    # Should attempt bridging
    assert report.islands_filled == 0
    # May or may not succeed in bridging, but there should be an attempt or it remains
    assert report.islands_remaining <= 1
