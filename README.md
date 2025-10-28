# Diagram Extraction Tool

A Docker-based tool that extracts non-handwriting diagrams/sketches from handwritten notes (PNG) into separate PNG files with JSON manifest. Available as both a CLI tool and HTTP REST API.

## Quick Start

### CLI Tool

#### Build the Docker Image

```bash
./scripts/build.sh
```

#### Run the Tool

```bash
# Using the run script (recommended)
./scripts/run.sh input_note.png ./output/

# Or run Docker directly
docker run --rm -v $(pwd):/workspace diagram-extractor /workspace/input_note.png /workspace/output/
```

### HTTP API

#### Build and Start the API

```bash
# Build both CLI and API containers
./scripts/build_api.sh

# Start the API server
docker-compose up

# Or run standalone
docker run -p 8000:8000 diagram-extractor-api

# Or start locally for development
./scripts/start_api.sh
```

#### Use the API

```bash
# Health check
curl http://localhost:8000/health

# Process an image
curl -X POST -F "file=@input_note.png" http://localhost:8000/api/v1/extract

# Or use the convenient test script to process and download everything
./tests/test_api.sh "input_note.png" output_folder

# View API documentation
open http://localhost:8000/docs
```

## Usage

### CLI Usage

The CLI tool accepts a PNG image of handwritten notes and extracts any diagrams into separate files:

```bash
# Basic usage
docker run --rm diagram-extractor input.png output/

# With verbose output
docker run --rm diagram-extractor input.png output/ --verbose
```

### API Usage

The HTTP API provides REST endpoints for processing images:

#### Main Endpoints

- `GET /health` - Health check
- `POST /api/v1/extract` - Process image and extract diagrams
- `GET /api/v1/files/{session_id}/{filename}` - Download extracted files
- `GET /api/v1/sessions/{session_id}/info` - Get session information
- `DELETE /api/v1/files/{session_id}` - Clean up session files

#### Example Workflow

```bash
# 1. Process an image
RESPONSE=$(curl -X POST -F "file=@note.png" \
  http://localhost:8000/api/v1/extract)

# 2. Extract session ID
SESSION_ID=$(echo "$RESPONSE" | jq -r '.session_id')

# 3. Download extracted diagrams
curl "http://localhost:8000/api/v1/files/$SESSION_ID/diagram_0.png" -o diagram_0.png
curl "http://localhost:8000/api/v1/files/$SESSION_ID/diagram_1.png" -o diagram_1.png

# 4. Download manifest
curl "http://localhost:8000/api/v1/files/$SESSION_ID/manifest.json" -o manifest.json

# 5. Clean up (optional - files auto-expire after 1 hour)
curl -X DELETE "http://localhost:8000/api/v1/files/$SESSION_ID"
```

**Note**: Add `-F "debug=true"` to generate visualization images of the processing pipeline.

#### API Features

- **File Auto-Cleanup**: Downloaded files are automatically deleted by default
- **Session Management**: Files are organized in temporary sessions with TTL
- **Debug Images**: Optional debug visualizations of the processing pipeline
- **Comprehensive Error Handling**: Structured error responses with details
- **OpenAPI Documentation**: Interactive docs at `/docs` and `/redoc`

## Output

The tool creates:
- `manifest.json` - JSON file describing detected diagrams
- `diagram_0.png`, `diagram_1.png`, etc. - Extracted diagram images (cropped regions)

### Manifest Format

```json
{
  "original_file": "input_note.png",
  "diagrams": [
    {
      "file": "note_diagram_1.png",
      "bbox": [x, y, w, h],
      "confidence": 0.92
    }
  ]
}
```

## Configuration

The tool can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MIN_CONTOUR_AREA` | 750 | Minimum diagram contour area in pixels |
| `CLUSTERING_PROXIMITY` | 25 | Clustering proximity in pixels |
| `PADDING` | 3 | Padding around extracted regions |
| `MAX_DIAGRAMS` | 10 | Maximum diagrams per note |

Example with custom configuration:
```bash
docker run --rm -e MIN_CONTOUR_AREA=1000 diagram-extractor input.png output/
```

## Development

### Project Structure

```
/
├── Dockerfile                       # CLI container build
├── Dockerfile.api                   # API container build  
├── docker-compose.yml               # Simple API deployment
├── src/
│   ├── extract_diagrams.py          # Main CLI entry point
│   ├── api/                         # HTTP API layer
│   │   ├── main.py                  # FastAPI application
│   │   ├── routes/                  # API endpoints
│   │   ├── models/                  # Pydantic models
│   │   ├── services/                # Business logic
│   │   └── middleware/              # CORS, auth, etc.
│   ├── core/                        # Core processing modules
│   │   ├── preprocessor.py          # Image preprocessing
│   │   ├── classifier.py            # Handwriting vs diagram classification
│   │   └── clusterer.py             # Diagram clustering
│   └── utils/
│       ├── config.py                # Configuration parameters
│       └── image_utils.py           # Image utilities
├── scripts/
│   ├── build.sh                     # CLI Docker build script
│   ├── run.sh                       # CLI Docker run script
│   ├── build_api.sh                 # API Docker build script
│   └── start_api.sh                 # API startup script
├── tests/
│   ├── test_api.sh                  # API testing script
│   ├── error_test.sh                # Error condition tests
│   └── README.md                    # Testing documentation
├── requirements.txt                 # Core Python dependencies
├── requirements-api.txt             # API-specific dependencies
└── README.md                        # This file
```

### Current Status

**CLI Tool Complete**: ✅
- Full image processing pipeline implemented
- Handwriting vs diagram classification
- Diagram clustering and extraction
- PNG output with JSON manifest
- Docker containerization

**HTTP API Complete**: ✅
- Lightweight FastAPI-based REST API
- File upload and processing endpoints
- Simple session-based file management with auto-cleanup
- Comprehensive error handling
- OpenAPI documentation
- Simple Docker containerization
- Testing scripts

**Ready for Production**: ✅
- Both CLI and API fully functional
- Comprehensive documentation
- Docker deployment options
- Testing infrastructure

## Requirements

- Docker
- Input: PNG images from Apple Notes with Apple Pencil
- Output: Extracted diagram PNGs (cropped regions) + JSON manifest

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
