#!/bin/bash
set -e

# Render injects $PORT - Streamlit must bind to it.
# FastAPI runs internally on 8000 (not exposed publicly).
STREAMLIT_PORT="${PORT:-8501}"

echo "==> Starting FastAPI backend on internal port 8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "==> Waiting for FastAPI backend to become ready..."
for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo "==> Backend is ready after $i attempts!"
        break
    fi
    echo "    Attempt $i/30 - backend not ready yet, retrying in 2s..."
    sleep 2
done

echo "==> Starting Streamlit frontend on port $STREAMLIT_PORT..."
streamlit run frontend/app.py \
    --server.port "$STREAMLIT_PORT" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false &
FRONTEND_PID=$!

echo "==> Both services started."
echo "    Backend  PID: $BACKEND_PID (port 8000)"
echo "    Frontend PID: $FRONTEND_PID (port $STREAMLIT_PORT)"

# Keep container alive; exit if either process dies
wait -p EXITED_PID
if [ "$EXITED_PID" -eq "$BACKEND_PID" ]; then
    echo "Backend exited unexpectedly! Shutting down frontend..."
    kill "$FRONTEND_PID" 2>/dev/null
else
    echo "Frontend exited unexpectedly! Shutting down backend..."
    kill "$BACKEND_PID" 2>/dev/null
fi
