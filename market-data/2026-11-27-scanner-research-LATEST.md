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

## Latest frozen holdout — 21:03 Taipei
[404 observation test](2026-11-27-404-holdout.md). Seven original exports, latest2456 raw/404 new/261 consolidated. Reproduced prior49-event reconstruction scores exactly. New 2s CC net -24.801s, 11 gains>=1s vs25 losses, conditional floor190/261 vs242/261. No confidence threshold positive. Original logistic weights unavailable; reconstructed model not deployable. Prior [81-event code](models/2026-11-27-positioning-frozen-reconstruction.cjs) and [results](results/2026-11-27-positioning-frozen-81-holdout.json) preserved. Next cutoff21:02:59.731. No runtime changes.

## Decision-focused methodology reset — 21:19 Taipei
[Research and executed test](2026-11-27-decision-focused-methodology-reset.md). Latest2558 raw,1237 evening consolidated,86 new consolidated. Continuous-state simulator supersedes independent interval-reset proxy; train/validation/test chronological, 225 candidate policies. Best validation policy abstains; retrospective test net0s, no speculative switches. No validated predictive advantage. True alert timing, eligibility and movement measurements missing; no runtime edits. Code/results saved; next cutoff21:19:37.057.

## Method 1/5 — marked point process
[Executed comparison](2026-11-27-method01-marked-point-process.md), 106 policies, selected validation +2s, retrospective test -3.31s, 7 speculative switches, 0 gains>=1s/3 losses. Not deployable; next Hawkes, then renewal, HSMM, decision-focused ensemble. Freeze identical splits and costs; fresh prospective final validation needed. No runtime edits.

## Method 2/5 — exponential Hawkes
[Method 2 test](2026-11-27-method02-hawkes.md). 25 fits,106 policies, best validation/test 0s (abstention), best active validation1 switch net0; test none. Fitted self20s cross1s, not scanner movement proof. Method1 -3.31s test. Same simulator baseline reproduced exactly. Next renewal, then HSMM and ensemble. No deployment.

## Method 3/5 — renewal and recurrence modulation
[Method3 test](2026-11-27-method03-renewal.md). Four variants,141 policies, no validation proactive switches, selected net0s validation/test. 720–960s pooled hazard 2.91x480–720s;54/125 long observed episode gaps within120s of multiples855s; not verified scanner cycles. Best recurrence60s test logloss3.3122 but net0. Next HSMM and ensemble; no deployment.

## Method 4/5 — phase-expanded HSMM
[Method4 test](2026-11-27-method04-hsmm.md). 12 fits,106 policies, validation+3.076s/3 speculative switches/2 gains>=1s/0 losses; test0s/no speculative switches. Best nominal855s; model-implied5.44 active channels, not verified workers. Conditional floor slightly worse than fixed2. Next decision-focused ensemble, fresh prospective validation required. No runtime edits.

## Shop density correction — before Method 5
[User prior and executed HSMM challenger](2026-11-27-shop-density-prior.md). Shop population varies by channel/room; row hierarchy1–6 >7–12 >13–16 >17–20, lower channels generally more populated. Exact counts unknown. Four variants/141 policies: uniform wins selection, mild/proxy tie +3.076s validation, strong+.579; all test0s. Strong prior reduces conditional floor distance79→70/86 on reused test, exploratory only. Preserve separate visit and emission models. Carry soft density prior into Method5; no live changes.

## Method 5/5 — decision-focused ensemble completed
[Final five-method comparison](2026-11-27-method05-ensemble.md). 95 mixtures/3326 policies, selected original uniform HSMM validation+3.076s/test0; best genuine blend25% Hawkes+75% mild density HSMM +2.257/0; equal four-way0/0. None of five selected methods positive on common test. Freeze contenders; next new prospective data after21:19:37.057. No runtime edits.

## Frozen prospective evaluation protocol
[Three-contender protocol](2026-11-27-frozen-prospective-protocol.md). Original HSMM, density+historical-alert HSMM, and75% mild HSMM/25% Hawkes frozen. Evaluator and regression saved; old86-event baseline and all three results reproduced; empty/synthetic extension/prefix rejection checks passed. Await new real cumulative export after21:19:37.057; no tuning on new data. No runtime edits.

