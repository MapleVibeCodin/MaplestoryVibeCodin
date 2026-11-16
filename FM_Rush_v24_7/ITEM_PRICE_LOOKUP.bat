@echo off
setlocal
cd /d "%~dp0"
set "PY=py -3.13"
%PY% --version >nul 2>&1
if errorlevel 1 set "PY=py -3"
%PY% --version >nul 2>&1
if errorlevel 1 set "PY=python"
if exist ".venv\Scripts\python.exe" (
  .venv\Scripts\python.exe item_price_lookup.py
) else (
  %PY% item_price_lookup.py
)
if errorlevel 1 pause
