# FM1 movement and scanner checkpoint — 2026-11-25

This is a research handoff, not a new scanner runtime release. Preserve the existing scanner's passive/manual-click design. Logitech G HUB macros are independent experiments, not integrated into FM Rush. Do not publish game screenshots, account details, local archives, or personal data in this public repository.

## Current verified published scanner
- Desktop title in `Scanner Nov 20/fm_rush.py`: FM Rush v24.53.1 - Camera alignment (blob 3003be0a814acb8a647a2a02da3fce230b015869).
- Browser extension manifest version 24.39.1 (blob c9fabc64c10959cd05a8ead9c6e9c6a80f0a74c0).
- Universal updater inspected: `Scanner Nov 20/UPDATE_FM_RUSH.ps1` (blob c490c8693847cddf0109fbb56164d3b7602caac9). Default desktop only; -UpdateExtension optionally updates existing unpacked browser extension. Reload the extension and refresh HeneFM if updated.
- Latest known published runtime commit 01f3f212803daafb507d631e02874b2a719a0748 (from existing checkpoint); source version verified directly again. No runtime changes requested or made in this checkpoint.
- Automatic grass camera alignment, cave estimated/manual, chase hard-lock, non-obscuring red marker, click-only listing PNG capture. Windows/Brave live tests remain unverified.

## User-confirmed controls and goal
A left, D right, W up/portal, S down, Shift Teleport, Space jump. **S + Space simultaneously is down-jump**, not Space alone. Starting location: base of FM14–15 rope. Target: align directly above/at FM7, drop vertically to FM1, enter with W; avoid overshooting left and correcting right. User wants each failure analysis followed immediately by concrete next PowerShell update, not just explanation.

## Test history (previous conversation observations; not remeasured at this checkpoint)
Original manual attempts (video filenames 15-20-16, 15-22-48, 15-24-23) had reported travel times 2.62, 2.55, 2.15 s respectively; fastest pre-fade estimated 2.37 s. These are provisional video observations, not verified key timings. Original teleport interval estimated ~650 ms and distance ~147 recorded pixels; camera and scale influence measurements.
- V1: 3 left Teleports and W; test video 15-37-41 showed it stopped on FM7 platform left of door. Missing explicit down-jump.
- V2: added further left travel then right correction; no confirmed test.
- V3: restored three Teleports, added S+Space; test 15-44-49 reached bottom but too far left of FM1. Prior response reported bottom alignment failure, not a measured pixel offset.
- V4: proposed rightward corrective Teleport after descent; untested and superseded by explicit user preference not to go so far left.
- V5: proposed two Teleports, shorter left travel, then S+Space and W; no submitted V5 result. Next action: assess a V5 video and adjust the second-Teleport follow-on movement and landing wait only as evidence warrants. Never assert reliable FM1 entry until observed. If first platform descent is missing, explicitly verify geometry and use an appropriate drop action only after alignment.

## Exact V5 programmed event timings
The latest suggested macro has total explicit delay 2760 ms. All other delays depend on G HUB playback and game behavior; no claim of actual time to portal.
| t (ms) | event |
|---:|---|
| 0 | A down |
| 10 | Left Shift down |
| 40 | Left Shift up |
| 660 | Left Shift down |
| 690 | Left Shift up |
| 1300 | A up |
| 1650 | S down |
| 1660 | Space down |
| 1710 | Space up; S up |
| 2460 | W down |
| 2760 | W up |

HID usages A=4, Shift=225, S=22, Space=44, W=26, D=7. G HUB macro name FM 01 FAST; no-repeat SEQUENCE, explicit delays, preserve card ID/application ID, back up SQLite settings.db before updates; do not overwrite other cards or edit while G HUB is running. The proposed update commands used Python sqlite3 and the local G HUB settings database. No local install success or live timing validation is claimed.

## Recording workflow
OBS 1280×720 output, 60 FPS, 4–6 s clips, about 0.5 s idle before/after. Game Capture only, no OBS interface or duplicate Display Capture; mute audio. Key overlay W,A,S,D,Shift,Space helps identify actual input times; previous response proposed Input Overlay plugin installation and a separate FM Research profile, but plugin installation and scene configuration are unverified. Keep high FPS; shorten clips instead. No actual Windows OBS changes were executed by ChatGPT.

## Access and transcript scope
The separate visible-message archive contains exact user text and selected assistant text/code recoverable in the current context. It is not a full platform export; older condensed messages, collapsed/tool/private content, and original UI rendering cannot be reconstructed verbatim. Private videos should remain in ChatGPT Library, under /FM Rush Research/2026-11-24, not GitHub. Read [prior viewport research](2026-11-24-viewport-and-input-observations.md) and root AGENTS.md before resuming. No account details in public checkpoint.
