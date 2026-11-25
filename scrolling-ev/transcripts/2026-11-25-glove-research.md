# Glove research exchange — 2026-11-25
Accessible dialogue excerpt, citations and rendered components flattened. Numerical tables, sources, full methodology and limitations preserved separately in ../GLOVE_RESEARCH.md. This is not a complete verbatim archive; intermediate prose/tables omitted where explicitly marked.

## User

okay now do the same whole calculation for gloves. every stat available and cost and increase in damage range

## Assistant

# Gloves — damage and cost optimization

The major difference from earrings, overalls and capes is that **gloves can directly increase weapon attack**. One point of weapon attack is considerably more valuable than one point of LUK for our illustrative level-50 Assassin.

There are four glove scroll families, with four tiers each: weapon attack, magic attack, accuracy and critical rate. No DEX or LUK glove scroll family exists in the current catalogue.

## 1. Every available glove scroll type

| Scroll family | Lesser 100% | Intermediate 60% | Greater 10% | Chaos 10% |
|---|---:|---:|---:|---:|
| Weapon attack | +1 | +2 | +3 | +4 |
| Magic attack | +2 | +4 | +6 | +8 |
| Critical rate | +1% | +2% | +3% | +4% |
| Accuracy | +1 | +2 | +3 | +4 |

Chaos scrolls have a 45% unconditional probability of destroying the equipment: 50% destruction conditional on a failed 90% roll.

For your Assassin, weapon attack increases the displayed damage range, crit rate increases actual average damage without increasing displayed range, and accuracy improves effective damage only when you would otherwise miss. Magic attack provides no direct benefit to claw attacks.

[Sections 2–7 omitted from this excerpt; exact model inputs, market observations, budget results, Chaos plan and crafting calculation recorded in GLOVE_RESEARCH.md. Rendered card omitted.]

## 8. My recommendation for your 5m capital

| Equipment | Spending cap | Expected added max range |
|---|---:|---:|
| Gloves — Chaos-first, 3 WATK | 2.570m | +23.52 |
| Overall | 750k | +8.43 |
| Cape | 500k | +6.89 |
| Earring | 1m | +10.20 |
| **Total** | **4.820m** | **+49.04** |

Expected net spending is about 4.53m. This leaves 180k unallocated even if each strategy uses its full modeled cap. You also get the natural glove stats and the additional crit rate, which are not included in the scrolling-only range total.

If pure damage range matters more than Chaos, save 645k of the glove cap and use three guaranteed Attack Lesser scrolls for 1.925m instead.

For pure crit, five guaranteed Crit Lesser cost 350k including the base, or 70k per point. The best tested cost-aware crit-only policy under 200k per crit point gives +8.36% expected added crit at 1.672m expected spend and a 2.235m cap, but zero displayed-range increase.

Remaining limitations: clean Moon Glove prices and Accuracy Lesser/Chaos quotes remain unverified; all other prices are indexed HeneFM observations, not synchronized authenticated quotes. The numerical optimizer used a 5k cash grid, one active glove and one parked fallback; mixed Chaos/attack results are exact for the specified simple policy, not a globally optimized mixed inventory policy. All range calculations are illustrative, and the gear allocation assumes full DEX conversion and no existing scrolled gear. No citizenship access, actual purchases, or production engine updates.

[Post-save verification metadata omitted.]
