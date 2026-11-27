# Dense-feed research — new chat handoff

User exact request: copy everything verbatum and start new chat. save to github

## Read in this order
1. AGENTS.md (repository root, read entire file; historical sections are not latest state)
2. checkpoints/LATEST.md (entire file, latest dated entries supersede older entries)
3. market-data/2026-11-27-scanner-research-LATEST.md
4. This handoff and the following linked research:
- [Exact-count identifiability audit](2026-11-27-scanner-count-identifiability.md)
- [Dense scanner tracking](2026-11-27-dense-scanner-tracking.md)
- [Frozen 6.721s route replication](2026-11-27-zero-filter-next-holdout.md)
- [Zero-filter route analysis](2026-11-27-zero-filter-route-analysis.md)
- [Full-history positioning](2026-11-27-final-full-history-positioning-analysis.md)
- [Raw originals manifest](raw/2026-11-27/README.md)
- [All 12 original Git blob checks](results/2026-11-27-final-handoff-integrity.json)
- [Latest exact-count dialogue](transcripts/2026-11-27-exact-count-exchange-verbatim.md)
- [Live-feed and filter exchanges](transcripts/2026-11-27-live-filter-exchanges-verbatim.md)

## Current state
Objective: position in correct channel before a desirable deal announcement or close to correct FM room, even one second saved matters. Use observed market records to evaluate hypotheses; distinguish actual gameplay timing from simulation. User changed filters to 0,0,0,0 approximately before dense period, still profitable-listing selection. Keep datasets by observation regime separate. Last raw record 2026-11-27 22:55:03.028 Taipei (+08:00), last consolidated dense event 22:55:02.101. Twelve original exports re-fetched, all twelve blob hashes independently matched manifest; union 11208 distinct filenames, not unique listing IDs. Full union consolidated count not recalculated. Never discard overlap or backfill; preserve originals. No runtime deployment.
815 consolidated dense observations from22:34 onward, 314 compatible directly adjacent forward transitions vs10 reverse with4–12s gaps; median7.0055s, sum of 20 edge medians141.641s. Circular route 1,7,17,18,19,20,16,15,14,13,8,9,10,11,12,6,5,4,3,2,1. 35 compatible wraps, 16 direct FM2->1 same channel. Fixed room extrapolation dwell6.721s not retuned: 471 combined evaluation events,243 exact room,351 exact row,444 within1 row,151 aggregate row distance vs405 fixed. Conditional on known target channel; not actual player position or elapsed gameplay. Earlier frozen channel policies across1172 holdout events saved only A1.407/B2/C.407s on one common CH19 opportunity; no further positive gain. Channel recency15s 36/242 fixed-lead correct vs19 persistence in latest batch. Default FM9–10 remains.
44 strong episode envelopes peak7; minimum seven-track cover feasible with120s allowed unobserved gaps,8 with90s. Actual cross-channel assignment unverified; only9/37 hypothetical edges stable at80% across40 perturbations. Fixed channel-group coloring feasible but not unique; no repeated strict cross-channel handoff. Individual timestamp audit contradicts a hard count7 if timestamps exact and minCC2s: 8 distinct channels in2s, min cover9 at CC2/step2; excluding first2 minutes min6. User's own2s CC not scanner timing. Download timestamps are not verified scan timestamps. Seven anonymous tracks with overflow is working configuration only, no exact physical count or upper bound established. Next work should not repeat these tests absent changed assumptions or new evidence. Do not fabricate identities, exact count, or channel order.

## Continuity and preservation
Current research pre-handoff main e838c7793e556102c7a8d70bddfab2cd9cb3ec9b; original files all verified at current main in this handoff. Latest transcript files exact remote readback at commits63214ea27c738847dc4c50eb54ead8925cd48913 and bd44c619f46f79f17ec0a26ce8e1ec6d96821705. Integrity manifest280d54faf389f0c7f339154cfc981606fdb9ebd6. A larger attempted verbatim archive of earlier dialogue was blocked by the tool. No claim all earlier replies copied. Missing: first 288-event deep-dive response, full-history response, past-hour response, zero-filter analysis, next-holdout response, full tracking response, and earlier inaccessible messages/rendering. Structured numerical reports already archived but not substitutes for missing dialogue. No platform-wide transcript export or direct new-chat creation available. Full ten-check historical continuity audit remains incomplete; next chat must read all required sources and run ten checks without claiming previous full execution. No runtime edits, deletions or unrelated private information added.
