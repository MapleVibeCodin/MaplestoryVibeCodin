# Scanner research checkpoint — 2026-11-27

## Current user-defined goals (supersedes speculative deal forecasting)
1. Establish exactly how many independent HeneFM scanners exist, if available evidence permits.
2. Establish their actual movement pattern: room order, direction, channel assignments, transition delays, and repeat-cycle duration.

Retain all historical observations. Do not discard prior batches or restrict extraction to a recent window. When overlapping exports contain identical screenshot identifiers, count the observation once for statistical analysis while retaining original evidence. The user explicitly said "no exclude. the goal is to find out 1. exactly how many scanners there are. 2. the pattern."

## Current evidence and limitations
- Latest previously analyzed export: 741 unique screenshot identifiers, 389 channel-room combinations, all 40 channels, local filename times 19:36:18.097–19:55:27.883 (+08:00 assumed from export header). These are export/delivery timestamps, not verified server visit timestamps.
- Four historical Flips snapshots indicate concurrent observation streams and approximately seven-second adjacent-room intervals, with ascending and descending sequences. Six distinct channels observed within 4.5 seconds in one snapshot is conditional evidence, not a verified physical scanner count.
- Working hypothesis of 4–6 scanners remains unverified. Exact count cannot be established without sufficient independently timed observations or authorized source data distinguishing workers; batching and missing observations may confound inference.
- The earlier locked deal-location baseline scored 0/100 exact ordered room pairs in historical holdout and 0/41 in partial live test. Preserve the test, but it is no longer the primary research goal. Do not claim exact movement routes or generate speculative forecasts as a substitute for evidence.

## Full-history manual export command (Windows PowerShell)
```powershell
& { "EXPORT TIME: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff zzz')"; Get-ChildItem "$HOME\Downloads" -Recurse -File -Filter "*.png" | Where-Object { $_.Name -match 'CH\d+-FM\d+' } | Sort-Object Name | Select-Object -ExpandProperty Name | Out-String -Width 4096 | Set-Clipboard }
```
No time limit. User pastes export in chat. Preserve raw files locally; archive derived metrics and methodology rather than raw premium listing/seller records.

## Evidence index
- [Concurrency and observed movement hypothesis](2026-11-27-scanner-concurrency-hypothesis.md)
- [Expanded filename timing audit](2026-11-27-download-filename-timing-followup.md)
- [Initial filename timing audit](2026-11-27-download-filename-timing.md)
- [Coverage comparison](2026-11-27-coverage-two-snapshot-comparison.md)
- [Clock alignment](2026-11-27-coverage-clock-alignment.md)
- [Coverage cadence](2026-11-27-coverage-cadence.md)
- [Coverage cadence follow-up](2026-11-27-coverage-cadence-followup.md)
- [Locked prediction](2026-11-27-prediction-baseline-locked.md)
- [Partial live test](2026-11-27-live-forecast-test-01-partial.md)

No scanner runtime changes. No historical files deleted. Next step: analyze the next complete manual export with all prior observations, separating source observation timing from local exporter timing. Report evidence and uncertainty; exact worker count and route are not yet verified.
