# Methodology reset: decision-focused predictive positioning (2026-11-27)

User: remember the goal. now fix your methology and look at your thought process, and compare on the internet best approach for this statistical model.

Goal: be on EXACT channel before the next desirable deal appears, physically near the correct FM room when possible, maximize seconds saved relative to reactive positioning, including failed predictions and unnecessary channel changes. Never substitute room prediction accuracy for primary objective.

## Evidence and corrections
Eighth immutable export: raw/2026-11-27/Pasted text(20261127-131959).txt, 2558 unique observations, 102 new, last 21:19:37.057 Taipei, blob 68f456d30f5887421107fda32ffe29ad09ab5aca. Evening 1909 raw, 1237 consolidated (same channel-room less than 2 seconds apart). Latest 86 consolidated. Earlier interval-reset simulator omitted overlapping moves, and timestamps are screenshot-download proxies rather than actual alerts. No verified complete feed, actual deal eligibility labels, or walking-time measurements. Missing capture intervals may be misread as zero activity. Do not infer exact worker identities or true channel visit times.

## Literature reviewed
- Shchur et al., Neural Temporal Point Processes: A Review, IJCAI 2021 https://ijcai.org/proceedings/2021/623 — event time and mark jointly via conditional intensity.
- Elmachtoub & Grigas, Smart Predict, then Optimize, Management Science 2022 https://doi.org/10.1287/mnsc.2020.3922 — decision loss instead of prediction loss.
- Hyndman & Athanasopoulos, Forecasting: Principles and Practice, time series cross-validation https://otexts.com/fpptr/tscv.html — forward chronological evaluation.
- Renewal and hidden semi-Markov models are plausible hypotheses for scanner phase, not established scanner behavior. Hawkes models can model clustering but download bursts and censoring may create artificial self-excitation.

## Executed experiment
Code: models/2026-11-27-continuous-positioning-hazard.cjs
Results: results/2026-11-27-continuous-positioning-hazard.json
Discrete-time empirical pooled age/episode-recurrence bin forecast (855s recurrence assumption; smoothing 120 pseudo-exposures, frequency scaling); not fitted full Hawkes/HSMM or calibrated next-event probabilities. Expected counts in 0–2 and 2–12s windows. Per-second decisions use strictly prior event data. 225 candidate policies (224 parameter combinations plus stay-reactive). Train to 20:35:05.774, select on 261 consolidated validation events through 21:02:59.731, test retrospectively on 86 through 21:19:37.057. Noncancelable assumed 2s CC, persistent state within each block, latest reactive target queued, earliest possible arrival if alert prioritized measured at event arrival. No walking, human reaction, competing buyers or measured latency. Sum of per-event counterfactual delays is not elapsed play time. Initial state reset at block boundaries only. Objective is still proxy. Candidate policy heuristic scores later expected counts minus risk-weighted immediate counts; not exact expected decision loss.
Validation best net 0s (560.443s baseline and policy, 17 early hits each, no speculative switches). Test 196.878s both, 1 early hit each, no speculative switches. No positive validation advantage; do not deploy speculative switching. Test previously inspected in old method, not fresh prospective test; no statistical confidence claimed. Code and results verified exact readback.

## Next methodology
Log true alert-observed timestamp (separate from screenshot timestamp), eligibility/filters, channel and FM, feed coverage/heartbeat, actual position and change start/end and room arrival. Fit a marked competing-risk intensity model on eligible alerts with an explicit missing observation mechanism; only add semi-Markov phase or Hawkes excitation if they improve chronological out-of-sample scoring. Evaluate calibrated next-event probabilities and true decision regret using persistent-state replay, with risk/latency cost, no-switch option, room travel-time matrix and actual timely reach. Freeze policy before new data, rolling origins and block-level uncertainty, report net seconds and count of gains/losses >=1s. No runtime changes. Preserve originals, previous results and failures. Full historical ten-check continuity audit remains incomplete. Prior full transcript unavailable; this is a methodological checkpoint, not a complete verbatim transcript.
