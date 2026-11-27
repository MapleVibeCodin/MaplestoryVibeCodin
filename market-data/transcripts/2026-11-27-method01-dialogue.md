# Method 1 — accessible dialogue

Verbatim authored text through the pre-verification response. Citation rendering and final receipt are not captured.

## User

use all of those methologies. lets do one at a time to find which is best

## Assistant commentary

I’ll start with a marked temporal point process, then test Hawkes, renewal and hidden semi-Markov models individually. Each will use the same chronological splits and movement-cost benchmark, so we can compare them fairly.

## Assistant

## Method 1 of 5 — Marked temporal point process

This is where I would start because it models **when the next deal may appear and which channel it may appear in jointly**, rather than predicting a channel without considering the available travel time. <Cite refs={["turn420883search1","turn420883search22"]}/>

We will compare the methods in this order:

| # | Method | Primary purpose |
|---:|---|---|
| 1 | Marked temporal point process | Joint channel and event-time prediction |
| 2 | Hawkes process | Predict clustered announcements |
| 3 | Renewal process | Predict recurring channel visits |
| 4 | Hidden semi-Markov model | Infer scanner movement and interruptions |
| 5 | Decision-focused ensemble | Combine useful signals to maximize seconds saved |

Each method must beat the same reactive baseline. A model that saves zero seconds by doing nothing is not considered a winner.

## Method 1 results

<card gap={3}>
  <caption>106 positioning policies tested · 2-second channel change</caption>
  <grid columns={2}>
    <grid-item>
      <caption>Validation — 261 events</caption>
      <title size="2xl" color="success">+2.00 s</title>
    </grid-item>
    <grid-item>
      <caption>Test — 86 events</caption>
      <title size="2xl" color="danger">−3.31 s</title>
    </grid-item>
    <grid-item>
      <caption>Test gains ≥1s</caption>
      <title size="xl">0</title>
    </grid-item>
    <grid-item>
      <caption>Test losses ≥1s</caption>
      <title size="xl">3</title>
    </grid-item>
  </grid>
</card>

The statistical prediction itself improved over a fixed historical channel-frequency baseline:

| Metric | Frequency baseline | Marked point process |
|---|---:|---:|
| Next-channel accuracy at sampled test times | 0.6% | 6.4% |
| Channel prediction log loss (lower is better) | 3.700 | 3.577 |
| Net simulated seconds saved | — | −3.31 s |

The new model predicted the probability of an event occurring in each of the 40 channels, accounting for the probability of an alert interrupting an unfinished channel change. It selected only seven speculative switches in the test period.

**Verdict: not good enough for deployment.** Better probability estimates did not translate into faster arrival.
