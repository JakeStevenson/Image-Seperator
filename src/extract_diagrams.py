#!/usr/bin/env python3
"""
Diagram Extraction Tool for Handwritten Notes

Extracts non-handwriting diagrams/sketches from handwritten notes (PNG)
into separate transparent-background PNGs with JSON manifest.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

from utils.config import Config


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract diagrams from handwritten notes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract_diagrams.py --input note.png --output ./out/
  python extract_diagrams.py note.png ./out/
        """
    )
    
    parser.add_argument(
        'input_file',
        nargs='?',
        help='Input PNG file path'
    )
    
    parser.add_argument(
        'output_dir',
        nargs='?',
        help='Output directory path'
    )
    
    parser.add_argument(
        '--input', '-i',
        dest='input_file_flag',
        help='Input PNG file path (alternative to positional argument)'
    )
    
    parser.add_argument(
        '--output', '-o',
        dest='output_dir_flag',
        help='Output directory path (alternative to positional argument)'
    )
    
    parser.add_argument(
        '--config',
        help='Configuration JSON file path (optional)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> tuple[Path, Path]:
    """Validate and normalize arguments."""
    # Determine input file
    input_file = args.input_file or args.input_file_flag
    if not input_file:
        print("Error: Input file is required", file=sys.stderr)
        sys.exit(1)
    
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: Input file does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    if input_path.suffix.lower() != '.png':
        print(f"Error: Input file must be a PNG: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    # Determine output directory
    output_dir = args.output_dir or args.output_dir_flag
    if not output_dir:
        print("Error: Output directory is required", file=sys.stderr)
        sys.exit(1)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    return input_path, output_path


def main():
    """Main entry point."""
    args = parse_arguments()
    input_path, output_path = validate_arguments(args)
    
    if args.verbose:
        print(f"Input file: {input_path}")
        print(f"Output directory: {output_path}")
        print(f"Configuration: {Config.to_dict()}")
    
    # TODO: Implement the actual diagram extraction pipeline
    # For now, create a placeholder manifest
    manifest = {
        "original_file": input_path.name,
        "diagrams": [],
        "message": "Diagram extraction not yet implemented"
    }
    
    # Write manifest file
    manifest_path = output_path / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    if args.verbose:
        print(f"Created manifest: {manifest_path}")
    
    print("Phase 1 complete: Project structure and CLI interface ready")


if __name__ == "__main__":
    main()