## Frozen three-contender holdout — 288 new records
[Deep dive](2026-11-27-frozen-holdout-288-deep-dive.md). Ninth original2846,232 consolidated new; all frozen policies net0s, baseline479.91s, A/B1 speculative switch each C0. Fixed 2–3s lead top1 A27/B19/C26 vs persistence29/232. Conditional floor B157 vs fixed178/232. 22m17s capture gap; 3 new strong route episodes, median compatible step7.10s, one CH38 recurrence near8*855. No confirmed scanner count or proactive advantage. No tuning/runtime changes. Next cutoff22:12:57.929.

## Final finite-data analysis — all nine exports
[Final positioning report](2026-11-27-final-full-history-positioning-analysis.md). Union9218 filenames/7296 consolidated across12 dates; all intermediate exports covered. No more data requests. Reactive chase plus fixed FM7–12 (approx FM9–10) best robust combined strategy; Nov27 either correct channel or within1 row1414/1639, latest211/232 conditional on position retention. 41 channel policies,68 spatial,122 standby. Standby-only recent15 margin.25 improves over fixed channel147 vs49/1639, latest20 vs9/232; 226/45 changes, not proven while pursuing selected deals. No proactive improvement under chase-all. No live deployment.

## Extended frozen holdout — 582 new screenshots
[Past-hour deep dive](2026-11-27-hour-live-tracking-holdout.md). 296 new consolidated, shared CH12->19 FM5 prediction gives A+1.407/B+2/C+.407s, no tuning. One shared opportunity only. Hybrid40/296 fixed lead hits vs persistence29; original HSMM conditional floor170 vs267 fixed. Latest cutoff22:36:41.931. Large late batch, five new strong route episodes. No deployment.

## Zero-filter route analysis — 22:45 Taipei
[Broader-feed results](2026-11-27-zero-filter-route-analysis.md). 968 new filenames,401 consolidated after cutoff,257/342 route compatible, peak7 overlapping strong episodes (not proven worker count). Train dwell6.721s; dense test229 conditional route exact room126, row176, within1 214, distance71 vs205 fixed; channel top25/229 vs persistence21. Frozen models no additional savings. No runtime changes.

## Dense route replication — 22:55 Taipei
[Latest results](2026-11-27-zero-filter-next-holdout.md). 440 new/242 consolidated. Frozen6.721s conditional route exact117,near230,dist80 vs200 fixed. Recency36/242 vs persistence19. Older frozen policies net0. Peak7 overlaps again;57 candidate handoffs/56 pairs, strict7/7 with zero repeats. Exact worker count/channel assignment unverified. No runtime edits.

## Dense scanner track reconstruction
[Tracking analysis](2026-11-27-dense-scanner-tracking.md). 815 dense events,314 direct route transitions median7.006s, sum edge medians141.641s.35 wraps including16 FM2->1; no mandatory exit at FM2.44 strong envelopes peak7, min path cover7 for120s gaps,8 for90s; seven feasible fixed-group coloring but assignment unstable. Working7–8 conditional, no exact count or repeatable CC order. No runtime edits.

## Scanner count identifiability audit
[Exact-count audit](2026-11-27-scanner-count-identifiability.md). Dense815 marks, eight distinct channels within2s; min individual cover9 for CC2s/step2s, six excluding first2min. Seven concurrent envelopes/short compatible intervals remain feasible, exact physical count unidentifiable; timestamps are downloads, scanner CC speed unknown. No claim exact seven or nine; no runtime changes.


## Dense-feed holdout — 23:13 Taipei
Read [latest holdout report](2026-11-27-dense-holdout-2313.md). Thirteenth original verified SHA4c59dd31094b106798d51f8cca4086e3b9b21cf0,642 new/363 consolidated, total11850 filenames/8599 consolidated, latest23:13:51.174. Frozen6.721s route160/363 exact room,334 near row; recent15 channel39/363. Frozen channel-switch policies net0 new. Peak7 strong envelopes,80 total,7 feasible tracks with300s gaps, no exact count; 3 repeated broad channel links,0 strict repeats. Keep seven anonymous tracks with overflow and FM9–10 standby. No runtime edits or prior file deletions. Transcript partial, prior missing evidence remains.


## One-scanner rolling-hour trajectory
Read [one-scanner reconstruction](2026-11-27-one-scanner-hour-reconstruction.md). New retrospective synthetic one-worker model on exact rolling hour22:13:51.434–23:13:51.434, full timeline505 room intervals/25 CCs,151 supported/354 silent,160 matched marks of1299,15 distinct channels. 7s fixed room window,20-room full sweep, arbitrary entry phase,2–12s CC assumed. Primary CH11 FM6 at cutoff; equally supported alternative CH39 FM11 (objective difference .035 only). No exact physical worker recovered. No new data or change to frozen channel model. Complete room/minute CSV and reproducible model, alternate fits archived. Earlier sparse phase especially ambiguous. Next data cutoff unchanged23:13:51.174. Transcript partial; no historical deletions.


