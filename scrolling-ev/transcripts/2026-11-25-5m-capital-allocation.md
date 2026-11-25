# Five million capital allocation

## User

i have 5m capital, what about now?

## Assistant

With **5m total capital**, I would not spend it all on the cape. Your 200k-per-added-stat ceiling is more useful than the size of your bankroll.

The larger reserve lets you attempt riskier Chaos strategies and absorb bad luck, while keeping enough money to upgrade your overall and earrings. From our previous results, spending across those three equipment slots produces substantially more damage than concentrating everything on one item.

## 1. Cape results with more capital

I reran the cost-aware optimizer across cash reserves up to 5m, retaining your preference for a Chaos opening attempt.

| Available cape budget | Expected added stat | Expected spend | Cost per stat |
|---|---:|---:|---:|
| 1.5m | +6.91 | 1.380m | 199,680 |
| **2m** | **+7.19** | **1.434m** | **199,484** |
| 3m | +7.44 | 1.484m | 199,446 |
| 5m | +7.52 | 1.503m | 199,768 |

Increasing your cape reserve from 2m to 5m buys only **0.33 additional expected stats** under your efficiency ceiling.

If we abandon the ceiling and try to maximize stats using the entire 5m, the unrestricted model produces +9.19 expected added stats at approximately **527k per stat**. That's not worth it under your stated preference.

## 2. How I'd allocate your 5m

| Equipment | Allocated budget | Expected net spend | Expected added stat |
|---|---:|---:|---:|
| Cape — Chaos-first | 2m | 1.434m | +7.19 |
| Overall | 1.5m | 1.449m | +8.89 |
| Earring | 1m | 944k | +7.70 |
| Untouched reserve | 500k | — | — |
| **Total** | **5m** | **3.827m** | **+23.79** |

[Rendered card flattened: expected added effective stats +23.79; added maximum range +31.52; average cost per stat 160,890; expected remaining capital 1.17m. Allocations 40% cape, 30% overall, 20% earring, 10% reserve.]

If you prefer to allocate every meso, increase the overall budget to 2m instead. That raises combined expected added stats to **25.11** and illustrative maximum range gain to **33.26**, but leaves no guaranteed unallocated reserve.

## 3. If you prefer crafting your cape

At a 2m liquidity cap, a self-crafted White Justice Cape with a Chaos opener yields +6.98 expected added stats, costs about 1.385m on average and stays under your ceiling at 198,346 per stat. Green Napoleon still wins on natural stats: about 10.19 total effective stats versus 7.98 on White Justice.

**My recommendation: reserve 2m for a Chaos-first Green Napoleon, then spend on overall and earring.** Choose the crafted White Justice instead if the enjoyment of making the base is worth approximately 2.21 effective stats to you.

The new cape calculation uses a restricted adaptive policy and a grid of cost-penalty values, not a proof of global optimality. The combined allocation reuses the prior independent gear models, assumes all bases are clean and DEX is fully convertible, and uses illustrative 53 WATK. No new live prices, no citizenship sources, no actual purchases. Expected cost per stat is not guaranteed on every run.

[Post-save verification metadata omitted.]
