# FIX-010: Earlier geometry, scroll, sold-row, price, camera and update defects

Status: **Historical evidence; requalify when changed**

Existing detailed root [AGENTS.md](../../../AGENTS.md) release chronology, [R4-HISTORICAL-REGRESSION-AUDIT.md](../../research/R4-HISTORICAL-REGRESSION-AUDIT.md), [FINAL-RELEASE-GATE.md](../../research/FINAL-RELEASE-GATE.md), and [continuation](../../../fm-sprint/NEXT-CHAT.md) are authoritative for earlier versions. Retain exact item/price/scroll safeguards, stale/tooltip/sold checks, room geometry, focus/identity checks, local-data protection. Do not assume historical FM Rush fixes all inherited into Beast; current name-only path has acknowledged limitations. On specific recurrence create a dedicated child issue or separate ID, link exact implementation and tests, do not repeat broad research. Prior test results are evidence only for their pinned builds.

Update this record with each recurrence, actual check results, and the new commit. Never overwrite historical evidence.


## Centered live evidence
2026-11-27 directional misses: user reports top/left/right shops missed. Centered FM12 had 18 shop pointer requests and zero recorded successful movement. Pinned base fm_rush.py lines 687–708 and 722–724 contain silent early returns/cancellation after request logging; shop_position.py lines 15–26, 71–124 uses grouped estimated camera anchors and removes entirely offscreen markers. Logs do not record actual pin coordinates or pixels, so exact offset/cause unverified. Future regression: reason for missing/clipped marker or cancellation, visual geometry verification before coordinate corrections. No runtime fix or new executable test.


## Spatial implementation — source verified; live pending
Runtime 4b1635d4b85dfc183fc6f0ac2f3d2e61380a436c. New beast_spatial.py reuses pinned GrassCameraTracker (two-landmark consensus, 10Hz maximum, 200ms age, generation scoped to listing/room/CC profile; manual alignment takes precedence). Grass projection remains estimated, cave uses existing entry/CC estimates or explicit manual portal alignment. Offscreen/too-small sign gets passive direction guidance and no pointer preview; four edges/diagonal supported. Actual target/window/camera projection included in pointer snapshot, no extra input dispatch. Camera accuracy, cave room corrections, and live latency not qualified. Fourteen copied pure helper cases passed; six staged unittest methods including AST gate execute before launcher; full source test and Windows trial not run here.


## Spatial live trial evidence
Spatial live session 2026-11-27: 100 shop shortcut outcomes, 58 preview unavailable/title_unconfirmed, 5 projected offscreen (3 above, 2 right), 3 shop already detected, 25 moved, 6 expired, 2 superseded, 1 focus_not_released. 413 projection events: 217 landmark estimate, 196 CC-entry estimate. 172 adjacent same-attempt camera mode changes, largest observed absolute summed-axis shift 191px (2 X/189 Y), repeated [254,317] vs [252,128]. Mode flapping confirmed, true sign accuracy unknown. Room-title gate is largest recorded rejection, not proof every frame was actually a valid room. Pinned source requires narrow bounded title glyph match before projection/inventory, and resets inventory when unconfirmed. Next regression: validate room gate against native labeled entrance/room/transition/occluded samples; avoid switching from fresh landmark alignment to stale entry estimates within same view; preserve confidence and fail closed, no blind offsets or automatic input. No runtime changes.
