# Cape 200k efficiency ceiling, Chaos and crafting

## User

im willing to pay 200k per added stat. reverse engineer that. also i have a preference for playing with the new chaos scrolls, and also preference for making my own equips using crafting. run the calculation again for cape

## Assistant

# Cape optimization — 200k per added stat

Using your new efficiency ceiling, there is room to spend significantly more than 500k while including Chaos scrolls.

I rechecked HeneFM and found DEX Chaos offers at 170k, 180k and 200k. I retained 180k as the working price for comparison with our previous model.

## 1. Reverse-engineered spending limit

Using the previous 30k Green Napoleon base and scroll prices of 75k Lesser, 380k Intermediate, 50k Greater and 180k Chaos:

| Budget | Expected added stat | Expected net cost | Cost per stat |
|---|---:|---:|---:|
| 500k | 5.20 | 462,800 | 89,000 |
| 1m | 6.24 | 920,970 | 147,520 |
| 1.25m | 6.64 | 1,149,067 | 173,130 |
| **1.484m** | **6.97** | **1,391,325** | **199,619** |
| 1.5m | 6.98 | 1,414,545 | 202,517 |
| 2m | 7.50 | 1,883,426 | 251,184 |

For the maximum-stat policy at each budget, **approximately 1.48m is the spending cap that best uses your 200k-per-stat tolerance** in the tested 1k budget grid through 2m.

However, this mathematical optimum almost never uses Chaos. Since you enjoy using Chaos, I tested a separate policy that guarantees a Chaos opening attempt.

## 2. Best cost-aware strategy

A second optimization allows early stopping instead of trying to maximize stats regardless of spending. This gives a better result with 2m available:

| Policy | Expected added stat | Expected spend | Cost per stat |
|---|---:|---:|---:|
| Best tested unrestricted | 7.21 | 1,388,176 | 192,492 |
| **Chaos-first adaptive** | **7.19** | **1,436,181** | **199,698** |

The Chaos-first policy sacrifices only 0.02 expected stat compared with the best tested unrestricted policy. Begin with one Chaos on a clean cape. If it succeeds, the next action is Lesser; if it fails without destruction, NPC immediately; if destroyed, buy a fresh cape. After either failure, begin the next cape with Greater. Subsequent decisions depend on remaining cash, slots and retained stats.

## 3. Simpler Chaos-heavy plan

At 180k per Chaos, attempt up to five clean Green Napoleons, one Chaos per cape. Stop immediately at the first success and finish with four Lesser scrolls. If all five fail, buy a fresh cape and finish with five Lesser.

| Maximum Chaos attempts | Chance of +8 scroll stats | Expected added stat | Average cost/stat | Worst-case cash required |
|---|---:|---:|---:|---:|
| 2 | 19.00% | 5.57 | 138,768 | 825k |
| 3 | 27.10% | 5.81 | 159,950 | 1.035m |
| 4 | 34.39% | 6.03 | 177,556 | 1.245m |
| 5 | 40.95% | 6.23 | 192,343 | 1.455m |
| 6 | 46.86% | 6.41 | 204,875 | 1.665m |

Five attempts average 1,198,016 net spend. Final cape has 11 total DEX on success or 8 total DEX on fallback. For a strict realized cost/stat ceiling in every outcome, use only two attempts; five failed attempts can exceed 200k/stat. The adaptive policy is stronger in expected stats; this is an easy, deliberately Chaos-heavy alternative.

## 4. Self-crafted cape

White Justice Cape (Tailoring 7, natural +1 DEX, five slots) is craftable; Green Napoleon has no verified recipe. Craft inputs: 9 Processed Cloth at350 each, 1 Moon Rock18k, 3 Diamond2k each, 21 Spool of Thread10 each, 6k fee. Total33,360, rounded to34k in the model; NPC6k.

The five-Chaos plan on crafted White Justice costs 1,229,658 expected net, gives 6.23 expected added stat, costs 197,423 per point and needs at most 1.479m. It finishes at 9 or 6 total DEX, versus 11 or 8 on Napoleon. The tested cost-aware crafted Chaos-first policy at 1.904m cap yields 6.98 added points, 1,387,385 average spend, 198,680 per point, and 7.98 total stat.

Armor Crafting Catalyst costs about55–65k in observed market listings but its stat-roll distribution is unverified, so no assumed positive boost. Scroll catalysts cannot solve the Arcforge10 gate while the cap is9.

## Recommendation

Keep 2m available but target about1.44m expected spend on the adaptive Chaos-first Green Napoleon strategy. If you want a fully self-crafted base, use White Justice at Tailoring7 and accept the lower natural stat. The 200k/stat constraint is a ratio of expectations including all failed attempts and NPC salvage, not a guarantee for an individual run. All results depend on repeatable market inputs, independent rolls, full DEX conversion, and assumed scrolled NPC payout. No citizenship, no actual purchases, no global proof or production engine update.

[Post-save verification metadata omitted; citations flattened, sources in research file.]
