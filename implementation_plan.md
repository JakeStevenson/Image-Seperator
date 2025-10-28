# Implementation Plan: Diagram Extraction Tool

## Overview

This document outlines the implementation plan for a handwritten notes diagram extraction tool that processes Apple Notes PNG files and extracts non-handwriting diagrams into separate transparent-background PNG files.

## Implementation Status

**Phase 1**: ✅ **COMPLETE** - Project Setup & Docker Infrastructure  
**Phase 2**: ✅ **COMPLETE** - Core Image Preprocessing Pipeline  
**Phase 3**: ✅ **COMPLETE** - Handwriting vs Diagram Classification  
**Phase 4**: ✅ **COMPLETE** - Diagram Clustering & Bounding Box Detection  
**Phase 5**: ✅ **COMPLETE** - Diagram Extraction & PNG Output  
**Phase 6**: ✅ **COMPLETE** - JSON Manifest Generation  
**Phase 7**: 🔧 **REFINEMENT** - Testing & Bug Fixes  

## Architecture Overview

The tool will be built using **Python 3 + OpenCV** with a modular, containerized architecture using Docker for consistent build, testing, and deployment environments.

### Project Structure

```
/tool
├── Dockerfile                       # Multi-stage Docker build
├── docker-compose.yml              # Development and testing environment
├── .dockerignore                   # Docker build optimization
├── src/
│   ├── extract_diagrams.py          # Main CLI entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── preprocessor.py          # Image preprocessing pipeline
│   │   ├── classifier.py            # Handwriting vs diagram detection
│   │   ├── clusterer.py             # Diagram grouping and bounding boxes
│   │   └── extractor.py             # PNG extraction and manifest generation
│   └── utils/
│       ├── __init__.py
│       ├── image_utils.py           # Image manipulation utilities
│       └── config.py                # Configuration parameters
├── tests/
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   └── fixtures/                   # Test images and expected outputs
├── examples/
│   ├── input/                      # Sample input images
│   └── expected_output/            # Expected extraction results
├── requirements.txt                # Python dependencies
├── requirements-dev.txt            # Development dependencies
├── pytest.ini                     # Test configuration
├── README.md                       # Project documentation
└── scripts/
    ├── build.sh                    # Docker build script
    ├── test.sh                     # Docker test runner
    └── run.sh                      # Docker run script
```

### Docker Strategy

### Single-Stage Docker Build

**Base Image**: `python:3.11-slim` for optimal size and performance

**Dockerfile Features**:
- Single-stage build for simplicity
- OpenCV installation with minimal dependencies
- Direct file argument passing (no volume mounts needed)
- Optimized for local CLI usage

### Container Usage Pattern

**Local Usage**:
```bash
# Build once
docker build -t diagram-extractor .

# Run with direct file arguments
docker run --rm diagram-extractor /path/to/input.png /path/to/output/
```

**No CI/CD Pipeline Required** - This is a local development tool

## Detailed Implementation Plan

### 1. **Project Setup & Docker Infrastructure** ✅ **COMPLETE**
**Priority: High**

**Tasks**: ✅ **ALL COMPLETE**
- ✅ Create single-stage Dockerfile with OpenCV optimization
- ✅ Implement direct file argument handling with volume mounts
- ✅ Create simple build script for local usage
- ✅ CLI interface with argument parsing and validation
- ✅ Configuration system with environment variables
- ✅ Git repository initialization with proper .gitignore
- ✅ Tested successfully with sample PNG file

**Dependencies**: 
- OpenCV (cv2), NumPy, argparse, json, pathlib
- Development: pytest, black, flake8, mypy
- Container: python:3.11-slim base image

**Docker Considerations**:
- Optimize OpenCV installation for container size
- Handle file I/O through direct argument passing
- Simple container execution without orchestration

### 2. **Core Image Preprocessing Pipeline** ✅ **COMPLETE**
**Priority: High**

**Key Components**: ✅ **ALL COMPLETE**
- ✅ **Grayscale conversion** with proper contrast preservation
- ✅ **Adaptive thresholding** to handle varying lighting conditions
- ✅ **Morphological operations** (dilation/erosion) to clean up strokes
- ✅ **Contour detection** using OpenCV's `findContours()`
- ✅ **Contour property extraction** (area, bbox, ratios, circularity)
- ✅ **Debug visualization** with processing steps grid
- ✅ **Comprehensive testing** with Tech Friday.png (12 contours detected)

**Technical Approach**:
```python
# Preprocessing steps
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
```

**Docker Integration**:
- Containerized image processing for consistent results
- Direct file processing without volume complexity
- Optimized for single-image CLI usage

### 3. **Handwriting vs Diagram Classification** ✅ **COMPLETE**
**Priority: High**

**Classification Heuristics**: ✅ **ALL COMPLETE**
- ✅ **Stroke analysis**: Straightness, curvature variation, stroke width analysis
- ✅ **Shape regularity**: Corner detection, line/curve segments, geometric features
- ✅ **Geometric analysis**: Rectangularity, circularity, triangularity detection
- ✅ **Multi-factor scoring**: Size, aspect ratio, solidity, extent analysis
- ✅ **Conservative bias**: When uncertain, classify as handwriting (per spec)

**Key Features Implemented**: ✅ **ALL COMPLETE**
- ✅ **Diagram indicators**: Straight lines, perfect curves, geometric shapes, high regularity
- ✅ **Handwriting indicators**: Irregular shapes, low regularity, text-like aspect ratios
- ✅ **Confidence scoring**: Multi-factor analysis with 0-1 confidence values
- ✅ **Debug visualization**: Color-coded classification overlays (green=diagrams, red=handwriting)
- ✅ **Comprehensive testing**: 6 diagrams + 6 handwriting detected in Tech Friday.png

