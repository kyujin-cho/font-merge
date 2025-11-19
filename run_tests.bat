@echo off
REM Test runner script for font-merge integration tests (Windows)

echo ===================================
echo Font Merge Integration Test Suite
echo ===================================
echo.

REM Check if fonttools is installed
python -c "import fontTools" 2>nul
if errorlevel 1 (
    echo Error: fontTools not installed
    echo Run: pip install fonttools
    exit /b 1
)

REM Check if required font files exist
if not exist "PretendardJPVariable.ttf" (
    echo Warning: Source font 'PretendardJPVariable.ttf' not found
    echo Some tests may fail
)

if not exist "GoogleSansFlex-VariableFont_GRAD,ROND,opsz,slnt,wdth,wght.ttf" (
    echo Warning: Destination font 'GoogleSansFlex-VariableFont_GRAD,ROND,opsz,slnt,wdth,wght.ttf' not found
    echo Some tests may fail
)

echo.
echo Running integration tests...
echo.

REM Run the tests
python test_integration.py

if errorlevel 1 (
    echo.
    echo X Some tests failed
    exit /b 1
) else (
    echo.
    echo √ All tests passed!
    exit /b 0
)
