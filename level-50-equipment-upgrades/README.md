# Level 50 equipment upgrades — durable resume point

Updated 2026-11-27. Dedicated archive for the hypothetical level-50 Assassin equipment-upgrade research. This folder is the starting point for future equipment questions; it is separate from FM Rush, market flipping and other projects. Do not treat example builds as actual account records.

## Read first
1. [Recovered late requests and audit](transcripts/RECOVERED_LATE_REQUESTS.md) — exact available user requests for glove, claw, weapon/armor catalysts, boots, hat, and final 5m allocation; original missing assistant replies are explicitly marked.
2. [Research snapshots](RESEARCH_SNAPSHOTS.txt) — exact copies of 8 existing source files, including earring, female overall, cape, glove, catalyst research and v1.0 optimizer code/HTML; source paths and blob SHAs are preserved. For runnable code, use original [scrolling-ev](../scrolling-ev/) files.
3. [Earring dialogue](transcripts/EARRINGS.txt) — 10 existing dialogue files.
4. [Overall/cape/glove dialogue](transcripts/OVERALL_CAPE_GLOVES.txt) — 10 existing dialogue files.
5. [Related catalyst and earlier dialogue](transcripts/CATALYST_AND_EARLIER.txt) — 9 existing dialogue files.
6. [Original master checkpoint](../checkpoints/LATEST.md) — earlier project index; equipment section ends with glove allocation, not the final all-slot optimization.

All five archive files were written to main and read back exactly against their prepared text. Original 29 dialogue source files were copied without rewriting their content. Source archive files are themselves partial transcripts in places, not a complete platform export. Existing original files have not been deleted or altered.

## Latest known planning constraints
- Level 50 Assassin, female equipment where relevant; start with clean equipment, self-scroll, allow buying clean bases, tradeable scrolls, and materials from FM. No citizenship-gated acquisition or recipes, no AP resets. Do not assume DEX can be converted to LUK on a fixed AP build.
- Optimize highest displayed damage range, not crit-weighted combat damage. Report actual combat damage/critical rate separately. Compare net expected cost per retained added stat and per range point, target probabilities, failure/disposal costs, clean base cost, and budget on every branch.
- HeneFM only for market prices; use verified Classic-specific mechanics sources separately. Refresh actual executable quotes and depth before recommendations; archived quotes are historical.
- Pansy earrings 30k, 5 slots, 3% natural crit damage as model assumptions. Always NPC the failed four-slot zero-stat opener; 13.5k recovery was an assumption. Original earring work excluded 100% actual applications, later context indicates 100% allowed if available in FM for earrings/overalls; do not silently reuse older restrictions or claim live supply. Overall FM-only Lesser explicitly allowed.
- Scroll crafting catalyst tier convention: 75% Intermediate, 20% Greater, 5% Chaos. Armor and weapon catalyst user-estimated direction: 15% positive, 25% negative, 60% neutral; not official probabilities and not the same process.
- Cape 200k per added stat efficiency ceiling, preference for Chaos and self-crafting, not permission to assume inaccessible recipes. Claw 100% scroll benchmark 70k; compare Steel Slain and eligible newer claws, clean +1/+2/+3 weapon variants and 2H catalyst. Hat 100% accuracy benchmark.
- Final budget 5m total across equipment starting clean; earlier 1m/2m earring/overall comparisons and individual 5m glove/claw scenarios are not additive allocations.

## Recovered quantitative checkpoints (historical models, not new calculations)
| Slot | Archived checkpoint |
| --- | --- |
| Earrings | Constrained 1m no-Lesser mean added stat 7.70156, net spend 943,623, 122,524 per stat, illustrative W53 range +10.20. Later rule permitting FM 100% would require a rerun. |
| Overall | 750k–1m preferred in historical restricted model. At 1m E added 7.36378, 129,519 per stat; at 2m E 10.21342, 190,382 per stat. |
| Cape | 500k simple plan E added 5.2, net 462,800; separate cost-aware Chaos-first scenario at 2m E 7.19175, net 1,436,181, 199,698 per stat. |
| Gloves | 3 guaranteed WATK modeled at 1.925m, illustrative +23.52 max range; 5m WATK E added 5.72, expected net 4.843m, historical quotes. Crit does not directly add displayed range. |
| Claw, boots, hat | Later user requests recovered; original results not found. |
| Final all-slot 5m | Not recovered. Earlier cap 4.82m glove/overall/cape/earring plan is incomplete, not final all-slot optimum. |

These examples carry old price, mastery and AP-conversion assumptions. Do not use them as validated current character stats or a fresh optimum. The original engine is a scalar v1.0 renewal optimizer, not a fully implemented all-slot hard-cap optimizer.

## Resume protocol
Read this README and the relevant original research snapshots before doing anything. Preserve old research; recover or recompute only missing results when necessary, and distinguish original outputs from fresh reruns. Use newest instructions over older assumptions. Append new user-visible dialogue and actual calculations to this dedicated folder, then commit and read back; record scope and missing content honestly. Never silently declare a full transcript if access is partial. Keep credentials, private/account identifiers, hidden instructions, and unrelated chats out of the public repository. GitHub is the durable project source of truth; ChatGPT memory is a short index, not a verbatim archive or automatic sync.

## Remaining gaps
The 2026-11-27 chat-history searches did not recover the original assistant answers after glove optimization. Expected claw/boot/hat/equipment research paths returned 404 and claw/equipment commit searches were empty. No complete chat export was available. Some original transcripts omit rendered UI, attachments, raw provider responses and sections of replies. Do not claim all prior chat messages or every original calculation have been archived. Next substantive equipment task should first recover the missing original answers if accessible; otherwise rerun only those missing calculations with current inputs.

## Resume prompt
Resume level-50 equipment upgrades from https://github.com/MapleVibeCodin/MaplestoryVibeCodin/tree/main/level-50-equipment-upgrades. Read README.md, research snapshots, recovered late requests, and relevant dialogue files. Reuse verified prior work; do not restart completed research. Apply latest constraints, refresh HeneFM only when needed, identify missing results, and save every new substantive turn in this folder with verified readback.


## Superseding boot base rule — 2026-11-27
User: "no lets only use Black Green-Lined". For subsequent equipment optimization, use Black Green-Lined Shoes exclusively as the boot base unless the user changes this instruction. Level 40, standard clean +4 DEX, +4 avoidability, 22 WDEF, no natural speed, 5 upgrade slots. Historical HeneFM clean quote 15,000 mesos; NPC recovery 4,200 assumed for surviving failed openers. Refresh clean price when needed. Speed is a valued secondary utility objective; compare speed scroll policies on this base only. Historical Lesser/Greater/Chaos inputs 15k/7k/29k: five Lesser +5 speed at 90k; Greater opener then four Lesser +7 speed at expected 10*(15k+7k)-9*4.2k+60k = 242,200; Chaos opener then four Lesser +8 speed at expected 481,100. Renewal costs not guaranteed hard-budget outcomes. Do not substitute Blue-Lined, Goni or lower-level boots. Prior comparison remains historical.
