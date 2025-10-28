#!/bin/bash
set -e

API_BASE="http://localhost:8000"

# Check if input file is provided
if [ $# -eq 0 ]; then
  echo "Usage: $0 <input_image.png> [output_folder]"
  echo "Example: $0 'Tech Friday.png' results"
  exit 1
fi

TEST_IMAGE="$1"
OUTPUT_FOLDER="${2:-api_test_results}"

echo "=== Diagram Extraction API Testing Script ==="
echo "API Base: $API_BASE"
echo "Test Image: $TEST_IMAGE"
echo "Output Folder: $OUTPUT_FOLDER"
echo

# Check if test image exists
if [ ! -f "$TEST_IMAGE" ]; then
  echo "Error: Test image '$TEST_IMAGE' not found"
  echo "Please provide a valid PNG file path"
  exit 1
fi

# Create output folder
mkdir -p "$OUTPUT_FOLDER"
echo "Created output folder: $OUTPUT_FOLDER"
echo

echo "1. Health Check"
echo "GET $API_BASE/health"
curl -s "$API_BASE/health" | jq '.' || echo "Failed to connect to API"
echo

echo "2. Root Endpoint"
echo "GET $API_BASE/"
curl -s "$API_BASE/" | jq '.' || echo "Failed to get root info"
echo

if [ -f "$TEST_IMAGE" ]; then
  echo "3. Process Image (Synchronous)"
  echo "POST $API_BASE/api/v1/extract"
  RESPONSE=$(curl -s -X POST \
    -F "file=@$TEST_IMAGE" \
    "$API_BASE/api/v1/extract")

  echo "$RESPONSE" | jq '.'

  # Extract session ID for next steps
  SESSION_ID=$(echo "$RESPONSE" | jq -r '.session_id // empty')

  if [ -n "$SESSION_ID" ]; then
    echo "Session ID: $SESSION_ID"
    echo

    echo "4. Check Session Info"
    echo "GET $API_BASE/api/v1/sessions/$SESSION_ID/info"
    curl -s "$API_BASE/api/v1/sessions/$SESSION_ID/info" | jq '.'
    echo

    echo "5. Download Manifest"
    echo "GET $API_BASE/api/v1/files/$SESSION_ID/manifest.json"
    curl -s "$API_BASE/api/v1/files/$SESSION_ID/manifest.json?keep=true" \
      -o "$OUTPUT_FOLDER/manifest.json" && echo "Downloaded manifest.json to $OUTPUT_FOLDER/" || echo "Failed to download manifest"
    echo

    echo "6. Download All Diagrams"
    DIAGRAM_COUNT=$(echo "$RESPONSE" | jq -r '.diagrams | length')
    echo "Found $DIAGRAM_COUNT diagrams to download"

    for i in $(seq 0 $((DIAGRAM_COUNT - 1))); do
      DIAGRAM_FILE=$(echo "$RESPONSE" | jq -r ".diagrams[$i].filename // empty")
      if [ -n "$DIAGRAM_FILE" ]; then
        echo "  Downloading $DIAGRAM_FILE..."
        curl -s "$API_BASE/api/v1/files/$SESSION_ID/$DIAGRAM_FILE?keep=true" \
          -o "$OUTPUT_FOLDER/$DIAGRAM_FILE" && echo "    ✓ Saved to $OUTPUT_FOLDER/$DIAGRAM_FILE" || echo "    ✗ Failed to download $DIAGRAM_FILE"
      fi
    done
    echo

    echo "7. Download Debug Images (if any)"
    DEBUG_COUNT=$(echo "$RESPONSE" | jq -r '.debug_images | length // 0')
    if [ "$DEBUG_COUNT" -gt 0 ]; then
      echo "Found $DEBUG_COUNT debug images to download"
      mkdir -p "$OUTPUT_FOLDER/debug"

      for i in $(seq 0 $((DEBUG_COUNT - 1))); do
        DEBUG_FILE=$(echo "$RESPONSE" | jq -r ".debug_images[$i].name // empty")
        if [ -n "$DEBUG_FILE" ]; then
          echo "  Downloading debug/$DEBUG_FILE..."
          curl -s "$API_BASE/api/v1/files/$SESSION_ID/$DEBUG_FILE?keep=true" \
            -o "$OUTPUT_FOLDER/debug/$DEBUG_FILE" && echo "    ✓ Saved to $OUTPUT_FOLDER/debug/$DEBUG_FILE" || echo "    ✗ Failed to download $DEBUG_FILE"
        fi
      done
    else
      echo "No debug images to download"
    fi
    echo

    echo "8. Check Session Info After Downloads"
    echo "GET $API_BASE/api/v1/sessions/$SESSION_ID/info"
    curl -s "$API_BASE/api/v1/sessions/$SESSION_ID/info" | jq '.'
    echo

    echo "9. Clean Up Server Files"
    echo "DELETE $API_BASE/api/v1/files/$SESSION_ID"
    curl -s -X DELETE "$API_BASE/api/v1/files/$SESSION_ID" | jq '.'
    echo

    echo "=== Download Summary ==="
    echo "All files saved to: $OUTPUT_FOLDER/"
    ls -la "$OUTPUT_FOLDER/"
    if [ -d "$OUTPUT_FOLDER/debug" ]; then
      echo
      echo "Debug images in: $OUTPUT_FOLDER/debug/"
      ls -la "$OUTPUT_FOLDER/debug/"
    fi
    echo
  else
    echo "No session ID found in response - skipping file tests"
  fi
else
  echo "3-9. Skipping image processing tests (no test image)"
fi

echo "=== Test Complete ==="
