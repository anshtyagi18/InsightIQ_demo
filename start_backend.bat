@echo off
echo Starting Insightia FastAPI Backend on http://127.0.0.1:8000 ...
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause

