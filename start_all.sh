#!/bin/bash
echo "Starting Insightia Platform..."

# Start backend
(cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload) &
BACKEND_PID=$!

# Start frontend
npm run dev &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID (http://localhost:8000)"
echo "Frontend PID: $FRONTEND_PID (http://localhost:3000)"

trap "kill $BACKEND_PID $FRONTEND_PID" SIGINT SIGTERM
wait

