"""Tests for autotune functionality."""

from pathlib import Path

from PIL import Image

from stencilify.autotune import (
    CandidateParams,
    evaluate_candidate,
    run_autotune,
    save_candidates_csv,
)
from stencilify.config import AutotuneConfig, PipelineConfig
from stencilify.imageio import load_rgba
from stencilify.masks import silhouette_from_alpha


def create_test_image(tmp_path: Path) -> Path:
    """Create a small test image for autotuning."""
    # Create 100x100 RGBA image
    img = Image.new("RGBA", (100, 100), (128, 128, 128, 255))

    # Add some pattern
    pixels = img.load()
    if pixels is not None:
        for i in range(50):
            for j in range(50):
                pixels[i, j] = (200, 200, 200, 255)

    input_path = tmp_path / "test.png"
    img.save(input_path)

    return input_path


def test_evaluate_candidate(tmp_path: Path) -> None:
    """Test evaluating a single candidate."""
    input_path = create_test_image(tmp_path)

    config = PipelineConfig(
        input_image=input_path,
        palette=["#000000", "#ffffff"],
        seed=42,
    )

    rgb, alpha = load_rgba(input_path)
    silhouette = silhouette_from_alpha(alpha)

    params = CandidateParams(
        n_segments=500,
        smooth_lambda=10.0,
        slic_compactness=10.0,
        cleanup_strength=1.0,
    )

    result = evaluate_candidate(params, config, rgb, alpha, silhouette, px_per_mm=10.0)

    # Check result has all required fields
    assert result.params == params
    assert result.score >= 0
    assert result.palette_error >= 0
    assert result.cutout_components >= 0
    assert result.island_count >= 0
    assert result.contour_complexity >= 0


def test_run_autotune_small_grid(tmp_path: Path) -> None:
    """Test autotuning with a small parameter grid."""
    input_path = create_test_image(tmp_path)

    config = PipelineConfig(
        input_image=input_path,
        palette=["#000000", "#ffffff"],
        autotune=AutotuneConfig(enabled=True),
        seed=42,
    )

    # Run autotune
    result = run_autotune(config, px_per_mm=10.0)

    # Check result
    assert result.best_params is not None
    assert result.best_score >= 0
    assert len(result.all_candidates) > 0

    # Check best params are valid
    assert result.best_params.n_segments in [800, 1200, 1800, 2500]
    assert result.best_params.smooth_lambda in [5.0, 10.0, 20.0]
    assert result.best_params.slic_compactness in [10.0, 15.0, 20.0]
    assert result.best_params.cleanup_strength in [0.8, 1.0, 1.2]


def test_autotune_deterministic(tmp_path: Path) -> None:
    """Test that autotune is deterministic with same seed."""
    input_path = create_test_image(tmp_path)

    config1 = PipelineConfig(
        input_image=input_path,
        palette=["#000000", "#ffffff"],
        autotune=AutotuneConfig(enabled=True),
        seed=42,
    )

    config2 = PipelineConfig(
        input_image=input_path,
        palette=["#000000", "#ffffff"],
        autotune=AutotuneConfig(enabled=True),
        seed=42,
    )

    # Run autotune twice with same seed
    result1 = run_autotune(config1, px_per_mm=10.0)
    result2 = run_autotune(config2, px_per_mm=10.0)

    # Results should be identical
    assert result1.best_params == result2.best_params
    assert result1.best_score == result2.best_score
    assert len(result1.all_candidates) == len(result2.all_candidates)


def test_save_candidates_csv(tmp_path: Path) -> None:
    """Test saving candidates to CSV."""
    from stencilify.autotune import CandidateResult

    candidates = [
        CandidateResult(
            params=CandidateParams(
                n_segments=500,
                smooth_lambda=10.0,
                slic_compactness=10.0,
                cleanup_strength=1.0,
            ),
            score=100.0,
            palette_error=10.0,
            cutout_components=5,
            island_count=2,
            contour_complexity=1000.0,
        ),
        CandidateResult(
            params=CandidateParams(
                n_segments=800,
                smooth_lambda=20.0,
                slic_compactness=15.0,
                cleanup_strength=0.8,
            ),
            score=80.0,
            palette_error=8.0,
            cutout_components=4,
            island_count=1,
            contour_complexity=900.0,
        ),
    ]

    csv_path = tmp_path / "candidates.csv"
    save_candidates_csv(candidates, csv_path)

    # Check file exists
    assert csv_path.exists()

    # Check content
    content = csv_path.read_text()
    assert "n_segments" in content
    assert "score" in content
    assert "500" in content
    assert "800" in content


def test_autotune_finds_best_candidate(tmp_path: Path) -> None:
    """Test that autotune selects the candidate with lowest score."""
    input_path = create_test_image(tmp_path)

    config = PipelineConfig(
        input_image=input_path,
        palette=["#000000", "#ffffff"],
        autotune=AutotuneConfig(enabled=True),
        seed=42,
    )

    result = run_autotune(config, px_per_mm=10.0)

    # Check that best candidate has lowest score
    all_scores = [c.score for c in result.all_candidates]
    assert result.best_score == min(all_scores)

    # Find the candidate with best score
    best_candidate = min(result.all_candidates, key=lambda c: c.score)
    assert result.best_params == best_candidate.params
