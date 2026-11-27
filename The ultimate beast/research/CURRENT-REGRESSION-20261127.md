# Exact full historical regression — 2026-11-27

Target runtime 4c938a5816bf87542603840587e33d69b1c9ba76. Isolated Windows GitHub Actions QA run [45968901695](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/actions/runs/45968901695), job 140404195833, workflow e07f5bb08c17eede412eb84412a7561ac8c8c621. Local checkout unavailable (DNS resolution failed); actual hosted Windows offline execution used instead, no game/browser login or live mouse input.

| Suite | Observed |
|---|---|
| Original Beast research discovery | 60 executed, 4 failures, 6 errors (including SoftLock setUpClass failure; ten SoftLock methods not reached) |
| Current Exact test_spatial.py | 9/9 passed |
| Popup placement | Passed (see job logs) |
| Original pinned scanner discovery | 190 executed, 7 failures, 183 passes |
| Full run | FAILED |

Beast historical test errors: mock AST base omits spatial mixin methods beast_cancel_audit/beast_reject, plus pinned archive hash mismatch on Windows. Old tests assert obsolete FINAL title, disabled screenshot recorder, old four-source compile fixture and UTF-8-dependent status text. These must be requalified with current contract, not treated as runtime failures or silently counted as passes. Original pinned scanner failures: six tracker fixture failures (partial tooltip, seller-free scan, exact/geometry/lost/switch geometry) and old cached-anchor capture fixture. Pinned source was not changed by Exact. Earlier name-only/partial/sold advisory expectations conflict with explicit exact active name AND price requirement; current integration must preserve valid positives and reject uncertain candidates. Actual native screenshot and private recording replay not yet performed; archive ground truth unavailable.

Next: run original checks as recorded, retain original source/test history, update current-contract fixtures separately, exercise actual Exact _scan with positive and negative scenarios, verify results. No production release qualification.

## Requalified full execution
Final isolated Windows run [45969348478](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/actions/runs/45969348478), job 140405663970, QA workflow commit 0e93a88df1b92d1ab82e024faa3f6ae0092ffad8, checkout 3ca447ed5c10b86b245f3f60c6bd6d7097134805. Logs verified: 82/82 current-contract Beast research tests (70 historical plus 12 new actual Exact _scan mocked-capture integration tests), 9/9 current spatial/exact guard tests, 1/1 centered popup, 190/190 pinned historical tests with current-contract fixture adapters. **282/282**, all four suite exit codes zero; 3.017s summed test execution. Archived test files retained unchanged. The original run still stands as 4 failures/6 errors in Beast research and 7 pinned failures; the new adapters use actual spatial audit methods in historical mocks, UTF-8, normalize CRLF only with preserved blob hash check, update deliberate build/screenshot policy and complete runtime-file list, adapt old inventory mocks to actual Exact scan, reject occluded candidates, and use full observation capture fixture. No runtime source edits. Tested positive exact correct second-row match, wrong name/price, missing or rounded target price, duplicate, independent OCR disagreement, changed price pixels, sold/blocked rows, geometry fallback positive, strict scroll rejection, lost geometry and seller-free OCR. Native recordings unavailable from current upload/library search, screenshot/real OCR replay and live Windows game remain unverified. Do not count media integrity as accuracy.
