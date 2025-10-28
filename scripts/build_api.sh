#!/bin/bash
set -e

echo "Building Diagram Extraction API..."

# First build the base CLI container
echo "Building base CLI container..."
docker build -t diagram-extractor .

# Then build the API container
echo "Building API container..."
docker build -f Dockerfile.api -t diagram-extractor-api .

echo "Build complete!"
echo "To start the API: docker-compose up"
echo "Or run standalone: docker run -p 8000:8000 diagram-extractor-api"
