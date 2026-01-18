"""Tests for lock mask loading and superpixel mapping."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from stencilify.locks import load_lock_mask, map_locks_to_superpixels, parse_lock_spec


def test_load_lock_mask_basic(tmp_path: Path) -> None:
    """Test basic lock mask loading."""
    # Create a simple black and white mask
    mask_img = Image.new("L", (10, 10), color=0)
    # Draw white rectangle
    for i in range(3, 7):
        for j in range(3, 7):
            mask_img.putpixel((j, i), 255)

    mask_path = tmp_path / "mask.png"
    mask_img.save(mask_path)

    # Load mask
    mask = load_lock_mask(mask_path, target_shape=(10, 10))

    # Check shape
    assert mask.shape == (10, 10)

    # Check values
    assert mask[0, 0] == 0
    assert mask[5, 5] == 1


def test_load_lock_mask_resize(tmp_path: Path) -> None:
    """Test that lock mask is resized to target shape."""
    # Create 20x20 mask
    mask_img = Image.new("L", (20, 20), color=255)

    mask_path = tmp_path / "mask.png"
    mask_img.save(mask_path)

    # Load and resize to 10x10
    mask = load_lock_mask(mask_path, target_shape=(10, 10))

    # Check shape
    assert mask.shape == (10, 10)

    # Should be all ones
    assert np.all(mask == 1)


def test_load_lock_mask_threshold(tmp_path: Path) -> None:
    """Test that thresholding works correctly."""
    # Create mask with various gray levels
    mask_img = Image.new("L", (10, 10))
    for i in range(10):
        for j in range(10):
            mask_img.putpixel((j, i), i * 25)  # 0, 25, 50, ..., 225

    mask_path = tmp_path / "mask.png"
    mask_img.save(mask_path)

    mask = load_lock_mask(mask_path, target_shape=(10, 10))

    # Threshold is 128
    # Rows 0-5 should be 0 (0, 25, 50, 75, 100, 125 < 128)
    # Rows 6-9 should be 1 (150, 175, 200, 225 > 128)
    assert mask[0, 0] == 0
    assert mask[5, 0] == 0
    assert mask[6, 0] == 1
    assert mask[9, 0] == 1


def test_load_lock_mask_rgb(tmp_path: Path) -> None:
    """Test loading RGB image as lock mask."""
    # Create RGB mask
    mask_img = Image.new("RGB", (5, 5), color=(255, 255, 255))

    mask_path = tmp_path / "mask.png"
    mask_img.save(mask_path)

    # Should convert to grayscale and threshold
    mask = load_lock_mask(mask_path, target_shape=(5, 5))

    assert mask.shape == (5, 5)
    assert np.all(mask == 1)


def test_load_lock_mask_not_found(tmp_path: Path) -> None:
    """Test that missing file raises FileNotFoundError."""
    mask_path = tmp_path / "nonexistent.png"

    with pytest.raises(FileNotFoundError, match="not found"):
        load_lock_mask(mask_path, target_shape=(10, 10))


def test_load_lock_mask_invalid_file(tmp_path: Path) -> None:
    """Test that invalid image file raises ValueError."""
    # Create a text file
    invalid_path = tmp_path / "invalid.png"
    invalid_path.write_text("not an image")

    with pytest.raises(ValueError, match="Failed to load"):
        load_lock_mask(invalid_path, target_shape=(10, 10))


def test_map_locks_to_superpixels_simple() -> None:
    """Test simple lock mapping."""
    # 4x4 image with 2 superpixels
    spx_labels = np.array(
        [
            [0, 0, 1, 1],
            [0, 0, 1, 1],
            [0, 0, 1, 1],
            [0, 0, 1, 1],
        ],
        dtype=np.int32,
    )

    silhouette = np.ones((4, 4), dtype=np.uint8)

    # Lock mask for palette 0 covers left half
    lock_mask_0 = np.array(
        [
            [1, 1, 0, 0],
            [1, 1, 0, 0],
            [1, 1, 0, 0],
            [1, 1, 0, 0],
        ],
        dtype=np.uint8,
    )

    lock_masks = {0: lock_mask_0}

    locked_spx = map_locks_to_superpixels(lock_masks, spx_labels, silhouette)

    # Superpixel 0 should be locked to palette 0
    assert locked_spx == {0: 0}


def test_map_locks_to_superpixels_multiple() -> None:
    """Test mapping multiple locks."""
    # 6x6 image with 3 superpixels
    spx_labels = np.array(
        [
            [0, 0, 1, 1, 2, 2],
            [0, 0, 1, 1, 2, 2],
            [0, 0, 1, 1, 2, 2],
            [0, 0, 1, 1, 2, 2],
            [0, 0, 1, 1, 2, 2],
            [0, 0, 1, 1, 2, 2],
        ],
        dtype=np.int32,
    )

    silhouette = np.ones((6, 6), dtype=np.uint8)

    # Lock masks
    lock_mask_0 = np.zeros((6, 6), dtype=np.uint8)
    lock_mask_0[:, :2] = 1  # Lock left third

    lock_mask_1 = np.zeros((6, 6), dtype=np.uint8)
    lock_mask_1[:, 4:] = 1  # Lock right third

    lock_masks = {0: lock_mask_0, 1: lock_mask_1}

    locked_spx = map_locks_to_superpixels(lock_masks, spx_labels, silhouette)

    # Superpixels 0 and 2 should be locked
    assert locked_spx == {0: 0, 2: 1}


def test_map_locks_to_superpixels_threshold() -> None:
    """Test that overlap threshold works correctly."""
    spx_labels = np.array(
        [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ],
        dtype=np.int32,
    )

    silhouette = np.ones((4, 4), dtype=np.uint8)

    # Lock mask covers only 25% of superpixel (4 out of 16 pixels)
    lock_mask = np.array(
        [
            [1, 1, 0, 0],
            [1, 1, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )

    lock_masks = {0: lock_mask}

    # With threshold 0.5, should NOT lock (only 25% overlap)
    locked_spx = map_locks_to_superpixels(lock_masks, spx_labels, silhouette, overlap_threshold=0.5)
    assert locked_spx == {}

    # With threshold 0.2, should lock (25% > 20%)
    locked_spx = map_locks_to_superpixels(lock_masks, spx_labels, silhouette, overlap_threshold=0.2)
    assert locked_spx == {0: 0}


def test_map_locks_to_superpixels_with_silhouette_mask() -> None:
    """Test lock mapping respects silhouette."""
    spx_labels = np.array(
        [
            [0, 0, -1, -1],
            [0, 0, -1, -1],
            [-1, -1, -1, -1],
            [-1, -1, -1, -1],
        ],
        dtype=np.int32,
    )

    silhouette = np.array(
        [
            [1, 1, 0, 0],
            [1, 1, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )

    # Lock mask covers entire image
    lock_mask = np.ones((4, 4), dtype=np.uint8)

    lock_masks = {0: lock_mask}

    locked_spx = map_locks_to_superpixels(lock_masks, spx_labels, silhouette)

    # Only superpixel 0 should be locked (within silhouette)
    assert locked_spx == {0: 0}


def test_map_locks_to_superpixels_conflict() -> None:
    """Test that conflicting locks raise error."""
    spx_labels = np.zeros((4, 4), dtype=np.int32)  # Single superpixel
    silhouette = np.ones((4, 4), dtype=np.uint8)

    # Two lock masks both covering the same superpixel
    lock_mask_0 = np.ones((4, 4), dtype=np.uint8)
    lock_mask_1 = np.ones((4, 4), dtype=np.uint8)

    lock_masks = {0: lock_mask_0, 1: lock_mask_1}

    with pytest.raises(ValueError, match="Conflicting locks"):
        map_locks_to_superpixels(lock_masks, spx_labels, silhouette)


def test_map_locks_to_superpixels_shape_mismatch() -> None:
    """Test that shape mismatch raises error."""
    spx_labels = np.zeros((4, 4), dtype=np.int32)
    silhouette = np.ones((4, 4), dtype=np.uint8)
    lock_mask = np.ones((5, 5), dtype=np.uint8)  # Wrong shape

    lock_masks = {0: lock_mask}

    with pytest.raises(ValueError, match="shape"):
        map_locks_to_superpixels(lock_masks, spx_labels, silhouette)


def test_map_locks_to_superpixels_empty_locks() -> None:
    """Test with no lock masks."""
    spx_labels = np.zeros((4, 4), dtype=np.int32)
    silhouette = np.ones((4, 4), dtype=np.uint8)
    lock_masks: dict[int, np.ndarray] = {}

    locked_spx = map_locks_to_superpixels(lock_masks, spx_labels, silhouette)

    assert locked_spx == {}


def test_parse_lock_spec_basic() -> None:
    """Test basic lock spec parsing."""
    color, path = parse_lock_spec("#FFD200=mask.png")

    assert color == "#FFD200"
    assert path == Path("mask.png")


def test_parse_lock_spec_without_hash() -> None:
    """Test parsing without # prefix."""
    color, path = parse_lock_spec("FFD200=mask.png")

    # Should add # prefix
    assert color == "#FFD200"
    assert path == Path("mask.png")


def test_parse_lock_spec_with_spaces() -> None:
    """Test parsing with whitespace."""
    color, path = parse_lock_spec(" #FFD200 = mask.png ")

    assert color == "#FFD200"
    assert path == Path("mask.png")


def test_parse_lock_spec_path_with_dirs() -> None:
    """Test parsing path with directories."""
    color, path = parse_lock_spec("#000000=path/to/mask.png")

    assert color == "#000000"
    assert path == Path("path/to/mask.png")


def test_parse_lock_spec_no_equals() -> None:
    """Test that missing = raises error."""
    with pytest.raises(ValueError, match="Invalid lock specification"):
        parse_lock_spec("#FFD200")


def test_parse_lock_spec_invalid_color() -> None:
    """Test that invalid color format raises error."""
    with pytest.raises(ValueError, match="Invalid color"):
        parse_lock_spec("#FFF=mask.png")  # Too short


def test_parse_lock_spec_multiple_equals() -> None:
    """Test spec with multiple = characters."""
    # Should split on first = only
    color, path = parse_lock_spec("#FFD200=path=with=equals.png")

    assert color == "#FFD200"
    assert path == Path("path=with=equals.png")
