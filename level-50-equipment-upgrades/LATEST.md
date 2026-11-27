# Current handoff — 2026-11-27

## Read first
Read [README.md](README.md), this handoff, and [market-data README](../market-data/README.md). For earlier overall/cape/glove research read [original dialogue archive](transcripts/OVERALL_CAPE_GLOVES.txt). Preserve all prior versions and history. Latest user instructions override older scenarios. Do not redo completed research. No raw API payloads, credentials, private account records or seller histories in this public repository.

## Active focus: repeatable fast non-scroll arbitrage
- User has finished Shoes Speed research for now; do not circle back unless asked. Gloves Accuracy and Shoes Jump excluded from catalyst shortlist; do not confuse this with personal equipment use.
- Hard evidence gate: >=24 distinct qualifying cheap purchase listings in trailing 24h, ideally distributed throughout the day, rather than a one-off misprice or 24 units from one seller. >=10k net profit per transaction or attainable practical batch; preferred liquidation <=1h, maximum 2h. Both entry and exit at or below 90% of 24h average sold price; purchase threshold also must preserve required margin. Rank net mesos per hour and capital turnover. Use 3% selling fee as modeling assumption, verify actual fees as needed.
- Measure historical cheap listings at threshold, unique listings and quantities, not aggregate sales or seller count as proxy. Document sample/window coverage, observed listing age, unsold/repriced listings, actual sale vs gone, and batch availability. P10 from partial sample is not market-wide percentile. HeneFM public histories truncated; personal API provides aggregate averages/count, not price-bucket counts or exact liquidation times. Don't invent missing evidence or present unverified source claims as freshly checked. If insufficient, label candidate unqualified, not conclusively absent.
- No new candidate has passed all gates, including the latest 24/day requirement. Glass Shoe excluded (two reported 50k sale observations plus one cheaper, not complete 24h listing count). Black Crystal Ore, Iron Ore, Screw, Overall DEX Greater, Orange/White Potion, Leather, Mokbi and Wooden Top require requalification. Palette coupon, slow arrows, speculative NX, small-margin processing, and low-volume equipment are not priorities.
- Black Crystal last authenticated 09:50 UTC: ore avg3115, refined avg4778, discounted exits2803/4300. Refining cost1200, ore buy2500 ->471 net, 22 units for10k; buy2700 ->271 net,37 units. Historical examples insufficient for 24 distinct qualifying opportunities. Glass Shoe direct resale superior to quest, but insufficient cheap supply. Do not claim full-batch sale time based on single historical rows.
- Seven-item observed lower-tail samples and star research are in linked files below; do not extrapolate full market counts.
- Next step: investigate genuinely new non-scroll candidates, then ask user for targeted authenticated price quotes only where useful. Do not use restricted API for automated deal-finding, bypass limits or bulk storage. Existing manual research workflow only; no new automation requested.

## Completed crafting research (reference, not active task)
60 API responses/20 scroll families, Nov27 09:25–09:30 UTC. Latest Shoes Speed 10:00 UTC snapshot, assumed 75/20/5 outcome mix, 3% fee, noncatalyst cost15200 carried forward. At 70k catalyst: 14311.09 net EV at averages,11886.57 at lowest asks. Under 90% fast-exit rule: net revenue89559.98, 63k catalyst gives11359.98 expected profit, 70k gives4359.98; provisional 63k alert, not guaranteed profit. Gloves Crit prior model positive but slower; LUK excluded for strict fast-exit margin. Arcforge route archived. No measured full-capital-cycle duration or guaranteed outcome. Historical numbers are not fresh actionable prices.

