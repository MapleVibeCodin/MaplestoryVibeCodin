# FIX-004-Macro-Timing: Macro clicks before pointer arrives

Status: **Open**

Existing 5 ms G HUB sequences: first Num+ nominally 20 ms after J/C key down; second 30 ms shop or 40 ms channel. Live 32 successful movements: median 43.1 ms, max 62.2 ms, 31/32 exceeded 20 ms. 89 requests, 19 explicit failures, 38 no terminal result. Physical key delivery not recorded. Do not claim compatibility, change G HUB blindly, or automate clicking as a workaround. Regression: compare actual explicit movement completion with actual key timing; log terminal outcomes and reject stale intent. Current code not a verified timing fix. Evidence: diagnostic checkpoint b531ba456321aa5416de9d5a55fa33db677e9f33; exact macro timing in [continuation](../../../fm-sprint/NEXT-CHAT.md).

Update this record with each recurrence, actual check results, and the new commit. Never overwrite historical evidence.
