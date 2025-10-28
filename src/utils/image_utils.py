"""
Image utility functions for diagram extraction.
"""

import cv2
import numpy as np
from typing import List, Tuple
from pathlib import Path


def save_debug_image(image: np.ndarray, output_path: Path, filename: str) -> None:
    """Save debug image for visualization."""
    debug_path = output_path / filename
    cv2.imwrite(str(debug_path), image)


def draw_contours_on_image(image: np.ndarray, contours: List[np.ndarray], 
                          color: Tuple[int, int, int] = (0, 255, 0), 
                          thickness: int = 2) -> np.ndarray:
    """Draw contours on image for visualization."""
    result = image.copy()
    cv2.drawContours(result, contours, -1, color, thickness)
    return result


def draw_bounding_boxes(image: np.ndarray, bboxes: List[Tuple[int, int, int, int]], 
                       color: Tuple[int, int, int] = (255, 0, 0), 
                       thickness: int = 2) -> np.ndarray:
    """Draw bounding boxes on image."""
    result = image.copy()
    for x, y, w, h in bboxes:
        cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
    return result


def create_visualization_grid(images: List[np.ndarray], titles: List[str], 
                             grid_size: Tuple[int, int] = None) -> np.ndarray:
    """Create a grid visualization of multiple images."""
    if not images:
        return np.zeros((100, 100, 3), dtype=np.uint8)
    
    n_images = len(images)
    if grid_size is None:
        cols = int(np.ceil(np.sqrt(n_images)))
        rows = int(np.ceil(n_images / cols))
    else:
        rows, cols = grid_size
    
    # Ensure all images are the same size and format
    target_height, target_width = 300, 300
    processed_images = []
    
    for img in images:
        # Convert to BGR if grayscale
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        
        # Resize to target size
        resized = cv2.resize(img, (target_width, target_height))
        processed_images.append(resized)
    
    # Create grid
    grid_height = rows * target_height
    grid_width = cols * target_width
    grid = np.zeros((grid_height, grid_width, 3), dtype=np.uint8)
    
    for i, img in enumerate(processed_images):
        row = i // cols
        col = i % cols
        
        y_start = row * target_height
        y_end = y_start + target_height
        x_start = col * target_width
        x_end = x_start + target_width
        
        grid[y_start:y_end, x_start:x_end] = img
        
        # Add title if provided
        if i < len(titles):
            cv2.putText(grid, titles[i], (x_start + 10, y_start + 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return grid


def calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """Calculate Euclidean distance between two points."""
    return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)


def get_image_stats(image: np.ndarray) -> dict:
    """Get basic statistics about an image."""
    if len(image.shape) == 2:
        # Grayscale
        return {
            'shape': image.shape,
            'dtype': str(image.dtype),
            'min': int(image.min()),
            'max': int(image.max()),
            'mean': float(image.mean()),
            'std': float(image.std())
        }
    else:
        # Color
        return {
            'shape': image.shape,
            'dtype': str(image.dtype),
            'channels': image.shape[2] if len(image.shape) > 2 else 1
        }
