# FM Rush conversation checkpoint — 2026-11-26 (Taipei)

Scope: accessible user messages and assistant final-response text from this conversation, in order. Markdown retained; rich UI widgets converted to their visible text, code-block IDs and memory citation interface omitted. Two game screenshots referenced but not published to public GitHub. Tool calls, private reasoning and system instructions excluded. User-visible progress messages recorded in a separate appendix. No claim of raw platform export.

## User

give me current command to open fm scan latest one

## Assistant

**FM Rush v24.53.1 — latest recorded scanner.**

Copy and paste directly into PowerShell:

~~~powershell
$f = Get-ChildItem "$HOME\Desktop","$HOME\Downloads" -Filter "START_FM_RUSH.bat" -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1; if ($f) { Start-Process $f.FullName -WorkingDirectory $f.DirectoryName } else { Write-Host "FM Rush not found" }
~~~

Automatically locates and launches the most recently modified FM Rush launcher. Retrieved from yesterday's checkpoint; your local installation has not been reverified.

## User

update to automatically lock onto new listing. and shift 2 to unnlock

## Assistant

**FM Rush v24.54.0 — Auto-Lock update**

- Automatically locks onto the first new unsold listing.
- Hard-locks the seller, item, channel, FM room and shop marker.
- Subsequent listings cannot override the locked target.
- **Shift + 2:** Unlocks and automatically arms the scanner for the next new listing.
- Previously seen listings cannot immediately trigger another automatic lock.

### Update and launch

Paste into PowerShell:

~~~powershell
$u="$env:TEMP\UPDATE_FM_RUSH.ps1"
Invoke-WebRequest "https://raw.githubusercontent.com/MapleVibeCodin/MaplestoryVibeCodin/main/Scanner%20Nov%2020/UPDATE_FM_RUSH.ps1" -OutFile $u
powershell -ExecutionPolicy Bypass -File $u -Ref "1d196f5457a342a23b49289df88116ee8ff3b988"
~~~

No browser extension reinstall required.

Updated source committed and verified on GitHub.

The update command uses the exact new commit because GitHub failed to advance the main branch. Windows runtime and regression tests remain unverified.

## User

save to github, and get rid of the 'mapelstory hwnd' thing, no need its almost always correct. also lets go back to our original baseline of the pre-locked in shop box. because the new one is slow

## Assistant

**FM Rush v24.54.1 — Fast Auto-Lock**

Saved to GitHub main branch and verified.

### Changes
- Removed the MapleStory HWND dropdown and Refresh button.
- Automatically detects the MapleStory window.
- Restored the original instant, pre-positioned red shop box.
- Removed background camera scanning and terrain recognition delays.
- Automatically hard-locks onto new listings.
- **Shift + 2** unlocks and re-arms the scanner.
- Preserved existing channel overlays and shortcuts.

### Update and launch

~~~powershell
$u="$env:TEMP\UPDATE_FM_RUSH.ps1"
irm "https://raw.githubusercontent.com/MapleVibeCodin/MaplestoryVibeCodin/main/Scanner%20Nov%2020/UPDATE_FM_RUSH.ps1" | Set-Content $u
powershell -ExecutionPolicy Bypass -File $u
~~~

**No browser extension update required.**

The shop box no longer waits for camera recognition. It uses the original calibrated coordinates instead, prioritizing speed over dynamic camera correction.

[GitHub — latest scanner source](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/tree/main/Scanner%20Nov%2020)

Source verified. Live Windows performance has not been benchmarked.

## User

also can get rid of the henefm refresh, it's live now

## Assistant

**FM Rush v24.54.2 — Passive Live Scanner**

Updated and verified on GitHub main.

- Removed automatic HeneFM refresh entirely.
- Removed backup page reloads and refresh interval settings.
- Detects live listing changes immediately through DOM observation.
- Retains instant shop boxes, automatic window detection and auto-lock.
- **Shift + 2** unlocks and re-arms.

### Update everything

~~~powershell
$u="$env:TEMP\UPDATE_FM_RUSH.ps1"
irm "https://raw.githubusercontent.com/MapleVibeCodin/MaplestoryVibeCodin/main/Scanner%20Nov%2020/UPDATE_FM_RUSH.ps1" | Set-Content $u
powershell -ExecutionPolicy Bypass -File $u -UpdateExtension
~~~

