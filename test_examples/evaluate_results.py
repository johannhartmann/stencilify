#!/usr/bin/env python3
"""Evaluate stencilify test results."""

import json
from pathlib import Path

import numpy as np
from PIL import Image


def evaluate_stencil_output(output_dir: Path) -> dict:
    """Evaluate quality metrics for a stencil output."""

    report_path = output_dir / "report.json"
    if not report_path.exists():
        return {"error": "No report.json found"}

    with open(report_path) as f:
        report = json.load(f)

    # Load layer masks to analyze
    layer_files = sorted(output_dir.glob("0*.png"))

    metrics = {
        "output_dir": output_dir.name,
        "num_layers": len(layer_files),
        "superpixels": report.get("superpixels_created", 0),
        "silhouette_pixels": report.get("silhouette_pixels", 0),
        "layers": []
    }

    for layer_file in layer_files:
        img = np.array(Image.open(layer_file))

        # Count material vs open pixels
        total = img.size
        white_pixels = np.sum(img == 255)  # Open/cutout
        black_pixels = np.sum(img == 0)     # Material

        layer_metrics = {
            "name": layer_file.stem,
            "open_pixels": int(white_pixels),
            "material_pixels": int(black_pixels),
            "open_percentage": float(white_pixels / total * 100),
            "islands": report.get("layers", {}).get(layer_file.stem, {}).get("islands_remaining", 0)
        }

        metrics["layers"].append(layer_metrics)

    return metrics


def compare_modes(knockout_dir: Path, overlapping_dir: Path):
    """Compare knockout vs overlapping mode results."""

    print("\n" + "=" * 80)
    print("COMPARISON: Knockout vs Overlapping Mode")
    print("=" * 80)

    knockout = evaluate_stencil_output(knockout_dir)
    overlapping = evaluate_stencil_output(overlapping_dir)

    print(f"\n{'Mode':<20} {'Layers':<10} {'Superpixels':<15} {'Silhouette':<15}")
    print("-" * 80)
    print(f"{'Knockout':<20} {knockout['num_layers']:<10} {knockout['superpixels']:<15} {knockout['silhouette_pixels']:<15}")
    print(f"{'Overlapping':<20} {overlapping['num_layers']:<10} {overlapping['superpixels']:<15} {overlapping['silhouette_pixels']:<15}")

    print("\n" + "=" * 80)
    print("LAYER ANALYSIS")
    print("=" * 80)

    print("\nKnockout Mode:")
    print(f"{'Layer':<15} {'Open %':<10} {'Material %':<12} {'Islands':<10}")
    print("-" * 80)
    for layer in knockout["layers"]:
        material_pct = 100 - layer["open_percentage"]
        print(f"{layer['name']:<15} {layer['open_percentage']:>7.1f}% {material_pct:>10.1f}% {layer['islands']:>10}")

    print("\nOverlapping Mode:")
    print(f"{'Layer':<15} {'Open %':<10} {'Material %':<12} {'Islands':<10}")
    print("-" * 80)
    for layer in overlapping["layers"]:
        material_pct = 100 - layer["open_percentage"]
        print(f"{layer['name']:<15} {layer['open_percentage']:>7.1f}% {material_pct:>10.1f}% {layer['islands']:>10}")

    # Check overlapping pattern
    print("\n" + "=" * 80)
    print("OVERLAPPING MODE VERIFICATION")
    print("=" * 80)

    if len(overlapping["layers"]) >= 2:
        layer1_open = overlapping["layers"][0]["open_percentage"]
        layer2_open = overlapping["layers"][1]["open_percentage"]

        if layer1_open > layer2_open:
            print("✓ Layer 1 has MORE open area than Layer 2 (correct descending pattern)")
        else:
            print("✗ WARNING: Layer 1 should have MORE open area than Layer 2")

        if len(overlapping["layers"]) >= 3:
            layer3_open = overlapping["layers"][2]["open_percentage"]
            if layer2_open > layer3_open:
                print("✓ Layer 2 has MORE open area than Layer 3 (correct descending pattern)")
            else:
                print("✗ WARNING: Layer 2 should have MORE open area than Layer 3")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_examples = Path("test_examples")

    # Find all test outputs
    knockout_dirs = sorted(test_examples.glob("output_*_knockout"))
    overlapping_dirs = sorted(test_examples.glob("output_*_overlapping"))

    # Pair them up
    pairs = []
    for ko_dir in knockout_dirs:
        base = ko_dir.name.replace("output_", "").replace("_knockout", "")
        ol_dir = test_examples / f"output_{base}_overlapping"
        if ol_dir.exists():
            pairs.append((ko_dir, ol_dir, base))

    if not pairs:
        print("No test results found. Run ./test_examples/run_tests.sh first.")
    else:
        for knockout_dir, overlapping_dir, base_name in pairs:
            print("\n" + "=" * 80)
            print(f"TESTING: {base_name}")
            compare_modes(knockout_dir, overlapping_dir)
            print()
