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

## Second live validation — latest
[Second validation](2026-11-27-second-live-route-validation.md), commit 2dfa92fdef7328a1569ce34adef564c2480eed79. 57 new IDs,27 eligible transitions, frozen7s exact15/27 vs6.25s10/27, both within1 22/27 and within2 23/27. Retain7s primary,6.25s challenger; next cutoff20:17:39.613 Taipei. Conditional next-room forecasts archived. No global channel-switch prediction or verified worker count. Recent Nov26–27 only, no runtime change.

## Third live validation — latest
[Third validation](2026-11-27-third-live-route-validation.md), commit 3f18f4fc187e7fa4a410f9ec3878e83abb478981. 30 new IDs,13 eligible transitions,7s exact6/13 vs6.25s4/13. Explicit prior forward predictions: 0/5 next changed observed room,1/5 within three predicted rooms; CH40 no observation. Do not conflate conditional timed accuracy with forward predictions. Latest cutoff20:19:28.203 Taipei. No runtime changes or new fit.

## Interruptible cycle tests — latest
[Full cycle and rolling model audit](2026-11-27-interruptible-cycle-backtest.md), commit 5388cd1848da462ceda8a6a2ff4903b1978eed19. User reports random scanner can be dispatched by users to scan arbitrary full channel. Fixed 640 schedules failed; explicit retest 706 consolidated evening observations,128 held out. Rolling model best held-out active candidate set8 with40% unexplained mixture; not eight physical workers or measured dispatch rate. Prospective exact1/128; conditional exact3/128. 33 coherent runs max5 simultaneous, sensitivity3–6. Five physical workers remains tentative; dedicated vs diverted scanner unresolved. No further data requested; no runtime change.

## Requested scan episode analysis — latest
[Episode recurrence audit](2026-11-27-requested-scan-episode-analysis.md), commit 71b9e52ba31d422772ffc77ad8fe36b930d496ff. Confirmed UI queued full-channel call, CH1 first in line screenshot after latest existing export; no labeled dispatch response. 706 consolidated evening events, 33 strong episodes on25 channels, six episode envelopes overlap (not six physical workers), threshold sensitivity4–6. Eight repeated strong episode intervals favor exploratory870s period, shuffled p=.033 before selection correction. Held-out broad episode recurrence model modest conditional likelihood gains but poor top5; strong episodes fail uniform log score. No verified worker count, request attribution or global forecast. No new data requested, no runtime changes.

## Controlled CH1 scan — latest
[CH1 experiment](2026-11-27-ch1-requested-scan-experiment.md), commit a57324bfa14b1d56b1bd1cf7c8ddfddd18c338c6. 1971 IDs,187 new; CH1 FM1 20:25:24.142→FM18 20:25:44.873 (20.731s,3 steps implied6.91s)→FM12 20:28:56.999 (late by115.126s vs fixed route). Approximate request20:25:25, completion20:29 minute precision. Three observed rooms only, attribution not certain; full uninterrupted route not confirmed. Other-channel activity continued. 20:24 onward44 eligible consolidated changed transitions,7s exact22,within1 38,within2 42;6.25s exact23,within1 36,within2 41. CH21 and CH18 nonnumeric sequences reinforce route. No runtime changes or verified worker count.

## Full recent reanalysis after CH1 — latest
[Reanalysis and held-out tests](2026-11-27-full-recent-reanalysis-after-ch1.md), commit bbc732d10ff553eb942121d63edd81bca2e498fe. Nov26–27 1971 IDs,1419 consolidated,841 evening. New93 eligible transitions7s exact45,within1 78,within2 87; short-gap22/27 exact successor. 42 strong visits,15 revisit intervals; pre-fitted855s recurrence top5 6/9 new episode channels conditional on onset; combined840s exploratory permutation p=.00333 (episode rule selection uncorrected). Weak FM12/20; effective18-position8s challenger 52/88 common-subset vs original43/88, not proof rooms skipped. Seven-worker point guess conditional on 14min full-sweep interpretation; count unverified, six overlap envelopes. Freeze next cutoff20:29:52.486, original7s and855s recurrence, retain challenger separately. No runtime edits.

## Objective corrected: next deal channel
[Advance channel prediction tests](2026-11-27-next-deal-channel-objective.md), commit 995f6e28fab97128d898aad81a385ef956eafb2e. Primary objective be on correct channel before announcement; prioritize top1 at practical lead time. Raw next event 58/187 exact equals persistence; consolidated next event17/135; 5s16/131,10s21/131,15s21/131,30s14/128; 10/15s persistence19/131. No reliable high-accuracy advance channel predictor yet; no further room speed tuning as primary goal. Filename timestamps proxy, no profit labels. No runtime changes.

## Exact channel, approximate FM positioning — latest objective
[Positioning test](2026-11-27-exact-channel-approximate-position.md), commit 8a0abb11d717455705c06e9d3ad32be79e1309dd. User requires exact channel; approximate FM physical location reduces travel versus central waiting. Conditional known-channel floor model on135 held-out observations mean distance.541 floors vs better fixed middle.844 (36% reduction), exact floor74/135, within1 123/135. No horizontal geometry/travel time measurement; separate channel prediction remains weak. Primary success exact channel before alert, secondary physical travel time. No runtime change.

## Next-chat checkpoint — latest
[Authoritative handoff](2026-11-27-next-chat-handoff.md), [byte-exact original exports](raw/2026-11-27/README.md), [dialogue part 1](transcripts/2026-11-27-scanner-validation-accessible-dialogue-part-1.md), [dialogue part 2](transcripts/2026-11-27-scanner-validation-accessible-dialogue-part-2.md). Six exports verified against original git hashes; latest2052 records/81 unscored. Primary metric exact channel before alert and net time saved. Screenshot binary and complete dialogue not archived; no runtime modifications. Preserve all prior findings and files.
