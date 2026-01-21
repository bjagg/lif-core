#!/usr/bin/env python3
"""Fix remaining corrupted unicode sequences in JSON files."""

import os
from pathlib import Path

# Common corrupted UTF-8 sequences when interpreted as Latin-1
REPLACEMENTS = {
    'â€"': '-',      # em-dash
    'â€"': '-',      # en-dash
    'â€™': "'",      # right single quote
    'â€˜': "'",      # left single quote
    'â€œ': '"',      # left double quote
    'â€': '"',       # right double quote (partial)
    'â€¯': ' ',      # narrow no-break space
    'â€¢': '-',      # bullet
    'â€šÃ„Ã´': "'",  # corrupted apostrophe pattern
}

def fix_file(filepath: Path) -> int:
    """Fix corrupted unicode in a file. Returns count of fixes."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    total_fixes = 0

    for corrupted, replacement in REPLACEMENTS.items():
        count = content.count(corrupted)
        if count > 0:
            content = content.replace(corrupted, replacement)
            total_fixes += count
            print(f"  Replaced {count}x '{repr(corrupted)}' -> '{replacement}'")

    if total_fixes > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    return total_fixes

def main():
    sample_data_dir = Path(__file__).parent.parent / 'projects' / 'mongodb' / 'sample_data'

    total_files_fixed = 0
    total_replacements = 0

    for json_file in sample_data_dir.rglob('*.json'):
        fixes = fix_file(json_file)
        if fixes > 0:
            print(f"Fixed {fixes} issues in {json_file.name}")
            total_files_fixed += 1
            total_replacements += fixes

    print(f"\nTotal: {total_replacements} replacements in {total_files_fixed} files")

if __name__ == '__main__':
    main()
