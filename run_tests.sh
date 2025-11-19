#!/bin/bash
# Test runner script for font-merge integration tests

echo "==================================="
echo "Font Merge Integration Test Suite"
echo "==================================="
echo ""

# Check if fonttools is installed
if ! python3 -c "import fontTools" 2>/dev/null; then
    echo "Error: fontTools not installed"
    echo "Run: pip install fonttools"
    exit 1
fi

# Check if required font files exist
if [ ! -f "PretendardJPVariable.ttf" ]; then
    echo "Warning: Source font 'PretendardJPVariable.ttf' not found"
    echo "Some tests may fail"
fi

if [ ! -f "GoogleSansFlex-VariableFont_GRAD,ROND,opsz,slnt,wdth,wght.ttf" ]; then
    echo "Warning: Destination font 'GoogleSansFlex-VariableFont_GRAD,ROND,opsz,slnt,wdth,wght.ttf' not found"
    echo "Some tests may fail"
fi

echo ""
echo "Running integration tests..."
echo ""

# Run the tests
python3 test_integration.py

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "✓ All tests passed!"
else
    echo "✗ Some tests failed"
fi

exit $exit_code
