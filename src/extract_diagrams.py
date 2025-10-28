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
import cv2
import numpy as np

from utils.config import Config
from core.preprocessor import ImagePreprocessor
from core.classifier import StrokeClassifier, ContentType
from core.clusterer import DiagramClusterer
from utils.image_utils import save_debug_image, draw_contours_on_image, create_visualization_grid, draw_bounding_boxes


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
    
    # Initialize processing modules
    preprocessor = ImagePreprocessor()
    classifier = StrokeClassifier()
    clusterer = DiagramClusterer()
    
    try:
        # Run preprocessing pipeline
        if args.verbose:
            print("\n=== Phase 2: Image Preprocessing ===")
        
        original_image, processed_image, contours, contour_properties = preprocessor.process_image(
            input_path, verbose=args.verbose
        )
        
        # Run classification pipeline
        if args.verbose:
            print("\n=== Phase 3: Handwriting vs Diagram Classification ===")
        
        classification_results = classifier.classify_contours(contours, original_image, contour_properties)
        
        # Separate diagrams from handwriting and connectors
        diagrams = []
        connectors = []
        handwriting = []
        uncertain = []
        
        for i, (content_type, confidence, props) in enumerate(classification_results):
            contour_info = {
                'id': i,
                'contour': contours[i],
                'properties': props,
                'classification': content_type.value,
                'confidence': confidence
            }
            
            if content_type == ContentType.DIAGRAM:
                diagrams.append(contour_info)
            elif content_type == ContentType.CONNECTOR:
                connectors.append(contour_info)
            elif content_type == ContentType.HANDWRITING:
                handwriting.append(contour_info)
            else:
                uncertain.append(contour_info)
        
        if args.verbose:
            print(f"Classification results:")
            print(f"  - Diagrams: {len(diagrams)}")
            print(f"  - Connectors: {len(connectors)}")
            print(f"  - Handwriting: {len(handwriting)}")
            print(f"  - Uncertain: {len(uncertain)}")
        
        # Run clustering pipeline
        if args.verbose:
            print("\n=== Phase 4: Diagram Clustering & Bounding Box Detection ===")
        
        diagram_clusters = clusterer.cluster_diagrams(
            diagrams, connectors, handwriting, original_image.shape[:2], verbose=args.verbose
        )
        
        # Ensure non-overlapping bounding boxes
        diagram_clusters = clusterer.ensure_non_overlapping_boxes(diagram_clusters, verbose=args.verbose)
        
        if args.verbose:
            print(f"Final diagram clusters: {len(diagram_clusters)}")
            for cluster in diagram_clusters:
                bbox = cluster.bounding_box
                print(f"  Cluster {cluster.id}: {len(cluster.contours)} contours, "
                      f"bbox={bbox}, area={cluster.total_area:.0f}, confidence={cluster.confidence:.3f}")
        
        # Create manifest first (before extraction)
        manifest = {
            "original_file": input_path.name,
            "processing_info": {
                "total_contours": len(contours),
                "contours_above_threshold": len([c for c in contour_properties if c['area'] >= Config.MIN_CONTOUR_AREA]),
                "classification_summary": {
                    "diagrams": len(diagrams),
                    "connectors": len(connectors),
                    "handwriting": len(handwriting),
                    "uncertain": len(uncertain)
                },
                "clustering_summary": {
                    "diagram_clusters": len(diagram_clusters),
                    "total_diagram_area": sum(cluster.total_area for cluster in diagram_clusters)
                },
                "config": Config.to_dict()
            },
            "classified_contours": [
                {
                    "id": result['id'],
                    "classification": result['classification'],
                    "confidence": round(result['confidence'], 3),
                    "area": result['properties']['area'],
                    "bbox": result['properties']['bbox'],
                    "aspect_ratio": round(result['properties']['aspect_ratio'], 3),
                    "extent": round(result['properties']['extent'], 3),
                    "solidity": round(result['properties']['solidity'], 3),
                    "circularity": round(result['properties']['circularity'], 3),
                    "regularity_score": round(result['properties'].get('regularity_score', 0), 3),
                    "straightness": round(result['properties'].get('straightness', 0), 3),
                    "has_straight_lines": result['properties'].get('has_straight_lines', False),
                    "has_perfect_curves": result['properties'].get('has_perfect_curves', False)
                }
                for result in diagrams + connectors + handwriting + uncertain
            ],
            "diagram_clusters": [
                {
                    "id": cluster.id,
                    "contour_count": len(cluster.contours),
                    "contour_ids": cluster.contour_ids,
                    "bounding_box": cluster.bounding_box,
                    "centroid": [round(cluster.centroid[0], 1), round(cluster.centroid[1], 1)],
                    "total_area": round(cluster.total_area, 1),
                    "confidence": round(cluster.confidence, 3)
                }
                for cluster in diagram_clusters
            ],
            "diagrams": [
                {
                    "id": cluster.id,
                    "file": f"diagram_{cluster.id}.png",
                    "bbox": cluster.bounding_box,
                    "confidence": round(cluster.confidence, 3),
                    "extracted": False  # Will be updated after extraction
                }
                for cluster in diagram_clusters
            ]
        }
        
        # Write manifest file first
        manifest_path = output_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Run extraction pipeline using manifest
        if args.verbose:
            print("\n=== Phase 5: Diagram Extraction & PNG Output ===")
        
        # Extract diagrams directly using the data we already have
        extracted_files = []
        
        for cluster in diagram_clusters:
            diagram_id = cluster.id
            bbox = cluster.bounding_box
            filename = f"diagram_{diagram_id}.png"
            
            if args.verbose:
                print(f"Extracting diagram {diagram_id}: {filename}")
                print(f"  Bounding box: {bbox}")
            
            # Extract region directly from original image (no transparency)
            x, y, w, h = bbox
            cropped_region = original_image[y:y+h, x:x+w]
            
            # Save directly as PNG (preserving original quality and color)
            output_file = output_path / filename
            success = cv2.imwrite(str(output_file), cropped_region)
            
            if success:
                extracted_files.append(filename)
                if args.verbose:
                    print(f"    Saved: {filename} ({w}x{h})")
            else:
                if args.verbose:
                    print(f"    Failed to save: {filename}")
        
        # Update manifest with extraction results
        manifest["diagrams"] = [
            {
                **diagram,
                "extracted": diagram["file"] in extracted_files
            }
            for diagram in manifest["diagrams"]
        ]
        
        # Create extraction summary
        extraction_summary = {
            "total_diagrams": len(manifest["diagrams"]),
            "successful_extractions": len(extracted_files),
            "failed_extractions": len(manifest["diagrams"]) - len(extracted_files),
            "success_rate": len(extracted_files) / len(manifest["diagrams"]) if manifest["diagrams"] else 0,
            "extracted_files": extracted_files
        }
        
        manifest["processing_info"]["extraction_summary"] = extraction_summary
        manifest["message"] = "Phase 5 complete: Manifest-based diagram extraction done. All phases complete!"
        
        if args.verbose:
            print(f"Extraction summary:")
            print(f"  - Success rate: {extraction_summary['success_rate']:.1%}")
            print(f"  - Files created: {extraction_summary['extracted_files']}")
        
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
            
            # Save classification visualizations
            diagram_contours = [d['contour'] for d in diagrams]
            handwriting_contours = [h['contour'] for h in handwriting]
            
            # Diagrams in green
            diagram_vis = draw_contours_on_image(original_image, diagram_contours, color=(0, 255, 0))
            save_debug_image(diagram_vis, output_path, "05_diagrams.png")
            
            # Handwriting in red
            handwriting_vis = draw_contours_on_image(original_image, handwriting_contours, color=(0, 0, 255))
            save_debug_image(handwriting_vis, output_path, "06_handwriting.png")
            
            # Combined classification view
            combined_vis = original_image.copy()
            cv2.drawContours(combined_vis, diagram_contours, -1, (0, 255, 0), 2)  # Green for diagrams
            cv2.drawContours(combined_vis, handwriting_contours, -1, (0, 0, 255), 2)  # Red for handwriting
            if uncertain:
                uncertain_contours = [u['contour'] for u in uncertain]
                cv2.drawContours(combined_vis, uncertain_contours, -1, (0, 255, 255), 2)  # Yellow for uncertain
            save_debug_image(combined_vis, output_path, "07_classification.png")
            
            # Save clustering visualizations
            cluster_bboxes = [cluster.bounding_box for cluster in diagram_clusters]
            
            # Bounding boxes visualization
            bbox_vis = draw_bounding_boxes(original_image, cluster_bboxes, color=(255, 0, 255), thickness=3)
            save_debug_image(bbox_vis, output_path, "08_bounding_boxes.png")
            
            # Combined clusters view (contours + bounding boxes)
            cluster_vis = original_image.copy()
            for cluster in diagram_clusters:
                # Draw contours in green
                cv2.drawContours(cluster_vis, cluster.contours, -1, (0, 255, 0), 2)
                # Draw bounding box in magenta
                x, y, w, h = cluster.bounding_box
                cv2.rectangle(cluster_vis, (x, y), (x + w, y + h), (255, 0, 255), 3)
                # Add cluster ID label
                cv2.putText(cluster_vis, f"C{cluster.id}", (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
            save_debug_image(cluster_vis, output_path, "09_clusters.png")
            
            # Create processing steps grid
            debug_images = [original_image, gray_image, thresh_image, processed_image, 
                          contour_vis, diagram_vis, handwriting_vis, combined_vis,
                          bbox_vis, cluster_vis]
            debug_titles = ["Original", "Grayscale", "Threshold", "Processed", 
                          "All Contours", "Diagrams", "Handwriting", "Classification",
                          "Bounding Boxes", "Clusters"]
            grid = create_visualization_grid(debug_images, debug_titles)
            save_debug_image(grid, output_path, "debug_grid.png")
            
            if args.verbose:
                print(f"Debug images saved to {output_path}")
        
        # Update final manifest with extraction results
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        if args.verbose:
            print(f"\nUpdated manifest: {manifest_path}")
            print(f"Found {len(contours)} contours for analysis")
        
        print("Phase 5 complete: Diagram extraction and PNG output ready")
        
    except Exception as e:
        print(f"Error during processing: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
