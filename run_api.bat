@echo off
echo Starting Smart Email Prioritization API...
call .venv\Scripts\activate.bat
python -m uvicorn api.main:app --reload --port 8000
pause
