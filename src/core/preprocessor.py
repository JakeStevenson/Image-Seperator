"""
Image preprocessing pipeline for diagram extraction.

This module handles the core image processing steps:
1. Grayscale conversion
2. Adaptive thresholding
3. Morphological filtering
4. Contour detection
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import Config


class ImagePreprocessor:
    """Handles image preprocessing for diagram extraction."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize preprocessor with configuration."""
        self.config = config or Config()
    
    def load_image(self, image_path: Path) -> np.ndarray:
        """Load image from file path."""
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        return image
    
    def convert_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert image to grayscale with proper contrast preservation."""
        if len(image.shape) == 3:
            # Convert BGR to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            # Already grayscale
            gray = image.copy()
        
        return gray
    
    def apply_adaptive_threshold(self, gray_image: np.ndarray) -> np.ndarray:
        """Apply adaptive thresholding to handle varying lighting conditions."""
        # Use adaptive threshold to handle varying lighting
        thresh = cv2.adaptiveThreshold(
            gray_image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            self.config.ADAPTIVE_THRESH_BLOCK_SIZE,
            self.config.ADAPTIVE_THRESH_C
        )
        
        return thresh
    
    def apply_morphological_operations(self, binary_image: np.ndarray) -> np.ndarray:
        """Apply morphological operations to clean up strokes."""
        # Create kernel for morphological operations
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, 
            self.config.DILATION_KERNEL_SIZE
        )
        
        # Apply morphological closing to connect nearby strokes
        processed = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel)
        
        # Optional: Apply opening to remove noise
        processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)
        
        return processed
    
    def detect_contours(self, binary_image: np.ndarray) -> List[np.ndarray]:
        """Detect contours in the processed binary image."""
        contours, _ = cv2.findContours(
            binary_image,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter contours by minimum area
        filtered_contours = [
            contour for contour in contours
            if cv2.contourArea(contour) >= self.config.MIN_CONTOUR_AREA
        ]
        
        return filtered_contours
    
    def get_contour_properties(self, contour: np.ndarray) -> dict:
        """Extract properties from a contour for classification."""
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        # Bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)
        
        # Aspect ratio
        aspect_ratio = float(w) / h if h > 0 else 0
        
        # Extent (ratio of contour area to bounding rectangle area)
        rect_area = w * h
        extent = float(area) / rect_area if rect_area > 0 else 0
        
        # Solidity (ratio of contour area to convex hull area)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = float(area) / hull_area if hull_area > 0 else 0
        
        # Circularity (4π * area / perimeter²)
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        
        return {
            'area': area,
            'perimeter': perimeter,
            'bbox': (x, y, w, h),
            'aspect_ratio': aspect_ratio,
            'extent': extent,
            'solidity': solidity,
            'circularity': circularity,
            'centroid': self._get_centroid(contour)
        }
    
    def _get_centroid(self, contour: np.ndarray) -> Tuple[float, float]:
        """Calculate centroid of a contour."""
        M = cv2.moments(contour)
        if M['m00'] != 0:
            cx = M['m10'] / M['m00']
            cy = M['m01'] / M['m00']
        else:
            cx, cy = 0, 0
        return (cx, cy)
    
    def process_image(self, image_path: Path, verbose: bool = False) -> Tuple[np.ndarray, np.ndarray, List[np.ndarray], List[dict]]:
        """
        Complete preprocessing pipeline.
        
        Returns:
            - original_image: Original loaded image
            - processed_image: Final processed binary image
            - contours: List of detected contours
            - contour_properties: List of contour property dictionaries
        """
        if verbose:
            print(f"Loading image: {image_path}")
        
        # Step 1: Load image
        original_image = self.load_image(image_path)
        
        if verbose:
            print(f"Image shape: {original_image.shape}")
        
        # Step 2: Convert to grayscale
        gray_image = self.convert_to_grayscale(original_image)
        
        if verbose:
            print("Converted to grayscale")
        
        # Step 3: Apply adaptive thresholding
        thresh_image = self.apply_adaptive_threshold(gray_image)
        
        if verbose:
            print("Applied adaptive thresholding")
        
        # Step 4: Apply morphological operations
        processed_image = self.apply_morphological_operations(thresh_image)
        
        if verbose:
            print("Applied morphological operations")
        
        # Step 5: Detect contours
        contours = self.detect_contours(processed_image)
        
        if verbose:
            print(f"Detected {len(contours)} contours (area >= {self.config.MIN_CONTOUR_AREA})")
        
        # Step 6: Extract contour properties
        contour_properties = [
            self.get_contour_properties(contour) 
            for contour in contours
        ]
        
        if verbose:
            print("Extracted contour properties")
        
        return original_image, processed_image, contours, contour_properties
