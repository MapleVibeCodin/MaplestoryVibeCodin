# Color vision failure modes and safeguards

Baseline c862d15d562a3222a696a3363fc64ca710116b9e. v24.63.1 desktop; browser v24.56.0 unchanged.

Research references:
- https://programmador.com/blog/2025/colorbot/ — color drift, shared-color false positives.
- https://docs.waspscripts.com/ocr.html — visually identical glyphs.
- https://github.com/ollydev/SimpleOCR — pixel font recognition.
- https://github.com/ra1nty/DXcam/blob/main/CHANGELOG.md — black-frame/rotation and frame timestamps.
- https://github.com/itechify/minerva/blob/main/crates/minerva-core/src/player_shop.rs — covered rows, geometry, physical price-width safeguards.

Implemented original code: strict grouped/ungrouped ASCII price grammar (no silent malformed comma repair), freshness expiry, immediate invalidation on failed crop, generation-aware renewal on unchanged fresh crop, amber/orange-only partial changed-frame retention for one exact non-scroll candidate, strict scroll full recheck, exception recovery, fail-closed updater. Five pure guard unittest methods run locally; four tracker integration checks staged but not executed here. All original regression fixtures preserved. No claim of full video replay with new version, native WinRT OCR, measured live latency, or 100% accuracy.

Remaining: validate entire Windows suite and live timing, independently label archive, compare geometric detector in shadow mode, glyph collision handling, price width checks, version-separated terminal-event telemetry, shared-frame capture. Existing gate remains deliberately unchanged until false-positive and native capture tests establish a better replacement.
