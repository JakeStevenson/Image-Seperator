# Diagram Extraction Tool

A Docker-based tool that extracts non-handwriting diagrams/sketches from handwritten notes (PNG) into separate transparent-background PNG files with JSON manifest.

## Quick Start

### Build the Docker Image

```bash
./scripts/build.sh
```

### Run the Tool

```bash
# Using the run script (recommended)
./scripts/run.sh input_note.png ./output/

# Or run Docker directly
docker run --rm -v $(pwd):/workspace diagram-extractor /workspace/input_note.png /workspace/output/
```

## Usage

The tool accepts a PNG image of handwritten notes and extracts any diagrams into separate files:

```bash
# Basic usage
docker run --rm diagram-extractor input.png output/

# With verbose output
docker run --rm diagram-extractor input.png output/ --verbose
```

## Output

The tool creates:
- `manifest.json` - JSON file describing detected diagrams
- `diagram_1.png`, `diagram_2.png`, etc. - Extracted diagram images with transparent backgrounds

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
/tool
├── Dockerfile                       # Single-stage Docker build
├── src/
│   ├── extract_diagrams.py          # Main CLI entry point
│   ├── core/                        # Core processing modules (TODO)
│   └── utils/
│       ├── config.py                # Configuration parameters
│       └── image_utils.py           # Image utilities (TODO)
├── scripts/
│   ├── build.sh                     # Docker build script
│   └── run.sh                       # Docker run script
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

### Current Status

**Phase 1 Complete**: ✅
- Project structure and Docker infrastructure
- CLI interface with argument parsing
- Configuration system
- Build and run scripts

**Phase 2 Pending**: 
- Core image preprocessing pipeline
- Handwriting vs diagram classification
- Diagram clustering and extraction
- PNG output with transparent backgrounds

## Requirements

- Docker
- Input: PNG images from Apple Notes with Apple Pencil
- Output: Extracted diagram PNGs with transparent backgrounds + JSON manifest

## License

This project is for local development use.
