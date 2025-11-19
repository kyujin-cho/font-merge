#!/usr/bin/env python3
"""
Integration tests for the font glyph copy script.
Tests actual font merging operations with real font files.
"""

import os
import sys
import subprocess
import unittest
from pathlib import Path

try:
    from fontTools.ttLib import TTFont
except ImportError:
    print("Error: fontTools library is required for testing.")
    print("Install it with: pip install fonttools")
    sys.exit(1)


class FontMergeIntegrationTest(unittest.TestCase):
    """Integration tests for copy_font_glyphs.py"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are used across all tests."""
        cls.script_path = Path(__file__).parent / "copy_font_glyphs.py"
        cls.source_font = Path(__file__).parent / "PretendardJPVariable.ttf"
        cls.dest_font = Path(__file__).parent / "GoogleSansFlex-VariableFont_GRAD,ROND,opsz,slnt,wdth,wght.ttf"
        cls.output_font = Path(__file__).parent / "test_output.ttf"
        cls.output_renamed = Path(__file__).parent / "test_output_renamed.ttf"

        # Verify required files exist
        if not cls.script_path.exists():
            raise FileNotFoundError(f"Script not found: {cls.script_path}")
        if not cls.source_font.exists():
            raise FileNotFoundError(f"Source font not found: {cls.source_font}")
        if not cls.dest_font.exists():
            raise FileNotFoundError(f"Destination font not found: {cls.dest_font}")

    def setUp(self):
        """Set up before each test."""
        # Clean up any existing test output files
        self._cleanup_output_files()

    def tearDown(self):
        """Clean up after each test."""
        self._cleanup_output_files()

    def _cleanup_output_files(self):
        """Remove test output files if they exist."""
        for output_file in [self.output_font, self.output_renamed]:
            if output_file.exists():
                output_file.unlink()

    def _run_script(self, *args):
        """
        Run the copy_font_glyphs.py script with given arguments.

        Returns:
            subprocess.CompletedProcess with stdout, stderr, and returncode
        """
        cmd = [sys.executable, str(self.script_path)] + list(args)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        return result

    def test_script_help(self):
        """Test that the script shows help message."""
        result = self._run_script("--help")
        self.assertEqual(result.returncode, 0, "Help command should exit with code 0")
        self.assertIn("Copy glyphs", result.stdout, "Help should mention 'Copy glyphs'")
        self.assertIn("--range", result.stdout, "Help should document --range option")
        self.assertIn("--family-name", result.stdout, "Help should document --family-name option")

    def test_copy_cjk_range(self):
        """Test copying CJK Unified Ideographs range (U+4E00-U+9FFF)."""
        result = self._run_script(
            str(self.source_font),
            str(self.dest_font),
            str(self.output_font),
            "-r", "U+4E00-U+9FFF"
        )

        # Print output for debugging
        print("\n--- Script Output ---")
        print(result.stdout)
        if result.stderr:
            print("--- Script Errors ---")
            print(result.stderr)

        # Check script executed successfully
        self.assertEqual(result.returncode, 0, f"Script should exit with code 0. Error: {result.stderr}")

        # Verify output file was created
        self.assertTrue(self.output_font.exists(), "Output font file should be created")

        # Load the output font
        output = TTFont(str(self.output_font))

        # Verify the font can be loaded
        self.assertIsNotNone(output, "Output font should be loadable")

        # Check that cmap table exists
        self.assertIn('cmap', output, "Output font should have cmap table")

        # Get all Unicode codepoints from cmap
        cmap_codepoints = set()
        for table in output['cmap'].tables:
            if hasattr(table, 'cmap'):
                cmap_codepoints.update(table.cmap.keys())

        # Test some specific CJK characters that should be present
        test_codepoints = [
            0x4E00,  # 一 (one)
            0x4E8C,  # 二 (two)
            0x4E09,  # 三 (three)
            0x6C34,  # 水 (water)
            0x706B,  # 火 (fire)
            0x6728,  # 木 (tree/wood)
            0x91D1,  # 金 (gold/metal)
            0x571F,  # 土 (earth)
        ]

        # Load source font to check which codepoints are available
        source = TTFont(str(self.source_font))
        source_codepoints = set()
        for table in source['cmap'].tables:
            if hasattr(table, 'cmap'):
                source_codepoints.update(table.cmap.keys())

        # Check that test codepoints that exist in source are in output
        copied_count = 0
        for cp in test_codepoints:
            if cp in source_codepoints:
                self.assertIn(cp, cmap_codepoints,
                    f"Codepoint U+{cp:04X} ({chr(cp)}) should be in output font")
                copied_count += 1

        self.assertGreater(copied_count, 0, "At least some test codepoints should be copied")

        # Verify glyphs were actually copied (check glyf table)
        self.assertIn('glyf', output, "Output font should have glyf table")

        # Check metrics were copied
        self.assertIn('hmtx', output, "Output font should have hmtx table")

        print(f"\n✓ Successfully verified {copied_count} test codepoints")
        print(f"✓ Total codepoints in output font: {len(cmap_codepoints)}")

        # Clean up
        source.close()
        output.close()

    def test_copy_small_range(self):
        """Test copying a small specific range to verify precision."""
        result = self._run_script(
            str(self.source_font),
            str(self.dest_font),
            str(self.output_font),
            "-r", "U+4E00-U+4E10"  # Small range: 17 characters
        )

        self.assertEqual(result.returncode, 0, "Script should exit successfully")
        self.assertTrue(self.output_font.exists(), "Output font should be created")

        # Load fonts
        output = TTFont(str(self.output_font))
        source = TTFont(str(self.source_font))

        # Get codepoints
        output_codepoints = set()
        for table in output['cmap'].tables:
            if hasattr(table, 'cmap'):
                output_codepoints.update(table.cmap.keys())

        source_codepoints = set()
        for table in source['cmap'].tables:
            if hasattr(table, 'cmap'):
                source_codepoints.update(table.cmap.keys())

        # Check the range
        expected_range = set(range(0x4E00, 0x4E11))
        available_in_source = expected_range & source_codepoints
        copied_codepoints = expected_range & output_codepoints

        # All available characters in the range should be copied
        self.assertEqual(available_in_source, copied_codepoints,
            "All characters in the specified range that exist in source should be copied")

        print(f"\n✓ Copied {len(copied_codepoints)} characters from small range")

        source.close()
        output.close()

    def test_copy_with_rename(self):
        """Test copying glyphs and renaming the font family."""
        new_family_name = "TestMergedFont"

        result = self._run_script(
            str(self.source_font),
            str(self.dest_font),
            str(self.output_renamed),
            "-r", "U+4E00-U+4E20",  # Small range for faster testing
            "-f", new_family_name
        )

        self.assertEqual(result.returncode, 0, "Script should exit successfully")
        self.assertTrue(self.output_renamed.exists(), "Output font should be created")

        # Load the output font
        output = TTFont(str(self.output_renamed))

        # Check that name table exists
        self.assertIn('name', output, "Output font should have name table")

        # Check that family name was updated
        name_table = output['name']
        family_names = []
        for record in name_table.names:
            if record.nameID == 1:  # Font Family name
                family_names.append(record.toUnicode())

        self.assertTrue(any(new_family_name in name for name in family_names),
            f"Font family should be renamed to '{new_family_name}'")

        print(f"\n✓ Font family successfully renamed to: {new_family_name}")
        print(f"  Found family names: {family_names}")

        output.close()

    def test_missing_codepoints(self):
        """Test that the script handles missing codepoints gracefully."""
        # Use a range that likely doesn't exist in source font
        result = self._run_script(
            str(self.source_font),
            str(self.dest_font),
            str(self.output_font),
            "-r", "U+FFFF"  # Special character unlikely to be in font
        )

        # Script should still exit successfully even if no glyphs copied
        self.assertEqual(result.returncode, 0, "Script should handle missing codepoints gracefully")
        self.assertIn("Skip", result.stdout, "Should report skipped codepoints")

    def test_multiple_ranges(self):
        """Test copying multiple Unicode ranges in one operation."""
        result = self._run_script(
            str(self.source_font),
            str(self.dest_font),
            str(self.output_font),
            "-r", "U+4E00-U+4E10",
            "-r", "U+4E20-U+4E30"
        )

        self.assertEqual(result.returncode, 0, "Script should handle multiple ranges")
        self.assertTrue(self.output_font.exists(), "Output font should be created")

        # Verify glyphs from both ranges were copied
        output = TTFont(str(self.output_font))
        source = TTFont(str(self.source_font))

        output_codepoints = set()
        for table in output['cmap'].tables:
            if hasattr(table, 'cmap'):
                output_codepoints.update(table.cmap.keys())

        source_codepoints = set()
        for table in source['cmap'].tables:
            if hasattr(table, 'cmap'):
                source_codepoints.update(table.cmap.keys())

        # Check both ranges
        range1 = set(range(0x4E00, 0x4E11))
        range2 = set(range(0x4E20, 0x4E31))

        copied1 = range1 & output_codepoints & source_codepoints
        copied2 = range2 & output_codepoints & source_codepoints

        self.assertGreater(len(copied1), 0, "Should copy glyphs from first range")
        self.assertGreater(len(copied2), 0, "Should copy glyphs from second range")

        print(f"\n✓ Copied {len(copied1)} from range 1 and {len(copied2)} from range 2")

        source.close()
        output.close()

    def test_glyph_metrics_preserved(self):
        """Test that glyph metrics are properly copied."""
        result = self._run_script(
            str(self.source_font),
            str(self.dest_font),
            str(self.output_font),
            "-r", "U+4E00-U+4E05"
        )

        self.assertEqual(result.returncode, 0, "Script should exit successfully")

        # Load fonts
        source = TTFont(str(self.source_font))
        output = TTFont(str(self.output_font))

        # Get a codepoint that should be copied
        test_cp = 0x4E00

        # Get glyph names
        source_glyph_name = None
        for table in source['cmap'].tables:
            if test_cp in table.cmap:
                source_glyph_name = table.cmap[test_cp]
                break

        output_glyph_name = None
        for table in output['cmap'].tables:
            if test_cp in table.cmap:
                output_glyph_name = table.cmap[test_cp]
                break

        if source_glyph_name and output_glyph_name:
            # Check metrics
            if source_glyph_name in source['hmtx'].metrics:
                source_metrics = source['hmtx'][source_glyph_name]
                output_metrics = output['hmtx'][output_glyph_name]

                self.assertEqual(source_metrics[0], output_metrics[0],
                    "Advance width should be preserved")
                self.assertEqual(source_metrics[1], output_metrics[1],
                    "Left side bearing should be preserved")

                print(f"\n✓ Metrics preserved: advance={source_metrics[0]}, lsb={source_metrics[1]}")

        source.close()
        output.close()


def run_tests():
    """Run all integration tests."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(FontMergeIntegrationTest)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code based on results
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
