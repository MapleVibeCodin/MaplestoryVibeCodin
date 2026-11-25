# 2026-11-26 final continuation checkpoint — FM Rush v24.63.0

User's latest request: "ok update everything and new chat". Prior requests: "save all to github and memory and figure out what the issue is." and "do i have to send one by one? how come its not working? deep dive into your methology and fix".

## Current runtime
- Desktop v24.63.0, runtime repair commit c27c8671630225d94133e4194d5ac4584e5e0b8c, audit and regression checkpoint 86bdd67db919d37c40b371e1353f56a0a345e01d. Browser extension v24.56.0 restored, no refresh. All older commits/files/backups preserved. Read AGENTS.md and 2026-11-26-inventory-pipeline-audit.md before changing code.
- Root cause demonstrated by 03-55-12 video on v24.62.4: locked open shop while UI displays Waiting for confirmed FM room. Exact RGB minimap title gate prevented inventory OCR. Replaced with bounded shape matcher, keeping entrance/black exclusion. Offline 500 room/173 nonroom classified correctly, 58 ambiguous omitted, heuristic labels, no held-out accuracy claim; median 0.36 ms and p95 0.60 ms exclude capture/WinRT.
- Current capture-to-highlight design: confirmed FM room only; exact fixed three-button shop gate; ARMED scans displayed listing, LOCKED also enables navigation. Full seller/name/price strict, scrolls require second contrast confirmation, truncated scroll names never guessed. Non-scroll rounding/partial-row candidates amber, sold candidates orange; green verified name + price, not hidden stats. No automatic purchases or extra input. Hover and orange selected row preprocessing, row cache, generation guards. Four CC anchors for native 1366x768 preserved; first-frame estimates only, normal portal option and 1280x720 original calibration retained.
- New recorder logs scanner_gate and inventory_timing with OCR versus cache latency and corrected match classification. Raw OCR, images, names not logged. The recorder remains lock-only; timing events only from completed published scans.

## Five newly accessible uploaded performance logs
Parsed all JSONL lines successfully, 2,914 events across 37 unique attempt IDs. Four files tagged recorder 24.60.0; one tagged 24.58.0. These tags are recorder versions, not proof of desktop runtime version. These logs do NOT contain the new gate/timing events and cannot validate v24.63.0. Historical status classifier was stale relative to newer hit labels; absence of unique_match is not proof of zero correct highlights.

| Metric | n | Median | p90 | Max |
|---|---:|---:|---:|---:|
| Successful channel pointer total ms | 201 | 11.3 | 14.2 | 43.4 |
| Successful shop pointer total ms | 112 | 11.5 | 13.3 | 16.2 |
| Channel pointer to game focus ms | 199 | 63.6 | 67.0 | 185.3 |
| Shop pointer to game focus ms | 112 | 63.15 | 66.8 | 156.6 |
| Black interval associated with recent channel shortcut ms | 7 | 1529.6 | 1637.4 | 1640.6 |
| Unclassified black interval ms | 16 | 219.0 | 437.4 | 438.8 |

358 pointer requests; 313 successful pointer_result records; 2 explicit channel failures (focus_not_released, expired); four observed channel drift events (2,2,10,39 pixels), not a complete failure rate. 276 completed watches, channel 193 and shop 83, median and p90 maximum outside distance zero, channel maximum 110.5 pixels. Event count differences are not necessarily failures. 904 inventory state transitions: 443 reading, 340 other, 59 not_visible, 37 seller_unverified, 25 target_unavailable; 43 shop scene transitions, 39 entrance, 103 unclassified. Repeated reading/other transitions are a reason to instrument whole pipeline rather than patch individual rows; old classifier prevents reliable success-rate attribution. No confirmed purchase outcomes in these logs.

## Media and logs preservation
The previously unavailable two new recordings, three PNGs and five JSONL logs became accessible in the container. The two repeated screenshots (033328(1), 033457(1)) have SHA-256 duplicates in previous archive. Unique new screenshot 035825, two new recordings 03-56-42 (592 frames, 60fps, 9.867s) and 03-58-13 (818 frames, 60fps, 13.633s), and all five raw logs added to expanded local ZIP. ZIP integrity test succeeded: 57 unique originals (10 MP4, 42 PNG, 5 JSONL), plus MEDIA_MANIFEST.json, 109961754 bytes. File FM_Rush_2026-11-26_complete_checkpoint.zip. Media not published to GitHub (raw recordings may contain personal desktop/game info; existing project instruction prohibits public raw-video upload). No new video OCR replay performed in this checkpoint. The summary and hashes below are saved to GitHub. Full transcript verbatim and permanent ChatGPT memory write not available; do not claim otherwise. No source runtime changes in this final documentation checkpoint.

| Original | Bytes | SHA256 |
|---|---:|---|
| 03-56-42.mp4 | 6511580 | a9460a734c65e127a0acfa37c8906614d84974c18d8d15a723fef0f2333fc260 |
| 03-58-13.mp4 | 8213521 | c22ecae22e2af959d84dadc7484fa31606517559f0d92947414d1ca32486fb35 |
| Screenshot 2026-11-26 035825.png | 1037271 | 640d2aa1d2760a12fca2b3ca62d367ac39a8d49db797f6a15d9866a1979b4e64 |
| 79acca80d6214de3887a1085d033aeb4.jsonl | 879 | 78617a4b0fce4d86ae2e025f5e5747152a05004b914d750357bf9df0a74b82e5 |
| a3630688d87c460699286859eb36f7b7.jsonl | 462 | 02c8acd4090229d7abb82a6038ecc1f9761393b970060fad7069796bfd60de03 |
| bd7abcd3c39d4ad79b8a7bcec86e66dd.jsonl | 12432 | 1865e77cea2ce6575c7c130870c14a45f1c857870112f878dd8dc6b3a7d5a264 |
| cafe464492874c43b46a0983f738e5be.jsonl | 17636 | 96484b9485a834ae81bba6ce8f54c3321e709ddbdb6a08bd7c58c4da71de8185 |
| e28890f1e7c942a8a69027644ff31452.jsonl | 601376 | 69e0bdd4537ff4a00aa3bf72b32d9b82debad135869a155a416105c34f9cb78f |

## Next chat
Read latest AGENTS.md, both audit documents, all 10 continuity checks. Confirm actual main and runtime version. Install via pinned universal updater (runs staged Python tests before replacement, backs up installed files, preserves local data). No need extension update. If startup tests fail, diagnose exact failing test and fix before new features. If installed and live, export one fresh performance report after 30–50 ordinary attempts, inspect gate and inventory timing; distinguish missing data from failures. Do not require a video for every failed row. Analyze latest two clips and screenshot if available from chat/library, and include real WinRT OCR and older historical replay as unresolved. User requires direct ChatGPT workflow with GitHub and PowerShell, no Work or Codex suggestions.
