# Beast Fix Registry — permanent first read

One canonical folder per known problem. Read this index and the matching FIX.md before investigating or changing anything. Update the existing issue rather than solving it from scratch. New defects receive new IDs. Each record states the symptom, cause/evidence, fix or open status, source and regression requirements. Source-verified is not live-verified. Never mark an open issue solved without evidence. Preserve all previous commits. No private raw logs in GitHub.

| ID / problem | Status |
|---|---|
| [FIX-001-Focused-Mouse-Lock — Mouse cannot move while game has focus](FIX-001-Focused-Mouse-Lock/FIX.md) | Implemented; live pending |
| [FIX-002-Cursor-Jitter — Mouse flies across screen; unwanted shop clearing](FIX-002-Cursor-Jitter/FIX.md) | Source correction; live pending |
| [FIX-003-Logitech-Shortcuts — Shop/channel commands stopped working after jitter fix](FIX-003-Logitech-Shortcuts/FIX.md) | Source correction; live pending |
| [FIX-004-Macro-Timing — Macro clicks before pointer arrives](FIX-004-Macro-Timing/FIX.md) | Diagnostics added; timing open |
| [FIX-005-Missing-Highlight — Shop item fails to highlight or name mismatches](FIX-005-Missing-Highlight/FIX.md) | Open |
| [FIX-006-SoftLock-Stale-Target — Click next listing without manual unlock; stale pointer work](FIX-006-SoftLock-Stale-Target/FIX.md) | Implemented; live pending |
| [FIX-007-Launch-Download — Missing ZIP, wrong install, or unverified launch](FIX-007-Launch-Download/FIX.md) | Delivery workaround; live pending |
| [FIX-008-Diagnostic-Export — No matching build report; incorrect report filename](FIX-008-Diagnostic-Export/FIX.md) | Fallback supplied; local verification pending |
| [FIX-009-History-Continuity — Repeated work, lost context or overwritten history](FIX-009-History-Continuity/FIX.md) | Policy implemented |
| [FIX-010-Historical-Scanner-Regressions — Earlier geometry, scroll, sold-row, price, camera and update defects](FIX-010-Historical-Scanner-Regressions/FIX.md) | Camera oscillation mitigation; gate and live accuracy open |
| [FIX-011-Popup-Placement — Top-center route popup](FIX-011-Popup-Placement/FIX.md) | Source corrected; live pending |

Active runtime: 2a6a083553dcdd4f0e1f9e95729a2c87c7bff052 (Smooth Shortcuts Stable). Historical and current evidence: [continuation](../../fm-sprint/NEXT-CHAT.md). Mandatory first-read policy: [AGENTS.md](../../AGENTS.md). Local mirror: Desktop/Beast-Fixes, versioned snapshots, no scanner changes. For every later iteration, sync the latest registry and record actual test results. If a test fails, record it and do not claim release qualification.
