FM RUSH v24.54.12 — PASSIVE LIVE AUTO-LOCK

START
Run START_FM_RUSH.bat. FM Rush automatically detects the MapleStory window.
Keep browser_extension v24.54.9 loaded in Brave. Open brave://extensions,
enable Developer mode and Load unpacked if needed. Reload the extension
and reload the HeneFM Deals tab once after upgrading to remove old scripts.
HeneFM now controls its own live updates: no soft refresh or backup reload.
New unsold listings automatically hard-lock; Shift+2 unlocks and re-arms.
Shift+1 manually locks; Ctrl+Alt+N skips. Previously seen listings do not
automatically lock again in the same scanner session.

FM ENTRANCE
START is on row 3 at the central rope, between FM 14 and FM 15.
For FM 13–16 go directly left/right; for FM 17–20 climb; for FM 1–12 descend.
Green click-through outline for FM 7–20 when entrance scenery confirms position.
For FM 1–6, shows the measured down-warp, not a guessed bottom-row door.
When the door is off-screen, shows direction or target FM label. A small title
crop gates full entrance matching; fixed shop marker does not wait on it.

SHOP BOX
Immediate calibrated entry coordinates, not dynamic camera tracking.
FM 4 entry marker moved down 142 client pixels, plus 45px fine correction
at 1366x768 for the default projection only. Manual alignment is unchanged.
FM 9 native 1366x768 doorway anchor corrected left 108 and up 45 client pixels.
FM 5 native 1366x768 default projection moved down 48 client pixels; manual alignment unaffected.
Supported client sizes: 1280x720 and 1366x768. Camera movement can offset the
estimated box. Hover over doorway bottom center and press Ctrl+Alt+F to align.
Ctrl+Alt+C moves pointer to channel cell; Ctrl+Alt+M/J moves pointer to shop.
You click and confirm yourself. Tools contains pointer actions, map and archive.

UPDATE
$u = Join-Path $env:TEMP 'UPDATE_FM_RUSH.ps1'
Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/MapleVibeCodin/MaplestoryVibeCodin/main/Scanner%20Nov%2020/UPDATE_FM_RUSH.ps1' -OutFile $u -ErrorAction Stop; powershell.exe -NoProfile -ExecutionPolicy Bypass -File $u -UpdateExtension

If Brave uses a different unpacked folder, add -ExtensionDir with its actual path.
Reload FM Rush in brave://extensions and refresh HeneFM once after updating.
Updater preserves config.json and archives in LOCALAPPDATA/FM_Rush/archives.
Every explicit HeneFM Deals listing click or CHASE saves click-time JSON to
Desktop\Shit to sell\Click records and attempts a cropped PNG in Desktop\Shit to sell.
If the local bridge is unavailable, JSON falls back to Downloads/FM_Rush_Clicked_Listings.
A moved/disappeared card may prevent a PNG; the click record is still retained when writable.
Auto-lock, SKIP, UNLOCK and passive scans never trigger clicked capture. Bulk archive unchanged.
Project history: ../AGENTS.md

UI: channel navigation arrow text removed from bottom strip; channel and FM overlays unchanged.

FM16: restored room-specific zero bottom margin, moving the default shop projection down 192 client pixels. Manual doorway alignment is unchanged.

FM11: default 1366x768 shop projection moved down 66px based on screenshot 171034; manual alignment and other rooms unchanged.
