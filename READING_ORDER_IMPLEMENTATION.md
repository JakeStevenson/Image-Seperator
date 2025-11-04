# Reading Order Diagram Sorting - Implementation Summary

## Problem Solved
Previously, diagrams were sorted by **total area** (largest first), which didn't match human reading expectations. Now diagrams are sorted in **natural reading order** (top-to-bottom, then left-to-right).

## Changes Made

### 1. Configuration (`src/utils/config.py`)
- Added `DIAGRAM_SORTING_METHOD` config option
- Default: `'reading_order'`
- Environment variable: `DIAGRAM_SORTING_METHOD`
- Options: `'reading_order'` or `'area'`

### 2. Clusterer (`src/core/clusterer.py`)
- Added `sort_clusters_by_reading_order()` method
- Added `sort_clusters()` method for configurable sorting
- Replaced area-based sorting with configurable method
- Row detection using 50% of average cluster height as threshold

### 3. Test Suite (`test_reading_order.py`)
- Comprehensive tests for both sorting methods
- Tests row detection and left-to-right ordering within rows
- Tests backward compatibility with area-based sorting
- All tests pass ✅

## How Reading Order Works

1. **Row Detection**: Groups diagrams into rows based on vertical proximity
2. **Row Sorting**: Sorts rows top-to-bottom by Y-coordinate
3. **Within Row**: Sorts diagrams left-to-right by X-coordinate
4. **Flattening**: Combines all rows into final ordered list

## Usage

### Default (Reading Order)
```bash
docker run diagram-extractor:reading-order input.png output/
```

### Force Area-Based Sorting
```bash
docker run -e DIAGRAM_SORTING_METHOD=area diagram-extractor:reading-order input.png output/
```

### In Code
```python
from utils.config import Config
Config.DIAGRAM_SORTING_METHOD = 'reading_order'  # or 'area'
```

## Backward Compatibility
- Area-based sorting still available via config
- Existing API unchanged
- Environment variable override supported
- No breaking changes to existing functionality

## Testing Results
- ✅ Reading order: Top row (1,4,0), bottom row (2,3)
- ✅ Area-based: Large to small (2,0,1)
- ✅ Environment variable override works
- ✅ Docker build successful
- ✅ All tests pass

## Impact
Now `diagram_0.png` will be the top-left diagram, `diagram_1.png` the next one to the right, etc., matching human expectations for diagram numbering.