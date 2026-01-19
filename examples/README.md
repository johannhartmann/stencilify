# Stencilify Examples

This folder contains examples and guides to help you use stencilify effectively.

## Files

### `sample_config.json`

A complete example configuration file showing all available options. You can use this as a template for your own configurations.

**What's shown**:
- 3-color palette (black, gray, white)
- Auto paint order
- A4 page with auto orientation
- Default cuttability parameters
- CPU device (default)

**Modify for your needs**:
- Change `palette` colors
- Adjust `min_feature_mm` for detail control
- Enable `autotune` for automatic optimization
- Add `locks` for manual layer control

### `how_to_make_lock_masks.md`

Complete guide to creating lock masks for manual layer control.

**Learn how to**:
- Create masks in GIMP, Photoshop, or Python
- Understand white=cut, black=keep
- Use common lock mask patterns (borders, backgrounds)
- Troubleshoot mask issues
- Combine locks with autotune

**When to use lock masks**:
- Manual background control
- Preserve specific details
- Add decorative borders
- Import stencils from other sources

## Quick Recipes

### Recipe 1: High-Detail Portrait

```bash
stencilify generate portrait.png \
  --palette #000000,#555555,#aaaaaa,#ffffff \
  --min-feature-mm 1.5 \
  --min-island-area-mm2 20.0 \
  --autotune
```

### Recipe 2: Bold Graphic Design

```bash
stencilify generate logo.png \
  --palette #000000,#ffffff \
  --min-feature-mm 3.0 \
  --min-island-area-mm2 50.0
```

### Recipe 3: Manual Background + Auto Foreground

```bash
# First create background_mask.png with your design
stencilify generate portrait.png \
  --palette #000000,#666666,#ffffff \
  --lock "#000000=background_mask.png" \
  --autotune
```

### Recipe 4: Maximum Cuttability

```bash
stencilify generate input.png \
  --palette #000000,#666666,#ffffff \
  --min-feature-mm 2.5 \
  --min-island-area-mm2 40.0 \
  --bridge-width-mm 1.5 \
  --vector-backend potrace
```

## Tips for Success

1. **Start with autotune**: Run with `--autotune` first to see what parameters work best
2. **Check the preview**: Always examine `preview.png` before cutting
3. **Test on paper first**: Print masks on paper and overlay them to check alignment
4. **Iterate parameters**: Adjust one parameter at a time and compare results
5. **Use registration marks**: The automatic marks help with multi-layer alignment
6. **Check report.json**: Review metrics to understand what the tool did

## Common Workflows

### Workflow 1: Quick Test

```bash
# Fast iteration for testing
stencilify generate input.png \
  --palette #000000,#ffffff \
  --page A4 \
  --outdir test_out/
```

### Workflow 2: Production Quality

```bash
# Final output with optimization
stencilify generate input.png \
  --palette #000000,#666666,#ffffff \
  --autotune \
  --page A3 \
  --vector-backend potrace \
  --seed 42 \
  --outdir final_out/
```

### Workflow 3: Troubleshooting

```bash
# Check system first
stencilify doctor

# Run with verbose logging
stencilify generate input.png \
  --palette #000000,#ffffff \
  --verbose \
  --outdir debug_out/
```

## Need Help?

1. Run `stencilify doctor` to check your system setup
2. Check the main README.md for detailed documentation
3. Review `report.json` after generation for metrics and warnings
4. Read `how_to_make_lock_masks.md` for manual control
5. File issues at: https://github.com/anthropics/claude-code/issues

Happy stenciling!
