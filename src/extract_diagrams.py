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
from core.preprocessor import ImagePreprocessor
from utils.image_utils import save_debug_image, draw_contours_on_image, create_visualization_grid


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
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Save debug images showing processing steps'
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
        print(f"Debug mode: {args.debug}")
    
    # Initialize preprocessor
    preprocessor = ImagePreprocessor()
    
    try:
        # Run preprocessing pipeline
        if args.verbose:
            print("\n=== Phase 2: Image Preprocessing ===")
        
        original_image, processed_image, contours, contour_properties = preprocessor.process_image(
            input_path, verbose=args.verbose
        )
        
        # Save debug images if requested
        if args.debug:
            if args.verbose:
                print("\nSaving debug images...")
            
            # Save grayscale version
            gray_image = preprocessor.convert_to_grayscale(original_image)
            save_debug_image(gray_image, output_path, "01_grayscale.png")
            
            # Save thresholded version
            thresh_image = preprocessor.apply_adaptive_threshold(gray_image)
            save_debug_image(thresh_image, output_path, "02_threshold.png")
            
            # Save final processed version
            save_debug_image(processed_image, output_path, "03_processed.png")
            
            # Save contours visualization
            contour_vis = draw_contours_on_image(original_image, contours)
            save_debug_image(contour_vis, output_path, "04_contours.png")
            
            # Create processing steps grid
            debug_images = [original_image, gray_image, thresh_image, processed_image, contour_vis]
            debug_titles = ["Original", "Grayscale", "Threshold", "Processed", "Contours"]
            grid = create_visualization_grid(debug_images, debug_titles)
            save_debug_image(grid, output_path, "debug_grid.png")
            
            if args.verbose:
                print(f"Debug images saved to {output_path}")
        
        # Create manifest with preprocessing results
        manifest = {
            "original_file": input_path.name,
            "processing_info": {
                "total_contours": len(contours),
                "contours_above_threshold": len([c for c in contour_properties if c['area'] >= Config.MIN_CONTOUR_AREA]),
                "config": Config.to_dict()
            },
            "contours": [
                {
                    "id": i,
                    "area": props['area'],
                    "bbox": props['bbox'],
                    "aspect_ratio": round(props['aspect_ratio'], 3),
                    "extent": round(props['extent'], 3),
                    "solidity": round(props['solidity'], 3),
                    "circularity": round(props['circularity'], 3)
                }
                for i, props in enumerate(contour_properties)
            ],
            "diagrams": [],
            "message": "Phase 2 complete: Image preprocessing and contour detection done. Classification pending."
        }
        
        # Write manifest file
        manifest_path = output_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        if args.verbose:
            print(f"\nCreated manifest: {manifest_path}")
            print(f"Found {len(contours)} contours for analysis")
        
        print("Phase 2 complete: Image preprocessing and contour detection ready")
        
    except Exception as e:
        print(f"Error during processing: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
