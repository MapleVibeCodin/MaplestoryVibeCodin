# Remaining scanner residual reconstruction (7–12)

User verbatim: do the rest

Same exact hour22:13:51.434–23:13:51.434 Taipei, cutoff latest observed23:13:51.174. No new observations. Primary tracks1–6 frozen. Original 2s CH/FM consolidation first; remove marks covered by prior room windows, match raw filenames to previously unused room windows only. Same nominal7s room window,20-room circular sweep,arbitrary phase at channel entry,2–12s CC,DP score1 per supported room minus .035 per second of CC beyond2s. Fit candidates7–12 sequentially; no joint optimization. Validate all six full-hour paths gap-free, all anchors matched exact original filenames, combined1955 unique raw and970 consolidated; no duplicate raw attribution. No count or physical identities established. 

| Track | Raw | Anchors | Supported rooms | Silent visits | CCs | End | Sweeps >=5 supported rooms |
|---|---:|---:|---:|---:|---:|---|---:|
| 7 | 139 | 72 | 70 | 436 | 26 | CH8 FM10 | 5 |
| 8 | 125 | 62 | 60 | 443 | 25 | CH20 FM7 | 4 |
| 9 | 107 | 55 | 54 | 450 | 25 | CH8 FM12 | 3 |
| 10 | 86 | 44 | 43 | 465 | 26 | CH24 FM17 | 0 |
| 11 | 94 | 39 | 39 | 468 | 26 | CH27 FM19 | 0 |
| 12 | 69 | 34 | 34 | 473 | 25 | CH10 FM2 | 0 |

Combined twelve tracks1955/2625 raw (74.48%),970/1299 consolidated (74.67%),670 raw/329 consolidated left. Nine-track prefix1706 raw (65.0%),853 consolidated (65.7%),919 raw/446 consolidated left. Strong sweep criterion >=5 matching room windows chosen descriptively, not pre-registered. No such sweeps in tracks10–12; fitting indefinitely would assign incidental matches. Stop at12 as a diagnostic, not claim twelve or nine actual scanners. Tracks7–9 are exploratory candidates, not verified identities.

## Negative controls
Track7: actual70 supported, shuffled 53/52/50; actual strong sweeps5, shuffled 1/0/0.
Track9: actual54 supported, shuffled 45/44/44; actual strong sweeps3, shuffled 0/0/0.
Track10: actual43 supported, shuffled 37/39/42; actual strong sweeps0, shuffled 0/0/0.
Track12: actual34 supported, shuffled 29/34/33; actual strong sweeps0, shuffled 0/0/0.
Three seeds711/722/733 per selected residual stage. Shuffle room labels within channel and 10-minute block after consolidation and previous-track exclusion, preserving exact times, channel activity and room frequencies. Same DP optimization. Residuals conditioned on earlier data-fitted tracks; small number of shuffles and retrospective model selection prevent formal p-value or count inference. Track7 and9 show residual route structure beyond these controls, 10 close,12 matched by shuffled control. Track8/11 not shuffled. Stop adding arbitrary paths; do not interpret remaining screenshots as necessarily distinct workers. Next step joint assignment and held-out time prediction, with alternative sweep durations/phase and actual scan-time evidence if available.

Source original model six-scanner residual, verified source blobs d0c127f02350b2da92d1dec69d5ba4ecd5a2a967, 44c62b08457cc81ed3662cdacc451f110ae55a7d, 4c59dd31094b106798d51f8cca4086e3b9b21cf0. Model assumptions unchanged, no historical tracks overwritten, no new runtime deployment. Full CSV has all exact deal filenames for tracks7–12 and 60 minute positions for all12; full result includes every room and switch and overlap. Same-room overlaps remain possible: track7 158 pairwise seconds; track8 95 pairwise seconds; track9 0 pairwise seconds; track10 203 pairwise seconds; track11 203 pairwise seconds; track12 114 pairwise seconds. These are hypotheses with unobserved endpoints except track10 matching CH24 FM17 window. No live current position claim. Earlier full verbatim platform transcript incomplete.
