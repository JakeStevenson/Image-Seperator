#!/bin/bash
set -e

echo "Starting Diagram Extraction API..."

# Check if we're in a container or local development
if [ -f "/.dockerenv" ]; then
    # Running in container
    echo "Running in container mode"
    cd /app
    exec python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
else
    # Running locally for development
    echo "Running in development mode"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install -r requirements.txt
    pip install -r requirements-api.txt
    
    # Set environment variables for development
    export PYTHONPATH=$(pwd)
    export API_HOST=127.0.0.1
    export API_PORT=8000
    export TEMP_DIR=/tmp/diagram_api
    
    # Create temp directory
    mkdir -p /tmp/diagram_api/sessions
    
    # Start the API
    echo "Starting API server at http://127.0.0.1:8000"
    python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
fi
