"""Configuration parameters for diagram extraction."""

import os
from typing import Dict, Any


class Config:
    """Configuration class for diagram extraction parameters."""
    
    # Image processing parameters
    MIN_CONTOUR_AREA = int(os.getenv('MIN_CONTOUR_AREA', '500'))  # Lowered to catch smaller sketches
    CLUSTERING_PROXIMITY = int(os.getenv('CLUSTERING_PROXIMITY', '150'))  # Increased to group distant parts of same sketch and flow diagrams
    PADDING = int(os.getenv('PADDING', '10'))  # Increased padding to avoid clipping sketch edges
    MAX_DIAGRAMS = int(os.getenv('MAX_DIAGRAMS', '10'))
    
    # Morphological operations
    DILATION_KERNEL_SIZE = (3, 3)
    
    # Adaptive threshold parameters
    ADAPTIVE_THRESH_BLOCK_SIZE = 11
    ADAPTIVE_THRESH_C = 2
    
    # Confidence threshold (return all, consumer filters later)
    CONFIDENCE_THRESHOLD = 0.0
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'min_contour_area': cls.MIN_CONTOUR_AREA,
            'clustering_proximity': cls.CLUSTERING_PROXIMITY,
            'padding': cls.PADDING,
            'max_diagrams': cls.MAX_DIAGRAMS,
            'dilation_kernel_size': cls.DILATION_KERNEL_SIZE,
            'adaptive_thresh_block_size': cls.ADAPTIVE_THRESH_BLOCK_SIZE,
            'adaptive_thresh_c': cls.ADAPTIVE_THRESH_C,
            'confidence_threshold': cls.CONFIDENCE_THRESHOLD
        }
