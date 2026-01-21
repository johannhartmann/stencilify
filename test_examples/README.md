# Test Examples for Stencilify

This directory contains test images for evaluating stencilify's performance.

## Test Images

1. **batman_kid.jpg** - Child in Batman costume (clean white background)
2. **supergirl_kid.jpg** - Child in Supergirl costume (clean white background)

## Expected Challenges

- Automatic subject detection with clean backgrounds
- Complex costume details (logos, textures)
- Facial features and masks
- Multiple colors in costumes

## Test Commands

```bash
# Test with knockout mode (default)
uv run stencilify generate test_examples/batman_kid.jpg \
  --palette "#000000" --palette "#808080" --palette "#ffffff" \
  --outdir test_examples/output_batman_knockout

# Test with overlapping mode
uv run stencilify generate test_examples/batman_kid.jpg \
  --palette "#000000" --palette "#808080" --palette "#ffffff" \
  --layer-mode overlapping \
  --outdir test_examples/output_batman_overlapping
```
