#!/bin/bash
# Automated test script for stencilify

set -e

echo "========================================="
echo "Stencilify Test Suite"
echo "========================================="
echo ""

# Find all jpg files in test_examples
for img in test_examples/*.jpg; do
    if [ -f "$img" ]; then
        filename=$(basename "$img" .jpg)
        echo "Testing: $filename"
        echo "-----------------------------------------"

        # Test 1: Knockout mode
        echo "  [1/2] Knockout mode..."
        uv run stencilify generate "$img" \
            --palette "#000000" --palette "#808080" --palette "#ffffff" \
            --outdir "test_examples/output_${filename}_knockout" \
            > /dev/null 2>&1

        # Test 2: Overlapping mode
        echo "  [2/2] Overlapping mode..."
        uv run stencilify generate "$img" \
            --palette "#000000" --palette "#808080" --palette "#ffffff" \
            --layer-mode overlapping \
            --outdir "test_examples/output_${filename}_overlapping" \
            > /dev/null 2>&1

        echo "  ✓ Complete"
        echo ""
    fi
done

echo "========================================="
echo "All tests complete!"
echo "========================================="
echo ""
echo "Results saved in test_examples/output_*/"
