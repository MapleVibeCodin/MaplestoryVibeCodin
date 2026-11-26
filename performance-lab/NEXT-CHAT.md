# FM Rush Performance Lab — next-chat checkpoint
Date: 2026-11-26. Continue the existing GitHub + Windows PowerShell workflow. Do not suggest Work or Codex. Read AGENTS.md for original project constraints; this file supersedes its lab status only.

## Exact state
- Production main and historical/pre-optimized backups have not been modified by lab work. Original production checkpoint 45e68cef9f1eb10c950bc811fec8f193ffeb62d2; do not conflate lab recorder 24.63.4-lab6 with production desktop 24.63.6/browser 24.56.1 or separate MetaScanner.
- Branch performance-lab/step-8-cleanup. Actual Windows-tested checkout 5e394e92c56cd046bfbfcb9f1ae9d2bbe0e2f3a3. Documentation-only checkpoint 99246e1a8869334fba3ad51a11e9424290e55d43. Local isolated checkout: $env:LOCALAPPDATA\FM_Rush_Lab_20261126_154536. Do not overwrite installed scanner or change main. No confirmed live launch yet.
- Step 1 legacy dashboard, Step 2 unlocked segments, Step 3 purchase pairing fail-closed (no qualified receipt detector), Step 4 gate-based transition estimates (no verified channel identity), Step 5 integrity and bounded export, Step 6 batching/rotation and overhead benchmark, Step 7 historical replay, Step 8 Windows qualification tooling and cleanup.
- Windows tests on fcc23d02c441541f026e447a7fe0b6a9de563a60: 170/170, 64/64 recorder, 7/7 calibration. Two obsolete test expectations corrected, no runtime changes at that point. Synthetic paired recorder benchmark 3,042/3,042 events, zero drops, worst p95 enqueue about 0.024 ms in first run, no live CPU/capture claim. See detailed reports rather than extrapolate.
- Historical replay on Windows: user supplied FM_Rush_Lab7_Replay.json; 57 archive members verified, 42 PNGs decoded, 116 unique older Git PNGs recovered/hash checked/decoded_unscored, ten videos 5,777 decoded frames and 199 sampled outcomes reproduced. 47 geometry positives, 140 room positives, no exact gate positives in compressed videos. Five legacy JSONL logs 2,914 events, 35/37 closed segments included (2,909 events), no invalid lines/duplicates. Legacy sequence completeness unverified. PNG prior comparison not supplied in Windows run. All 116 older images decoded, NOT 116 item OCR matches. Separate prior offline replay also included later 04-39-52 video. No new full replay after cleanup patch; recognition logic unchanged by inspection.
- Windows OCR cleanup: source fixed owned subprocess terminate/wait/kill fallback, pipe closure, reader join, stale-worker isolation, terminal shutdown and tracker worker join. Actual Windows command with tracemalloc and ResourceWarning enabled at 5e394e9: 174 tests in 13.788s, OK, no warnings reported. This is suite evidence, not proof of all real WinRT lifecycles.
- All raw private screenshots, recordings and logs remain private; do not push raw media/logs to GitHub. No full verbatim chat transcript or permanent memory write verified. Current notes preserve substantive decisions/results, not every message.

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
