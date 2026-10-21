#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
[ -f .env ] || cp .env.example .env
echo "=== Spider Jarvis (PAPER TRADING) ==="
cd backend
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
pip install -q -r requirements.txt
mkdir -p logs
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ../frontend
npm install --silent 2>/dev/null || true
npm install zustand --silent 2>/dev/null || true
npm run dev -- --host &
FRONTEND_PID=$!
echo "Backend:  http://localhost:8000  (PID $BACKEND_PID)"
echo "Frontend: http://localhost:5173 (PID $FRONTEND_PID)"
echo "Safety:   http://localhost:8000/api/safety"
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
