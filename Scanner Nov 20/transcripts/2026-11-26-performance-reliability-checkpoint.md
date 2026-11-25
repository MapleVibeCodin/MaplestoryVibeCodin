# 2026-11-26 — FM Rush performance and reliability checkpoint

This is a project-state record, not a complete verbatim transcript. Quoted user messages below are the accessible exact project requests from this session; earlier messages, images and full assistant replies may be incomplete. No claim that all conversation history or new screenshots are archived. No private local records or unrelated personal data included.

## User messages (chronological, accessible excerpts)
- "okay lets do that" (approved pointer latency optimization)
- "now is there any way for you to do data collecting? like how to improve? because i dont feel like reocording every single purchase attempt (movement to portal, opening portal, seeing how long portal takes before black screen is gone, then changing channel, then finding and opening shop, and purchasing). im already doing that, how can you most easily and efficiently data collect to speed up"
- "ok lets do that" (approved passive performance recorder)
- "Great. Lets work on Henefm. These are the past 100 listings that are on the flips : 

Any way to improve visually or otherwise? i want things intuitive"
- "okay. I dont want the page to be delayed too much either, can you test how long this change takes from original page?"
- "ehh i dont like any of the new stuff get rid of"
- User reported updater failure: SyntaxError: unterminated string literal (detected at line 15); Python validation failed; no installed files changed.
- "any other way to improve specifically the logitec macros? currently its a pain and my mouse moves accidentally sometimes missing the shop or channel because when i spam click the left side buttons i move mouse too sometimes."
- "well i have 3 numpresses because sometimes it doesnt register, and then sometimes im not actually focused onto maplestory. any upgrades?"
- "ok then do that"
- "save everything to memory and github. also is it time to change to new chat or are we still ok"

## Verified repository state
- Runtime head 858c4b034ac6bd7387eea45569edcc2b4dc9bced, desktop v24.60.0; browser extension v24.56.0 (restored exactly).
- v24.57.0 priority hotkey FIFO and adaptive focus-release wait; one scene refresh, validated target snapshot; 5 ms polls, 75 ms focus cap, 150 ms expiry. Commit de99525cf19fc5f80f926854e16882c74bfd0efd; eight mocked pointer test cases added a05382887c93c6237574c753980282abc98c2b4b.
- v24.58.0 local passive recorder fc98d14983750b2a6cd63616e171e792e0da2d04; staged test gate 3d82f07928015c60eb2076e22c13b82f8b6432d7. Records scanner lock/scene/inventory/pointer and estimated black intervals. 3 patches of 16x16, up to 20 Hz, foreground only, no raw frames or uploads. Outcome unknown. No actual movement-key, exact portal activation, or purchase confirmation measurement. Tools > Export performance report; JSONL at %LOCALAPPDATA%/FM_Rush/performance. User wants to play normally rather than manually record videos.
- HeneFM Pro v24.59.0 37f81727fc07598c8393859716e260a770696c9b was explicitly rejected. Reverted by 625b3911e6f2bb28a19f6a1231e7f0580e9cf496. All original extension blobs restored; unused Pro source retained on GitHub, not loaded. Do not redesign/dim/group/reorder the browser page or reintroduce Pro unless requested. Prior reported fixture figures are not live HeneFM timings; actual end-to-end latency unverified.
- Syntax failure in deal_archive.py, line 15, repaired by 778e37b51b15cf782eabc48e7d16d6122a6ea6ce: close Seen-age regex, remove accidentally duplicated class text, retain updated semantic comparison and SQLite batch rollback. Added existing auto-lock tests to pre-install gate. Prior response reported local isolated compilation/checks; exact Windows install not confirmed.
- v24.60.0 7c74a1c17865b142a169e90249e988bf3113c271 plus warning fix 858c4b034ac6bd7387eea45569edcc2b4dc9bced. Coalesce only identical pending same-kind/target requests; distinct requests supersede; expired requests don't cancel valid pending request. Read-only 10ms/180ms post-placement watch measures return of game focus and cursor drift outside target rectangle. Stop on unlock, new request, geometry change or item marker. Drift warning stays visible after focus recovery. No extra click, keyboard injection, forced game focus, cursor confinement or repeated reposition. No guarantee of click success. Existing focus-loss workaround retained. Performance export includes counts and timing distributions. Eleven pointer, six recorder and four auto-lock test cases (21 total) staged; tests not executed by connector; local updater runs when venv Python exists.
- Keep pre-optimized c4f58d3eac23ad8b35c44d12866c56e800997ad3 and archive/historical-screenshots abac54c3d3a20f25c4b0bb416b81d983a67ddae5 intact; 127 image paths, 116 unique blobs per earlier verified tree. Full historical replay not yet complete; no new image archive claim.

## G HUB observed mappings and constraints
User supplied screenshots earlier in this session. Their prior inspection indicated: right button BUY ITEM, forward thumb TO SHOP, rear thumb INSTA CC, ordinary primary left and middle click. No Repeat macros. BUY ITEM: Num+ down, 5ms, up, Enter down, 5ms, up. TO SHOP: Ctrl+Alt+J chord then 3 Num+ presses, standard delays 5ms. INSTA CC: Ctrl+Alt+C chord then Num+, Esc, Num+, standard delays 5ms. Do not change three Num+ retries: user explicitly says first attempts sometimes don't register or game lacks focus. Num+ exact behavior depends on Windows Mouse Keys configuration; no live verification. No G HUB modifications performed. 100–200 DPI precision profile and custom inter-press delays were suggestions only, not adopted or tested. Physical thumb-button pressure can move mouse; current release detects drift, not prevents it. Keep manual input control. Analyze actual focus/displacement data before any further timing changes.

## Next action
Run latest staged updater, verify startup and actual local regression results. Play normally and export performance report after roughly 30–50 attempts (or earlier if error occurs). Analyze median/p90 latency, focus observations, drift and duplicate counts separately for shop vs channel. Distinguish visual estimates from server events. Never claim purchase success or all screenshot tests passed. Preserve existing route/calibrations, scanner overlay colors and original HeneFM layout. If user reports failures, inspect evidence and current source before changing code. Do not reintroduce rejected redesign or remove historical files. 
