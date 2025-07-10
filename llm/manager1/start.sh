#!/bin/sh
set -e

echo "[start.sh] Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

echo "[start.sh] Waiting for Ollama to start..."
sleep 5

echo "[start.sh] Starting Manager1 FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8080 --proxy-headers

wait $OLLAMA_PID
