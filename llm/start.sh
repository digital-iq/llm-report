#!/bin/bash
set -e

echo "[start.sh] Starting Ollama server in background..."
ollama serve &
OLLAMA_PID=$!

echo "[start.sh] Waiting for server to start..."
sleep 5

echo "[start.sh] Pulling model: $MODEL_NAME"
ollama pull "$MODEL_NAME"

echo "[start.sh] Model pull complete."

echo "[start.sh] Bringing Ollama server to foreground..."
wait $OLLAMA_PID
