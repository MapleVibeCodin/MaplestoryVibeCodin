@echo off
setlocal
cd /d "%~dp0"
set "PY=py -3.13"
%PY% --version >nul 2>&1
if errorlevel 1 set "PY=py -3"
%PY% --version >nul 2>&1
if errorlevel 1 set "PY=python"
if not exist ".venv-web\Scripts\python.exe" (
  echo Creating a lightweight FM Rush environment (NO OCR)...
  %PY% -m venv .venv-web
  if errorlevel 1 (echo Python not found & pause & exit /b 1)
)
.venv-web\Scripts\python.exe -c "import PIL, numpy" >nul 2>&1
if errorlevel 1 (
  .venv-web\Scripts\python.exe -m pip install -r requirements-web-only.txt
  if errorlevel 1 (echo Install failed & pause & exit /b 1)
)
set "FM_RUSH_WEB_ONLY=1"
.venv-web\Scripts\python.exe fm_rush.py
if errorlevel 1 pause
