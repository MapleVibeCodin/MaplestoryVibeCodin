# Method 3 — accessible dialogue excerpt

Verbatim user and assistant prose through pre-verification, excluding chart/card markup, rendered citations and final receipt. Not a complete transcript.

## User

no do 3

## Assistant commentary

I’ll test Method 3 now: a renewal model that estimates when each channel is due for its next visit, using the same movement-cost benchmark.

## Assistant

# Method 3 of 5 — Renewal process

Unlike Hawkes, which predicts bursts following recent activity, a renewal process estimates the probability of another event based on how long it has been since the previous event. <Cite refs={["turn373098search3","turn373098search4"]}/>

For our objective, this could be more useful because we want to identify a channel **before the scanner returns to it**, not after deals have started appearing.

I will test an ordinary renewal model against three recurrence-aware variants using our previously estimated 855-second cycle (14 minutes and 15 seconds). That cycle remains a hypothesis, not a confirmed scanner schedule.

## Results — 141 positioning policies tested

## What the renewal model discovered

There is evidence of renewed activity around **12–16 minutes** after the last observed event.

- The fitted event rate in the 720–960-second interval was approximately 2.9 times the rate in the preceding 480–720-second interval.
- Of 125 longer observed episode intervals, 54 (43.2%) fell within two minutes of a multiple of the hypothesized 855-second cycle.

However, this recurring activity is not sufficiently precise to justify switching to a specific channel in advance.

## Statistical comparison

| Renewal variant | Test prediction accuracy | Log loss ↓ |
|---|---:|---:|
| Ordinary renewal | 4.94% | 3.319 |
| Cycle-aware ±60s | 5.09% | **3.312** |
| Cycle-aware ±120s | 4.94% | 3.333 |
| Cycle-aware ±240s | 4.94% | 3.334 |

The ±60-second variant produced the best probability estimates of the renewal variants, but still delivered no time savings. These accuracy measurements use correlated one-second forecast samples, not independent deals.

## Archive index (editorial)
Full numerical results: ../results/2026-11-27-method03-renewal.json; methodology: ../2026-11-27-method03-renewal.md.
