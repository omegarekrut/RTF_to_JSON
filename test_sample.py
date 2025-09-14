#!/usr/bin/env python3
"""Manual test of RTF conversion with a sample file."""

from pathlib import Path
from rtf_to_json.rtf_converter import RTFConverter


def main():
    """Test RTF conversion with a sample file."""
    converter = RTFConverter()
    sample_path = Path('rtf/r.rtf')

    if not sample_path.exists():
        print(f"Sample file not found: {sample_path}")
        return

    print("Testing RTF conversion with sample file...")
    try:
        result = converter.convert_file(sample_path)
        print(f"Successfully converted RTF file. Text length: {len(result)} characters")
        print("First 500 characters:")
        print(result[:500])
        print("...")
    except Exception as e:
        print(f"Error converting RTF: {e}")


if __name__ == '__main__':
    main()