@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run START_FM_RUSH.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m unittest test_name_finder test_reported_misses test_new_screenshot_names test_name_worker test_fast_gate test_scan_budget test_verification_work test_multi_shop_worker test_room_entry_burst test_deal_archive test_deal_selection test_shop_marker test_browser_bridge -v
pause
