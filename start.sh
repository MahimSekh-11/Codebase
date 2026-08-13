#!/bin/bash
set -e

echo "Starting FastAPI backend on port 8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Waiting for backend to become ready..."
for i in $(seq 1 30); do
    if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

echo "Starting Streamlit frontend on port 8501..."
streamlit run frontend/app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false &
FRONTEND_PID=$!

echo "Both services are running."
echo "  Backend PID:  $BACKEND_PID"
echo "  Frontend PID: $FRONTEND_PID"

# Wait for either process to exit, then shut down the other
wait -p EXITED_PID
if [ "$EXITED_PID" -eq "$BACKEND_PID" ]; then
    echo "Backend exited! Killing frontend..."
    kill "$FRONTEND_PID"
else
    echo "Frontend exited! Killing backend..."
    kill "$BACKEND_PID"
fi
