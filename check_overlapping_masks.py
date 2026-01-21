"""Check what's actually in the overlapping masks."""

import numpy as np
from PIL import Image

# Load the three layers
layer1 = np.array(Image.open("test_output_overlapping/01_000000.png"))
layer2 = np.array(Image.open("test_output_overlapping/02_808080.png"))
layer3 = np.array(Image.open("test_output_overlapping/03_ffffff.png"))

print("Layer analysis (white=255=open, black=0=material):")
print(f"\nLayer 1 (darkest #000000):")
print(f"  Shape: {layer1.shape}")
print(f"  Unique values: {np.unique(layer1)}")
print(f"  White pixels (open): {np.sum(layer1 == 255):,}")
print(f"  Black pixels (material): {np.sum(layer1 == 0):,}")
print(f"  Percentage open: {np.sum(layer1 == 255) / layer1.size * 100:.1f}%")

print(f"\nLayer 2 (mid #808080):")
print(f"  Shape: {layer2.shape}")
print(f"  Unique values: {np.unique(layer2)}")
print(f"  White pixels (open): {np.sum(layer2 == 255):,}")
print(f"  Black pixels (material): {np.sum(layer2 == 0):,}")
print(f"  Percentage open: {np.sum(layer2 == 255) / layer2.size * 100:.1f}%")

print(f"\nLayer 3 (lightest #ffffff):")
print(f"  Shape: {layer3.shape}")
print(f"  Unique values: {np.unique(layer3)}")
print(f"  White pixels (open): {np.sum(layer3 == 255):,}")
print(f"  Black pixels (material): {np.sum(layer3 == 0):,}")
print(f"  Percentage open: {np.sum(layer3 == 255) / layer3.size * 100:.1f}%")

print("\n\nFor overlapping traditional stencils:")
print("  Layer 1 should have MOST open (full silhouette)")
print("  Layer 2 should have MEDIUM open (mid+light areas)")
print("  Layer 3 should have LEAST open (only highlights)")
