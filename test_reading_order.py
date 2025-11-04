#!/usr/bin/env python3
"""
Test script to verify reading order sorting functionality.
"""

import sys
import os
sys.path.append('/app/src')

from core.clusterer import DiagramClusterer
from utils.config import Config
import numpy as np

def create_test_cluster(id, x, y, w, h, area):
    """Create a test cluster with given parameters."""
    from dataclasses import dataclass
    from typing import List, Tuple
    
    @dataclass
    class TestCluster:
        id: int
        contour_ids: List[int]
        contours: List
        bounding_box: Tuple[int, int, int, int]
        centroid: Tuple[float, float]
        total_area: float
        confidence: float
    
    return TestCluster(
        id=id,
        contour_ids=[id],
        contours=[],
        bounding_box=(x, y, w, h),
        centroid=(x + w/2, y + h/2),
        total_area=area,
        confidence=0.8
    )

def test_reading_order_sorting():
    """Test the reading order sorting functionality."""
    print("=== Testing Reading Order Sorting ===")
    
    # Create test clusters in different positions
    clusters = [
        create_test_cluster(0, 200, 50, 50, 30, 1000),  # Top-right
        create_test_cluster(1, 20, 60, 40, 25, 800),    # Top-left  
        create_test_cluster(2, 30, 120, 60, 35, 1500), # Bottom-left
        create_test_cluster(3, 150, 110, 45, 28, 700),  # Bottom-right
        create_test_cluster(4, 100, 55, 45, 30, 900),   # Top-middle
    ]
    
    print(f"Config sorting method: {Config.DIAGRAM_SORTING_METHOD}")
    print("\nOriginal clusters (ID, position):")
    for c in clusters:
        print(f"  Cluster {c.id}: ({c.bounding_box[0]}, {c.bounding_box[1]})")
    
    # Test reading order sorting
    clusterer = DiagramClusterer()
    reading_order = clusterer.sort_clusters_by_reading_order(clusters)
    
    print("\nReading order (ID, position):")
    for c in reading_order:
        print(f"  Cluster {c.id}: ({c.bounding_box[0]}, {c.bounding_box[1]})")
    
    # Test configured sorting method
    config_sorted = clusterer.sort_clusters(clusters)
    print(f"\nConfig method sorting (ID, position):")
    for c in config_sorted:
        print(f"  Cluster {c.id}: ({c.bounding_box[0]}, {c.bounding_box[1]})")
    
    # Verify expected order: top row (1, 4, 0), then bottom row (2, 3)
    expected_order = [1, 4, 0, 2, 3]
    actual_order = [c.id for c in reading_order]
    
    print(f"\nExpected reading order: {expected_order}")
    print(f"Actual reading order:   {actual_order}")
    
    if actual_order == expected_order:
        print("✅ Reading order sorting works correctly!")
        return True
    else:
        print("❌ Reading order sorting failed!")
        return False

def test_area_sorting():
    """Test area-based sorting for backward compatibility."""
    print("\n=== Testing Area-Based Sorting ===")
    
    # Temporarily change config to area-based
    original_method = Config.DIAGRAM_SORTING_METHOD
    Config.DIAGRAM_SORTING_METHOD = 'area'
    
    clusters = [
        create_test_cluster(0, 100, 50, 50, 30, 1000),  # Medium
        create_test_cluster(1, 20, 60, 40, 25, 800),    # Small
        create_test_cluster(2, 30, 120, 60, 35, 1500),  # Large
    ]
    
    clusterer = DiagramClusterer()
    area_sorted = clusterer.sort_clusters(clusters)
    
    print("Area-based sorting (ID, area):")
    for c in area_sorted:
        print(f"  Cluster {c.id}: {c.total_area}")
    
    # Should be sorted by area descending: 2, 0, 1
    expected_order = [2, 0, 1]
    actual_order = [c.id for c in area_sorted]
    
    print(f"Expected area order: {expected_order}")
    print(f"Actual area order:   {actual_order}")
    
    # Restore original config
    Config.DIAGRAM_SORTING_METHOD = original_method
    
    if actual_order == expected_order:
        print("✅ Area-based sorting works correctly!")
        return True
    else:
        print("❌ Area-based sorting failed!")
        return False

if __name__ == "__main__":
    success1 = test_reading_order_sorting()
    success2 = test_area_sorting()
    
    if success1 and success2:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)