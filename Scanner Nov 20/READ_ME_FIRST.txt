FM RUSH v24.63.2 — PASSIVE LIVE AUTO-LOCK

START
Run START_FM_RUSH.bat. FM Rush automatically detects the MapleStory window.
Keep browser_extension v24.56.0 loaded in Brave. Open brave://extensions,
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

INVENTORY RECOGNITION
Exact shop gate stays the fast path. Fixed-anchor geometry fallback requires
multiple visible row backgrounds and expected button strips. Fallback is amber
or sold-candidate only, never a green match or strict scroll match. No changes
to browser extension, hotkeys, click behavior, or local settings.

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

SHOP INVENTORY FINDER
When a locked target's shop opens, suppress room/channel guides. Local Windows OCR
reads the seller and six visible name/price rows; green exact name+price candidate,
yellow multiple candidates, orange unavailable. No automatic scroll, hover or buy.
Verify hidden stats manually. English Windows OCR language required; supported
centered native shop UI is calibrated from the supplied screenshot. No runtime
latency benchmark; scroll manually when target not visible.

OCR v24.55.1: suppresses full-width divider artifacts in sold rows, requests Gray8
from the Windows decoder, reports worker exit and retries stale frames explicitly.
The screenshot confirmed shop detection and the sold-row pixel classification;
Windows OCR recognition and live latency still require validation.

CACHED SHOP FINDER v24.55.2: learns the shop UI anchor once per resolution,
checks a fixed 85x53 pixel gate, fingerprints only native seller/name/price
pixels before preprocessing, and caches 64 recognized inventories per session.
Unchanged inventory and exact cached revisits do not invoke OCR. New visible
text/price/sold pixels or scrolling require recognition. Target changes can
reuse cached text, but still require exact seller/name/price matching. No
live Windows timing measured. FM coordinate projections unchanged.

v24.55.3: FM18 default native 1366x768 shop box lowered 48px. Shop OCR now
uses a grayscale PNG, default WinRT decode followed by BGRA8 conversion, and
stage-specific errors. Seeded 1366x768 shop anchor is pixel-verified, with
fallback to previous calibrated gate. Cache and exact match retained.
Windows OCR must still be tested on the user's machine.

OPTIMIZED v24.56.0: browser semantic card cache with periodic full reconciliation,
batched FULL-durability SQLite writes, no writes for recognized Seen age-only text changes,
no redundant stationary overlay positioning or map/grid redraws, stopped hidden
overlay timers, persistent capture workers and bounded per-worker GDI surfaces,
entrance landmark revalidation, and exact seller/row pixel OCR caches. Install
both desktop and extension. Existing click records and local archives are kept.
Windows and Brave end-to-end performance must still be measured.
Quiet browser heartbeats reuse the last parsed snapshot; a full reconciliation occurs every 10 seconds.

POINTER LATENCY v24.57.0 (desktop only): event-driven GUI wake for Windows hotkeys,
FIFO priority over routine archive polling, one scene/overlay refresh per request,
5ms focus-readiness checks (75ms cap), stale shortcut rejection (150ms), and
revalidation of locked listing, game window/client and alignment before cursor move.
Status reports total, queue and focus timing on successful pointer movement.
No click or game key injection; G HUB remains separate. Windows/Tk focus behavior
and end-to-end latency require live validation. Extension remains v24.56.0.

PERFORMANCE RECORDER v24.58.0 (desktop only)
Automatically records locked listing attempts locally, existing scene and inventory
observations and pointer shortcut/arrival timing. A separate bounded worker samples
three 16x16 game-client patches at up to 20 Hz while the selected game is focused;
slow capture backs off. No raw pixels, text, seller names, keyboard hooks, uploads,
or automated input. A black interval is a visual estimate; nearby channel shortcut
is only an association. Focus loss interrupts measurement; purchase success unknown.
Tools > Export performance report exports all local session logs and timing summaries.
Tools > Pause/resume performance recording controls collection for this session.
Logs: %LOCALAPPDATA%/FM_Rush/performance (separate from listing archive).
No extension update required. Windows sampling and overhead unverified.

POINTER RELIABILITY v24.60.0 (desktop only): same-kind pending pointer requests
coalesce only for the identical validated listing/window; a different request
still supersedes. After successful placement, read-only checks every 10ms for
up to 180ms observe game focus and cursor drift outside the target box. Stops
on superseding request, unlock, geometry change or visible item marker. Reports
focus/distance in performance export. No cursor confinement, extra moves, clicks,
keypress injection or forced game focus. Existing G HUB macros unchanged.
Timing defaults need live validation; the watcher cannot guarantee a click lands.
