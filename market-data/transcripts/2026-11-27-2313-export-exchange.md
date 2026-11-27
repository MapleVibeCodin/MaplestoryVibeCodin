# Accessible 23:13 export exchange (pre-verification)

Manual visible text archive; attachment bytes preserved separately; chart UI flattened/omitted, no platform-wide export. Final verification response is outside this pre-verification archive.

## User

great give me command

## Assistant

Keep HeneFM filters at **0,0,0,0**. Run this in PowerShell:

```powershell
& { $now = Get-Date; $from = $now.AddHours(-1).ToString('yyyy-MM-dd_HH-mm-ss-fff'); $t = "EXPORT TIME: $($now.ToString('yyyy-MM-dd HH:mm:ss.fff zzz'))"; $f = Get-ChildItem "$HOME\Downloads" -Recurse -File -Filter "*.png" | Where-Object { $_.Name -match '^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}-\d{3}_CH\d+-FM\d+' -and $_.Name.Substring(0,23) -ge $from } | Sort-Object Name | Select-Object -ExpandProperty Name; (@($t) + @($f)) -join "`r`n" | Set-Clipboard }
```

Paste here using **Ctrl+V**. I'll merge the new observations with our existing dataset, remove duplicate observations from the analysis, and continue tracking from **22:55:03.028**.

## User

[Attachment: Pasted text(20261127-151407).txt, exact original separately archived.]

## Assistant (commentary)

I’ll compare this export against the 22:55 cutoff, score the frozen model on the new observations, and check for repeated cross-channel transitions.

## Assistant (partial answer)

# Scanner tracking — 23:13 Taipei update

New screenshots
642

New consolidated observations
363

Total historical screenshots
11,850

Channels observed in new data
40/40

Latest observation: **23:13:51.174 Taipei time.** All 1,983 overlapping filenames have been excluded from new-observation scoring, without deleting any originals.

## 1. Scanner count

Seven overlapping scanning tracks have now been observed again, but the longer dataset introduces an important complication.

| Metric | Previous | Updated |
|---|---:|---:|
| Strong scanning episodes | 44 | 80 |
| Peak overlapping episodes | 7 | 7 |
| Median room interval | 7.006 s | 7.021 s |
| Estimated circular sweep | 141.64 s | 141.88 s |

The movement speed is remarkably consistent. However, linking episodes into individual scanner histories produces the following results:

[Chart: 60s 25,90s 17,120s 13,180s 9,300s 7.]

Maximum permitted unobserved gap between scanning episodes. These are conditional track counts, not physical scanner counts.

Seven tracks remain mathematically feasible, but only when allowing longer observation gaps. I am retaining seven as the initial tracking configuration with overflow, rather than treating it as a confirmed count.

## 2. Cross-channel assignments

We now have three repeated candidate channel transitions.

| Candidate transition | Observations |
|---|---:|
| CH14 → CH7 | 2 |
| CH16 → CH15 | 2 |
| CH11 → CH12 | 2 |

CH11 → CH12 is particularly worth tracking because both candidate transitions followed an observation in FM3.

However, none of the 11 strict cross-channel transition candidates repeated. Only 5 of 73 inferred worker links remained stable across at least 80% of assignment simulations.

**There still isn't enough evidence to assign permanent channel routes to individual scanners.**

## 3. Prediction accuracy on the new data

The model was tested without changing its parameters.

[Chart: exact room44.1% vs6.9%; exact row68.3% vs31.1%; within one row92.0% vs83.7%.]

These room forecasts assume the target channel is known. Average row distance decreased by **52.8%** compared with waiting at FM9.

For exact advance channel prediction:

| Model | Correct channel |
|---|---:|
| Recent activity, 15-second decay | 39/363 (10.7%) |
| Scanner route activity | 35/363 (9.6%) |
| Last observed channel | 27/363 (7.4%) |
| Historical channel frequency | 14/363 (3.9%) |

The three previously frozen channel-switching strategies produced **zero additional net seconds saved** on this batch. I would not deploy automatic speculative switching based on these results.
