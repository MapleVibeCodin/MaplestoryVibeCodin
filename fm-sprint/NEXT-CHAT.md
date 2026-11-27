# FM Sprint R3 — current continuation checkpoint

Date: 2026-11-27. Branch: `fm-sprint/dual-engine`. R3 runtime checkpoint: `aeb991dafc99ac335d8a2726419e7dbfca4bc50d`. R2 rollback: `4ebabffc4ee8cf45fdfb7adfb9c3dfae020f28ed`. Pinned underlying FM Rush lab base: `a80a9ffbcc2a4a1616b5cfdc8c91b35c430df8fb`. Production main and historical branches untouched.

## Resume order
1. Read this file, fm-sprint/README.md, fm_sprint.py, fm_sprint_core.py, tests and launcher, then root AGENTS.md and performance-lab/NEXT-CHAT.md for the underlying runtime and previous research. Older notes are historical; R3 is the latest Sprint version.
2. Goal: human-centered minimum alert-to-item time. Use the existing HeneFM feed, auto-lock newest eligible listing until Shift+2, no redundant refresh. Starting position assigned CH20 (configurable; not detected), row 3 central rope foot FM14–15. WASD; Shift teleport; S+Space down-jump. Preserve existing portal/camera geometry; no invented movement timings. Current route uses right-hand warp for FM1–6, drop for 7–12, direct for 13–16, climb for 17–20.
3. R3 changes: top-right 160x185 native-pixel transparent click-through map, 12px inset, green fixed start, yellow target and route, short key cues, hides when observed portal fade/room entry/unlock/focus loss/stop. Old external map no automatic popup; Tools > FM map still available. User prefers minimal eye travel and decision making.
4. On initial confirmed black transition park pointer at fixed channel cell. Hold F9 (unbound in game) through manually opened channel menu; one select and confirm per uninterrupted hold with fresh menu validation, re-aim before each click. Release cancels; release/rehold retries failed/unregistered click. F12 stops current locked run. F8 repeats route. F9 only on native 1366x768; do not assume other coordinate scales. Optional experimental -Navigate retains bounded automatic channel/one estimated shop click; default does not open shop automatically. No rapid-fire mouse clicks or unattended purchasing.
5. Both engines share lifecycle: RuneScape native bitmap/sprite fingerprint bank learned from OCR, conflicts abstain, compact OCR fallback; MapleStory native fixed rows/compact WinRT OCR and raw-pixel cache. Existing strict scroll path, hover/sold/stale checks and overlay remain. Cash/scroll/statless classification must be proven, not inferred from blank stats. User wants early shop access while avatar drops after channel return; camera projection is estimated, not verified sign identity.
6. Latest package FM_Sprint_R3.zip SHA256 ab1dfe18d08d74b081ec46cdedc142efc6c86754994a464dc3b645669f732082. All seven packaged file Git blob hashes verified against R3 checkpoint. ZIP was delivered in chat; source files now fully committed. Re-ran all 29 offline tests successfully on current local source. No Windows execution/live integration/50ms end-to-end result verified. Prior Step12/13 datasets remain historical evidence only. PurchaseProof tests are not a live purchase engine. Automated gameplay can violate game rules; maintain manual purchasing and clear distinction between observed/estimated/unverified.
7. Next work: qualify actual Windows overlay/route cue readability and menu registration, measure alert-to-portal and portal-to-channel transition, then first-frame shop projection and recognition on independently labeled native captures. User asked for both engines, fastest human workflow, minimal unnecessary input; preserve prior backups. Do not suggest Work/Codex.
8. Recovery protocol: checkpoint small commits, verify blob hashes and tests, report the last successful operation if interrupted. Last interruption was during R2 GitHub writes; exact platform cause unknown. R3 package is now synchronized, not merely documented. These notes are a substantive engineering handoff, not a verbatim full chat export or confirmation of account memory.

## Package file manifest (Git blob SHA-1)
- `README.md`: `e1fbfd1a553f3f72f94d7f4075d572842ae19c79`
- `START_FM_SPRINT.ps1`: `c6d0643fed254930ddbf8a6d7694182830bf5391`
- `START_MAPLESTORY.bat`: `8ac0b6f5db4ff43d35b2715e17bc28396469f2d7`
- `START_RUNESCAPE.bat`: `d4bc1782d8276456b9e194f7cf556f199839b6b4`
- `fm_sprint.py`: `f3e224ba6c14d1c93d07f5598b4d99a85f871e34`
- `fm_sprint_core.py`: `d8f6e0ff4071b36db9ea84ad266a79c44eb141af`
- `test_fm_sprint.py`: `14f044495e40163579d4a8b2166a5741bead032c`