**Testing Strategy**:
- Containerized unit tests for classification accuracy
- Automated visual regression testing
- Performance benchmarking in controlled Docker environment

### 4. **Diagram Clustering & Bounding Box Detection**
**Priority: High**

**Clustering Algorithm**:
- **Proximity-based clustering**: Group contours within 25px of each other
- **Connected components analysis**: Merge overlapping or touching shapes
- **Bounding box calculation**: Non-overlapping rectangles with 3px padding

**Anti-patterns to Handle**:
- **Text-touching diagrams**: Reject any diagram that intersects with detected text regions
- **Overlapping bounding boxes**: Ensure clean separation between extracted regions

### 5. **Diagram Extraction & PNG Output**
**Priority: Medium**

**Extraction Process**:
- **Transparent background creation**: Use alpha channel for clean extraction
- **Lossless PNG output**: Maintain original line quality without smoothing
- **Cropping**: Extract only the bounding box region with padding

**Confidence Scoring**:
- **Geometric regularity**: Higher confidence for perfect shapes
- **Stroke consistency**: Lower confidence for irregular strokes
- **Isolation from text**: Higher confidence for standalone diagrams

### 6. **CLI Interface**
**Priority: Medium**

**Command Structure**:
```bash
# Direct execution
python extract_diagrams.py --input note.png --output ./out/ [--config config.json]

# Docker execution
docker run -v $(pwd):/workspace diagram-extractor --input /workspace/note.png --output /workspace/out/
```

**Features**:
- **Input validation**: Check file existence and format
- **Output directory management**: Create directories as needed
- **Progress feedback**: Show processing status
- **Error handling**: Graceful failure with informative messages
- **Docker-aware file paths**: Handle container volume mounts properly

### 7. **JSON Manifest Generation**
**Priority: Medium**

**Manifest Structure**:
```json
{
  "original_file": "input_note.png",
  "processing_metadata": {
    "timestamp": "2025-10-28T13:05:00Z",
    "version": "1.0.0",
    "docker_image": "diagram-extractor:latest"
  },
  "diagrams": [
    {
      "file": "note_diagram_1.png",
      "bbox": [x, y, w, h],
      "confidence": 0.92
    }
  ]
}
```

**Edge Cases**:
- **No diagrams found**: Return empty array with explanatory message
- **Multiple diagrams**: Sequential numbering with unique filenames

### 8. **Comprehensive Testing Strategy**
**Priority: Medium**

**Docker-Based Testing**:
- **Containerized test environment**: Consistent testing across platforms
- **Automated CI/CD**: Docker-based GitHub Actions or similar
- **Performance testing**: Containerized benchmarking

**Test Categories**:
- **Unit tests**: Individual component functionality
- **Integration tests**: End-to-end pipeline testing
- **Visual tests**: Compare expected vs actual extracted diagrams
- **Performance tests**: Memory usage and processing time benchmarks

**Test Scenarios**:
- Simple boxed diagrams
- Multiple clustered shapes
- Handwriting-only notes (no extraction)
- Diagrams touching text (should reject)
- Mixed content differentiation

**Docker Test Commands**:
```bash
# Run all tests
docker-compose run test

# Run specific test categories
docker-compose run test pytest tests/unit/
docker-compose run test pytest tests/integration/

# Performance benchmarking
docker-compose run benchmark
```

### 9. **Documentation & Examples**
**Priority: Low**

**Deliverables**:
- **README.md**: Installation, usage, and Docker deployment guide
- **Example images**: Diverse test cases with expected outputs
- **API documentation**: Function and class documentation
- **Docker documentation**: Container usage and deployment guide

## Technical Considerations

### **Performance Targets**
- **Processing time**: ≤3 seconds per note on modern laptop (containerized)
- **Memory efficiency**: Stream processing for large images within container limits
- **Quality preservation**: Lossless PNG output with sharp lines
- **Container startup**: <2 seconds for CLI usage

### **Configuration Parameters**
- **Minimum contour area**: 750px (adjustable via environment variables)
- **Clustering proximity**: 25px (adjustable via environment variables)  
- **Padding**: 3px around extracted regions
- **Max diagrams**: 10 per note (configurable)

### **Docker-Specific Considerations**
- **Volume mounts**: Proper handling of input/output directories
- **Environment variables**: Configuration through Docker environment
- **Security**: Non-root user execution within containers
- **Logging**: Structured logging for container orchestration
- **Health checks**: Container health monitoring
- **Resource limits**: Memory and CPU constraints for production deployment

### **Error Handling Strategy**
- **Conservative bias**: When uncertain, classify as handwriting (don't extract)
- **Graceful degradation**: Continue processing even if some diagrams fail
- **Detailed logging**: Track decision-making process for debugging
- **Container-aware errors**: Proper exit codes and error messages for Docker environments

## Deployment Strategy

### **Development Deployment**
```bash
# Build development image
docker-compose build dev

# Run with hot-reload
docker-compose up dev

# Execute tests
docker-compose run test
```

### **Production Deployment**
```bash
# Build optimized production image
docker build -t diagram-extractor:latest .

# Run with volume mounts
docker run -v /path/to/input:/app/input -v /path/to/output:/app/output diagram-extractor:latest

# Or use docker-compose for production
docker-compose -f docker-compose.prod.yml up
```

### **CI/CD Integration**
- **Automated testing**: Docker-based test execution in CI pipeline
- **Image building**: Multi-architecture Docker image builds
- **Registry deployment**: Push to container registry (Docker Hub, ECR, etc.)
- **Version tagging**: Semantic versioning for Docker images

This implementation plan provides a robust, containerized foundation for building the diagram extraction tool while maintaining the conservative, accuracy-focused approach specified in the requirements. The Docker integration ensures consistent behavior across development, testing, and production environments.
