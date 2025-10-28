#!/bin/bash
set -e

API_BASE="http://localhost:8000"

echo "=== Error Condition Testing ==="

echo "1. Test invalid file type"
echo "Creating test.txt file..."
echo "test content" > test.txt
echo "POST $API_BASE/api/v1/extract (with .txt file)"
curl -X POST -F "file=@test.txt" "$API_BASE/api/v1/extract" | jq '.'
rm test.txt
echo

echo "2. Test missing file"
echo "POST $API_BASE/api/v1/extract (no file)"
curl -X POST "$API_BASE/api/v1/extract" | jq '.'
echo

echo "3. Test non-existent session"
echo "GET $API_BASE/api/v1/sessions/invalid-session-id/info"
curl -s "$API_BASE/api/v1/sessions/invalid-session-id/info" | jq '.'
echo

echo "4. Test non-existent file download"
echo "GET $API_BASE/api/v1/files/invalid-session/nonexistent.png"
curl -s "$API_BASE/api/v1/files/invalid-session/nonexistent.png" | jq '.'
echo

echo "5. Test invalid JSON config"
echo "POST $API_BASE/api/v1/extract (with invalid JSON config)"
if [ -f "test_images/simple_diagram.png" ]; then
    curl -X POST \
        -F "file=@test_images/simple_diagram.png" \
        -F "config={invalid json}" \
        "$API_BASE/api/v1/extract" | jq '.'
else
    echo "Skipping (no test image available)"
fi
echo

echo "=== Error Testing Complete ==="
