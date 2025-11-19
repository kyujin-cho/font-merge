#!/usr/bin/env python3
"""
Font Glyph Copy Script
Copies designated Unicode ranges of glyphs from one TrueType font file to another.
"""

import sys
import argparse
import copy
import traceback
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


def get_component_glyphs(font, glyph_name):
    """
    Recursively get all component glyph names that a glyph depends on.

    Args:
        font: TTFont object
        glyph_name: Name of the glyph to analyze

    Returns:
        Set of glyph names that this glyph depends on
    """
    components = set()

    if 'glyf' not in font:
        return components

    try:
        glyph = font['glyf'][glyph_name]

        # Check if this is a composite glyph
        if glyph.isComposite():
            for component in glyph.components:
                component_name = component.glyphName
                components.add(component_name)
                # Recursively get components of components
                components.update(get_component_glyphs(font, component_name))
    except:
        pass

    return components


def generate_glyph_name(codepoint, existing_names):
    """
    Generate a glyph name for a codepoint that doesn't conflict with existing names.

    Args:
        codepoint: Unicode codepoint
        existing_names: Set of existing glyph names to avoid conflicts

    Returns:
        A unique glyph name
    """
    # Standard glyph naming: uni + 4-digit hex for BMP, u + 5+ digits for others
    if codepoint <= 0xFFFF:
        base_name = f"uni{codepoint:04X}"
    else:
        base_name = f"u{codepoint:04X}"

    # If no conflict, return the base name
    if base_name not in existing_names:
        return base_name

    # If there's a conflict, add a suffix
    counter = 1
    while f"{base_name}.alt{counter}" in existing_names:
        counter += 1

    return f"{base_name}.alt{counter}"


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

    # Collect all glyphs to copy (including components)
    glyphs_to_copy = {}  # Maps source_glyph_name -> (codepoint, dest_glyph_name)
    component_glyphs = set()  # Component glyphs that need to be copied

    # Get existing glyph names in destination to avoid conflicts
    existing_glyph_names = set(dest_glyf.keys())

    # First pass: collect main glyphs and their codepoints
    for codepoint in codepoints_to_copy:
        # Get glyph name from source font
        source_glyph_name = get_glyph_name_for_codepoint(source_font, codepoint)

        if source_glyph_name is None:
            char = chr(codepoint) if codepoint <= 0x10FFFF else '?'
            print(f"  Skip: U+{codepoint:04X} ({char}) - not in source font")
            skipped_count += 1
            continue

        # Generate appropriate glyph name that matches the codepoint
        # Always generate a new name to ensure consistency between name and codepoint
        dest_glyph_name = generate_glyph_name(codepoint, existing_glyph_names)
        existing_glyph_names.add(dest_glyph_name)

        glyphs_to_copy[source_glyph_name] = (codepoint, dest_glyph_name)

        # Get all component glyphs this glyph depends on
        components = get_component_glyphs(source_font, source_glyph_name)
        component_glyphs.update(components)

    # Add component glyphs to the copy list
    for component_name in component_glyphs:
        if component_name not in glyphs_to_copy and component_name in source_glyf:
            # Component glyphs keep their original names and don't have direct codepoint mappings
            glyphs_to_copy[component_name] = (None, component_name)

    print(f"Total glyphs to copy (including components): {len(glyphs_to_copy)}")

    # Second pass: copy all glyphs
    for source_glyph_name, (codepoint, dest_glyph_name) in glyphs_to_copy.items():
        try:
            # Get the source glyph
            source_glyph = source_glyf[source_glyph_name]

            # Use TTGlyphPen to properly copy the glyph
            # This handles both simple and composite glyphs correctly
            pen = TTGlyphPen(dest_font.getGlyphSet())

            # Draw the source glyph using the pen
            source_glyph_set = source_font.getGlyphSet()
            if source_glyph_name in source_glyph_set:
                try:
                    source_glyph_set[source_glyph_name].draw(pen)
                    new_glyph = pen.glyph()

                    # Preserve glyph properties
                    if hasattr(source_glyph, 'program'):
                        new_glyph.program = source_glyph.program

                    dest_glyf[dest_glyph_name] = new_glyph
                except:
                    # Fallback: direct copy for glyphs that can't be drawn
                    dest_glyf[dest_glyph_name] = copy.deepcopy(source_glyph)
            else:
                # Direct copy for glyphs not in glyph set
                dest_glyf[dest_glyph_name] = copy.deepcopy(source_glyph)

            # Copy metrics from hmtx table
            if 'hmtx' in source_font and 'hmtx' in dest_font:
                if source_glyph_name in source_font['hmtx'].metrics:
                    source_metrics = source_font['hmtx'][source_glyph_name]
                    dest_font['hmtx'][dest_glyph_name] = source_metrics

            # Copy vertical metrics if present
            if 'vmtx' in source_font and 'vmtx' in dest_font:
                if source_glyph_name in source_font['vmtx'].metrics:
                    source_vmetrics = source_font['vmtx'][source_glyph_name]
                    dest_font['vmtx'][dest_glyph_name] = source_vmetrics

            # Update cmap if this glyph has a codepoint
            if codepoint is not None:
                for table in dest_font['cmap'].tables:
                    if hasattr(table, 'cmap'):
                        table.cmap[codepoint] = dest_glyph_name

                char = chr(codepoint) if codepoint <= 0x10FFFF else '?'
                print(f"  ✓ Copied: U+{codepoint:04X} ({char}) -> {dest_glyph_name}")
                copied_count += 1
            else:
                print(f"  ✓ Copied component: {dest_glyph_name}")

        except Exception as e:
            if codepoint is not None:
                char = chr(codepoint) if codepoint <= 0x10FFFF else '?'
                print(f"  Error copying U+{codepoint:04X} ({char}): {e}")
            else:
                print(f"  Error copying component {source_glyph_name}: {e}")
            skipped_count += 1
            traceback.print_exc()

    # Rename font family if requested
    if new_family_name:
        print(f"\nRenaming font family to: {new_family_name}")
        rename_font_family(dest_font, new_family_name)

    # Remove variable font tables to avoid corruption
    # When glyphs are copied, variation tables become invalid
    variation_tables = ['fvar', 'gvar', 'avar', 'STAT', 'MVAR', 'HVAR', 'VVAR']
    removed_tables = []
    for table_tag in variation_tables:
        if table_tag in dest_font:
            del dest_font[table_tag]
            removed_tables.append(table_tag)

    if removed_tables:
        print(f"\nNote: Removed variable font tables: {', '.join(removed_tables)}")
        print("      Output font will be a static font (non-variable)")

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
