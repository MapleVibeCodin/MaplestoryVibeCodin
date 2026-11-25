# FM Rush checkpoint — geometry, tooltip, and sold-row recognition (2026-11-26)

## Accessible user messages (verbatim)

- "Resume FM Rush checkpoint v24.63.1. Read https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/AGENTS.md and the latest color-vision research audit and continuation transcript. Verify GitHub checkpoint 44d0aeb5 and run all 10 continuity checks. Continue our existing GitHub and PowerShell workflow. Apply the research from Minerva, mpl-ocr, Simba, SRL, WaspLib and SimpleOCR. Prioritize systemic recognition improvements, failsafes, native glyph recognition and full-pipeline regression across all archived videos and screenshots. Preserve all historical files. Distinguish verified results from experimental findings. Never suggest Work or Codex."
- "is fm rus also updated?"
- "then do full update"
- [Uploaded Windows installer log, 282 lines.]
- [Uploaded screenshot] "no highlight in shop?"
- [Uploaded 2026-11-26 04-39-52.mp4; no text.]
- "save everything to history and gihub"

This is a structured checkpoint, not a complete verbatim platform export. Previous transcript and research files are retained.

## Release chronology

| Commit | Change |
|---|---|
| 44d0aeb54a5377b3979a67f91effbb1c4cbccedc | Starting research checkpoint, desktop 24.63.1 |
| 5498eb4088bf9258b62da56cbc9f564d9e9ea3fc | Geometry research-only checkpoint |
| 7d454f6ffae0437ae6d1e18b3dd36450b91cc667 | v24.63.2 fixed-anchor fallback released |
| 6e6044059e2cd122502a8eb1500afdd7520a99a4 | Mock OCR dependency fix; installer regression gate retained |
| e56fce7470833ed35fb4a60646381efffd722d5a | Corrected v24.63.2 checkpoint |
| 26144410e269e5b1f8e98e02e57dbc6c330a4b87 | v24.63.3 tooltip-safe recognition |
| b11768a4cd424293f24026b061b61c0574e4fdce | v24.63.4 sold-row contrast retry |
| a7bdbe0cbc11d1e9cdae1ab6f0981e761f077622 | Staged alternate sold recognition tests |
| 9b35a301a66d54fe591053a86fe9774037122143 | Published v24.63.4 synchronized release |

Browser remains 24.56.0. Latest screenshot and recording show local v24.63.2. Later desktop installation not confirmed. No historical file deletion or force push.

## Geometry research and validation

Earlier session reported reopening complete private 57-original archive, 10 videos/42 PNG/5 JSONL, 5777 decoded frames, 199 half-second samples, 2914 log events; old exact gate 0/47 video shop anchors; experimental geometry 47/47 known open-shop samples, ten known native anchor PNGs, maximum offline geometry processing 0.89 ms. See existing research/2026-11-26-geometry-shadow-replay.md and fixed-geometry release transcript for limitations. These are prior reported detector results, not newly repeated in this checkpoint, not held-out or full OCR validation. Windows log directly verifies five initial reported v24.63.2 suites passed (34 tests), final inventory suite 29/33 passed; updater refused replacement. Missing mocked _ocr was corrected. Screenshot subsequently demonstrates v24.63.2 running; no complete successful installer log for corrected release supplied.

## Screenshot and video observations

Aqua Brace screenshot: existing tooltip overlaps right of row 2. Visible shop price 8888 vs HeneFM rounded 8900. Prior analysis reported native exact gate and room-title pass, tooltip edge x155, price ink end x139, gap; new safe prefix x152 for normal row. v24.63.3 retains raw row fingerprint and prefix cache key, masks covered right pixels, rejects text touching tooltip, only amber/orange candidate, strict scroll unchanged. Live focus and OCR outcome not independently established.

Blue Arten video 2026-11-26 04-39-52.mp4: previous analysis reported 20.05 s/1203 frames/60fps; visible faded sold item row 5 at 11–12 s, hover at 13–14 s, scroll at 15 s, close around 16–17 s. Price 400000; faded-row preprocessing reportedly retained legible name/price and sold mask passed at 12 s. Actual WinRT OCR return and reason for missed publish not captured; suspected OCR/cache weakness, not proven exact live root cause. New SoldRetryCache: one alternate contrast pass per exact seller/visible sold-row evidence and target, only non-scroll, exact seller/item/price, unique SOLD result downgraded SOLD_CHECK; rejects covered rows and ambiguous matches. Bounded 128 entries, includes alternate timing. Caveat: negative alternate results cached for identical evidence; no universal retry guarantee. Three new test methods staged; full Windows suite not yet run. No native glyph engine or independent price-width verification implemented. Do not claim 100% end-to-end recognition.

## Next action

Read live AGENTS.md, current source and all relevant transcripts; ten continuity checks before further edits. Verify Windows staged updater result for 24.63.4 first, then fresh performance report and native glyph/price width/full-pipeline replay. Historical 116 screenshot blobs and independent held-out OCR/latency testing remain unresolved. No more item-specific patches without evidence. Use pinned PowerShell updater from any directory, no extension flag:
```powershell
$u = Join-Path $env:TEMP 'UPDATE_FM_RUSH.ps1'
$ref = '9b35a301a66d54fe591053a86fe9774037122143'
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/MapleVibeCodin/MaplestoryVibeCodin/$ref/Scanner%20Nov%2020/UPDATE_FM_RUSH.ps1" -OutFile $u -ErrorAction Stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $u -Ref $ref
```
Preserve passive/manual-click workflow, all previous files, settings, archives and branches. No public upload of private raw media or user-local paths. Never suggest Work or Codex.
