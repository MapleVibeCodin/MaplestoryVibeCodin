# Overall 2m budget comparison

## User

what if i up the budget to 2m? whats the improvement

## Assistant

Doubling your overall budget from **1m to 2m increases expected added stats by 38.7%**, but dramatically improves your chances of obtaining a strong finished overall.

I reran the optimizer using the same 15k Dark Avenger, 9k assumed NPC recovery, 19k Greater, 370k Intermediate and optional market-sourced 170k STR Lesser. No citizenship sources.

## 1. Expected improvement

[Rendered cards: 1m budget +7.36 expected added stat; 2m budget +10.21 expected added stat.]

| Metric | 1m budget | 2m budget |
|---|---:|---:|
| Expected added stat | 7.36 | **10.21** |
| Total effective stat | 13.36 | **16.21** |
| Added maximum range | +9.76 | **+13.53** |
| Expected net expenditure | 953,750 | 1,944,452 |
| Cost per added stat | 129,519 | 190,382 |

The extra million buys approximately **2.85 additional effective stats and 3.78 maximum damage range**, assuming 53 total weapon attack and fully convertible DEX.

## 2. Chances of achieving stronger overalls

[Rendered chart flattened: target +8, 1m 56.92%, 2m 91.37%; +9, 42.36%, 79.83%; +10, 25.76%, 69.22%; +12, 12.34%, 42.47%; +15, 2.13%, 11.52%; +18, 0.24%, 1.58%. Each target uses its own probability-maximizing policy.]

The biggest practical difference is **+10 added stats**: your chance increases from 25.76% to 69.22%.

## 3. If you buy cheaper Greater scrolls

| Greater price | Expected added stat at 2m | Added max range | Cost per stat |
|---|---:|---:|---:|
| 10k | 11.18 | +14.82 | 174,589 |
| 15k | 10.60 | +14.05 | 183,595 |
| 19k | 10.21 | +13.53 | 190,382 |

**At 2m, I'd target +10 added stats (16 total effective stats).** Target +12 if you're comfortable with a 42.47% success chance. If your goal is the highest average range rather than hitting a specific target, use the mean-optimal adaptive policy instead.

The trade-off is diminishing returns: the incremental cost is roughly 348k per extra expected stat. The 2m budget is much better for reliability, not cost efficiency.

Same recorded prices, no new live quote or stock-depth verification. STR Lesser is optional and adds only 0.0235 expected effective stats at 2m; without it, expected added stats are 10.19. The restricted optimizer still assumes one active overall and one parked fallback. I have treated 2m as a comparison, not a permanent change to your default budget.

[Post-save verification metadata omitted.]
