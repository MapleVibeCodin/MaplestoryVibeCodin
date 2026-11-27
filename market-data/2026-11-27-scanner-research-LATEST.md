# Scanner research checkpoint — 2026-11-27

## Word-for-word dialogue archive

Read the [user-supplied verbatim conversation](transcripts/2026-11-27-scanner-count-movement-verbatim.md), verified exact readback at commit `6a6407f42f3e8bdf008d59dacbbfb78ded02390d`. Historical three-hour export and exclusion plan were explicitly superseded by the full-history export and scanner-count/movement objectives below. Always archive accessible dialogue word for word alongside separate research summaries. No new scanner evidence or raw screenshot files added.

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

## Latest full-history audit — 20:10 Taipei
Read [full historical export audit](2026-11-27-full-history-export-audit.md), verified at commit e4ff1e1fbe7889e152967eaecc04ca93ed9b2679. 7970 files,7535 IDs,786/800 room pairs,40 channels, Nov14–27; 208 additional evening observations beyond prior741. Variable-length hex parser corrected, zero unmatched. 24 channels in4.475s download window establishes local batching confound; within-channel adjacent-room proportions 92/202 at5.5–8.5s and78/175 at8.5–12s support broad cadence only. Exact worker count/route unverified; 4–6 remains working hypothesis. Locked forecast completed0/100 exact ordered pair. No new forecast. Next evidence needed: time-anchored displayed Seen ages and room observations including no-deal rooms, or authorized anonymous worker event records. Retain full history; raw names/listing data not public. Research only, no runtime tests or changes.

## Discovered room route and best-fit scanner count — latest
[Held-out assumption tests](2026-11-27-room-route-assumption-tests.md), verified at 0900bae35be8bb12ffce166c53bb8526b311e3b0. User now explicitly wants best predictive guess, not absolute certainty. Learned from Nov14–24 by max-weight one-to-one room transitions, independently yielded complete 20-room loop: 1→7→17→18→19→20→16→15→14→13→8→9→10→11→12→6→5→4→3→2→1. Holdout Nov26–27 65/113 exact next-room within5.5–12s, vs snake51/113, descending30/113, ascending19/113. Recent7s timed model late Nov27 102/189 exact,140/189 within one route step, conditional on observed elapsed gap. 5 overlapping coherent runs at19:43:58.030 across CH2/5/18/21/39, strict thresholds yield3–4. Best estimate5 physical scanners, plausible4–6; no verified channel assignment or cycle boundary. Model not verified as actual server route/live tracker. Full prior evidence preserved; no runtime changes.

## Recent-only frozen model validation — latest
[New screenshot test](2026-11-27-recent-only-route-validation.md), verified at e114656d5e1bdd3c42062c07a361a820d442ce5f. User now requests only Nov26–27 evidence for current fitting/testing. 1697 filenames/IDs, 99 after prior cutoff20:04:41.078, new cutoff20:15:34.707 Taipei. Frozen 20-room route/7s timed model on33 eligible new changed-room same-channel transitions 4–90s: exact9/33, within1 21/33, within2 25/33. All99 incl excluded exact37/99. Recent pre-cutoff fit independently selects7s, exact186/413. Alternative routes weaker on new holdout (snake7/33, descending4/33, ascending3/33). Post-hoc 6.25s challenger exact13/33, within1 22/33, within2 25/33; lock both7 and6.25 for next unseen batch strictly after20:15:34.707, do not call 6.25 independently validated. Recent-only route reconstruction agrees18/20 edges, FM20 unresolved; preserve 20-room model. No verified live position or new bot-count evidence. No raw records or runtime changes.
