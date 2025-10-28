"""
Diagram Clustering and Bounding Box Detection

This module groups nearby diagram contours together and creates clean,
non-overlapping bounding boxes for extraction.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
import math

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import Config


@dataclass
class DiagramCluster:
    """Represents a cluster of diagram contours."""
    id: int
    contour_ids: List[int]
    contours: List[np.ndarray]
    bounding_box: Tuple[int, int, int, int]  # (x, y, w, h)
    centroid: Tuple[float, float]
    total_area: float
    confidence: float


class DiagramClusterer:
    """Clusters diagram contours and creates bounding boxes."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize clusterer with configuration."""
        self.config = config or Config()
    
    def calculate_distance(self, bbox1: Tuple[int, int, int, int], 
                          bbox2: Tuple[int, int, int, int]) -> float:
        """Calculate minimum distance between two bounding boxes."""
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        # Calculate centers
        center1 = (x1 + w1/2, y1 + h1/2)
        center2 = (x2 + w2/2, y2 + h2/2)
        
        # Calculate edge-to-edge distance
        left1, right1 = x1, x1 + w1
        top1, bottom1 = y1, y1 + h1
        left2, right2 = x2, x2 + w2
        top2, bottom2 = y2, y2 + h2
        
        # Check for overlap
        if (right1 >= left2 and left1 <= right2 and 
            bottom1 >= top2 and top1 <= bottom2):
            return 0  # Overlapping
        
        # Calculate minimum distance
        dx = max(0, max(left1 - right2, left2 - right1))
        dy = max(0, max(top1 - bottom2, top2 - bottom1))
        
        return math.sqrt(dx*dx + dy*dy)
    
    def should_cluster(self, bbox1: Tuple[int, int, int, int], 
                      bbox2: Tuple[int, int, int, int]) -> bool:
        """Determine if two bounding boxes should be clustered together."""
        distance = self.calculate_distance(bbox1, bbox2)
        return distance <= self.config.CLUSTERING_PROXIMITY
    
    def merge_bounding_boxes(self, bboxes: List[Tuple[int, int, int, int]]) -> Tuple[int, int, int, int]:
        """Merge multiple bounding boxes into one encompassing box."""
        if not bboxes:
            return (0, 0, 0, 0)
        
        min_x = min(bbox[0] for bbox in bboxes)
        min_y = min(bbox[1] for bbox in bboxes)
        max_x = max(bbox[0] + bbox[2] for bbox in bboxes)
        max_y = max(bbox[1] + bbox[3] for bbox in bboxes)
        
        return (min_x, min_y, max_x - min_x, max_y - min_y)
    
    def add_padding(self, bbox: Tuple[int, int, int, int], 
                   image_shape: Tuple[int, int]) -> Tuple[int, int, int, int]:
        """Add padding around bounding box, ensuring it stays within image bounds."""
        x, y, w, h = bbox
        padding = self.config.PADDING
        
        # Add padding
        new_x = max(0, x - padding)
        new_y = max(0, y - padding)
        new_w = min(image_shape[1] - new_x, w + 2 * padding)
        new_h = min(image_shape[0] - new_y, h + 2 * padding)
        
        return (new_x, new_y, new_w, new_h)
    
    def check_text_intersection(self, diagram_bbox: Tuple[int, int, int, int], 
                               handwriting_bboxes: List[Tuple[int, int, int, int]]) -> bool:
        """Check if diagram bounding box intersects with any handwriting."""
        dx, dy, dw, dh = diagram_bbox
        
        for hx, hy, hw, hh in handwriting_bboxes:
            # Check for actual overlap (not just proximity)
            # Add small buffer to avoid rejecting diagrams that are just very close
            buffer = 5  # pixels
            if (dx < hx + hw + buffer and dx + dw > hx - buffer and 
                dy < hy + hh + buffer and dy + dh > hy - buffer):
                
                # Calculate overlap area to determine if it's significant
                overlap_x = max(0, min(dx + dw, hx + hw) - max(dx, hx))
                overlap_y = max(0, min(dy + dh, hy + hh) - max(dy, hy))
                overlap_area = overlap_x * overlap_y
                
                diagram_area = dw * dh
                handwriting_area = hw * hh
                
                # Only reject if there's very significant overlap (>25% of diagram area)
                # This allows sketches near text but rejects diagrams that truly overlap
                if overlap_area > 0.25 * diagram_area:
                    return True
        
        return False
    
    def cluster_diagrams(self, diagram_contours: List[Dict], 
                        handwriting_contours: List[Dict],
                        image_shape: Tuple[int, int],
                        verbose: bool = False) -> List[DiagramCluster]:
        """
        Cluster diagram contours into groups and create bounding boxes.
        
        Args:
            diagram_contours: List of diagram contour info dicts
            handwriting_contours: List of handwriting contour info dicts
            image_shape: (height, width) of the image
            verbose: Enable verbose output
            
        Returns:
            List of DiagramCluster objects
        """
        if not diagram_contours:
            return []
        
        if verbose:
            print(f"Clustering {len(diagram_contours)} diagram contours...")
        
        # Extract bounding boxes for clustering
        diagram_bboxes = [d['properties']['bbox'] for d in diagram_contours]
        handwriting_bboxes = [h['properties']['bbox'] for h in handwriting_contours]
        
        # Create adjacency graph for clustering
        n = len(diagram_contours)
        adjacency = [[False] * n for _ in range(n)]
        
        # Build adjacency matrix based on proximity
        for i in range(n):
            for j in range(i + 1, n):
                if self.should_cluster(diagram_bboxes[i], diagram_bboxes[j]):
                    adjacency[i][j] = True
                    adjacency[j][i] = True
        
        # Find connected components (clusters)
        visited = [False] * n
        clusters = []
        cluster_id = 0
        
        for i in range(n):
            if not visited[i]:
                # Start new cluster
                cluster_contour_ids = []
                stack = [i]
                
                while stack:
                    current = stack.pop()
                    if visited[current]:
                        continue
                    
                    visited[current] = True
                    cluster_contour_ids.append(current)
                    
                    # Add adjacent unvisited nodes
                    for j in range(n):
                        if adjacency[current][j] and not visited[j]:
                            stack.append(j)
                
                # Create cluster
                cluster_contours = [diagram_contours[idx]['contour'] for idx in cluster_contour_ids]
                cluster_bboxes = [diagram_bboxes[idx] for idx in cluster_contour_ids]
                
                # Merge bounding boxes
                merged_bbox = self.merge_bounding_boxes(cluster_bboxes)
                
                # Add padding
                padded_bbox = self.add_padding(merged_bbox, image_shape)
                
                # Check for text intersection
                intersects_text = self.check_text_intersection(padded_bbox, handwriting_bboxes)
                
                if intersects_text:
                    if verbose:
                        print(f"  Cluster {cluster_id}: REJECTED (intersects with text)")
                    continue  # Skip this cluster as per spec
                
                # Calculate cluster properties
                total_area = sum(cv2.contourArea(contour) for contour in cluster_contours)
                
                # Calculate centroid
                x, y, w, h = padded_bbox
                centroid = (x + w/2, y + h/2)
                
                # Calculate confidence (average of constituent contours)
                confidences = [diagram_contours[idx]['confidence'] for idx in cluster_contour_ids]
                avg_confidence = sum(confidences) / len(confidences)
                
                cluster = DiagramCluster(
                    id=cluster_id,
                    contour_ids=cluster_contour_ids,
                    contours=cluster_contours,
                    bounding_box=padded_bbox,
                    centroid=centroid,
                    total_area=total_area,
                    confidence=avg_confidence
                )
                
                clusters.append(cluster)
                
                if verbose:
                    print(f"  Cluster {cluster_id}: {len(cluster_contour_ids)} contours, "
                          f"bbox={padded_bbox}, confidence={avg_confidence:.3f}")
                
                cluster_id += 1
        
        # Sort clusters by area (largest first)
        clusters.sort(key=lambda c: c.total_area, reverse=True)
        
        # Limit to max diagrams
        if len(clusters) > self.config.MAX_DIAGRAMS:
            if verbose:
                print(f"  Limiting to {self.config.MAX_DIAGRAMS} largest clusters")
            clusters = clusters[:self.config.MAX_DIAGRAMS]
        
        # Reassign IDs after sorting and limiting
        for i, cluster in enumerate(clusters):
            cluster.id = i
        
        if verbose:
            print(f"Created {len(clusters)} diagram clusters")
        
        return clusters
    
    def ensure_non_overlapping_boxes(self, clusters: List[DiagramCluster], 
                                   verbose: bool = False) -> List[DiagramCluster]:
        """Ensure bounding boxes don't overlap by adjusting smaller ones."""
        if len(clusters) <= 1:
            return clusters
        
        if verbose:
            print("Ensuring non-overlapping bounding boxes...")
        
        # Sort by area (largest first) to prioritize larger diagrams
        sorted_clusters = sorted(clusters, key=lambda c: c.total_area, reverse=True)
        
        for i, cluster in enumerate(sorted_clusters):
            x1, y1, w1, h1 = cluster.bounding_box
            
            for j, other_cluster in enumerate(sorted_clusters[i+1:], i+1):
                x2, y2, w2, h2 = other_cluster.bounding_box
                
                # Check for overlap
                if (x1 < x2 + w2 and x1 + w1 > x2 and 
                    y1 < y2 + h2 and y1 + h1 > y2):
                    
                    if verbose:
                        print(f"  Overlap detected between clusters {cluster.id} and {other_cluster.id}")
                    
                    # Shrink the smaller cluster's bounding box
                    # Simple approach: reduce by moving edges inward
                    overlap_x = min(x1 + w1, x2 + w2) - max(x1, x2)
                    overlap_y = min(y1 + h1, y2 + h2) - max(y1, y2)
                    
                    # Adjust the smaller cluster (other_cluster)
                    if overlap_x < overlap_y:
                        # Adjust horizontally
                        if x2 < x1:
                            # Move right edge of other_cluster left
                            new_w2 = max(10, x1 - x2 - 1)
                        else:
                            # Move left edge of other_cluster right
                            shift = (x1 + w1) - x2 + 1
                            x2 += shift
                            new_w2 = max(10, w2 - shift)
                        other_cluster.bounding_box = (x2, y2, new_w2, h2)
                    else:
                        # Adjust vertically
                        if y2 < y1:
                            # Move bottom edge of other_cluster up
                            new_h2 = max(10, y1 - y2 - 1)
                        else:
                            # Move top edge of other_cluster down
                            shift = (y1 + h1) - y2 + 1
                            y2 += shift
                            new_h2 = max(10, h2 - shift)
                        other_cluster.bounding_box = (x2, y2, w2, new_h2)
        
        return clusters
