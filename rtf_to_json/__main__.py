"""CLI interface for RTF to JSON converter."""

import argparse
import sys
from pathlib import Path
from typing import Optional

import json
from .rtf_converter import RTFConverter
from .parser import CampaignParser
from .models import CampaignData
from .validation import validate_campaign_data


def _generate_output_path(input_path: Path) -> Path:
    """Generate output path from input RTF path."""
    json_dir = Path("json")
    json_dir.mkdir(exist_ok=True)

    output_filename = input_path.stem + ".json"
    return json_dir / output_filename


def convert_rtf_to_json(rtf_path: Path, output_path: Optional[Path] = None) -> Path:
    """Convert RTF file to JSON format."""
    converter = RTFConverter()
    parser = CampaignParser()

    structured_text = converter.convert_file(rtf_path)
    campaign_data = parser.parse(structured_text)

    # Wrap in a campaign_data object as per plan specification
    output_data = {"campaign_data": campaign_data.model_dump()}

    # Validate against schema
    validation_errors = validate_campaign_data(output_data)
    if validation_errors:
        print("Warning: Validation errors found:")
        for error in validation_errors:
            print(f"  - {error}")

    json_data = json.dumps(output_data, indent=2)

    # Auto-generate output path if not provided
    if not output_path:
        output_path = _generate_output_path(rtf_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(json_data)

    print(f"JSON output written to: {output_path}")
    return output_path


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
        help="Output path for JSON file (default: auto-generate json/<filename>.json)"
    )

    args = parser.parse_args()

    try:
        output_path = convert_rtf_to_json(args.rtf_file, args.output)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Conversion failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
