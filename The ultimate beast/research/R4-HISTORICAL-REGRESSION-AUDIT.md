# The ultimate beast R4 — historical regression audit
2026-11-27. User: "go through all the previous issues and mistakes, make sure this version doesnt have it". Reviewed main AGENTS.md historical notes (v24.53 through 24.63.6), hybrid NEXT-CHAT, plan/README, complete replay report, actual pinned FM Rush, game_window, shop_inventory, henefm_bridge and route_logic, plus exact R3 package and current Beast source. Scope is accessible recorded history, not all inaccessible chats or Windows execution.

## Executed results
R3 42/42 offline tests (29 original Sprint, 8 focus release, 5 feedback). R4 55/55 offline tests (same 42 + 13 integrated method/launcher/feedback checks); final repository-style command from Beast root: python -m unittest discover -s research -p "test_*.py" -v, 0.136s, OK. Tests extract actual nested App methods using AST and mocked platform interfaces, not actual live Windows. All four runtime Python files compiled. Archive CRC and six runtime blob hashes verified; unchanged recognition core, no rerun of 3261 frame recognition benchmark. Prior 174-test Windows lab suite not rerun or counted as R4 evidence. PowerShell execution not available on this Linux host.

## Confirmed integration repairs
- Pending automatic park and inherited manual shortcut generation invalidated on explicit unlock, skip, new target, context change, F12 or close; manual pointer shortcut blocked for stopped run. Full context now includes listing ID, seller metadata (no seller OCR), shop position, item, buy price, CH/FM, window and client geometry. Recheck before deferred move and focused click, cancel on sold, target mismatch or archive lock contention. Focus release from R3 retained, max 75ms, manual click after fallback, no clipping override or additional mouse retry loop. Browser-thread timing races and real cursor behavior still require Windows validation.
- Launcher checks critical import module origins and local bridge port 18773 before GUI; warns/fails if port occupied instead of pretending live feed works. One-shot probe does not guarantee later bind against concurrent process. Compile preflight before launching; existing pinned checkout reused when verified, no overwrite. R4 title identifies build.
- Existing recorder summary now counts pointer handoffs, successes, reason and timing; no new screen sampler, screenshot worker, OCR, continuous polling or online requests.

## Historical issue matrix and release boundaries
| Issue | Current result |
|---|---|
| Focused cursor lock | R3 focus-release retained, 8 helper tests + new integration checks passed; physical movement unverified |
| Rapid unlock/relock, skip, F12, wrong listing target | R4 guards and integrated simulated tests passed |
| Repeated F9 clicks, release/retry, unsupported resolution, stale/sold candidate | Original lifecycle and fresh-inventory synthetic tests pass; actual click registration and live UI still pending |
| Excess movement text / standalone map | R2 status-text removal retained, map auto-open suppression retained; optional F8 and graphical minimap remain |
| Wrong shop position / FM15-16 / camera alignment | Pinned base geometry unchanged; automatic early parking still estimates projection and may miss; no independently verified live coordinates |
| Missed shop highlight, fixed geometry, stale row, duplicate/truncated names | Pinned source has exact/geometry gates, name-only advisory path, duplicate and freshness checks. Live highlight correctness not proven. Historical cold video results 35/54 names, not 100% |
| Tooltip and faded sold rows | Strict scroll path retains guards; current fast non-scroll name path excludes blocked/sold rows rather than using earlier tooltip-prefix/sold contrast recovery. Known limitation: can miss otherwise readable targets. No risky recognition change shipped without independent replay |
| OCR speed, unnecessary full OCR / seller OCR | RuneCache and compact name OCR unchanged; price excluded from signature, seller name not OCR'd; tested cache reuse. OCR-derived visual identities can preserve spelling errors, no independently qualified icon-only engine |
| Exact HeneFM price / rounded hover price | Pinned parser supports Buy exact marker; browser extension must actually provide exact unit prices, installed browser extension not verified or changed |
| HeneFM refresh / 429 | No refresh logic or requests added by Beast; external extension behavior not verified |
| Auto-lock and click-only export | Pinned archive/bridge retained; actual browser/Windows integration pending |
| Extra screenshots, heavy telemetry | Automatic game screenshot worker intentionally disabled for one-hour trial; queue recorder only; 500-event test plus failure/shutdown tests pass; no measured CPU impact on user's PC |
| Channel-change black screen delay, first visible frame | Prior video timing is recognition-only; no server delay reduction or first-correct-highlight guarantee |
| Starting position/channel and G HUB macro registration | Existing CH20 default/route assumption retained (START.ps1 -StartChannel for other channels); no claim actual avatar/channel or G HUB configuration verified |
| 100% accuracy / hybrid merge | Not achieved; hybrid research preserved separately, Rune R3 still advisory trial default, no autonomous buy |
| Bad launch/update / lost historical files | Runtime compile, source-origin and port guards; separate ZIP; historical versions untouched, Windows setup not exercised |

## Mandatory future release procedure
From Beast root run all 55 current tests (do not reduce count without reason), compile runtime, compare all packaged blob hashes with GitHub, preserve history, repeat source audit for touched dependencies, and qualify live Windows cases before saying fixed in game. Keep FOCUS-REGRESSION.md active. No auto screenshots/OCR for feedback, no new refresh or auto purchase. Do not repeat historical replay unless recognition changes. Known unresolved recognition/geometry issues need independent held-out validation, not cosmetic changes. User should use R4 as one-hour diagnostic trial, send JSON and note wrong/missed highlights; no claim of production qualification.

## Runtime manifest
The_ultimate_beast_Trial_R4.zip: 17186 bytes, SHA256 8c0b8f4cefd80126066481c8995979d10f2fa0138da63cd2d422ec5448ca3334.
START.bat cea1ec0fb7078fbcd434da25f15b3cf518d44c67
START.ps1 e91edbf9ad7ca9641a9840d9f3ffab1e0e6a0863
run_beast.py f7792dbd363935c0a58f6b68219e535a8e962b92
beast_feedback.py 20836c408da762676405f5e80dbc4740d80d5c0e
fm_sprint.py 2538f4e02304241adfbdd5e81d14889d5d48ed9d
fm_sprint_core.py d8f6e0ff4071b36db9ea84ad266a79c44eb141af
Runtime commits 0f64143, 7f87b47, 8630bf6, 963c329. Research test commits c45c7c6, 65fe5e2, 998f546; prior b515131. All fetched back with matching local blob SHA. R1-R3 and original engines retained.