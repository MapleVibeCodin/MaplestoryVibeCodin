# Windows qualification checkpoint — 2026-11-26

User-supplied PowerShell report, candidate fcc23d02c441541f026e447a7fe0b6a9de563a60, Windows 11 build 26200, Python 3.14.7. Report UTC 07:49:10.

- Recorder: 64/64 passed.
- Calibration: 7/7 passed.
- Full scanner discovery: 170/170 passed (includes the preceding suites).
- Synthetic recorder benchmark: passed, three paired 10-second runs at 100 Hz. All 3,042 accepted events written, zero drops. Worst paired on-mode enqueue p95 0.0233 ms; median added observe p95 0.0188 ms; median CPU overhead 1.09479 percentage points of one logical core, not total system CPU. Separate traced Python peak delta 7,900 bytes. CPU pair variability remains; live capture and full process CPU unmeasured.
- Two previous failures resolved by test-only fixture corrections. Runtime unchanged.
- Full discovery emitted ResourceWarning for a still-running subprocess and an unclosed text file; test suite passed, but cleanup requires investigation.
- Historical replay not run: archive absent from selected local directory. Private archive gate and 116-image historical Git decode gate remain pending on Windows. Earlier offline archive results remain documented separately.
- Live Windows qualification and release approval false. No production installation or raw log upload.

Next: run historical replay alone on the existing corrected checkout to avoid repeating successful benchmarks; verify pinned historical Git object, original archive availability and Python media dependencies. Then investigate cleanup warnings and qualify live passive observation.
