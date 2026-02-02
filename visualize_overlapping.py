"""Visualize what the overlapping stencils actually look like."""

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

# Load layers
layer1 = np.array(Image.open("test_output_overlapping/01_000000.png"))
layer2 = np.array(Image.open("test_output_overlapping/02_808080.png"))
layer3 = np.array(Image.open("test_output_overlapping/03_ffffff.png"))

# Create figure
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

axes[0].imshow(layer1, cmap='gray')
axes[0].set_title(f'Layer 1 (darkest)\n{np.sum(layer1==0):,} material pixels')
axes[0].axis('off')

axes[1].imshow(layer2, cmap='gray')
axes[1].set_title(f'Layer 2 (mid)\n{np.sum(layer2==0):,} material pixels')
axes[1].axis('off')

axes[2].imshow(layer3, cmap='gray')
axes[2].set_title(f'Layer 3 (lightest)\n{np.sum(layer3==0):,} material pixels')
axes[2].axis('off')

plt.tight_layout()
plt.savefig('overlapping_layers_visualization.png', dpi=150, bbox_inches='tight')
print("Saved visualization to overlapping_layers_visualization.png")

# Check if there's ANY material in layer 1
if np.sum(layer1 == 0) == 0:
    print("\nPROBLEM: Layer 1 has NO material at all - the entire page is cut out!")
    print("This means there are no borders/margins being added.")
    print("A physical stencil needs material around the edges to hold it together.")
