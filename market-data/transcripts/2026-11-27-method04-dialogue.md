# Method 4 — accessible dialogue excerpt

Verbatim authored prose; interactive cards, diagram, table markup and final receipt excluded. Not a complete verbatim transcript.

## User

okay now do method 4

## Assistant commentary

I’ll test a hidden semi-Markov model with explicit scanner-visit durations and uncertain room positions, using the same dataset and movement-cost benchmark as Methods 1–3.

## Assistant

# Method 4 of 5 — Hidden semi-Markov model (HSMM)

This method is more directly aligned with our scanner-movement hypothesis. Instead of treating every announcement as an isolated event, it estimates an underlying scanner state that we cannot observe directly.

The crucial difference is that the model can update its estimated scanner position even when no new deals appear. It will also allow variable dwell times and interrupted visits rather than assuming a perfectly fixed schedule.

## Method 4 results — 12 model configurations, 106 positioning policies

This is our strongest validation result so far, although it did not produce a positive time saving on the test batch.

## What the model discovered

| Parameter | Best-fitting configuration |
|---|---:|
| Nominal scanner recurrence | 855 seconds |
| Assumed mean room dwell | 7 seconds |
| Estimated simultaneous active channels | 5.44 |
| Exact next-channel forecast accuracy | 8.43% |
| Accuracy with at least 2s warning | 9.06% |

The model favored the 855-second recurrence assumption over the 600- and 1,200-second alternatives tested. The estimated 5.44 active channels is a model-derived average, **not confirmation that HeneFM operates five or six scanners**.

The seven-second room dwell was fixed from previous research rather than independently estimated in this experiment.

## FM room positioning

Even assuming the correct channel is known, Method 4 did not improve the waiting position.

| Waiting strategy | Average distance from target floor |
|---|---:|
| Fixed middle floor | 0.895 floors |
| HSMM positioning | 0.919 floors |

The scanner-state model is not yet reliable enough to improve physical positioning either.

## Overall comparison

**Method 4 is worth retaining for the ensemble**, particularly because it had the highest next-channel accuracy among the selected models and the largest validation time savings. Method 3 still has better conditional probability calibration as measured by log loss.

Neither has demonstrated a positive net time advantage on the common test set.

## Archive index (editorial)
Full outputs: ../results/2026-11-27-method04-hsmm.json; methodology: ../2026-11-27-method04-hsmm.md. Log loss measures overall probabilistic prediction quality, not calibration alone.
