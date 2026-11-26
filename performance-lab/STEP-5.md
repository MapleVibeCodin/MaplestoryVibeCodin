# Performance Lab — Step 5: data integrity and failure handling

Base: Step 4 head a9dc7a4d72f00494d6432b41eb12ab32f96e3e30. Recorder tag 24.63.4-lab5; isolated branch only. No production files, calibrations, raw logs, or prior branches modified.

## Changes
- Assign monotonically increasing per-session enqueue sequence numbers, including events rejected when the bounded queue is full. No producer disk I/O or queue-space waits; a short shared lock serializes sequence assignment.
- Writer emits health records at startup, about every five seconds, and after a normal drain. Final counters reconcile accepted writes and dropped events. Normal shutdown flushes and fsyncs; a crash or incomplete shutdown can leave final health absent. Writer exceptions disable further recording rather than deliberately stopping the scanner. A failed writer is not automatically restarted.
- Bounded-line JSONL reading rejects malformed shapes, duplicate JSON keys, invalid encodings, nonfinite numbers, invalid timing fields and invalid purchase evidence. Detect exact duplicate events, conflicting sequences, missing sequences, mixed versions and missing or inconsistent final counters. Original logs remain read-only.
- Conservative exclusion policy: malformed files taint their identified sessions, and sequence/dropped-event conflicts quarantine entire affected sessions. Only closed, structurally valid segments from non-quarantined sessions enter metric calculations; open/invalid segments counted separately. Legitimate late callbacks may conservatively exclude a segment. Legacy logs have no sequence coverage; active or interrupted sessions may have unknown trailing loss. No cryptographic authenticity or complete coverage is implied.
- Export adds integrity summary, current queue depth, recorder status, and metrics_by_recorder_version; combined metrics withheld when several versions contribute. Reports written to a temporary sibling, flushed and atomically replaced; .jsonl destination rejected.
- Standalone transition dashboard displays exclusions, duplicates, partial tails, quarantines and session quality, including when no metrics are eligible. Existing Space dashboard not modified (Page connector unavailable).

## Verification performed
- 16/16 Python copied-helper tests using temporary files: normal finalization, duplicates, conflict, gap, trailing drop, malformed valid JSON, partial tail, bad encoding/nonfinite, invalid metrics, open segment, legacy, unrelated good session, orphan purchase, failed writer attribution, atomic replacement, and raw log protection. Original fixture bytes verified unchanged.
- 1/1 isolated copied enqueue-method harness: queue-full sequence gap and stopped writer rejection.
- 7/7 JavaScript integrity reducer checks. Dashboard browser rendering not executed.
- 17 additional repository unit tests staged; full repository suite, live Windows integration, actual disk failure, full threaded writer shutdown, capture overhead, historical archive replay and real report import not run in this session.
- Source readback: recorder 54bb0a303556da4b9cafe617c3cf3d45ede33295; tests 14f750c38217d1fcf2d580ce6c6bd06628136135; dashboard eb2e23ec18d8768f4735e2c855fc6f3d5726d26a.

## Remaining gates
Step 6: quantify producer contention and sampling/IO overhead in recorder off/on cohorts; add rotation/retention and bounded aggregate-memory policy before long-running deployment. Step 7: full historical regression. Step 8: live Windows qualification. Step 3 receipt and Step 4 actual destination channel detection remain unqualified. Do not install or merge this lab branch as a production release until qualified.
