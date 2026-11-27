# One-scanner reconstruction — 22:13:51.434–23:13:51.434 Taipei

User request verbatim: make yourself one of the bots. track your movement room by room channel by channel. remember some rooms may have noithing to scan. no people. tell me excat times you spent and where you are minute by minute. you should be able to tell me based on the scans the past hour

## Source and method
Exact latest rolling-hour original raw blob 4c59dd31094b106798d51f8cca4086e3b9b21cf0, 2625 screenshot filenames. Two-second consolidation by CH/FM against last retained mark yields1299 observations in exact hour. Model is new retrospective maximum-score single-worker reconstruction, not existing frozen predictor or actual worker identification. Existing circular route fixed; nominal room interval rounded to7s from previously estimated median7.021s. Force 20 rooms per sweep with arbitrary entry phase each channel; force different channel between sweeps, 2–12s modeled transition gap, allow partial first/last sweeps. These are assumptions, not observed scanner rules. Silent room visits retained regardless of matching deal alert. Objective counts one point per room window with at least one consolidated mark, penalizes excess CC gap by .035 per second above2s. No reward for multiple alerts in one room. Dynamic programming on one-second start grid, 40 channels,20 entry phases; exhaustive best path under these discretized assumptions. No new market data, no direct scan times, no live current position or physical scanner ID. Download timestamps may lag scanning.

## Results
505 room windows,151 with matching alerts,354 silent,160 matching consolidated marks of1299. 26 sweeps (24 complete,2 partial),25 CCs,15 distinct channels,3529s room windows,71s transitions, sum3600s. Timeline continuity validated:530 consecutive nonoverlapping room/CC intervals cover exact entire hour with no gaps or overlaps. Early segment before22:34 by visit start:20/170 supported; dense segment131/335. No alert cannot distinguish empty room, no profitable listing, already observed deal or delayed delivery. Times modeled, not exact measured dwell; timestamps with milliseconds inherited from export boundary, not millisecond precision.

Primary channel sequence: 5 -> 40 -> 2 -> 12 -> 33 -> 2 -> 40 -> 11 -> 18 -> 4 -> 5 -> 28 -> 40 -> 11 -> 5 -> 3 -> 25 -> 33 -> 17 -> 11 -> 14 -> 9 -> 15 -> 40 -> 4 -> 11.
Primary cutoff CH11 FM6 inferred, matching CH11 FM12 mark23:13:50.367; actual last screenshot CH11 FM12 at23:13:51.174 not matched by primary model. End location not verified.
Primary objective150.265 and151 supported. Alternative excluding primary CH4 at t3500 supports151 at149.285. Alternative forcing entry FM1 each sweep91 supported, objective87.745, ends CH1 FM4. Critically, alternative forbidding CH11 at t3599.99 produces151 supported, objective150.230 (difference only .035), ends CH39 FM11. Both primary and final-excluded alternative share trajectory through CH4 exit23:13:12.434 but choose different final sweep and only1s gap difference. Thus equally many matched rooms, different ending channels. No identified exact scanner; one-bot trajectory remains a hypothesis, not a recovered route or usable next-alert prediction. No changes to prior frozen model or seven-anonymous-track configuration.

## Files
- [Reproducible model](models/2026-11-27-one-scanner-hour.cjs)
- [Full result incl alternative paths](results/2026-11-27-one-scanner-hour.json)
- [Every room and channel transition](results/2026-11-27-one-scanner-room-visits.csv)
- [Every minute](results/2026-11-27-one-scanner-minute-positions.csv)
- [Accessible exchange](transcripts/2026-11-27-one-scanner-reconstruction-exchange.md)
