# FM Rush continuation — color vision research and replay, 2026-11-26

This is a structured record of the available current-session user requests and assistant findings, not a complete platform transcript. Preserve earlier checkpoint and audit records.

## User requests (verbatim as available)

- "Resume FM Rush checkpoint v24.63.0. Read https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/AGENTS.md and latest transcripts, including the final continuation and pipeline audit. Run all 10 continuity checks. Review all performance logs, regression fixtures, screenshots and recordings. Continue our existing GitHub and PowerShell workflow. Preserve all historical files. Prioritize systemic fixes and end-to-end regression testing, not individual item patches. Never suggest Work or Codex."
- "ok now rerun using this version onto all of the gvideos. i need 100% accuraccy"
- "deep dive into runescape botting (or color botting) and find out better methods to do what your doing"
- "this is great. now dive even deeper because if this quick 10 second research could yield you so much, dive into how to create your own color bots and things like that"
- "incredible. now seach simba and all other botting sites, and find their raw code. and github. anything pub;licly available and quality"
- "incredible. now search through all known hardships specifically for runescape and implement failsafes"
- "update all of this onto github"

## Recovered state

Initial static continuity 10/10 recovered at c862d15d562a3222a696a3363fc64ca710116b9e, v24.63.0 desktop / v24.56.0 browser. Earlier five logs: 2914 events/37 attempts; median channel pointer 11.3 ms (n=201), shop pointer 11.5 ms (n=112), channel focus 63.6 ms (n=199), shop focus 63.15 ms (n=112), channel-associated black interval 1529.6 ms (n=7). These are older recorder results, not new version validation.

The complete archive was subsequently located via Library metadata (not semantic title search): FM_Rush_2026-11-26_complete_checkpoint.zip, 109961754 bytes, 57 originals (10 MP4, 42 PNG, 5 JSONL) and manifest. Earlier archive remains. No raw private desktop media or logs published to public GitHub. Prior replay output named replay_summary.json, previously delivered in chat. This record preserves the reported replay totals, not a new raw-file replay.

## Prior v24.63.0 replay report

| Recording (time) | Frames | Visually labeled room result | Exact gate open-shop samples |
|---|---:|---:|---:|
| 03-14-15 | 367 | 12/12 | n/a |
| 03-14-30 | 406 | 12/12 | n/a |
| 03-14-46 | 362 | 13/13 | n/a |
| 03-15-01 | 353 | 11/11 | n/a |
| 03-38-05 | 724 | 24/24 | 0/10 |
| 03-42-22 | 522 | 17/17 | 0/2 |
| 03-46-13 | 1174 | 38/38 | 0/6 |
| 03-55-12 | 461 | 16/16 | 0/10 |
| 03-56-42 | 591 | 18/18 | 0/11 |
| 03-58-13 | 817 | 27/27 | 0/8 |
| Total | 5777 | 188/188 | 0/47 |

Reported replay processed decoded frames using copied published detector logic, with accuracy based on visually reviewed half-second samples, 11 ambiguous transition samples excluded; not individually labeled every frame. Exact gate rejected all 47 visible open-shop compressed samples but also rejected all 141 closed samples. Experimental compression-tolerant version detected 46/47 open, 141/141 closed rejected; remaining miss 03-46-13 at 16.5 s, third button changed substantially. Example required BGR (67,223,208) vs decoded strip median (67,221,205). Exact gate located shop anchors in 10 of 42 native PNGs; denominator is the entire archive, not 42 verified open shops. Compression artifacts do not prove native live failure. No exact seller/name/price, WinRT or complete highlight replay validated. Experimental gate not released; no 100% end-to-end claim.

## Research decisions

Read research/2026-11-26-color-vision-source-audit.md for actual pinned sources, algorithms, license cautions, failure modes, module architecture and rollout. Major findings: Minerva same-game shop band detection, price physical-width checks and 24 public PNG paths; mpl-ocr same-game glyph engine and GDI font identification; Simba DTM/color/packed pixel OCR, SimpleOCR expected-text masks, WaspLib glyph ambiguity and item masks, SRL-T hashes, OSBC/ChromaScape portable methods. Precompile expected text but avoid target-induced confirmation bias. Use native UI scale, occlusion and exact evidence; shadow-test improvements. External benchmark figures are developer-reported, not validated on this user's scanner.

## Latest release

Desktop v24.63.1 68b8b7a1cbe75d805ab78314458f8ff1c72a1ed5, browser unchanged. Nine files added/modified, no removed paths. Source read-back and main ref were verified. See 2026-11-26-color-vision-failsafes.md for implementation and validation limits. No new runtime edits in this documentation checkpoint. Prior response reported five standalone tests passed; this turn does not re-run them. Four tracker regression checks staged; live Windows/WinRT and complete corpus still unverified.

## Next session

Read live AGENTS.md, this continuation and research audit, previous final-continuation and pipeline audit, then verify actual latest main and runtime. Run ten continuity checks and staged tests, then prioritize real full-pipeline fixtures, native font and geometry shadow tests, no item-specific guesses. Use pinned PowerShell updater with runtime release 68b8b7a1cbe75d805ab78314458f8ff1c72a1ed5; document any startup test failure before adding features. One fresh performance report after 30–50 ordinary attempts; no need for one video per failed item. Raw archive already exists in Library; use exact metadata retrieval before asking user to resend. Preserve every old file and branch. No Work or Codex suggestions.
