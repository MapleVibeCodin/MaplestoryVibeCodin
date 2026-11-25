# 2026-11-26 — systemic FM Rush audit / checkpoint

## User instructions preserved verbatim (accessible late-chat messages)
- "how do i give you the performance?"
- "ok now look at that video"
- "ok update"
- "do i have to send one by one? how come its not working? deep dive into your methology and fix"
- "save all to github and memory and figure out what the issue is."

Earlier instructions in this session: four room groups share first-frame channel-change motion; immediate manual clicking, no additional OCR/capture delay for projection; exact fixed shop gate; inventory scan only in actual FM room, not entrance; strict similar-scroll matching; allow armed mode inventory recognition without navigation or automatic lock; retain all history.

## Root cause and release
The 03-55-12 recording shows v24.62.4, a locked listing in FM9 and an open shop, but the UI remains "Waiting for confirmed FM room". The hardcoded title byte strips were overly restrictive: even lossless original room screenshots failed the first exact strip. Inventory OCR is gated upstream by this result. Replace byte equality with a bounded shape matcher that tests the title prefix and opening bracket separately. Do not remove the room gate. Preserve exact shop gate, camera profiles, scroll strictness, hover changes, armed/locked separation, historical files and browser v24.56.0.

Runtime repair commit: c27c8671630225d94133e4194d5ac4584e5e0b8c (v24.63.0).
Additional regression checkpoint: four actual thresholded title ROI masks inline in staged test_inventory_hover.py (two PNGs and two video frames), and this record.

## Replay evidence (2026-11-26)
All eight accessible video originals sampled every six frames, about 10Hz. Labels use stricter fixed-position title similarity and black-frame heuristics; these are NOT independent manual ground truth. The room template was obtained from 03-55-12, so this is an offline engineering regression, not a held-out accuracy estimate.

| Filename (time) | Room | Nonroom | Ambiguous | Miss | False positive |
|---|---:|---:|---:|---:|---:|
| 03-14-15 | 37 | 22 | 3 | 0 | 0 |
| 03-14-30 | 45 | 20 | 3 | 0 | 0 |
| 03-14-46 | 39 | 19 | 3 | 0 | 0 |
| 03-15-01 | 36 | 20 | 3 | 0 | 0 |
| 03-38-05 | 101 | 17 | 3 | 0 | 0 |
| 03-42-22 | 67 | 17 | 3 | 0 | 0 |
| 03-46-13 | 117 | 43 | 36 | 0 | 0 |
| 03-55-12 | 58 | 15 | 4 | 0 | 0 |
| Total | 500 | 173 | 58 | 0 | 0 |

731 samples, 673 scored; median matcher 0.363ms, p95 0.603ms, offline Python implementation equivalent to committed matcher, not screen capture or Windows runtime. PNG replay: 21 title-aligned room screenshots accepted and two entrance screenshots rejected. Other PNGs omitted from title score when no reliable alignment. Fixed shop gate still detects known open shop anchors. Full historical 116-image corpus not replayed; real WinRT OCR, startup tests and latency not verified here. No claim of zero matching errors. Current strict scroll identity and price policies unchanged.

## Diagnostics
Recorder now emits scanner_gate states and inventory_timing, recognizes actual current hit modes; report shows scan/row recognition latency (OCR vs cache), candidate/sold/match vs failure state. Recorder remains lock-only; early-return scans without a final timing result not included in timing distribution. Use existing Tools > Export performance report. No raw screenshots/identifying OCR text added to telemetry. One combined report is preferable to separate videos.

## Media preservation and limits
A separate local ZIP was generated containing 49 unique accessible originals (8 MP4, 41 PNG), 95,178,243 bytes including embedded MEDIA_MANIFEST.json with SHA256 and relative path for each original. This ZIP is available in the chat attachment; it is NOT a GitHub upload. Connector cannot directly transfer these container binaries. Existing repository archive untouched. The three inline screenshots in the final interruption were not exposed in the file attachment list (turn 23) and could not be inspected or archived byte-for-byte. No fabricated visual findings. Full chat verbatim archive and raw new media upload not completed; this is a structured checkpoint, with the latest accessible user text verbatim. Permanent ChatGPT memory cannot be forced or directly written by available tools; AGENTS.md is the durable handoff.
