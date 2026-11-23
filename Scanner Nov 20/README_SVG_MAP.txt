FM RUSH v24.32 — LIVE SVG ROUTE MAP

This is a COMPLETE install based on v24.31 (the fast OCR build), with an
additional integrated SVG navigator. No Python dependencies were added.
The original Tk FM map is preserved in Tools > FM map.

QUICK START
1. Unzip latest.zip to a NEW folder. Do not unzip into your old scanner folder.
2. Run START_FM_RUSH.bat. It will check Python 3.12 / dependencies.
3. In Brave, the HeneFM extension must be loaded and watching:
     https://henefm.com/flips/deals
   If you moved/deleted the old extension folder, open brave://extensions and
   'Load unpacked' from the new latest/browser_extension folder.
4. Open Tools > SVG Map in the Windows app or double-click OPEN_SVG_MAP.bat.
   Direct map address: http://127.0.0.1:18773/fm-map

BEHAVIOR
- The first visible HeneFM deal is the default route and selected seller.
- Seller IGN and the selected item are clearly highlighted.
- CHASE locks the selected listing; incoming deals cannot override it.
- UNLOCK / FOLLOW FIRST returns to the first visible listing.
- Clicking a numbered portal previews the route for 60 seconds, then restores
  the first live deal unless a chase is locked.
- All 20 portals, 4 rows, center ropes and map routes match route_logic.py.
- SVG and the feed share the local archive/state; the SVG page never calls OCR.
- Changes to the local selected listing update the SVG map in ~0.4 seconds
  while the tab is active. This is a polling interval, NOT a measured end-to-end
  scanner latency guarantee.
- The browser route is a SCHEMATIC. It does not estimate travel duration,
  teleport timing, player movement, nor exact pixel alignment in the game.

PERFORMANCE / SAFETY
- The map uses the browser's vector renderer, not the OCR recognition worker.
- Runs only on 127.0.0.1:18773; no external map or network service.
- Local map actions require a same-origin request and custom header.
- The old v24.31 OCR fixes are unchanged.

VERIFICATION
- Python source compiles; JavaScript syntax checked.
- HTTP integration: first listing, state, routing, lock/unlock, portal preview,
  input/origin validation, and 60-second restoration passed on mock app state.
- Chromium UI test: SVG rendering, 20 portal clicks, chase, unlock and manual
  preview passed using mock deal data.
- Actual Windows + MapleStory speed and live app UI have NOT been measured here.

IMPORTANT
The scanner reuses its deal archive in %LOCALAPPDATA%\FM_Rush\archives.
If you changed any local config.json, copy that file to the NEW folder manually
(after backing it up). Keep your previous scanner folder until this version runs.

v24.33: The SVG dashboard also reports the item icon finder status, and the
channel destination is prehighlighted before any game OCR. The in-game item
finder outlines candidate artwork only; it does not validate stats/price.
