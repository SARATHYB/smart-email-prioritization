@echo off
echo Starting Smart Email Prioritization Dashboard...
call .venv\Scripts\activate.bat
python -m streamlit run frontend/streamlit_app.py
pause
