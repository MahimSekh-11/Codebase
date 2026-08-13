#!/bin/bash
set -e

# Render injects $PORT — Streamlit MUST bind to it or Render kills the container.
STREAMLIT_PORT="${PORT:-8501}"

echo "==> Starting FastAPI backend on internal port 8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Give uvicorn a 5-second head-start. Render's port scanner waits at least 60s.
echo "==> Giving backend 5s head-start before starting Streamlit..."
sleep 5

echo "==> Starting Streamlit frontend on public port $STREAMLIT_PORT..."
streamlit run frontend/app.py \
    --server.port "$STREAMLIT_PORT" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false &
FRONTEND_PID=$!

echo "==> Both services running."
echo "    Backend  PID: $BACKEND_PID (internal port 8000)"
echo "    Frontend PID: $FRONTEND_PID (public port $STREAMLIT_PORT)"

# Keep container alive
wait $BACKEND_PID $FRONTEND_PID
