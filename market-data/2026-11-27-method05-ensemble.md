# Method 5/5 — decision-focused ensemble

## User verbatim
ok now do next

## Objective and inputs
Exact channel before desirable deal announcement, approximate FM position secondary, maximize actual seconds saved. All previous sources preserved; data blob 68f456d30f5887421107fda32ffe29ad09ab5aca, 2558 total,1909 evening,1237 consolidated,889 training,261 validation through21:02:59.731,86 retrospective test through21:19:37.057 Taipei. Same 2s noncancelable continuous-state replay as methods1–4. Baseline560.442999/196.878002s reproduced exactly. No new dataset. Do not treat filename time as actual announcement time or simulated summed per-alert delays as real elapsed gameplay.

## Executed implementation
models/2026-11-27-method05-ensemble.cjs extracts fixed forecast grids from exact archived source prefixes, no modifications to component files. TPP shrink30; Hawkes best training fit; renewal ±60s chosen by validation log loss; HSMM nominal855s with uniform/mild/strong/rank+historical-alert-proxy emission weights. Sources and blob IDs in results JSON. All four models predict 30s first-event joint channel mass and expected unfinished 2s movement penalty. Mix unconditional mark masses, no-event survival mass and penalty linearly with weights on .25 lattice. 95 configurations including single-component controls and four density variants wherever HSMM has nonzero weight; 7 margins x5 cooldowns x95 plus baseline =3326 policies. 355 active in validation. Select by validation net seconds, tie-break fewer speculative switches, then fixed enumeration. Exact expected first-event switch gain under assumed costs 2*(Ptarget-Pcurrent)-E[(2-T)+], with horizon truncation and component discretization. No long-horizon optimal control claimed. Event alignment, probability mass, baseline, method1 and HSMM replay checks all passed.

## Results
Selected single HSMM uniform, margin.04s cooldown0, validation+3.0759997s,3 speculative switches,2 gains>=1s/0 losses,18 vs17 early; test0s,0 speculative switches,1 early unchanged. Best genuine blend 25% Hawkes +75% mild density HSMM, margin0 cooldown0, validation+2.2569997s,1 speculative switch,2 gains>=1s/0 losses; test0s/no proactive action. Equal four-way uniform HSMM mixture validation/test0s, no switches. Best density-only HSMM rank+alert proxy validation+3.0759997s,3 switches,3 gains/1 loss; test0s/no switches. No mixture beat original HSMM validation result. No positive test net for any validation-selected individual or named best blend. Do not claim all possible policies' retrospective test scores evaluated: only selected candidates and controls scored.

Comparison: TPP validation+2/test-3.31s, test conditional sampled-origin accuracy44/688/logloss3.576545; Hawkes0/0,22/688/logloss3.611194; renewal0/0,35/688/logloss3.312213; HSMM+3.076/0,58/688/logloss3.499368; best genuine ensemble+2.257/0,38/688/logloss3.524691. Equal four-way51/688/logloss3.397536. These origins are correlated, not actual correct occupancy. Density-aware floor challenger previously improved conditional floor distance but not measured travel; ensemble evaluates channel positioning only.

## Decision and next work
No model demonstrated positive net simulated time saving on the common test batch. HSMM is leading validation candidate, not proven live winner. Freeze selected HSMM, density challenger and best genuine blend; use genuinely new observations for prospective comparison, avoid further selecting on reused test. Preserve soft shop-density prior distinct from actual shop counts and scanner state. Actual alert timestamps, desirable-deal eligibility, coverage and movement-time measurements remain missing. All eight originals retained. No runtime edits/deployment. Full ten-check historical continuity audit and complete verbatim historical dialogue remain incomplete.

Code exact readback commit 044284d6641b182b2762cc3f4f3d57860554f3cd; results exact readback commit 894be4a6f14fac0a41ee30b97ff2ec661c085b36.
