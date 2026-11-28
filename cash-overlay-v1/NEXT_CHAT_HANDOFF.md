# Cash Overlay v1.5 — new-chat handoff (2026-11-28)

## Resume target
Runtime release: 585ebb8c2b08e33e452b9b92a6632537d1c644cf. This handoff is documentation only; no runtime modifications. Read AGENTS.md and checkpoints/LATEST.md, then this document, RESEARCH_OBJECTIVES.md and README.md. Latest runtime is v1.5, not v1.3/v1.4. Preserve all historical files and local evidence. Use regular ChatGPT and GitHub connector; user prefers one copy-paste PowerShell command, not instructions to manually edit files. No upload of raw personal screenshots to public GitHub. Passive visible-screen research only; no game input.

## Objective
Map quality: EXP/hour, raw pickup mesos/hour, NPC value/hour, wallet change, actual paid costs, mobs/hour. Personal efficiency: movement, attack/kill/loot/wait times, time to kill, spawn and reappearance, neglected platforms, possible spawn-cap pressure, relative position to anonymous other players, and solo vs population comparisons. Capture first, analyze afterward. User wants all visible evidence before analytical questions, without redoing sessions. Separate observed, inferred, estimated, unknown. No continuous video. Preserve inventory snapshots (Use, all Etc pages, Equipment > Deco pet potion slots), map and status, wallet and messages. Do not double-count linked pet pot stacks.

## Runtime and data
- Upstream Javipen/maple-exp-overlay pinned 1a25186943a42fccd89eec2e0777c7b41ea5a21f. Local-only, no FM Rush edits. Installer creates separate timestamped build, uses own venv, preserves upstream license, includes MCWO dataset. Tesseract may be needed separately.
- v1.5 target cadence 2 Hz full native scene, 4 Hz eight-second burst on observed EXP change/map/page changes. Rich UI crops roughly 1 Hz; native JPEG65 4:4:4 scene, lossless deduplicated UI PNGs, full reference PNG about every 60s and detected map/page changes. Actual capture gap logged; real 2/4 Hz performance and storage untested.
- Local data root %LOCALAPPDATA%\MapleCashOverlayV1; screenshots/<timestamp_uuid>/ includes full scenes, JSON sidecars, ui/ hashes, recognized_messages.jsonl, message_evidence/ line crops and recognition attempts when delivered by upstream. cash-sessions.csv cumulative rows, do not sum. No automatic deletion; disk guard 5 GiB. Screenshot capture foreground only. Desktop shortcuts Maple Cash Overlay, Maple Cash Screenshots, Analyze Latest Maple Session.
- scene_analysis.py accepts old PNG/WebP and new JPG, excludes evidence crop folders; optional labeled templates in scene-templates/{monster,self,player,anchor}. Without templates, endpoint/camera analysis only. research_analysis.py computes registered candidate track points, visibility events, motion px/s, visible duration, paths, nearest-player proximity, region occupancy and reappearance candidates. Registration is epoch-local, not absolute map world coordinates. No automatic confirmed attacks or kills. Reviewed combat CSV supports attack/death timing brackets; reviewed counts lower bounds. No live calibrated templates supplied. No claim all 99 upstream repos integrated.
- MeowDB local reference JSON for Primeval Forest I only (010006010), source https://meowdb.com/msclassic/maps/010006010, recorded 23 possible points, modeled cap10, tick7.56s, modeled realistic 952 mobs/h and 88,949 EXP/h. Glowshroom 1377 HP/82 EXP/8 points; Aqumander 2069/98/9; Echopus 2163/107/6. Reverify page and model before conclusions; no automatic scraping, no exact map-world coordinate alignment. Source model not measured server capacity.
- Installer dependencies checked against committed tree: 15 referenced project files; missing [].

