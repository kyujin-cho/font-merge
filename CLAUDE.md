# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based font manipulation tool that copies glyphs from one TrueType font file to another for specified Unicode ranges. The primary use case is merging specific character sets (e.g., CJK characters, Latin alphabets) from different font files.

## Dependencies

- **fontTools**: Required Python library for font manipulation
  - Install with: `pip install fonttools`
  - Or use: `pip install -r requirements.txt`

## Core Script: copy_font_glyphs.py

The main script (`copy_font_glyphs.py`) is executable and can be run directly:

```bash
./copy_font_glyphs.py source.ttf dest.ttf output.ttf -r UNICODE_RANGE
```

### Key Functionality

The script operates on three font files:
1. **Source font**: Where glyphs are copied from
2. **Destination font**: The base font to modify
3. **Output font**: The resulting merged font file

### Unicode Range Formats

The script accepts flexible Unicode range specifications:
- Single codepoint: `U+4E00` or `0x4E00` or `4E00`
- Range: `U+4E00-U+9FFF` or `0x4E00-0x9FFF` or `4E00-9FFF`
- Multiple ranges: Use `-r` flag multiple times

### Common Usage Examples

```bash
# Copy CJK Unified Ideographs
./copy_font_glyphs.py source.ttf dest.ttf output.ttf -r U+4E00-U+9FFF

# Copy Latin uppercase (A-Z) and lowercase (a-z)
./copy_font_glyphs.py source.ttf dest.ttf output.ttf -r U+0041-U+005A -r U+0061-U+007A

# Copy specific characters
./copy_font_glyphs.py source.ttf dest.ttf output.ttf -r U+4E00 -r U+4E01 -r U+4E03

# Copy glyphs and rename the font family
./copy_font_glyphs.py source.ttf dest.ttf output.ttf -r U+4E00-U+9FFF -f "My Custom Font"
```

### Font Family Renaming

Use the `-f` or `--family-name` option to rename the font family in the output file. This updates:
- Font Family name (nameID 1)
- Full font name (nameID 4)
- PostScript name (nameID 6)
- Typographic Family name (nameID 16, if present)

## Architecture Notes

### Font Processing Flow

1. **Load fonts**: Opens both source and destination TTFont objects
2. **Parse ranges**: Converts Unicode range strings into lists of codepoints
3. **Glyph lookup**: For each codepoint, retrieves glyph names from font cmap tables
4. **Copy operations**:
   - Copies glyph data from source `glyf` table to destination `glyf` table
   - Copies horizontal metrics from `hmtx` table
   - Updates `cmap` table if codepoint doesn't exist in destination
5. **Rename (optional)**: Updates font family names in the `name` table if `-f` option is provided
6. **Save**: Writes modified font to output path

### Key Functions

- `parse_unicode_range()`: Handles flexible Unicode range string parsing
- `get_glyph_name_for_codepoint()`: Maps Unicode codepoints to font-internal glyph names
- `copy_glyphs()`: Main logic for copying glyphs between fonts
- `rename_font_family()`: Updates font family names in the font's name table

### Font Tables Used

- `cmap`: Character-to-glyph mapping (Unicode → glyph name)
- `glyf`: Glyph outline data
- `hmtx`: Horizontal metrics (advance width, left side bearing)
- `name`: Font naming table (used for font family renaming)

## Sample Font Files

The repository includes three font files likely used for testing:
- `GoogleSansFlex-VariableFont_GRAD,ROND,opsz,slnt,wdth,wght.ttf`
- `GoogleSansFlexCJK-Variable.ttf`
- `PretendardJPVariable.ttf`

These are variable fonts supporting multiple languages (Latin, CJK, Japanese).
