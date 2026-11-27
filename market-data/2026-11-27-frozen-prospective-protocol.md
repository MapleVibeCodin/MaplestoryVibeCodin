# Frozen three-contender evaluation protocol

User verbatim: ok do that

Goal: be in the exact channel before the next desirable deal announcement; approximate FM position secondary. Measure net seconds saved, including penalties for interrupted and unnecessary channel changes.

Freeze before receiving the next export. Archived cutoff 2026-11-27 21:19:37.057 +08:00. Original 2558 records, blob 68f456d30f5887421107fda32ffe29ad09ab5aca. New observations after this cutoff constitute an unseen chronological holdout if not previously inspected; observations collected before this model freeze are not literally prospective live forecasts.

Fixed models:
A: original HSMM emission weights, nominal855s/7s dwell, margin .04s.
B: HSMM density rank plus historical alert proxy (variant3), margin .04s.
C: 75% mild-density HSMM variant1 plus25% best-training-fit Hawkes, margin0.
All cooldown0, assumed noncancelable2s channel change, same reactive baseline. No fitting on new records, threshold changes or new candidate selection. Deterministic reconstruction of earlier training fits from the fixed old prefix is permitted. Forecast model filters update causally with past observations. Same 2s room-event consolidation and one-second decision grid. Player initial channel reset at cutoff to last observed channel as in previous replay; cumulative per-alert simulated delays, not actual gameplay elapsed time. No FM walking-time data, true alert timestamp, actual deal eligibility or verified feed coverage.

Evaluator: models/2026-11-27-frozen-prospective-replay.cjs, commit c1e75dbe0db1c5ceb57f6d7efd508be993632556. Original input and component hashes pinned in CLI. New cumulative export must preserve all original record lines in order, reject duplicates, reject timestamps at/before cutoff or out-of-order append. Reports baseline and per-model net latency, early hits, switches, gains/losses >=1s, per-event delays and speculative action traces. No parameter search.
Regression results: results/2026-11-27-frozen-prospective-regression.json, commit 5bb3e1fa26bf6db02c9f738f1e2d2543c6cba444. Executed historical86-event replay reproduced baseline196.87800192832947s, all three net0, zero proactive switches, one early hit each. Empty input returns awaiting new records. Synthetic one-row append passed extension test (not market evidence); changed-prefix rejection passed. Exact readback of both files verified. No new real data supplied in this exchange, so no fresh holdout result yet.

Export command: preserve Nov26/27 full prefix, not a sliding date filter that drops archived records when day changes.
```powershell
& { $t = "EXPORT TIME: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff zzz')"; $f = Get-ChildItem "$HOME\Downloads" -Recurse -File -Filter "*.png" | Where-Object { $_.Name -match '^\d{4}-\d{2}-\d{2}_.*CH\d+-FM\d+' -and $_.Name.Substring(0,10) -ge '2026-11-26' } | Sort-Object Name | Select-Object -ExpandProperty Name; (@($t) + @($f)) -join "`r`n" | Set-Clipboard }
```
Paste output into chat. No runtime changes; no historical deletions. Complete dialogue archive and historical ten-check audit remain incomplete.