## Evidence and known failures
Read FIRST_CAPTURE_QUALIFICATION.md (79 actual v1.3 screenshots, 1.010s cadence, 529KB/image, map null from overlay occlusion, undercounting pickup and item OCR, negative metadata ages), CAPTURE_COMPRESSION_BENCHMARK.md (native JPEG65 4:4:4 + lossless fixed-region crops ~281KB, ~10.5ms encode in Linux; not current Windows performance), SPATIAL_RESEARCH_SOURCE_CATALOG.md (29 refs, 8 pinned, 12 files read), and research/2026-11-28-primeval-forest-i-five-minute-method.md (paired endpoint reconciliation, no continuous five-minute archive). Raw personal evidence stays local; original upload not copied to public repo. Prior session images and results may be available in old chat but not guaranteed in new chat.
- First-session metadata ordering corrected in v1.4 code, initial minimap relocation implemented but not live validated, message evidence retention v1.5 does not repair recall by itself. Verify map visible, timestamps, pickups, item and pet counts, tab detection (including overlap/scroll), geometry and reminder acknowledgement. No complete inventory quantity extraction or automatic inventory delta reconciliation yet.
- v1.5 movement and reappearance candidates are not exact kills, respawns or server-side spawn data. Need real sprite templates, camera/motion validation, reviewed combat association and offline replay. Do not classify offscreen actors as absent or identify other players. Short endpoint tests cannot measure individual kill timing.
- Tests: five original core unit tests documented executed with matching blob hashes. First live v1.3 capture tested. Isolated synthetic translation +12,-7 and blank-frame rejection reported executed. Installer includes 5 cash, 7 screenshot, 5 scene, 6 hybrid, 8 research tests (31 total by source definitions); do not claim full suite passed. Windows v1.5 install/GUI, actual capture rate/storage, OCR recall, inventory detection, real actor tracking, and kill/respawn classification remain unverified. No additional tests executed in this documentation checkpoint.

## Immediate next step
Continue from v1.5: analyze the next actual session archive if available; first verify the installer/run and capture health, then calibrate real map-specific templates and replay historical evidence (do not request repeat captures for already-visible data). Prioritize reliable inventory/potion reconciliation, lossless message recall, camera registration and evidence-backed attack/death attribution, then spawn density and MeowDB comparison. Measure actual storage and latency; if necessary improve asynchronous capture and compression without deleting existing evidence. Keep all findings and regression fixes in GitHub with actual readback and update the continuation pointer.

## Source map
- cash-overlay-v1/{cash_overlay.py,screenshots.py,hybrid_capture.py,inventory_ui.py,scene_analysis.py,research_analysis.py,cash_core.py,meow_reference.json,INSTALL.ps1,TEST_EVIDENCE.md}
- research/tracker-source-collection-2026-11-28/EXPANDED.md and manifest.json (99 candidate catalog, 33 pinned); selected-source/ archived licensed blobs. Spatial catalog is separate, overlaps possible. No claim all ZIPs downloaded.
- research/2026-11-28-mcwo-level-20-50/data.json and README.md (62 query windows, 121 names, not complete underlying data). Original source refs and prior comparisons retained in checkpoints/LATEST.md.
- Runtime blob inventory: HANDOFF_MANIFEST.json.

## Scope and audit
Remote main before checkpoint 585ebb8c2b08e33e452b9b92a6632537d1c644cf; tree 485 entries, not truncated; compare from v1.3 5a6c2831fefd4dffbb3eb9b91bc05d264c3e66d4: 8 commits ahead, zero removed paths. Verified source/installer presence and prior documentation, no new runtime tests. Master AGENTS and LATEST fetched but output truncated, not full line-by-line audit. Complete verbatim conversation export and raw attachment recovery not achieved; do not claim otherwise. No personal character holdings or names added. Latest user directions recorded verbatim separately below.

## Accessible user directives (verbatim)
- "great. remember the goal for this is to 1. track how good the map is. metrics are exp/hour, mesos/hour, and mobs per hour.&#x20;

2. track how efficient i am being. are mobs spawning in places im not killing fast enough? Are they getting spawn stuck? is there better places? Am i in a map with too many players that doesnt support spawn? Am i by myself and im better off with a few people in the map? all these are potential questions. I want to have all the raw data before asking the questions so i dont have to go back to collect."
- "now look up github. all similar style code. minic and learn. get exact github links and tell me. just google search can find tons"
- "now upgrade it to be the very best it can be. also make it give me a reminder to show inventory (and etc tab) and pet equip inventory pot  (to track usage)"
- "great. now update"
- "yes you can. do"
- "real 5 minute session. analyze"
- "okay. now update everything to capture exactly what im talking about, and then also mob movement, kill time, kill speed, and connect that to the meow db comparison. For example, this map is [https://meowdb.com/msclassic/maps/010006010](https://meowdb.com/msclassic/maps/010006010)"
- "update everything and lets transition to new chat"

No full transcript represented by this excerpt.
