#!/bin/bash
# CubeSMS - Start dev servers
# Backend: http://localhost:8000
# Frontend: http://localhost:5173 (proxies API to backend)

set -e

echo "🚀 Starting CubeSMS..."

# Start backend
cd "$(dirname "$0")/backend"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level warning &
BACKEND_PID=$!

# Start frontend
cd "$(dirname "$0")/frontend"
/usr/bin/npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ CubeSMS running:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Default login: admin / admin123"
echo ""
echo "Press Ctrl+C to stop all services"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
