# FIX-004-Macro-Timing: Macro clicks before pointer arrives

Status: **Open**

Existing 5 ms G HUB sequences: first Num+ nominally 20 ms after J/C key down; second 30 ms shop or 40 ms channel. Live 32 successful movements: median 43.1 ms, max 62.2 ms, 31/32 exceeded 20 ms. 89 requests, 19 explicit failures, 38 no terminal result. Physical key delivery not recorded. Do not claim compatibility, change G HUB blindly, or automate clicking as a workaround. Regression: compare actual explicit movement completion with actual key timing; log terminal outcomes and reject stale intent. Current code not a verified timing fix. Evidence: diagnostic checkpoint b531ba456321aa5416de9d5a55fa33db677e9f33; exact macro timing in [continuation](../../../fm-sprint/NEXT-CHAT.md).

Update this record with each recurrence, actual check results, and the new commit. Never overwrite historical evidence.


## Centered live evidence
2026-11-27 Centered trial: 49 shop requests, 8 success events, one focus_not_released, 40 missing terminal events. Successful median 42.45ms (28.9–52.7ms); all 8 exceeded configured 20ms first-click delay. Actual click timing remains unobserved. No timing fix delivered; status open.


## Spatial iteration — partial mitigation, open
Runtime 4b1635d4b85dfc183fc6f0ac2f3d2e61380a436c. Explicit pointer controller retained; each observed locked handler invocation adds correlated request/outcome, including unavailable preview, duplicate, superseded, window/focus/error/cancellation and success; old event protocol preserved. Readiness message on completed move advises verifying sign before clicking; report summarizes unmatched IDs and movement durations. No G HUB modification or actual click observation, no guaranteed macro timing fix. Provisional first-click delay 100ms after J/M/C down if user elects to adjust, or manual click after visible pointer arrival; evaluate real delivery separately. Pre-dispatch expired events remain legacy telemetry. No full live test.
