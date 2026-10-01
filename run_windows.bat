@echo off
cd /d "%~dp0"
if not exist .venv (
  py -3 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if not exist .env (
  copy .env.example .env >nul
  echo Created .env. Add a new Gemini API key there, then run this script again.
  pause
  exit /b 0
)
python main.py
pause