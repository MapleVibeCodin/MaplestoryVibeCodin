@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run START_FM_RUSH.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m unittest test_name_finder test_reported_misses test_name_worker test_fast_gate -v
pause