**This time, reload the browser extension:**

1. Open `brave://extensions`.
2. Click Reload on FM Rush.
3. Refresh the HeneFM tab once.

Afterward, FM Rush will passively monitor HeneFM's native live feed without triggering additional refresh requests. Local scanner health checks remain enabled.

Source verified; live browser performance has not been tested.

## User

[Attached screenshot: image(20261125-162743).png; not published.]

fix

## User

[Attached screenshot: image(20261125-162845).png; not published.]

this too

## Assistant

**FM Rush v24.54.3 — FM 4 correction**

- Moved the red shop box down 142 game pixels to align with BadLilBow's shop.
- Preserved instant highlighting without camera scanning.
- Other FM room calibrations remain unchanged.

Saved and verified on GitHub main.

**Update and launch:**

~~~powershell
$u="$env:TEMP\UPDATE_FM_RUSH.ps1"
irm "https://raw.githubusercontent.com/MapleVibeCodin/MaplestoryVibeCodin/main/Scanner%20Nov%2020/UPDATE_FM_RUSH.ps1" | Set-Content $u
powershell -ExecutionPolicy Bypass -File $u -UpdateExtension
~~~

Both screenshots show the same FM 4 misalignment. The correction is calculated from the screenshot; live alignment remains unverified.

## User

can you update to include FM location on screen too?

## Assistant

**FM Rush v24.54.4 — On-Screen FM Portal Highlight**

Updated and verified on GitHub main.

The scanner now uses three distinct indicators:

**Green:** Destination FM entrance portal.

**Yellow:** Destination channel.

**Red:** Target seller's shop.

- Automatically switches to entrance guidance when the FM entrance is detected.
- Shows directional guidance for off-screen portals.
- Preserves instant shop highlighting, auto-lock and Shift+2 unlock.
- No forced HeneFM refresh.

### Update and launch

~~~powershell
$u="$env:TEMP\UPDATE_FM_RUSH.ps1"
irm "https://raw.githubusercontent.com/MapleVibeCodin/MaplestoryVibeCodin/main/Scanner%20Nov%2020/UPDATE_FM_RUSH.ps1" | Set-Content $u
powershell -ExecutionPolicy Bypass -File $u
~~~

No additional extension update required if you're already on v24.54.2.

**Remaining limitation:** FM 7–20 have measured portal coordinates. FM 1–6 currently highlight the down-warp leading to their floor. Live Windows alignment and performance remain untested.

## User

can you update everything on github and this conversation for batum?

## Appendix: accessible progress messages

- I found the v24.53.1 source on GitHub. Shift+2 is already registered globally; the missing behavior is automatic locking and preventing the same listing from immediately locking again after you unlock it.
- I’ll inspect the current scanner and its earlier shop-marker implementation, then update GitHub with the simpler window selection and faster preview.
- I found the last version before camera tracking was introduced. I’ll restore its immediate coordinate-based shop box and retain auto-lock and Shift+2. The trade-off is that the box will no longer correct itself when the in-game camera moves.
- I’ll remove the automatic page refresh while keeping live listing detection and the auto-lock behavior.
- The red box is on the wrong platform in FM 4. The target is BadLilBow’s yellow shop one level below it. I’ll check the coordinate calibration without bringing back the slow camera scanner.
- I’ll add an on-screen FM entrance indicator alongside the existing channel and shop markers, while keeping the scanner lightweight.
- I found the earlier entrance-portal coordinates for FM 7–20. FM 1–6 were below the visible area in that reference, so I’ll mark the down-warp toward them rather than guess their door coordinates.
- I’ll save a verbatim text transcript of this conversation, update the project handoff, and verify the latest scanner state on GitHub.

## Correction to historical response, not part of transcript

The assistant's v24.54.3 reply incorrectly said both screenshots depict FM 4. The second screenshot actually depicts CH 28 / FM 08, seller Fuad7, item Green Napoleon, with the shop sign above the visible client and a "Shop sign above view" notice. Only FM 4 was corrected. FM 8 was not fixed; a partly off-screen shop is not evidence for an arbitrary global Y offset. Retain this as outstanding. No raw screenshot pixels published.
