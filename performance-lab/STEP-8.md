# Performance Lab — Step 8: qualification tooling

Base: Step 7 head 0e21415fe094b93d7ca90577efd38f9fc39e8fb6. Isolated branch only. No scanner installation, game launch, input automation, calibration changes, or raw media uploads.

## Implemented
- qualify_offline.py checks the pinned Step 7 ancestry and tracked checkout cleanliness; runs exact recorder/calibration tests, test discovery, the actual synthetic recorder benchmark, and optionally the recovered private archive plus historical Git PNG replay. Writes separate results outside the checkout and preserves output after each completed check. Refuses to present partial archive results as full coverage: checks the expected ten clips, 199 sample outcomes, 42 PNGs, 57 verified members, 35 eligible closed segments and 2909 events. Historical Git decode gate requires all 116 unique blobs. It does not claim item OCR accuracy, even if all gates pass.
- windows_qualification.html reads six local Measure-FMRushOverhead.ps1 JSON reports. Requires three adjacent matched off/on pairs, both orderings, same process identity and lifetime, consistent logical processor counts, comparable duration, and non-overlapping sample windows (2 s tolerance). Reports CPU normalized across all logical processors, peak sampled working/private memory and available I/O transfer deltas. Proposed CPU threshold is <=1 percentage point in every pair. Missing I/O remains null. It never sets live qualification or release approval to true: mode and workload are operator-labeled, not independently verified, and game/capture/OCR evidence is missing.
- Executed 14/14 synthetic JavaScript evaluator checks: valid data, no release approval, missing I/O, CPU threshold failure, wrong process, CPU normalization, duplicate timestamp, overlap, unequal duration, same mode, unsupported report, insufficient reports, invalid memory and unbalanced order. Source readback verified. No exact Python qualification script execution, Windows PowerShell execution, actual live process sampling or browser rendering test in this turn.

## Run offline on Windows (no production changes)
Use a new checkout, not the installed FM Rush directory. Git access to the repository and a compatible Python environment are required. Full replay needs the original local private ZIP, optional additional MP4/prior replay summary, OpenCV, NumPy and Pillow. Full test discovery may need Windows-specific dependencies. Keep results outside the checkout.

```powershell
$Lab = Join-Path $env:LOCALAPPDATA ("FM_Rush_PerformanceLab_" + [Guid]::NewGuid().ToString("N"))
git clone --branch performance-lab/step-8-qualification --single-branch https://github.com/MapleVibeCodin/MaplestoryVibeCodin.git $Lab
if ($LASTEXITCODE -ne 0) { throw "Lab checkout failed; installed scanner unchanged." }
py -3 "$Lab\performance-lab\qualify_offline.py" --output-dir "$env:LOCALAPPDATA\FM_Rush\performance-lab\qualification"
```

Without --archive the replay is explicitly not run and the runner exits nonzero (2) for incomplete qualification. For full private replay, append --archive "<local complete checkpoint ZIP>" --historical-git-pngs and optionally --extra-video "<04-39-52 MP4>" --prior-summary "<replay_summary.json>". Do not upload raw private media to GitHub.

## Live qualification still required
After offline gates pass and the candidate has an independently qualified Windows deployment, use the existing read-only process monitor with the same scanner PID, build and normal manual workload. Explicitly pause/resume recorder between 120-second measurements. Recommended order: OFF, ON, ON, OFF, OFF, ON. Load six resulting JSON files into windows_qualification.html. Compare live capture/recognition latency, verify no dropped events or recorder errors, and gather 30–50 normal workflow observations. Qualification does not certify actual purchase outcomes or destination channel identity until independent visible-UI evidence is validated. Do not merge, install, or declare a release approved solely on this tool's CPU result.

## Status
Step 7 fresh replay evidence preserved; old 116-image full decode/replay and actual Windows tests still outstanding. Step 8 tooling implemented, qualification not yet executed. Space connector unavailable; no Page update. Production main and pre-optimized remain unchanged.
