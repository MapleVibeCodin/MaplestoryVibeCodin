FM RUSH — CLEAN EDITION (app v24.18 / extension 24.17.0)

1. Extract this entire ZIP into one folder. Do not run it from inside the ZIP.
2. Double-click START_FM_RUSH.bat. Keep the other files in place.
   First launch installs Python 3.12 if needed and downloads dependencies.
   Internet is required for setup. Later launches reuse the local environment.
3. Open brave://extensions and enable Developer mode.
   Remove the old FM Rush extension, click Load unpacked, and select the
   browser_extension folder inside this new FM Rush folder.
4. Reload https://henefm.com/flips/deals and select your buyer's game window.

The app scans sellers currently shown on your HeneFM Deals page.
Ctrl+Alt+B records the selected purchase. View prices in Trade Desk > Inventory.
Ctrl+Alt+N selects the next live deal; Ctrl+Alt+F retries the name finder.
Ambiguous names are marked CHECK NAME.

Automatic screenshots are off by default. Optional screenshots can be enabled
in the extension popup. Nothing in this ZIP contains your screenshots or data.

Existing Windows purchase records are reused automatically from:
%LOCALAPPDATA%\FM_Rushrchives
To retain old window/settings preferences, copy your old config.json into this
folder before starting. Otherwise the app creates fresh local preferences.
Do not delete your old folder until you have checked your records here.

This package contains only the app, required assets, extension and launcher.
No old versions, update tools, update notes, tests, sample images or screenshots.
Dependencies are installed on first launch rather than bundled in the ZIP.
