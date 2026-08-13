#!/bin/bash
set -e

# Render injects $PORT - Streamlit must bind to it immediately or Render will kill the container.
STREAMLIT_PORT="${PORT:-8501}"

echo "==> Starting FastAPI backend on internal port 8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "==> Starting Streamlit frontend on port $STREAMLIT_PORT (Render's public port)..."
# Start Streamlit immediately so Render can detect the open port.
# The frontend shows a warning if the backend isn't ready yet.
streamlit run frontend/app.py \
    --server.port "$STREAMLIT_PORT" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false &
FRONTEND_PID=$!

echo "==> Both services started."
echo "    Backend  PID: $BACKEND_PID (internal port 8000)"
echo "    Frontend PID: $FRONTEND_PID (public port $STREAMLIT_PORT)"

# Keep container alive; exit if either process dies
wait $BACKEND_PID $FRONTEND_PID
