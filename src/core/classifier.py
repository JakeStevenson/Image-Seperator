"""
Handwriting vs Diagram Classification Logic

This module implements heuristics to distinguish between handwritten text
and diagram elements based on contour properties and stroke analysis.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from enum import Enum
import math

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import Config


class ContentType(Enum):
    """Classification types for detected content."""
    HANDWRITING = "handwriting"
    DIAGRAM = "diagram"
    UNCERTAIN = "uncertain"


class StrokeClassifier:
    """Classifies contours as handwriting or diagrams based on stroke analysis."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize classifier with configuration."""
        self.config = config or Config()
    
    def analyze_stroke_properties(self, contour: np.ndarray, image: np.ndarray) -> Dict:
        """Analyze detailed stroke properties for classification."""
        # Basic contour properties
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if perimeter == 0:
            return self._default_properties()
        
        # Bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h if h > 0 else 0
        
        # Convex hull analysis
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = float(area) / hull_area if hull_area > 0 else 0
        
        # Circularity (4π * area / perimeter²)
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        
        # Extent (ratio of contour area to bounding rectangle area)
        rect_area = w * h
        extent = float(area) / rect_area if rect_area > 0 else 0
        
        # Stroke analysis
        stroke_props = self._analyze_stroke_characteristics(contour, image)
        
        # Shape regularity
        shape_props = self._analyze_shape_regularity(contour)
        
        # Geometric features
        geometric_props = self._analyze_geometric_features(contour)
        
        return {
            'area': area,
            'perimeter': perimeter,
            'aspect_ratio': aspect_ratio,
            'solidity': solidity,
            'circularity': circularity,
            'extent': extent,
            'bbox': (x, y, w, h),
            **stroke_props,
            **shape_props,
            **geometric_props
        }
    
    def _default_properties(self) -> Dict:
        """Return default properties for invalid contours."""
        return {
            'area': 0, 'perimeter': 0, 'aspect_ratio': 0, 'solidity': 0,
            'circularity': 0, 'extent': 0, 'bbox': (0, 0, 0, 0),
            'straightness': 0, 'curvature_variation': 0, 'stroke_width_variation': 0,
            'corner_count': 0, 'line_segments': 0, 'curve_segments': 0,
            'has_straight_lines': False, 'has_perfect_curves': False,
            'has_corners': False, 'regularity_score': 0
        }
    
    def _analyze_stroke_characteristics(self, contour: np.ndarray, image: np.ndarray) -> Dict:
        """Analyze stroke-specific characteristics."""
        # Approximate contour to reduce noise
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Calculate straightness (ratio of direct distance to contour length)
        if len(approx) >= 2:
            start_point = approx[0][0]
            end_point = approx[-1][0]
            direct_distance = np.linalg.norm(end_point - start_point)
            contour_length = cv2.arcLength(contour, False)
            straightness = direct_distance / contour_length if contour_length > 0 else 0
        else:
            straightness = 0
        
        # Analyze curvature variation
        curvature_variation = self._calculate_curvature_variation(contour)
        
        # Estimate stroke width variation (simplified)
        stroke_width_variation = self._estimate_stroke_width_variation(contour, image)
        
        return {
            'straightness': straightness,
            'curvature_variation': curvature_variation,
            'stroke_width_variation': stroke_width_variation
        }
    
    def _analyze_shape_regularity(self, contour: np.ndarray) -> Dict:
        """Analyze geometric regularity of the shape."""
        # Approximate contour
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        corner_count = len(approx)
        
        # Detect line segments vs curves
        line_segments = 0
        curve_segments = 0
        
        if corner_count >= 3:
            # Simple heuristic: if approximation has few points, likely geometric
            if corner_count <= 8:
                line_segments = corner_count
            else:
                curve_segments = corner_count
        
        # Check for geometric shapes
        has_straight_lines = self._has_straight_lines(approx)
        has_perfect_curves = self._has_perfect_curves(contour)
        has_corners = corner_count >= 3 and corner_count <= 12
        
        # Overall regularity score
        regularity_score = self._calculate_regularity_score(contour, approx)
        
        return {
            'corner_count': corner_count,
            'line_segments': line_segments,
            'curve_segments': curve_segments,
            'has_straight_lines': has_straight_lines,
            'has_perfect_curves': has_perfect_curves,
            'has_corners': has_corners,
            'regularity_score': regularity_score
        }
    
    def _analyze_geometric_features(self, contour: np.ndarray) -> Dict:
        """Analyze specific geometric features that indicate diagrams."""
        # Check for rectangular shapes
        x, y, w, h = cv2.boundingRect(contour)
        rect_area = w * h
        contour_area = cv2.contourArea(contour)
        rectangularity = contour_area / rect_area if rect_area > 0 else 0
        
        # Check for circular shapes
        (center_x, center_y), radius = cv2.minEnclosingCircle(contour)
        circle_area = np.pi * radius * radius
        circularity_fit = contour_area / circle_area if circle_area > 0 else 0
        
        # Check for triangular shapes
        triangle_area = 0.5 * w * h  # Simplified
        triangularity = contour_area / triangle_area if triangle_area > 0 else 0
        
        return {
            'rectangularity': rectangularity,
            'circularity_fit': circularity_fit,
            'triangularity': triangularity
        }
    
    def _calculate_curvature_variation(self, contour: np.ndarray) -> float:
        """Calculate variation in curvature along the contour."""
        if len(contour) < 5:
            return 0
        
        # Sample points along contour
        num_points = min(20, len(contour))
        indices = np.linspace(0, len(contour) - 1, num_points, dtype=int)
        points = contour[indices].reshape(-1, 2)
        
        curvatures = []
        for i in range(1, len(points) - 1):
            # Calculate curvature at each point using three consecutive points
            p1, p2, p3 = points[i-1], points[i], points[i+1]
            
            # Vectors
            v1 = p2 - p1
            v2 = p3 - p2
            
            # Cross product for curvature
            cross = np.cross(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            if norm_v1 > 0 and norm_v2 > 0:
                curvature = abs(cross) / (norm_v1 * norm_v2)
                curvatures.append(curvature)
        
        return np.std(curvatures) if curvatures else 0
    
    def _estimate_stroke_width_variation(self, contour: np.ndarray, image: np.ndarray) -> float:
        """Estimate variation in stroke width (simplified approach)."""
        # This is a simplified estimation
        # In a full implementation, you'd use distance transform
        x, y, w, h = cv2.boundingRect(contour)
        roi_area = w * h
        contour_area = cv2.contourArea(contour)
        
        # Rough estimate based on area vs perimeter ratio
        perimeter = cv2.arcLength(contour, True)
        if perimeter > 0:
            width_estimate = contour_area / perimeter
            # Normalize by expected width for this size
            expected_width = max(1, min(w, h) / 20)
            variation = abs(width_estimate - expected_width) / expected_width
            return min(variation, 2.0)  # Cap at 2.0
        
        return 0
    
    def _has_straight_lines(self, approx_contour: np.ndarray) -> bool:
        """Check if contour has predominantly straight line segments."""
        if len(approx_contour) < 2:
            return False
        
        # If approximation resulted in very few points, likely has straight lines
        return len(approx_contour) <= 8
    
    def _has_perfect_curves(self, contour: np.ndarray) -> bool:
        """Check if contour has smooth, regular curves."""
        # Check if contour fits well to an ellipse
        if len(contour) >= 5:
            try:
                ellipse = cv2.fitEllipse(contour)
                # Create ellipse contour
                center = (int(ellipse[0][0]), int(ellipse[0][1]))
                axes = (int(ellipse[1][0]/2), int(ellipse[1][1]/2))
                angle = ellipse[2]
                
                # Simple check: if contour is roughly elliptical
                contour_area = cv2.contourArea(contour)
                ellipse_area = np.pi * axes[0] * axes[1]
                
                if ellipse_area > 0:
                    fit_ratio = contour_area / ellipse_area
                    return 0.7 <= fit_ratio <= 1.3
            except:
                pass
        
        return False
    
    def _calculate_regularity_score(self, contour: np.ndarray, approx: np.ndarray) -> float:
        """Calculate overall regularity score (0-1, higher = more regular/geometric)."""
        scores = []
        
        # Approximation efficiency (fewer points = more regular)
        if len(contour) > 0:
            approx_efficiency = 1.0 - (len(approx) / len(contour))
            scores.append(approx_efficiency)
        
        # Solidity (convex shapes are more regular)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        contour_area = cv2.contourArea(contour)
        if hull_area > 0:
            solidity = contour_area / hull_area
            scores.append(solidity)
        
        # Aspect ratio regularity (squares, circles are regular)
        x, y, w, h = cv2.boundingRect(contour)
        if h > 0:
            aspect_ratio = w / h
            # Score higher for ratios close to 1 (square) or common ratios
            if 0.8 <= aspect_ratio <= 1.2:
                aspect_score = 1.0
            elif 0.4 <= aspect_ratio <= 2.5:
                aspect_score = 0.7
            else:
                aspect_score = 0.3
            scores.append(aspect_score)
        
        return np.mean(scores) if scores else 0
    
    def classify_contour(self, contour: np.ndarray, image: np.ndarray, 
                        properties: Optional[Dict] = None) -> Tuple[ContentType, float]:
        """
        Classify a single contour as handwriting or diagram.
        
        Returns:
            - ContentType: Classification result
            - float: Confidence score (0-1)
        """
        if properties is None:
            properties = self.analyze_stroke_properties(contour, image)
        
        # Extract key features for classification
        area = properties['area']
        aspect_ratio = properties['aspect_ratio']
        solidity = properties['solidity']
        circularity = properties['circularity']
        extent = properties['extent']
        straightness = properties['straightness']
        regularity_score = properties['regularity_score']
        has_straight_lines = properties['has_straight_lines']
        has_perfect_curves = properties['has_perfect_curves']
        corner_count = properties['corner_count']
        
        # Classification heuristics
        diagram_indicators = 0
        handwriting_indicators = 0
        
        # Size-based indicators
        if area > 5000:  # Large shapes more likely to be diagrams
            diagram_indicators += 1
        elif area < 1500:  # Very small shapes might be punctuation
            handwriting_indicators += 0.5
        
        # Shape regularity indicators
        if regularity_score > 0.7:
            diagram_indicators += 2
        elif regularity_score < 0.3:
            handwriting_indicators += 1
        
        # Geometric shape indicators
        if has_straight_lines and corner_count <= 8:
            diagram_indicators += 2  # Likely geometric shape
        
        if has_perfect_curves:
            diagram_indicators += 2  # Likely circle/ellipse
        
        # Aspect ratio indicators with line detection
        if 0.8 <= aspect_ratio <= 1.2:  # Square-like
            diagram_indicators += 1
        elif aspect_ratio > 10 or aspect_ratio < 0.1:  # Extremely elongated - likely lines/rules
            handwriting_indicators += 2  # Reject as simple lines, not diagrams
        elif aspect_ratio > 5 or aspect_ratio < 0.2:  # Very elongated
            if straightness > 0.8:
                handwriting_indicators += 1  # Likely simple line/rule, not diagram
            else:
                handwriting_indicators += 1  # Likely text line
        
        # Solidity indicators
        if solidity > 0.9:  # Very solid shapes
            diagram_indicators += 1
        elif solidity < 0.5:  # Very irregular shapes
            handwriting_indicators += 1
        
        # Circularity indicators
        if circularity > 0.7:  # Very circular
            diagram_indicators += 2
        elif circularity < 0.1:  # Very non-circular
            if not has_straight_lines:
                handwriting_indicators += 1
        
        # Extent indicators
        if extent > 0.8:  # Fills bounding box well
            diagram_indicators += 1
        elif extent < 0.3:  # Sparse in bounding box
            handwriting_indicators += 1
        
        # Sketch detection - complex shapes that aren't simple lines
        is_complex_shape = (
            area > 800 and  # Even lower size threshold for smaller sketches
            0.15 <= aspect_ratio <= 6.0 and  # Even more flexible aspect ratio
            extent > 0.1 and  # More flexible density
            corner_count >= 3 and  # Even lower complexity threshold
            regularity_score < 0.9  # Very flexible regularity
        )
        
        if is_complex_shape:
            diagram_indicators += 5  # Very strong indicator for sketches
        
        # Simple line detection - reject these
        is_simple_line = (
            (aspect_ratio > 8 or aspect_ratio < 0.125) and  # Very elongated
            straightness > 0.7 and  # Very straight
            corner_count <= 4  # Simple shape
        )
        
        if is_simple_line:
            handwriting_indicators += 3  # Strong rejection for simple lines
        
        # Additional boost for medium-sized shapes that might be sketches
        if (area > 1500 and aspect_ratio > 0.3 and aspect_ratio < 3.0 and 
            extent > 0.2 and not is_simple_line):
            diagram_indicators += 2  # Boost for potential sketches
        
        # Make classification decision
        total_indicators = diagram_indicators + handwriting_indicators
        
        if total_indicators == 0:
            return ContentType.UNCERTAIN, 0.5
        
        diagram_confidence = diagram_indicators / total_indicators
        
        # Apply conservative bias (when uncertain, classify as handwriting)
        if diagram_confidence >= 0.7:
            return ContentType.DIAGRAM, diagram_confidence
        elif diagram_confidence <= 0.3:
            return ContentType.HANDWRITING, 1.0 - diagram_confidence
        else:
            # Uncertain case - bias toward handwriting as per spec
            return ContentType.HANDWRITING, 0.6
    
    def classify_contours(self, contours: List[np.ndarray], image: np.ndarray, 
                         contour_properties: List[Dict]) -> List[Tuple[ContentType, float, Dict]]:
        """
        Classify multiple contours.
        
        Returns:
            List of (ContentType, confidence, properties) tuples
        """
        results = []
        
        for i, (contour, props) in enumerate(zip(contours, contour_properties)):
            # Add stroke analysis to existing properties
            stroke_props = self.analyze_stroke_properties(contour, image)
            combined_props = {**props, **stroke_props}
            
            # Classify
            content_type, confidence = self.classify_contour(contour, image, combined_props)
            
            results.append((content_type, confidence, combined_props))
        
        return results