## Personal-use equipment (separate objective)
Female-compatible level40–50 Assassin planning, no citizenship-gated acquisition, no AP reset, self-scroll. Lock Dark Pilfer, Pansy Earrings (NPC surviving failed zero-stat four-slot opener), Black Green-Lined Shoes. Compare all compatible tiers, including Chaos, and natural above-standard variants. Keep displayed range distinct from combat/utility. Prior conditional package: Dark Pilfer 4 HP/3 ACC Lesser, Pansy 5 LUK Lesser or Greater opener, White Napoleon 5 LUK Lesser, female Dark Shadow top/bottom 14 HP Lesser combined, Black Green-Lined Greater Speed opener +4 Lesser (with guaranteed +5 fallback), 31ATT Steel Slain +7 Attack Lesser; gloves deferred. Expected ~2.032m, modeled gross cap ~2.327m excluding gloves. 23 LUK,4 DEX,38 weapon ATT,+180HP,+3% crit damage, +10 equipment speed on boot success /+8 fallback. Historical assumptions, not actual inventory or verified global 5m optimum. Earlier DEX range results assume AP conversion, incompatible with no-reset rule; prefer Dark Avenger natural6 LUK for LUK scrolling, Blue/Purple if actual DEX requirement matters. Avenger base variants and Red Sauna Robe in original overall dialogue. 750k–1m overall historical budget sweet spot, but DEX model is not direct LUK upgrade. Refresh eligible scrolls/clean bases via authenticated price data before new allocation. Original late answers missing, no claim of complete historical global optimum.

## API execution continuity
Use installed Windows PowerShell client, no key reset. Verified outer powershell.exe -NoProfile -ExecutionPolicy Bypass -Command wrapper, regex JSON extraction (banner previously broke parser), validate itemId/asOf, stop on error, 2100ms start spacing, skip final delay. Save Desktop HeneFM_Results.json and clipboard only on full success. Copying a clipboard inspection command overwrites results; paste immediately or attach backup. Four-item run confirmed 10:00 UTC. No measured run duration. Use narrow on-demand permitted lookups, not polling or automated underpriced-listing detection. No suggestion of Work/Codex.

## Archive index
- [authenticated-partial-craft-recalculation](transcripts/2026-11-27-authenticated-partial-craft-recalculation.md)
- [authenticated-19-craft-quotes](transcripts/2026-11-27-authenticated-19-craft-quotes.md)
- [authenticated-35-craft-quotes](transcripts/2026-11-27-authenticated-35-craft-quotes.md)
- [authenticated-complete-craft-ev](transcripts/2026-11-27-authenticated-complete-craft-ev.md)
- [ten-craft-liquidation-comparison](transcripts/2026-11-27-ten-craft-liquidation-comparison.md)
- [arcforge-level-6](transcripts/2026-11-27-arcforge-level-6.md)
- [repeatable-conversions](transcripts/2026-11-27-repeatable-conversions.md)
- [arbitrage-turnover-evidence](transcripts/2026-11-27-arbitrage-turnover-evidence.md)
- [arbitrage-api-validation](transcripts/2026-11-27-arbitrage-api-validation.md)
- [expanded-crafting-arbitrage-screen](transcripts/2026-11-27-expanded-crafting-arbitrage-screen.md)
- [non-scroll-turnover-screen](transcripts/2026-11-27-non-scroll-turnover-screen.md)
- [seven-item-low-tail-sample](transcripts/2026-11-27-seven-item-low-tail-sample.md)
- [black-crystal-ore-deep-dive](transcripts/2026-11-27-black-crystal-ore-deep-dive.md)
- [glass-shoe-deep-dive](transcripts/2026-11-27-glass-shoe-deep-dive.md)
- [personal-use-deep-dive](transcripts/2026-11-27-personal-use-deep-dive.md)
- [green-lined-1m-speed-optimization](transcripts/2026-11-27-green-lined-1m-speed-optimization.md)
- [second-chaos-resale](transcripts/2026-11-27-second-chaos-resale.md)

## Scope and audit
This handoff consolidates accessible project state and links to previously saved derived calculations and partial transcripts. It does not constitute a verbatim platform export, independent verification of every earlier public-web observation, a raw data archive, or an automatic background sync. Prior assistant replies contain some rounded estimates and unverifiable historical citation references; use exact derived formulas and recheck sources when necessary. Preserve original files and prior versions. No fresh market research or trades performed during checkpoint.
