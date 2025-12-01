#!/bin/bash

# Check if virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Virtual environment already active: $VIRTUAL_ENV"
fi

# Start FastAPI with reload
echo "Starting backend with uvicorn..."
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000