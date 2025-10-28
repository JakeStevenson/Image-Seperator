#!/bin/bash
# Build script for diagram extraction tool

set -e

echo "Building diagram-extractor Docker image..."
docker build -t diagram-extractor .

echo "Build complete!"
echo ""
echo "Usage:"
echo "  docker run --rm diagram-extractor input.png output/"
echo ""
echo "Example:"
echo "  docker run --rm -v \$(pwd):/workspace diagram-extractor /workspace/note.png /workspace/output/"
