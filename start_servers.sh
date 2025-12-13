#!/bin/bash

# Stop old servers if any
pkill -f "uvicorn backend.main:app" || true
pkill -f "python3 -m http.server" || true

# Start backend
nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
echo "Backend started with PID $!"
echo "Backend URL: http://3.23.74.167:8000"

# Start frontend
nohup python3 -m http.server 8080 --bind 0.0.0.0 > frontend.log 2>&1 &
echo "Frontend started with PID $!"
echo "Frontend URL: http://3.23.74.167:8080"

echo "All servers started!"