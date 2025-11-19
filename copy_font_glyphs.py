#!/usr/bin/env python3
"""
Font Glyph Copy Script
Copies designated Unicode ranges of glyphs from one TrueType font file to another.
"""

import sys
import argparse
from pathlib import Path

try:
    from fontTools.ttLib import TTFont
    from fontTools.pens.ttGlyphPen import TTGlyphPen
except ImportError:
    print("Error: fontTools library is required.")
    print("Install it with: pip install fonttools")
    sys.exit(1)


def parse_unicode_range(range_str):
    """
    Parse Unicode range string.
    Formats supported:
    - Single codepoint: U+4E00 or 0x4E00 or 4E00
    - Range: U+4E00-U+9FFF or 0x4E00-0x9FFF or 4E00-9FFF
    """
    range_str = range_str.strip().upper()

    # Handle range
    if '-' in range_str:
        start_str, end_str = range_str.split('-', 1)
        start = parse_single_codepoint(start_str.strip())
        end = parse_single_codepoint(end_str.strip())
        return list(range(start, end + 1))
    else:
        # Single codepoint
        return [parse_single_codepoint(range_str)]


def parse_single_codepoint(cp_str):
    """Parse a single codepoint string."""
    cp_str = cp_str.strip().upper()

    # Remove U+ prefix if present
    if cp_str.startswith('U+'):
        cp_str = cp_str[2:]
    # Remove 0x prefix if present
    elif cp_str.startswith('0X'):
        cp_str = cp_str[2:]

    return int(cp_str, 16)


def get_glyph_name_for_codepoint(font, codepoint):
    """Get the glyph name for a given Unicode codepoint."""
    for table in font['cmap'].tables:
        if codepoint in table.cmap:
            return table.cmap[codepoint]
    return None


def copy_glyphs(source_font_path, dest_font_path, output_path, unicode_ranges, new_family_name=None):
    """
    Copy glyphs from source font to destination font for specified Unicode ranges.

    Args:
        source_font_path: Path to source font file
        dest_font_path: Path to destination font file
        output_path: Path to save the modified font
        unicode_ranges: List of Unicode codepoint ranges to copy
        new_family_name: Optional new font family name for the output font
    """
    print(f"Loading source font: {source_font_path}")
    source_font = TTFont(source_font_path)

    print(f"Loading destination font: {dest_font_path}")
    dest_font = TTFont(dest_font_path)

    # Collect all codepoints to copy
    codepoints_to_copy = []
    for range_str in unicode_ranges:
        codepoints = parse_unicode_range(range_str)
        codepoints_to_copy.extend(codepoints)

    print(f"Processing {len(codepoints_to_copy)} codepoints...")

    copied_count = 0
    skipped_count = 0

    # Get glyph set from both fonts
    source_glyf = source_font['glyf']
    dest_glyf = dest_font['glyf']

    # Process each codepoint
    for codepoint in codepoints_to_copy:
        # Get glyph name from source font
        source_glyph_name = get_glyph_name_for_codepoint(source_font, codepoint)

        if source_glyph_name is None:
            char = chr(codepoint) if codepoint <= 0x10FFFF else '?'
            print(f"  Skip: U+{codepoint:04X} ({char}) - not in source font")
            skipped_count += 1
            continue

        # Get glyph name from destination font (may be different)
        dest_glyph_name = get_glyph_name_for_codepoint(dest_font, codepoint)

        if dest_glyph_name is None:
            # Codepoint doesn't exist in destination, need to add it
            # For now, we'll use the source glyph name
            dest_glyph_name = source_glyph_name

            # Add to cmap table
            for table in dest_font['cmap'].tables:
                if hasattr(table, 'cmap'):
                    table.cmap[codepoint] = dest_glyph_name

        # Copy the glyph data
        try:
            source_glyph = source_glyf[source_glyph_name]
            dest_glyf[dest_glyph_name] = source_glyph

            # Copy metrics from hmtx table
            if 'hmtx' in source_font and 'hmtx' in dest_font:
                source_metrics = source_font['hmtx'][source_glyph_name]
                dest_font['hmtx'][dest_glyph_name] = source_metrics

            char = chr(codepoint) if codepoint <= 0x10FFFF else '?'
            print(f"  ✓ Copied: U+{codepoint:04X} ({char}) - {source_glyph_name}")
            copied_count += 1

        except Exception as e:
            char = chr(codepoint) if codepoint <= 0x10FFFF else '?'
            print(f"  Error copying U+{codepoint:04X} ({char}): {e}")
            skipped_count += 1

    # Rename font family if requested
    if new_family_name:
        print(f"\nRenaming font family to: {new_family_name}")
        rename_font_family(dest_font, new_family_name)

    # Save the modified font
    print(f"\nSaving modified font to: {output_path}")
    dest_font.save(output_path)

    print(f"\n✓ Complete!")
    print(f"  Copied: {copied_count} glyphs")
    print(f"  Skipped: {skipped_count} glyphs")

    source_font.close()
    dest_font.close()


