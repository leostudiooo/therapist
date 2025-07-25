#!/bin/bash

# CSM AI Therapist Backend Startup Script
echo "Starting CSM AI Therapist Backend..."

# Set environment variables for clean startup
export TOKENIZERS_PARALLELISM=false

# Run the FastAPI server with UV
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload