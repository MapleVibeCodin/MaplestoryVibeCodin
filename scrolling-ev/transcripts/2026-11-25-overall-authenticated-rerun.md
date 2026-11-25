# Authenticated overall rerun exchange — 2026-11-25

## User

[Seven HeneFM API responses pasted, all asOf 2026-11-25T15:15:00Z. Raw provider payload omitted under the standing archival rule; derived quotes and counts in ../OVERALL_RESEARCH.md.]

## Assistant

# Updated female overall optimization — authenticated HeneFM prices

Your API results confirm the following prices as of **November 25, 11:15 PM Taipei time**.

| Scroll | Lowest ask | Usual price | 24h average sold | 24h sold |
|---|---:|---:|---:|---:|
| DEX Intermediate 60% | 370k | 395k | 378,367 | 160 |
| **DEX Greater 10%** | **10k** | **20k** | **18,840** | **925** |
| LUK Intermediate 60% | 845k | 929,999 | 884,892 | 60 |
| LUK Greater 10% | 27k | 32,999 | 30,058 | 1,060 |
| DEX Chaos | No listings | — | — | 0 |
| LUK Chaos | No listings | — | — | 0 |

DEX Lesser also has no listings.

**DEX Greater is the clear starting choice if DEX is fully convertible to LUK.** It has 491 distinct sellers and costs considerably less than its LUK equivalent. Both Chaos scrolls are excluded from the executable strategy because none are currently listed.

The 10k listing is particularly interesting, but we cannot assume the entire batch is available at that price.

## 1. Updated 1m budget simulation

I reran the finite-state budget optimizer and reproduced the previous 19k-scroll results as a regression check.

Using a 12k clean Blue Avenger, 9k assumed NPC recovery, ten slots and mandatory NPC disposal of failed openers:

| DEX Greater purchase price | Expected added stat | Total effective stat | Average net spend | Cost per added stat |
|---|---:|---:|---:|---:|
| **10k — lowest ask** | **8.96** | **14.96** | 964,076 | 107,646 |
| 15k — discounted bulk scenario | 8.08 | 14.08 | 957,409 | 118,516 |
| 19k — rounded sold average | 7.58 | 13.58 | 957,869 | 126,397 |
| 20k — usual price | 7.38 | 13.38 | 956,473 | 129,678 |

The 20k scenario also uses the usual Intermediate price of 395k rather than 370k.

[Rendered chart omitted; all values appear in the table.]

Buying Greater scrolls at 10k rather than 19k improves expected added stats by approximately **18.2%**.

## 2. Best targets for the Blue Avenger

| Added scroll stat | Total effective stat | Success at 10k Greater | Success at 19k Greater | Added max range |
|---|---:|---:|---:|---:|
| +8 | 14 | 76.45% | 58.93% | +10.60 |
| **+9** | **15** | **65.89%** | **44.11%** | **+11.93** |
| +10 | 16 | 39.76% | 25.63% | +13.25 |
| +12 | 18 | 23.17% | 13.29% | +15.90 |

Each target has its own optimized policy. Range uses the illustrative 53 WATK, not measured character stats.

At 10k Greater, targeting +9 costs 859,328 on average, produces 7.67 expected retained scroll stats and costs 111,974 per retained stat across all runs. At 19k, the corresponding figures are 910,331, 6.02 and 151,151.

## 3. Actual starting strategy

- Buy clean six-stat Blue Avengers around 12k, if DEX converts fully; otherwise prefer Dark Avenger and use LUK.
- Use Greater DEX as the first scroll. NPC every failed opener.
- After success, apply another Greater DEX. This is optimal at the starting budget in all tested scenarios.
- Keep Intermediate available as a later conditional option, rather than spending 370k immediately.

At 10k Greater, a failed Blue opener loses 13k net. At 19k, it loses 22k. The mean cost of obtaining the first successful opener through unlimited retries is 139k or 229k, respectively.

Greater-only mean added stats are 8.61 at 10k and 7.23 at 19k; allowing Intermediate increases these to 8.96 and 7.58. Intermediate is useful, but not the opening scroll.

If DEX cannot convert to LUK, a 15k Dark Avenger with the actual 27k LUK Greater and 845k Intermediate prices produces +6.18 expected LUK, costing 151,511 per retained point.

**My practical target is +9 scroll stats, for 15 total effective stats on the Avenger, if Greater scrolls can be acquired near 10k.** At 19k, target +8 for a better chance of success or follow the unrestricted mean-optimal policy for highest average range.

The 10k scenario assumes repeatable stock; base prices and NPC recovery are still prior assumptions. The rerun uses the restricted one-active-base plus parked fallback, 1k cash-grid model, not a global inventory optimum. No new catalyst eligibility, actual purchase or production engine edit.

[Post-save verification metadata omitted.]