## Second scanner residual fit
[Two-scanner report](2026-11-27-two-scanner-residual-reconstruction.md): original scanner1 frozen; scanner2 273 raw/134 consolidated/131 supported,373 silent,504 rooms/25 CC,ends CH39 FM11. Combined584 unique raw/294 consolidated, no duplicate attribution and zero simultaneous same-channel occupancy. Alternate ends CH29 FM15 with130 supported. Sequential fit only; identities unverified, no new data or changed cutoff. Full minute/room/deal CSVs and model archived. No prior deletions.


## Third scanner residual fit
[Three-scanner report](2026-11-27-three-scanner-residual-reconstruction.md): scanner1 and scanner2 frozen; scanner3 240 raw/113 consolidated/110 supported,393 silent,503 rooms/25 CC,ends CH38 FM12. Combined824 unique raw/407 consolidated, no duplicate attribution or same-room overlap. Same-channel overlap33s/109s; forcing separation costs1 supported visit, retains end. Alternate ends CH29 FM8 with109 supported. Sequential fit only; identities unverified, no new data or changed cutoff. Full minute/room/deal CSVs and model archived. No prior deletions.


## Fourth scanner residual fit
[Four-scanner report](2026-11-27-four-scanner-residual-reconstruction.md): scanners1–3 frozen; scanner4 185 raw/101 consolidated/97 supported,406 silent,503 rooms/25 CC,ends CH29 FM15. Combined1009 unique raw/508 consolidated, no duplicate attribution. Same-channel overlap186s/265s/194s and same-room overlap20s with scanner2. Separate-channel constraint costs4 supported visits and ends CH24 FM17; alternative excluding CH29 ends CH24 FM17 with96 supported, objective gap .265. Sequential fit only; identities unverified, no new data or changed cutoff. Full minute/room/deal CSVs and model archived. No prior deletions.


## Fifth scanner residual fit
[Five-scanner report](2026-11-27-five-scanner-residual-reconstruction.md): scanners1–4 frozen; scanner5 161 raw/81 consolidated/79 supported,426 silent,505 rooms/26 CC,ends CH29 FM13. Combined1170 unique raw/589 consolidated, no duplicate attribution. Same-channel overlap0s/80s/0s/343s and same-room overlap44s with scanner2. Separate-channel variant same79 supported ends CH8 FM10; end-excluded variant same79 supported ends CH10 FM2, objective gap .070. Sequential fit only; identities unverified, no new data or changed cutoff. Full minute/room/deal CSVs and model archived. No prior deletions.


## Sixth scanner residual fit
[Six-scanner report](2026-11-27-six-scanner-residual-reconstruction.md): scanners1–5 frozen; scanner6 165 raw/75 consolidated/75 supported,430 silent,505 rooms/25 CC,ends CH10 FM2. Combined1335 unique raw/664 consolidated, no duplicate attribution. Same-channel overlap83s/29s/113s/287s/0s and same-room overlap17s with scanner3. Separate-channel variant73 supported ends CH10 FM2; end-excluded variant74 supported ends CH8 FM10. Sequential fit only; identities unverified, no new data or changed cutoff. Large JSON retrieval fallback: fetch_blob by verified SHA if fetch_file content empty; six-scanner JSON compact. Full minute/room/deal CSVs and model archived. No prior deletions.


## Remaining scanner reconstruction (7–12)
[Report](2026-11-27-remaining-scanners-reconstruction.md): primary tracks1–6 frozen; tracks7–12 add139/125/107/86/94/69 raw,72/62/55/44/39/34 anchors. Combined1955/2625 raw and970/1299 consolidated, no duplicate assignment. Track7/8/9 have5/4/3 sweeps with>=5 matched rooms,10–12 zero. Exploratory three shuffled controls each for7/9/10/12: actual70/54/43/34 vs controls50–53/44–45/37–42/29–34. Additional fit near chance at12; stop arbitrary fitting at12, no exact worker count. Full movement, deal, minute records and controls archived. No new data, same cutoff. Preserve all previous paths and assumptions.
