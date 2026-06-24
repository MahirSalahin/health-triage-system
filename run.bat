@echo off
echo =========================================
echo   Starting Health Triage System
echo =========================================
echo.

echo Starting FastAPI Backend...
start "Health Triage Backend" cmd /k "cd backend && call venv\Scripts\activate && uvicorn app.main:app --reload"

:: Give the backend a second to start before firing up the frontend
timeout /t 2 /nobreak > nul

echo Starting Streamlit Frontend...
start "Health Triage Frontend" cmd /k "cd frontend && call ..\backend\venv\Scripts\activate && streamlit run app.py"

echo.
echo Both servers are starting up in separate windows.
echo To stop the servers, just close those new windows.
echo =========================================
