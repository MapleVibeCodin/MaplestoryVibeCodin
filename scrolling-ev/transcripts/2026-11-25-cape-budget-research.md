# Cape budget research exchange

## User

awesome. can you do that for cape too?

## Assistant

# Cape scrolling — optimal spending

The cape market is different from overalls: **100% DEX and LUK scrolls have observable Free Market offers**, so we can include them without relying on citizenship.

## 1. Best cape bases

| Cape | Level | Natural stat | Slots | Observed market price |
|---|---:|---:|---:|---:|
| **Green Napoleon** | 50 | +3 DEX | 5 | 17.5–50k |
| Black Napoleon | 50 | +3 LUK | 5 | 85–150k |
| Green Icarus Cape | 46 | +2 DEX | 5 | 15k |
| Black Justice Cape | 35 | +1 LUK | 5 | 43–49k |

Green Napoleon is the strongest value candidate if DEX can be converted into LUK. Its documented NPC sell-back is 13,200 mesos.

## 2. Scroll prices

| Scroll | DEX | LUK |
|---|---:|---:|
| Lesser 100%, +1 | 70–85k | 101–105k |
| Intermediate 60%, +2 | 360–400k | 380–400k |
| Greater 10%, +3 | 45–55k | 50–60k |
| Chaos 10%, +4 | 170–180k | 350k |

These are observed HeneFM listings or recent sales, not synchronized live API quotes.

Self-crafting the main-stat cape scrolls requires Arcforge level 10, above the documented current cap of 9. I am excluding it, including catalyst crafting, rather than assuming access.

## 3. Optimal spending by budget

Fresh finite-state optimization using Green Napoleon at 30k, NPC recovery conservatively rounded to 13k, and DEX scroll prices of 75k / 380k / 50k / 180k for Lesser / Intermediate / Greater / Chaos.

| Budget | Expected added stat | Total effective stat | Added max range | Cost per added stat |
|---|---:|---:|---:|---:|
| 250k | +2.30 | 5.30 | +3.05 | 100,000 |
| 300k | +3.00 | 6.00 | +3.98 | 85,000 |
| 400k | +4.30 | 7.30 | +5.70 | 88,372 |
| **500k** | **+5.20** | **8.20** | **+6.89** | **89,000** |
| 750k | +5.84 | 8.84 | +7.74 | 118,522 |
| 1m | +6.24 | 9.24 | +8.27 | 147,520 |
| 1.5m | +6.98 | 9.98 | +9.25 | 202,517 |
| 2m | +7.50 | 10.50 | +9.94 | 251,184 |

[Rendered chart omitted; data in research file.]

**500k is the sweet spot for capes.** You obtain 83% of the expected scrolling benefit of spending 1m, for half the budget.

## 4. Exact 500k scrolling strategy

1. Buy a clean +3 DEX Green Napoleon for 30k.
2. Apply one 50k Greater scroll.
3. If it succeeds, finish with four 75k Lesser scrolls: +7 added DEX, +10 total DEX, 380k net cost.
4. If it fails, NPC the cape for approximately 13k, buy a fresh one and apply five Lesser scrolls: +5 added DEX, +8 total DEX, 472k net cost.

This gives 90% chance of +5 and 10% chance of +7, with an expected cost of 462,800 and 89,000 per added stat. Alternatively, skip the gamble: five Lesser scrolls plus the cape cost 405k and guarantee +5.

## 5. Higher target probabilities

| Added stat target | 500k | 750k | 1m |
|---|---:|---:|---:|
| +5 | 100% | 100% | 100% |
| +6 | 35.05% | 66.14% | 77.62% |
| +7 | 23.35% | 49.67% | 66.96% |
| +8 | 7.20% | 21.35% | 36.77% |
| +9 | 4.66% | 9.69% | 17.85% |

Each row is a separate target-maximizing policy; not the distribution of the recommended 500k plan.

## 6. Spending priority across gear

| Equipment | Recommended budget | Expected added stat | Cost per added stat |
|---|---:|---:|---:|
| Cape | 500k | 5.20 | 89,000 |
| Overall | 750k | 6.37 | 111,067 |
| Earring | 1m | 7.70 | 122,524 |

I'd start with the cape. The three independent budgets total 2.25m and give approximately +19.27 effective scroll stats, or +25.53 displayed maximum range at illustrative 53 WATK, if all DEX is convertible. Not a joint equipment optimization.

The model assumes repeatable listed prices, NPC recovery on failed capes, one active cape and one parked fallback. STR is not jointly optimized; no live bulk-stock verification. If DEX cannot convert to LUK, Black Napoleon with LUK scrolls is the alternative, but at 500k yields only +3.30 expected scroll stats at modeled prices. No citizenship sources, no self-crafting assumption and no actual purchases.

[Post-save metadata omitted; citation markers flattened, sources in research file.]
