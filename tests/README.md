# API Testing

This directory contains testing scripts for the HTTP API.

## Test Scripts

- `test_api.sh` - Complete API workflow test with file downloads
- `error_test.sh` - Error condition testing

## Quick Start

```bash
# Start the API
docker-compose up

# In another terminal, test with your image
./tests/test_api.sh "your_image.png" output_folder
```

All extracted diagrams and metadata will be saved to the output folder.

### Running Tests

1. Start the API server:
   ```bash
   ./scripts/start_api.sh
   # OR
   docker-compose up
   ```

2. In another terminal, run the tests:
   ```bash
   # Basic API test with your own image
   ./tests/test_api.sh "your_image.png" output_folder
   
   # Example
   ./tests/test_api.sh "Tech Friday.png" results
   
   # Error condition tests
   ./tests/error_test.sh
   ```

### Test Script Features

The `test_api.sh` script:
- **Requires input file as parameter**: `./tests/test_api.sh "image.png" [output_folder]`
- **Organizes outputs in folders**: All results go to specified folder (default: `api_test_results`)
- **Downloads everything**: All extracted diagrams and processing manifest
- **Creates organized structure**:
  ```
  output_folder/
  ├── manifest.json       # Processing metadata and results
  ├── diagram_0.png      # First extracted diagram
  ├── diagram_1.png      # Second extracted diagram
  └── ...                # Additional diagrams as found
  ```
- **Cleans up server files**: Automatically deletes session files from server after download

### Prerequisites

- `curl` - for making HTTP requests
- `jq` - for JSON parsing and formatting

Install on macOS:
```bash
brew install curl jq
```

## What Gets Tested

### `test_api.sh`
1. **Health check** - Verify API is running
2. **Root endpoint** - Get API information
3. **Image processing** - Upload and process PNG file
4. **Session info** - Query session metadata
5. **File downloads** - Download all diagrams and manifest
6. **Cleanup verification** - Confirm server files are deleted

### `error_test.sh`
- Invalid file types (non-PNG files)
- Missing file uploads
- Non-existent session queries
- Invalid file downloads
- Malformed JSON configuration

## Example Output

When you run the test script, you'll see:
- Processing time and session ID
- List of extracted diagrams with confidence scores
- Download progress for each file
- Summary with file sizes and locations

The manifest.json contains complete processing metadata including:
- Original file information
- Bounding boxes for each diagram
- Classification statistics
- Processing configuration used
