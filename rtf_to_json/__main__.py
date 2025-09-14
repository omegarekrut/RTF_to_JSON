"""CLI interface for RTF to JSON converter."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .rtf_converter import RTFConverter
from .models import CampaignData, System


def create_basic_system_from_text(text: str) -> System:
    """Create a basic system from converted text (rudimentary parsing for Phase 1)."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    system_name = lines[0] if lines else "Unnamed System"

    return System(
        id="system_001",
        name=system_name,
        features=[],
        zones=[]
    )


def convert_rtf_to_json(rtf_path: Path, output_path: Optional[Path] = None) -> str:
    """Convert RTF file to JSON format."""
    converter = RTFConverter()

    text = converter.convert_file(rtf_path)

    system = create_basic_system_from_text(text)

    campaign = CampaignData(systems=[system])

    json_data = campaign.model_dump_json(indent=2)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_data)
        print(f"JSON output written to: {output_path}")

    return json_data


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert RTF files to structured JSON for Rogue Trader campaigns"
    )

    parser.add_argument(
        "rtf_file",
        type=Path,
        help="Path to the RTF file to convert"
    )

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output path for JSON file (default: print to stdout)"
    )

    args = parser.parse_args()

    try:
        json_output = convert_rtf_to_json(args.rtf_file, args.output)

        if not args.output:
            print(json_output)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Conversion failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
