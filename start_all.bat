@echo off
echo Starting Insightia Platform (Backend + Frontend)...
start "Insightia Backend" cmd /k "start_backend.bat"
start "Insightia Frontend" cmd /k "start_frontend.bat"
echo Both servers initiated!
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000

