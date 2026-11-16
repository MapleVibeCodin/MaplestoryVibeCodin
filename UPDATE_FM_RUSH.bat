@echo off
setlocal
cd /d "%~dp0"
echo Close FM Rush before updating. Your settings and installed dependencies will be kept.
if exist "%~dp0.venv\Scripts\python.exe" (
  "%~dp0.venv\Scripts\python.exe" "%~dp0update_fm_rush.py"
) else (
  py -3.12 "%~dp0update_fm_rush.py"
)
if errorlevel 1 (
  echo Update stopped. Keep the message above for diagnosis.
) else (
  echo Run START_FM_RUSH.bat to open the updated app.
)
pause
