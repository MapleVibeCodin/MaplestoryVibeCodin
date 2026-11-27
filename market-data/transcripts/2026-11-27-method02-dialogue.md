# Method 2 — accessible dialogue

User verbatim: lets do method 2

Assistant commentary verbatim:
I’ll fit a Hawkes process to the archived observations and compare its time-saving performance against Method 1 using the same splits and two-second channel-change assumption.

Assistant authored response excerpt (verbatim prose; interactive chart, cards, and final receipt not included; not a complete transcript):

## Method 2 of 5 — Hawkes process

A Hawkes process estimates how much an observed event temporarily increases the probability of subsequent events. It is particularly useful for clustered arrivals. <Cite refs={["turn371847search0","turn371847search1"]}/>

For HeneFM, I am testing two distinct signals:

- **Same-channel excitation:** Does an announcement indicate that more deals are about to appear in that channel?
- **Cross-channel excitation:** Does activity in one channel indicate an imminent burst elsewhere?

Unlike Method 1's empirical time bins, this model estimates how rapidly these signals decay using maximum-likelihood fitting.

## Hawkes model results

I fitted 25 combinations of same-channel and cross-channel decay rates, then evaluated 106 positioning policies using the same dataset, chronological splits and movement simulator as Method 1.

The best policy chose not to switch proactively. Even the best policy that attempted predictive switching during validation produced no net time savings.

## What Hawkes discovered

The best-fitting statistical model identified two very different timescales.

| Fitted characteristic | Result |
|---|---:|
| Same-channel decay time | 20 seconds |
| Same-channel influence half-life | 13.86 seconds |
| Cross-channel decay time | 1 second |
| Cross-channel influence half-life | 0.69 seconds |

**Important discovery:** Cross-channel activity decays too quickly to provide much practical warning when changing channels takes approximately two seconds. Same-channel clustering lasts considerably longer, but that signal generally favors remaining where you already are.

Download batching could also contribute to the apparent clustering. These fitted timescales do not establish the scanners' actual movement patterns.

Numerical outputs and implementation are archived separately in ../2026-11-27-method02-hawkes.md and ../results/2026-11-27-method02-hawkes.json.
