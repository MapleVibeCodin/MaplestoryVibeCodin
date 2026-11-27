# FM Rush Performance Lab — next-chat checkpoint

## Latest checkpoint — Step 13 (2026-11-27)
- Read `performance-lab/STEP-13-RUNESCAPE-1000-IMAGE-SHADOW.md`. Replayed 1,000 new unique image hashes, zero Step 12 overlap, using RuneScape-inspired multi-point color/bitmap templates. 968 corrected shop-interval positives, 32 reviewed controls. Nine known templates; same-corpus tuning, no independent holdout.
- V2: all 1,000 shadow scans <=50ms, P95 0.4575ms, max 3.2847ms. Gate 958/968, 32/32 controls. Target 386/388 unique positives, 340/340 expected rejects, 272 unscored. Replay reproduced all decisions. Step 13 has not replaced production OCR, strict scroll recognition, capture or overlay; Windows live 50ms remains unverified.
- Shadow source: `performance-lab/research/step13_rs_shadow.py`. Private replay artifacts in chat; no raw media committed. Next: independently labeled held-out native shop images and real Windows capture-to-overlay qualification. Preserve all branches and backups.


## Latest checkpoint — Step 12 (2026-11-27)
- Branch: `performance-lab/step-11-50ms-target`; read `performance-lab/STEP-12-1000-REAL-FRAME-AUDIT.md` before making latency claims.
- Recovered private 42-PNG/10-video archive without user upload. Decoded 5,777 video frames, selected 1,000 real shop-preview frames (982 unique crop SHA-256 hashes, **not** 1,000 independent shops). Private media was not pushed to GitHub.
- Executed offline Linux image preparation only: P50 3.403ms, P95 4.822ms, P99 6.725ms, max 9.798ms, 1000/1000 under 50ms. **No WinRT OCR, correctness, screen capture, UI poll, overlay drawing, or Windows end-to-end 50ms proof.**
- Step 11 source fixes on this branch: correct doubled byte-escape literals, do not cache blank OCR reads, reject ambiguous ellipsized competing names, exclude sold rows from fast amber highlight; new targeted regression tests staged. Windows tests **not run**.
- Original main and historical backups untouched. Next: independent native-image accuracy labels and actual Windows P95 queue-to-overlay/shop-open-to-overlay; do not confuse offline prep timing with real scanning.

Date: 2026-11-26. Continue the existing GitHub + Windows PowerShell workflow. Do not suggest Work or Codex. Read AGENTS.md for original project constraints; this file supersedes its lab status only.

## Exact state
- Production main and historical/pre-optimized backups have not been modified by lab work. Original production checkpoint 45e68cef9f1eb10c950bc811fec8f193ffeb62d2; do not conflate lab recorder 24.63.4-lab6 with production desktop 24.63.6/browser 24.56.1 or separate MetaScanner.
- Branch performance-lab/step-8-cleanup. Actual Windows-tested checkout 5e394e92c56cd046bfbfcb9f1ae9d2bbe0e2f3a3. Documentation-only checkpoint 99246e1a8869334fba3ad51a11e9424290e55d43. Local isolated checkout: $env:LOCALAPPDATA\FM_Rush_Lab_20261126_154536. Do not overwrite installed scanner or change main. No confirmed live launch yet.
- Step 1 legacy dashboard, Step 2 unlocked segments, Step 3 purchase pairing fail-closed (no qualified receipt detector), Step 4 gate-based transition estimates (no verified channel identity), Step 5 integrity and bounded export, Step 6 batching/rotation and overhead benchmark, Step 7 historical replay, Step 8 Windows qualification tooling and cleanup.
- Windows tests on fcc23d02c441541f026e447a7fe0b6a9de563a60: 170/170, 64/64 recorder, 7/7 calibration. Two obsolete test expectations corrected, no runtime changes at that point. Synthetic paired recorder benchmark 3,042/3,042 events, zero drops, worst p95 enqueue about 0.024 ms in first run, no live CPU/capture claim. See detailed reports rather than extrapolate.
- Historical replay on Windows: user supplied FM_Rush_Lab7_Replay.json; 57 archive members verified, 42 PNGs decoded, 116 unique older Git PNGs recovered/hash checked/decoded_unscored, ten videos 5,777 decoded frames and 199 sampled outcomes reproduced. 47 geometry positives, 140 room positives, no exact gate positives in compressed videos. Five legacy JSONL logs 2,914 events, 35/37 closed segments included (2,909 events), no invalid lines/duplicates. Legacy sequence completeness unverified. PNG prior comparison not supplied in Windows run. All 116 older images decoded, NOT 116 item OCR matches. Separate prior offline replay also included later 04-39-52 video. No new full replay after cleanup patch; recognition logic unchanged by inspection.
- Windows OCR cleanup: source fixed owned subprocess terminate/wait/kill fallback, pipe closure, reader join, stale-worker isolation, terminal shutdown and tracker worker join. Actual Windows command with tracemalloc and ResourceWarning enabled at 5e394e9: 174 tests in 13.788s, OK, no warnings reported. This is suite evidence, not proof of all real WinRT lifecycles.
- All raw private screenshots, recordings and logs remain private; do not push raw media/logs to GitHub. No full verbatim chat transcript or permanent memory write verified. Current notes preserve substantive decisions/results, not every message.

