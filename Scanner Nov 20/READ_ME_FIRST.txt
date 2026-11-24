FM RUSH v24.53 — AUTOMATIC GRASS CAMERA ALIGNMENT

START
1. Run START_FM_RUSH.bat. The launcher prepares 64-bit Python 3.12.
2. Keep browser extension v24.39.0 loaded. For a first installation, open
   chrome://extensions in Brave, enable Developer mode and Load unpacked
   using the browser_extension folder. Refresh HeneFM Deals once.
3. Select MapleStory in the FM Rush strip. Use Refresh after reopening the game.
4. Shift+1 locks the selected deal; clicking CHASE on a HeneFM card also locks it.
   Shift+2 unlocks; Ctrl+Alt+N skips.

ALIGNMENT
- Grass rooms FM 1–6 and FM 13–16 use passive terrain matching to track the
  camera. A match requires at least two independent landmarks. "Camera
  aligned" means the terrain matched, not that the seller or item was verified.
- "Waiting for grass FM scenery" means the automatic match is unavailable;
  the red box is hidden until alignment succeeds or manual alignment is used.
- Cave rooms still use estimated positioning unless manually aligned.
- Hover over the bottom center of the numbered doorway and press Ctrl+Alt+F
  for manual alignment. With an automatic grass match this adjusts the
  session's tracked doorway offset; otherwise it applies to the current chase.
- Supported client sizes: 1280x720 and 1366x768. Obscured scenery, changes to
  game rendering, stale HeneFM listings and unverified doorway calibration
  may affect accuracy. Automatic alignment still requires live Windows testing.

MANUAL POINTER SHORTCUTS
- Ctrl+Alt+C: move pointer to yellow channel cell; open the channel menu first.
- Ctrl+Alt+M or Ctrl+Alt+J: move pointer to red shop box.
- FM Rush may take focus before moving the pointer. You click and confirm
  yourself. Tools contains the same pointer actions and the FM map.
- Shift+1 / Shift+2 use the number keys above the letters and reserve ! / @
  while FM Rush is running. Close duplicate FM Rush instances if hotkeys fail.
- Tools > Export deal archive saves listings grouped by IGN.

UPDATE AND RESTART
Run the following two lines together in PowerShell from any directory:

$u = Join-Path $env:TEMP 'UPDATE_FM_RUSH.ps1'
Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/MapleVibeCodin/MaplestoryVibeCodin/main/Scanner%20Nov%2020/UPDATE_FM_RUSH.ps1' -OutFile $u -ErrorAction Stop; powershell.exe -NoProfile -ExecutionPolicy Bypass -File $u

The updater locates the scanner, resolves the current GitHub commit, stages and
checks desktop files, stops only the selected scanner and restarts it. It
preserves local config.json, archives and browser extension. It asks which
installation to use if there are several candidates. It does not reload the
browser extension; only do that when extension files actually change.

LOCAL FILES
config.json is generated when FM Rush closes and is intentionally not tracked
in Git. If using git pull on an old checkout, back up config.json first.
Archives live under LOCALAPPDATA/FM_Rush/archives and are never cleaned by
the updater. Python environments, caches and backups are ignored.

Project history and future-session instructions: ../AGENTS.md
Entry portal data: https://osmsdataexplorer.com/data/current/portals.json

CLICKED LISTING SCREENSHOTS (desktop v24.53.1 / extension v24.39.1)
Click a HeneFM deal or CHASE to save a cropped PNG of that listing in Desktop\Shit to sell (under your Windows user profile). Every explicit selection click saves independently of the chase lock and optional bulk screenshot archive. Auto-preview, SKIP and UNLOCK do not save. FM Rush must be running. The PNG includes the item, seller and price as displayed, not a game screenshot. If the card moves during capture, retry the click; failures are shown in the existing card status. The folder is created automatically.
Update desktop and unpacked extension together using UPDATE_FM_RUSH.ps1 -UpdateExtension. If the active extension lives elsewhere, add -ExtensionDir with its unpacked folder. Then reload FM Rush in brave://extensions and refresh HeneFM. No changes to navigation overlays.
