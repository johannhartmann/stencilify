# How to Make Lock Masks

Lock masks let you manually control specific layers in your stencil output. This is useful when you want artistic control over backgrounds, borders, or specific details.

## What is a Lock Mask?

A lock mask is a binary PNG image where:
- **White pixels (255, 255, 255) = open/cut** - These areas will be painted
- **Black pixels (0, 0, 0) = material/keep** - These areas remain as stencil material

This is the same format as stencilify's output masks.

## Requirements

- Must be a PNG file
- Must match your input image dimensions **exactly**
- Must be binary (only pure white and pure black)
- Grayscale or RGB both work

## Workflow 1: GIMP (Free)

### Step 1: Open Your Image

1. Open GIMP
2. Open your input image (e.g., `portrait.png`)

### Step 2: Create a New Layer

1. Layer → New Layer
2. Fill with: White
3. Click OK

### Step 3: Draw Your Mask

1. Select **black** as foreground color
2. Use tools to mark areas you want to **keep as material**:
   - **Pencil tool** (N) for hard edges
   - **Paintbrush tool** (P) for soft edges
   - **Selection tools** + Fill for large areas
3. Remember: Black = keep, White = cut

### Step 4: Flatten and Export

1. Image → Flatten Image
2. File → Export As
3. Save as `my_mask.png`
4. Use PNG export options (no compression needed)

### Step 5: Verify

Check your mask:
```bash
# Preview with any image viewer
open my_mask.png

# Should be pure black and white only
```

## Workflow 2: Photoshop

### Step 1: Open Image

1. File → Open (`portrait.png`)

### Step 2: Create Mask Layer

1. Layer → New → Layer
2. Fill with white (Edit → Fill → White)

### Step 3: Paint Mask

1. Select **black** brush
2. Paint areas to **keep as material**
3. Use selection tools for complex shapes

### Step 4: Flatten and Save

1. Layer → Flatten Image
2. File → Save As → PNG
3. Save as `my_mask.png`

## Workflow 3: Python Script

For programmatic mask creation:

```python
import numpy as np
from PIL import Image

# Load your input image to get dimensions
img = Image.open("portrait.png")
width, height = img.size

# Create white canvas (all cut)
mask = np.ones((height, width), dtype=np.uint8) * 255

# Draw black regions (material to keep)
# Example: Keep a 50px border
mask[0:50, :] = 0        # Top border
mask[-50:, :] = 0        # Bottom border
mask[:, 0:50] = 0        # Left border
mask[:, -50:] = 0        # Right border

# Save
Image.fromarray(mask).save("border_mask.png")
```

## Using Lock Masks

Once you have your mask, use it with stencilify:

```bash
stencilify generate portrait.png \
  --palette #000000,#666666,#ffffff \
  --lock "#000000=my_mask.png"
```

This locks the **black layer** to your custom mask. Stencilify will compute the other layers (gray, white) normally.

## Common Lock Mask Use Cases

### 1. Custom Background

Create a solid or patterned background:

```bash
# Lock black layer to a custom background
stencilify generate portrait.png \
  --palette #000000,#ffffff \
  --lock "#000000=custom_background.png"
```

### 2. Manual Borders

Add decorative borders that stencilify wouldn't generate:

```bash
# Create border mask with script or manually
stencilify generate portrait.png \
  --palette #000000,#666666,#ffffff \
  --lock "#000000=border.png"
```

### 3. Preserve Specific Details

Manually paint areas you want preserved:

```bash
# Lock one layer, let autotune handle others
stencilify generate portrait.png \
  --palette #000000,#666666,#ffffff \
  --lock "#666666=manual_midtones.png" \
  --autotune
```

### 4. Import External Stencils

Reuse stencils from other sources:

```bash
# Use a stencil from another tool or previous run
stencilify generate new_portrait.png \
  --palette #000000,#ffffff \
  --lock "#ffffff=previous_highlight.png"
```

## Troubleshooting

### Problem: "Mask file does not exist"

**Solution**: Check the file path is correct and relative to where you run the command.

```bash
# Use absolute paths if needed
stencilify generate portrait.png \
  --lock "#000000=/full/path/to/my_mask.png"
```

### Problem: "Mask shape mismatch"

**Solution**: Lock mask must match input image dimensions exactly.

```python
# Check dimensions
from PIL import Image
input_img = Image.open("portrait.png")
mask_img = Image.open("my_mask.png")
print(f"Input: {input_img.size}")
print(f"Mask: {mask_img.size}")
# These must match!
```

### Problem: Mask has gray pixels

**Solution**: Lock masks must be binary (only pure black and white).

```python
# Convert to binary in Python
from PIL import Image
mask = Image.open("my_mask.png").convert("L")
mask = mask.point(lambda x: 255 if x > 127 else 0)
mask.save("my_mask_binary.png")
```

Or in GIMP:
1. Colors → Threshold
2. Adjust threshold to 127
3. Click OK
4. Export

## Tips

- **Start simple**: Create a basic mask first, test it, then refine
- **Use layers**: Keep your original image visible while drawing
- **Check the preview**: After running stencilify, check `preview.png` to see if your lock worked as expected
- **Iterate**: If the result isn't right, adjust your mask and re-run
- **Multiple locks**: You can lock multiple colors at once:

```bash
stencilify generate portrait.png \
  --palette #000000,#666666,#ffffff \
  --lock "#000000=background.png" \
  --lock "#ffffff=highlights.png"
```

## Example Gallery

See the `examples/` folder for:
- `border_mask.png` - Simple border example
- `custom_background.png` - Background pattern example
- `manual_highlights.png` - Detail preservation example

Happy stenciling!
