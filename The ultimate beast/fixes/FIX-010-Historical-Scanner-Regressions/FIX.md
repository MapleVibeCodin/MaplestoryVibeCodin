# FIX-010: Earlier geometry, scroll, sold-row, price, camera and update defects

Status: **Historical evidence; requalify when changed**

Existing detailed root [AGENTS.md](../../../AGENTS.md) release chronology, [R4-HISTORICAL-REGRESSION-AUDIT.md](../../research/R4-HISTORICAL-REGRESSION-AUDIT.md), [FINAL-RELEASE-GATE.md](../../research/FINAL-RELEASE-GATE.md), and [continuation](../../../fm-sprint/NEXT-CHAT.md) are authoritative for earlier versions. Retain exact item/price/scroll safeguards, stale/tooltip/sold checks, room geometry, focus/identity checks, local-data protection. Do not assume historical FM Rush fixes all inherited into Beast; current name-only path has acknowledged limitations. On specific recurrence create a dedicated child issue or separate ID, link exact implementation and tests, do not repeat broad research. Prior test results are evidence only for their pinned builds.

Update this record with each recurrence, actual check results, and the new commit. Never overwrite historical evidence.


## Centered live evidence
2026-11-27 directional misses: user reports top/left/right shops missed. Centered FM12 had 18 shop pointer requests and zero recorded successful movement. Pinned base fm_rush.py lines 687–708 and 722–724 contain silent early returns/cancellation after request logging; shop_position.py lines 15–26, 71–124 uses grouped estimated camera anchors and removes entirely offscreen markers. Logs do not record actual pin coordinates or pixels, so exact offset/cause unverified. Future regression: reason for missing/clipped marker or cancellation, visual geometry verification before coordinate corrections. No runtime fix or new executable test.
