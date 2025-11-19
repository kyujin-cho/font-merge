# Font Merge

A Python utility for copying glyphs from one TrueType font to another for specific Unicode ranges. Perfect for creating custom font combinations or merging character sets from different typefaces.

## Features

- Copy specific Unicode ranges between TrueType fonts
- Support for flexible Unicode range notation (U+, 0x, or plain hex)
- Copy multiple ranges in a single operation
- Automatically handles composite glyphs and their components
- Rename font family in the output file
- Preserves glyph metrics (horizontal and vertical) and character mappings
- Proper deep copy of glyph data ensures correct rendering
- Works with both static and variable fonts (output is always static)

## Requirements

- Python 3.x
- fontTools library

## Installation

1. Clone or download this repository

2. Install the required dependencies:

   **Option 1: Direct installation**
   ```bash
   pip install fonttools
   ```

   **Option 2: Using requirements.txt**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Syntax

```bash
./copy_font_glyphs.py SOURCE_FONT DEST_FONT OUTPUT_FONT -r UNICODE_RANGE [OPTIONS]
```

### Arguments

- `SOURCE_FONT`: Path to the font file containing glyphs you want to copy
- `DEST_FONT`: Path to the base font file that will be modified
- `OUTPUT_FONT`: Path where the merged font will be saved
- `-r, --range`: Unicode range to copy (required, can be specified multiple times)
- `-f, --family-name`: New font family name for the output font (optional)

### Unicode Range Formats

The script accepts three Unicode notation formats:

- With U+ prefix: `U+4E00` or `U+4E00-U+9FFF`
- With 0x prefix: `0x4E00` or `0x4E00-0x9FFF`
- Plain hexadecimal: `4E00` or `4E00-9FFF`

## Examples

### Copy CJK Characters

Copy CJK Unified Ideographs from one font to another:

```bash
./copy_font_glyphs.py source.ttf dest.ttf output.ttf -r U+4E00-U+9FFF
```

### Copy Latin Alphabet

Copy both uppercase (A-Z) and lowercase (a-z) letters:

```bash
./copy_font_glyphs.py source.ttf dest.ttf output.ttf -r U+0041-U+005A -r U+0061-U+007A
```

### Copy Specific Characters

Copy only specific individual characters:

```bash
./copy_font_glyphs.py source.ttf dest.ttf output.ttf -r U+4E00 -r U+4E01 -r U+4E03
```

### Copy and Rename Font Family

Merge glyphs and give the output font a new family name:

```bash
./copy_font_glyphs.py source.ttf dest.ttf output.ttf -r U+4E00-U+9FFF -f "My Custom Font"
```

### Combine Latin and CJK

Use Latin characters from one font and CJK from another:

```bash
./copy_font_glyphs.py cjk-font.ttf latin-font.ttf output.ttf \
  -r U+4E00-U+9FFF \
  -f "Mixed Font"
```

## Common Unicode Ranges

Here are some commonly used Unicode ranges:

| Range | Description |
|-------|-------------|
| `U+0020-U+007F` | Basic Latin (ASCII) |
| `U+0080-U+00FF` | Latin-1 Supplement |
| `U+0100-U+017F` | Latin Extended-A |
| `U+0370-U+03FF` | Greek and Coptic |
| `U+0400-U+04FF` | Cyrillic |
| `U+3040-U+309F` | Hiragana |
| `U+30A0-U+30FF` | Katakana |
| `U+4E00-U+9FFF` | CJK Unified Ideographs |
| `U+AC00-U+D7AF` | Hangul Syllables |

For a complete list, see the [Unicode Character Code Charts](https://www.unicode.org/charts/).

## How It Works

1. **Load Fonts**: Opens both the source and destination font files using fontTools
2. **Parse Ranges**: Converts Unicode range strings into lists of codepoints
3. **Lookup Glyphs**: For each codepoint, finds the corresponding glyph name in the source font
4. **Collect Dependencies**: Identifies all component glyphs (for composite glyphs) that need to be copied
5. **Copy Data**: Properly copies glyph outlines (simple and composite), metrics, and character mappings to the destination font using deep copy techniques
6. **Rename (Optional)**: Updates the font family name in the font's metadata if specified
7. **Save**: Writes the modified font to the output file

## Use Cases

- **Multilingual Fonts**: Combine Latin characters from one font with CJK characters from another
- **Custom Typography**: Create unique font combinations for branding or design projects
- **Font Fallbacks**: Build fonts with specific character coverage for web or app use
- **Character Set Extension**: Add missing characters from another font to complete coverage
- **Font Family Creation**: Generate custom font families with specific character sets

## Font Tables Modified

The script modifies the following OpenType/TrueType tables:

- `cmap`: Character-to-glyph mapping
- `glyf`: Glyph outline data
- `hmtx`: Horizontal metrics (width and positioning)
- `name`: Font naming information (when using `-f` option)

**Note**: Glyphs are renamed using standard naming conventions (`uniXXXX` format) to ensure consistency between glyph names and Unicode codepoints. This prevents warnings from font validation tools.

## Limitations

- Currently supports TrueType fonts (.ttf) only
- **Variable fonts**: Input fonts can be variable, but the output font will always be a static font
  - Variable font tables (`fvar`, `gvar`, `STAT`, etc.) are removed to prevent corruption
  - Glyphs are copied from the default instance of variable fonts
- Does not copy OpenType features (GSUB/GPOS tables like ligatures, kerning rules remain from destination font)
- Kerning pairs between copied and existing glyphs are not automatically updated
- Font hinting instructions may not be perfectly preserved in all cases

## Testing

The project includes a comprehensive integration test suite to verify functionality.

### Running Tests

**Unix/Linux/Mac:**
```bash
./run_tests.sh
```

**Windows:**
```cmd
run_tests.bat
```

**Python directly:**
```bash
python test_integration.py
```

### Test Coverage

The test suite includes:
- CJK Unicode range copying (U+4E00-U+9FFF)
- Small range precision testing
- Font family renaming verification
- Glyph metrics preservation
- Multiple range copying
- Missing codepoint handling
- Script help and usage validation

All tests use the included sample fonts (PretendardJPVariable.ttf and GoogleSansFlex).

## Troubleshooting

**Error: fontTools library is required**
```bash
pip install fonttools
```

**Character not found in source font**
- Verify the Unicode range is correct
- Check that the source font actually contains the desired characters
- Use a font inspection tool to confirm character coverage

**Output font not working**
- Ensure both input fonts are valid TrueType files
- Some font validation tools may flag merged fonts; this is usually cosmetic
- Test the font in multiple applications to verify compatibility

## License

This script uses the fontTools library, which is licensed under the MIT License.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## See Also

- [fontTools Documentation](https://fonttools.readthedocs.io/)
- [Unicode Character Database](https://www.unicode.org/ucd/)
- [OpenType Specification](https://docs.microsoft.com/en-us/typography/opentype/spec/)