## Current checkpoint — Step 11 (50ms item target)
- Branch: `performance-lab/step-11-50ms-target`; current candidate commit: `522d001a8b638a0cc0ccfa53463ae64cdee12134`.
- Step 11 changes: compact six-row name-only OCR (no seller, price or stats), background WinRT warmup, row text cache independent of price pixels, one-frame exact-name target, amber overlay, 5ms worker scan cadence and 10ms UI polling in confirmed FM room. Scroll targets retain legacy strict path.
- Telemetry exports shop gate, name OCR, queue-to-target, scan-start-to-target, target-to-overlay, scan-start-to-overlay and queue-to-overlay timings, plus p95. Acceptance target is P95 `shop_open_to_overlay_ms` ≤ 50ms; `queue_to_overlay_ms` ≤ 40ms reserves approximately 10ms for polling. **Not yet measured.** Cold OCR can still exceed 50ms.
- Historical screenshot geometry checked across 16 captures: name glyphs fit the 20px crop; seller, price and stats are excluded. Raw captures remain in Library/private archives.
- Diff from Step 10 touches only `fm_rush.py`, `shop_inventory.py`, `performance_recorder.py`, tests and lab documentation. No production branch, backup or calibration modified.

## Next — targeted Windows qualification
Close FM Rush normally and paste:

```powershell
$Lab = "$env:LOCALAPPDATA\FM_Rush_Lab_20261126_154536"
$Fast = "$env:LOCALAPPDATA\FM_Rush_50MS"

git -C $Lab fetch origin performance-lab/step-11-50ms-target
if ($LASTEXITCODE -ne 0) { throw "Fetch failed" }

git -C $Lab worktree add --detach $Fast 522d001a8b638a0cc0ccfa53463ae64cdee12134
if ($LASTEXITCODE -ne 0) { throw "Worktree failed" }

$Scanner = "$Fast\Scanner Nov 20"
py -3 -m py_compile "$Scanner\shop_inventory.py" "$Scanner\fm_rush.py" "$Scanner\performance_recorder.py"
if ($LASTEXITCODE -ne 0) { throw "Compile failed" }

Push-Location $Scanner
py -3 test_fast_target.py
if ($LASTEXITCODE -ne 0) { throw "Step 11 tests failed" }
py -3 test_item_first.py
if ($LASTEXITCODE -ne 0) { throw "Step 10 tests failed" }
py -3 test_speed_equivalence.py
if ($LASTEXITCODE -ne 0) { throw "Step 9 differential tests failed" }
py -3 test_inventory_hover.py
if ($LASTEXITCODE -ne 0) { throw "Inventory regression failed" }
py -3 test_performance_recorder.py
if ($LASTEXITCODE -ne 0) { throw "Telemetry regression failed" }
Pop-Location

Start-Process -FilePath py.exe -ArgumentList "-3", "`"$Scanner\fm_rush.py`"" -WorkingDirectory $Scanner
```

Live qualification: run about 30 shop openings, include never-seen names and cache hits, and export Tools → Export performance report. Inspect P50/P95/max for `shop_open_to_overlay_ms` and `queue_to_overlay_ms`, plus name OCR/cache timing. If cold OCR misses 50ms, next work is an OCR-verified glyph/template matcher—not fuzzy matching.

Do not repeat the 174-test Step 8 suite or historical media replay without a reason. No release, merge or production install authorized.

## Read first
- performance-lab/STEP-7.md
- performance-lab/STEP-8.md
- performance-lab/2026-11-26-windows-checkpoint.md
- performance-lab/2026-11-26-windows-historical-replay.md
- performance-lab/OCR-CLEANUP.md
- performance-lab/2026-11-26-cleanup-verified.md

## Next: live qualification
Do not rerun already-passed unit tests or historical replay without a reason. Close running original FM Rush normally to avoid contention on browser bridge port 18773. Launch the Windows-tested isolated checkout with PowerShell:

```powershell
$Lab = "$env:LOCALAPPDATA\FM_Rush_Lab_20261126_154536"
git -C $Lab rev-parse HEAD
Start-Process -FilePath "py.exe" -ArgumentList "-3", "`"$Lab\Scanner Nov 20\fm_rush.py`"" -WorkingDirectory "$Lab\Scanner Nov 20"
```

Confirm HEAD is the tested 5e394e9 (or a verified documentation-only descendant) and the actual app launches. Check lab config/calibrations before comparing; the checkout has its own config path but uses existing local archive directory. Do not assume identical settings. Use ordinary manual workflow, not automated clicks, purchases, memory reads or packet interception. Collect 30–50 normal listing attempts with channel changes, entrances, shop opening, recognition and failures. Export via Tools → Export performance report. Close normally before final export if necessary to finalize segments; active/interrupted and legacy segments have different coverage, and closing the app prevents using its export UI, so preserve raw logs and use an offline export if needed. Do not mix old and new recorder versions or treat missing purchase evidence as zero purchases.

For actual process overhead use existing performance-lab/Measure-FMRushOverhead.ps1 against actual scanner PID, not Python launcher PID, paired on/off same build/settings/workload, six measurements with both orders. Use UI pause/resume recorder; no automatic game input. Load results in performance-lab/windows_qualification.html. Distinguish observer timings, CPU whole-process measurements, actual capture/OCR, independent ground truth and purchase/channel qualification. Do not claim 100% accuracy or release approval without evidence. Current blockers: live process/capture/recognition performance, independent receipt/channel detection, independent item identity accuracy. No production install or merge authorized.

## Continuity
The Performance Lab Space tracker was last verified only through Step 3; Space connector was unavailable during subsequent work. GitHub branch is authoritative. Preserve all history, old archives and calibrations. User prefers direct actionable commands and verified results, not repetitive questions.
