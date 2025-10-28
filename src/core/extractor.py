"""
Diagram Extraction and PNG Output

This module extracts diagram regions from the original image and creates
transparent-background PNG files for each diagram cluster.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import Config
from core.clusterer import DiagramCluster


class DiagramExtractor:
    """Extracts diagrams and creates transparent PNG files."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize extractor with configuration."""
        self.config = config or Config()
    
    def create_mask_from_contours(self, contours: List[np.ndarray], 
                                 image_shape: Tuple[int, int]) -> np.ndarray:
        """Create a binary mask from contours."""
        mask = np.zeros(image_shape, dtype=np.uint8)
        cv2.fillPoly(mask, contours, 255)
        return mask
    
    def extract_diagram_region(self, original_image: np.ndarray, 
                              processed_image: np.ndarray,
                              cluster: DiagramCluster,
                              verbose: bool = False) -> np.ndarray:
        """
        Extract a diagram region with transparent background.
        
        Args:
            original_image: Original color image
            processed_image: Binary processed image from preprocessing
            cluster: DiagramCluster containing contours and bounding box
            verbose: Enable verbose output
            
        Returns:
            RGBA image with transparent background
        """
        x, y, w, h = cluster.bounding_box
        
        if verbose:
            print(f"  Extracting cluster {cluster.id}: bbox={cluster.bounding_box}")
        
        # Crop the original image to bounding box
        cropped_original = original_image[y:y+h, x:x+w]
        
        # Create mask from cluster contours
        mask = np.zeros(original_image.shape[:2], dtype=np.uint8)
        
        # Adjust contours to be relative to the full image (they should already be)
        cv2.fillPoly(mask, cluster.contours, 255)
        
        # Crop the mask to the same bounding box
        cropped_mask = mask[y:y+h, x:x+w]
        
        # Apply morphological operations to clean up the mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cropped_mask = cv2.morphologyEx(cropped_mask, cv2.MORPH_CLOSE, kernel)
        cropped_mask = cv2.morphologyEx(cropped_mask, cv2.MORPH_OPEN, kernel)
        
        # Create RGBA image
        if len(cropped_original.shape) == 3:
            # Convert BGR to RGB
            cropped_rgb = cv2.cvtColor(cropped_original, cv2.COLOR_BGR2RGB)
        else:
            # Convert grayscale to RGB
            cropped_rgb = cv2.cvtColor(cropped_original, cv2.COLOR_GRAY2RGB)
        
        # Create RGBA image with alpha channel
        rgba_image = np.zeros((h, w, 4), dtype=np.uint8)
        rgba_image[:, :, :3] = cropped_rgb
        rgba_image[:, :, 3] = cropped_mask  # Alpha channel from mask
        
        return rgba_image
    
    def enhance_diagram_contrast(self, rgba_image: np.ndarray) -> np.ndarray:
        """Enhance contrast of the diagram while preserving transparency."""
        # Work on RGB channels only
        rgb = rgba_image[:, :, :3].copy()
        alpha = rgba_image[:, :, 3].copy()
        
        # Convert to grayscale for processing
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_gray = clahe.apply(gray)
        
        # Convert back to RGB
        enhanced_rgb = cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2RGB)
        
        # Combine with original alpha
        result = np.zeros_like(rgba_image)
        result[:, :, :3] = enhanced_rgb
        result[:, :, 3] = alpha
        
        return result
    
    def save_diagram_png(self, rgba_image: np.ndarray, output_path: Path, 
                        filename: str, verbose: bool = False) -> bool:
        """
        Save RGBA image as PNG with transparency.
        
        Args:
            rgba_image: RGBA image array
            output_path: Output directory path
            filename: Output filename
            verbose: Enable verbose output
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_path = output_path / filename
            
            # Convert RGBA to BGRA for OpenCV
            bgra_image = cv2.cvtColor(rgba_image, cv2.COLOR_RGBA2BGRA)
            
            # Save as PNG with transparency
            success = cv2.imwrite(str(full_path), bgra_image)
            
            if verbose:
                if success:
                    print(f"    Saved: {filename} ({rgba_image.shape[1]}x{rgba_image.shape[0]})")
                else:
                    print(f"    Failed to save: {filename}")
            
            return success
            
        except Exception as e:
            if verbose:
                print(f"    Error saving {filename}: {e}")
            return False
    
    def get_diagram_stats(self, rgba_image: np.ndarray) -> Dict:
        """Get statistics about the extracted diagram."""
        alpha = rgba_image[:, :, 3]
        
        # Count non-transparent pixels
        non_transparent_pixels = np.sum(alpha > 0)
        total_pixels = alpha.shape[0] * alpha.shape[1]
        
        # Calculate coverage
        coverage = non_transparent_pixels / total_pixels if total_pixels > 0 else 0
        
        # Get bounding box of non-transparent content
        coords = np.where(alpha > 0)
        if len(coords[0]) > 0:
            min_y, max_y = coords[0].min(), coords[0].max()
            min_x, max_x = coords[1].min(), coords[1].max()
            content_bbox = (min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
        else:
            content_bbox = (0, 0, 0, 0)
        
        return {
            'width': rgba_image.shape[1],
            'height': rgba_image.shape[0],
            'non_transparent_pixels': int(non_transparent_pixels),
            'total_pixels': int(total_pixels),
            'coverage': round(coverage, 3),
            'content_bbox': content_bbox
        }
    
    def extract_all_diagrams(self, original_image: np.ndarray,
                           processed_image: np.ndarray,
                           diagram_clusters: List[DiagramCluster],
                           output_path: Path,
                           verbose: bool = False) -> List[Dict]:
        """
        Extract all diagram clusters as PNG files.
        
        Args:
            original_image: Original color image
            processed_image: Binary processed image
            diagram_clusters: List of DiagramCluster objects
            output_path: Output directory path
            verbose: Enable verbose output
            
        Returns:
            List of extraction results with metadata
        """
        if verbose:
            print(f"Extracting {len(diagram_clusters)} diagrams...")
        
        extraction_results = []
        
        for cluster in diagram_clusters:
            if verbose:
                print(f"Processing cluster {cluster.id}...")
            
            # Extract diagram region
            rgba_image = self.extract_diagram_region(
                original_image, processed_image, cluster, verbose
            )
            
            # Enhance contrast (optional)
            enhanced_image = self.enhance_diagram_contrast(rgba_image)
            
            # Generate filename
            filename = f"diagram_{cluster.id}.png"
            
            # Save PNG file
            success = self.save_diagram_png(
                enhanced_image, output_path, filename, verbose
            )
            
            # Get diagram statistics
            stats = self.get_diagram_stats(enhanced_image)
            
            # Create result record (convert numpy types to Python types for JSON serialization)
            result = {
                'cluster_id': int(cluster.id),
                'filename': filename,
                'success': bool(success),
                'bounding_box': [int(x) for x in cluster.bounding_box],
                'confidence': float(cluster.confidence),
                'contour_count': int(len(cluster.contours)),
                'total_area': float(cluster.total_area),
                'width': int(stats['width']),
                'height': int(stats['height']),
                'non_transparent_pixels': int(stats['non_transparent_pixels']),
                'total_pixels': int(stats['total_pixels']),
                'coverage': float(stats['coverage']),
                'content_bbox': [int(x) for x in stats['content_bbox']]
            }
            
            extraction_results.append(result)
            
            if verbose:
                print(f"  Result: {'SUCCESS' if success else 'FAILED'}, "
                      f"coverage={stats['coverage']:.1%}")
        
        if verbose:
            successful = sum(1 for r in extraction_results if r['success'])
            print(f"Extraction complete: {successful}/{len(extraction_results)} successful")
        
        return extraction_results
    
    def create_extraction_summary(self, extraction_results: List[Dict]) -> Dict:
        """Create a summary of the extraction process."""
        successful = [r for r in extraction_results if r['success']]
        failed = [r for r in extraction_results if not r['success']]
        
        total_area = sum(r['total_area'] for r in successful)
        avg_coverage = np.mean([r['coverage'] for r in successful]) if successful else 0
        
        return {
            'total_diagrams': len(extraction_results),
            'successful_extractions': len(successful),
            'failed_extractions': len(failed),
            'success_rate': len(successful) / len(extraction_results) if extraction_results else 0,
            'total_extracted_area': round(total_area, 1),
            'average_coverage': round(avg_coverage, 3),
            'extracted_files': [r['filename'] for r in successful]
        }
