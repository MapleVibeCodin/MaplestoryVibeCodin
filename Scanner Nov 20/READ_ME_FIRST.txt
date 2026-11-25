FM RUSH v24.54.6 — PASSIVE LIVE AUTO-LOCK

START
Run START_FM_RUSH.bat. FM Rush automatically detects the MapleStory window.
Keep browser_extension v24.54.2 loaded in Brave. Open brave://extensions,
enable Developer mode and Load unpacked if needed. Reload the extension
and reload the HeneFM Deals tab once after upgrading to remove old scripts.
HeneFM now controls its own live updates: no soft refresh or backup reload.
New unsold listings automatically hard-lock; Shift+2 unlocks and re-arms.
Shift+1 manually locks; Ctrl+Alt+N skips. Previously seen listings do not
automatically lock again in the same scanner session.

FM ENTRANCE
Green click-through outline for FM 7–20 when entrance scenery confirms position.
For FM 1–6, shows the measured down-warp, not a guessed bottom-row door.
When the door is off-screen, shows direction or target FM label. A small title
crop gates full entrance matching; fixed shop marker does not wait on it.

SHOP BOX
Immediate calibrated entry coordinates, not dynamic camera tracking.
FM 4 entry marker moved down 142 client pixels using the supplied screenshot.
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
Explicit listing clicks still save PNGs to Desktop\Shit to sell; automatic
locks do not save screenshots. Optional bulk archive remains unchanged.
Project history: ../AGENTS.md