def rename_font_family(font, new_family_name):
    """
    Rename the font family in the font's name table.

    Args:
        font: TTFont object
        new_family_name: New family name to set
    """
    if 'name' not in font:
        print("Warning: Font does not have a 'name' table. Cannot rename.")
        return

    name_table = font['name']

    # Get the current subfamily (e.g., "Regular", "Bold") from nameID 2
    subfamily = None
    for record in name_table.names:
        if record.nameID == 2:
            subfamily = record.toUnicode()
            break

    if subfamily is None:
        subfamily = "Regular"

    # Update name records
    for record in name_table.names:
        # nameID 1: Font Family name
        if record.nameID == 1:
            record.string = new_family_name

        # nameID 4: Full font name (Family + Subfamily)
        elif record.nameID == 4:
            full_name = f"{new_family_name} {subfamily}"
            record.string = full_name

        # nameID 6: PostScript name (no spaces)
        elif record.nameID == 6:
            postscript_name = f"{new_family_name.replace(' ', '')}-{subfamily.replace(' ', '')}"
            record.string = postscript_name

        # nameID 16: Typographic Family name (if present)
        elif record.nameID == 16:
            record.string = new_family_name

    print(f"Font family renamed to: {new_family_name}")


def main():
    parser = argparse.ArgumentParser(
        description='Copy glyphs from one TrueType font to another for specified Unicode ranges.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Copy Latin uppercase letters (A-Z)
  %(prog)s source.ttf dest.ttf output.ttf -r U+0041-U+005A

  # Copy CJK Unified Ideographs
  %(prog)s source.ttf dest.ttf output.ttf -r U+4E00-U+9FFF

  # Copy multiple ranges
  %(prog)s source.ttf dest.ttf output.ttf -r U+0041-U+005A -r U+0061-U+007A

  # Copy specific characters
  %(prog)s source.ttf dest.ttf output.ttf -r U+4E00 -r U+4E01 -r U+4E03

  # Copy glyphs and rename font family
  %(prog)s source.ttf dest.ttf output.ttf -r U+4E00-U+9FFF -f "My Custom Font"
        """
    )

    parser.add_argument('source', type=str, help='Source font file (.ttf)')
    parser.add_argument('dest', type=str, help='Destination font file (.ttf)')
    parser.add_argument('output', type=str, help='Output font file (.ttf)')
    parser.add_argument('-r', '--range', action='append', dest='ranges', required=True,
                        help='Unicode range to copy (e.g., U+4E00-U+9FFF). Can be specified multiple times.')
    parser.add_argument('-f', '--family-name', type=str, dest='family_name',
                        help='New font family name for the output font (optional)')

    args = parser.parse_args()

    # Validate input files exist
    source_path = Path(args.source)
    dest_path = Path(args.dest)

    if not source_path.exists():
        print(f"Error: Source font file not found: {source_path}")
        sys.exit(1)

    if not dest_path.exists():
        print(f"Error: Destination font file not found: {dest_path}")
        sys.exit(1)

    output_path = Path(args.output)

    # Perform the copy operation
    try:
        copy_glyphs(str(source_path), str(dest_path), str(output_path), args.ranges, args.family_name)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
