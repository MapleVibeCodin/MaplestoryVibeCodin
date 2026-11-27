# Exact-count identifiability audit

User verbatim: i mean we have second by second data now. tell me eact

## Inputs
Same two zero-filter original exports, blobs9abca1d2a6c960b1b1b037d5479971bdc87e51c5 and c5c67a1b52d39bf27797086b6204ac58afb5b4b7. Dense window22:34:00 through22:55:02.101 last consolidated, 1803 raw/815 consolidated, no new observations. Raw filenames timestamp downloads, not verified exact scanner event times. Median adjacent raw interval .252s,1430/1802 (79.36%) below .5s, consistent with serial delivery but not proof of batching or backlog. Exact physical worker count not identified.

## Individual timestamp constraints
Max distinct channels in sliding half-open .5/1/2/3/5/7/10 second windows =3/5/8/9/10/10/13. Eight channels in 2s from22:35:17.113:2,6,10,12,20,23,26,36; 9 consolidated marks,10 raw. If exact scanner timestamps and >=2s to switch channel, seven impossible. Using Hopcroft-Karp exact minimum path cover on 815 marks, chronological allowed edges: any gap>=60s permits reset, same-channel same-room allowed, other same-channel route forward step count requires dt>=minStep*steps, cross-channel requires dt>=minCC (optionally phase-preservation penalty). All covers validated full partition. For CC1/2/3/4s with minStep2s, no phase constraint, conditional minima6/9/12/14; with step0,5/8/9/10. These are minimum feasible tracks for specified constraints, not exact worker counts. More tracks always fit by splitting. The user's own2s gameplay CC is not verified scanner CC time.

## Robustness
Remove early dense-feed burst by restricting from22:36:00:687 consolidated, max distinct channels in1/2/3s=5/6/7; min cover at CC1/2/3s, step2, no phase=5/6/7. From22:40=471, 5/6/6;22:45=264,3/4/6;22:50=112,3/3/4. High count bound driven by early burst, which may reflect feed delivery or actual concurrent scanners; neither explanation proven. Short direct forward adjacent observation intervals 4–12s overlap in six channels even trimming2s at each endpoint; allowing up to five steps and up to60s with2s trim gives seven. This is stronger evidence for seven concurrent scanning tracks under continuity assumptions, not exact worker IDs. Earlier seven-track long-envelope cover is feasible but cannot simultaneously claim all timestamps exact and minCC2s. Do not state exact seven or nine. Seven is a reasonable initial anonymous track setting with overflow, not upper bound; nine is conditional minimum under timestamp and speed assumptions for full window. No runtime changes.

## Archives
models/2026-11-27-scanner-count-identifiability.cjs commit253acd7d222fb1534999a2040b2b978176354f12; results/2026-11-27-scanner-count-identifiability.json commit ed8e8e852c0af8144ccd83f9e280b6052cc24d0c; results/2026-11-27-scanner-count-cutoff-sensitivity.json commit4108ea60b6e15a215e5af503cf86db98d93f0f48. All exact readback verified. Historical dialogue archive and ten-check audit incomplete.
