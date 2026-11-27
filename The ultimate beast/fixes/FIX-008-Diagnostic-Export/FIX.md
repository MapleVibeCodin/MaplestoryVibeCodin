# FIX-008-Diagnostic-Export: No matching build report; incorrect report filename

Status: **Fallback supplied; local verification pending**

Strict build filter rejected reports when Smooth Shortcuts metadata missing. Actual raw logs: performance/<session>.jsonl and rotated <session>.partNNNN.jsonl; report feedback/Trial-<session>.json. Source https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/456b90748e6440870b4f0ea9cbc475210c8b5c0e/The%20ultimate%20beast/beast_feedback.py, https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/a80a9ffbcc2a4a1616b5cfdc8c91b35c430df8fb/Scanner%20Nov%2020/performance_recorder.py. Reusable [Export-Diagnostics.ps1](Export-Diagnostics.ps1) selects latest session and pairs by ID, preserves original names, exports ZIP with version only if actual metadata is available; no invented build label. Regression: raw-only, report-only, rotated logs, missing metadata, newest session, empty directory; use existing logs without retesting. Export after normal close if practical. No live execution claimed.

Update this record with each recurrence, actual check results, and the new commit. Never overwrite historical evidence.


## Centered live evidence
2026-11-27 actual three uploaded ZIPs opened with CRC checks. Two earlier exports identical raw-only 1214 events; latest Centered archive contains matching session JSONL and report (1246 events, report raw_events equals JSONL, final health true, zero drops/invalid lines). Raw-only and paired export observed working for these samples; broader fallback cases not rerun.


## Spatial live trial evidence
Spatial archive contains valid raw-only JSONL, 4129 events, 1090.1382s, no numbered sequence gaps/duplicates, max recorded dropped=0, no final health marker and no report. Spatial build confirmed by 42 action metadata events; raw fallback worked, session final completeness not established. No retest required for analysis.
