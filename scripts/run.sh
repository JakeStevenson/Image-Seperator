#!/bin/bash
# Run script for diagram extraction tool

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 <input_file> <output_dir>"
    echo "Example: $0 note.png ./output/"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_DIR="$2"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Convert to absolute paths
INPUT_ABS=$(realpath "$INPUT_FILE")
OUTPUT_ABS=$(realpath "$OUTPUT_DIR")

echo "Running diagram extraction..."
echo "Input: $INPUT_ABS"
echo "Output: $OUTPUT_ABS"

# Run the Docker container with volume mounts
docker run --rm \
    -v "$(dirname "$INPUT_ABS"):/input" \
    -v "$OUTPUT_ABS:/output" \
    diagram-extractor \
    "/input/$(basename "$INPUT_ABS")" \
    "/output" \
    --verbose

echo "Extraction complete!"
