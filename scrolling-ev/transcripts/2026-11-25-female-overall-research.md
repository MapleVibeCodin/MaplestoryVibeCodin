# Female overall initial research exchange

Accessible dialogue copied with rendered images/cards and citation markers flattened or omitted. Source links and exact numerical methodology in ../OVERALL_RESEARCH.md. No private data.

## User

awesome! Now do the same starting methodology with female overall, for general or thief. Do everything we did with the scroll

## Assistant

# Female overall scrolling optimization

I'll use the same **1 million meso hard budget**, level-50 thief damage objective, and no 100% scroll applications as our starting model. The overall-specific advantage is ten scroll slots instead of five.

## 1. Best clean bases

**Dark Avenger — level 35**

Natural +6 LUK, 10 slots. Requires 25 DEX and 60 LUK. HeneFM observations at 12–15k for standard-stat clean bases.

**Blue Avenger — level 35**

Natural +6 DEX, 10 slots. Equivalent to Dark Avenger for displayed range if all six DEX points can be converted into LUK through AP reassignment.

**Purple Avenger — level 35**

Natural +3 DEX and +3 LUK, 10 slots. Another viable alternative under the same AP-conversion assumption.

**Red Sauna Robe — level 30**

General-class female overall. +1 to each of the four main stats, 10 slots, no secondary-stat requirements.

The Avenger family offers a substantial natural-stat advantage over Sauna Robes, provided you meet the equipment requirements. Red Avenger has +6 STR instead, making it less attractive for the ordinary Assassin range objective.

## 2. Important market discovery

Overall scroll economics are dramatically different from earrings.

| Scroll | Added stat | Success | Observed price |
|---|---:|---:|---:|
| Overall DEX Greater | +3 | 10% | 15,000 lowest; 18,800 average sold |
| Overall LUK Greater | +3 | 10% | 25,000 recent asking price |
| Overall LUK Intermediate | +2 | 60% | **845,000 lowest** |

HeneFM's accessible DEX Greater snapshot also reported approximately 1,600 scrolls in stock. The LUK Intermediate price is particularly unfavorable at almost the entire budget for one scroll.

This makes cheap Greater scrolls much more interesting for overalls than the earring strategy.

## 3. Complete starting inputs

DEX Intermediate: 370k lowest, 380.2k 24-hour sold average. For the model I used 19k Greater and 370k Intermediate, rather than assuming dozens of Greater scrolls can be bought at the single cheapest price. Avenger NPC recovery is 9k; Sauna Robe 5.4k. I extended your failed-opener rule to nine-slot overalls: NPC immediately after the first failed scroll.

## 4. Hard-budget optimization results

| Clean base | Modeled price | Expected scroll stat | Expected total effective stat | Expected net spend | Cost per added scroll stat |
|---|---:|---:|---:|---:|---:|
| Blue Avenger | 12k | 7.58 | 13.58 | 957,869 | 126,397 |
| Dark Avenger | 15k | 7.36 | 13.36 | 954,419 | 129,726 |
| Red Sauna Robe | 40k | 5.57 | 7.97 | 945,421 | 169,583 |

Blue wins at these modeled prices only if DEX is fully convertible. Purple is also viable at the observed 13.5k ask. If DEX cannot be converted, Dark is preferred; LUK-only scrolling at 25k Greater and 845k Intermediate yields +6.37 expected scroll LUK.

At illustrative 53 WATK, Dark adds +9.75 maximum range from scrolling, or +17.70 including natural stats compared with no armor. Blue adds +10.04 from scrolling, +17.99 including natural stats. Subtract your replaced armor's effective stats to determine actual upgrade.

## 5. Dark Avenger target optimization

| Added scroll stat | Total effective stat | Chance to reach target | Maximum range from scrolls | Cost per expected retained scroll stat |
|---|---:|---:|---:|---:|
| +8 | 14 | 55.94% | +10.60 | 146,500 |
| +9 | 15 | 41.40% | +11.93 | 164,217 |
| +10 | 16 | 23.77% | +13.25 | 186,285 |
| +12 | 18 | 12.21% | +15.90 | 236,211 |

Each row is its own target-optimized policy, not the probability distribution of the mean-optimal policy.

## 6. How to scroll

1. Buy a clean six-stat Avenger.
2. Open with a Greater DEX scroll if convertible, otherwise Greater LUK.
3. NPC failed openers immediately.
4. After a successful Greater, apply another Greater. At the starting budget this beats Intermediate, unlike earrings.
5. Adapt to remaining slots, stat and cash; park a better item as fallback if restarting.

A failed 19k Greater attempt on a 15k Dark Avenger costs 25k net after NPC recovery.

## 7. Benchmark and Chaos sensitivity

100% benchmark only: at the citizenship-gated 40k DEX Lesser price, ten guaranteed scrolls plus a 15k base cost 415k, or 41.5k per added stat. Not a verified freely purchasable market quote.

| Hypothetical Chaos price | Expected added scroll stat |
|---|---:|
| No Chaos | 7.36 |
| 10k | 8.82 |
| 20k | 8.01 |
| 30k | 7.47 |
| 50k | 7.37 |

Chaos has +4, 10% success and 45% unconditional destruction under the documented mechanics. These are sensitivity tests, not market quotes. No confirmed HeneFM Chaos listing was retrieved. STR gives only 40% of a convertible DEX/LUK point; INT and DEF do not directly increase range. The full joint STR/DEX/Chaos model remains outstanding.

The public Arcforge recipe catalogue does not show a stat-overall scroll recipe. No verified catalyst route; do not assume our earring crafting cost applies to overalls. If eligibility is confirmed, use our fixed 75/20/5 production convention.

## 8. 100-base triple Greater comparison

Reusing the previous seeded simulation for a fair comparison: 92 failed openers, six +3, two +6, zero +9, with seven slots remaining on each survivor. Net batch cost 2,876,000; expected cost 2,970,000. This is a simulation above the 1m budget, not actual crafts.

## 9. Next price refresh

```powershell
(2040508,2040509,2040510,2040511,2040517,2040518,2040519 | ForEach-Object { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\Get-HeneFMPrice.ps1" -ItemId $_ -Json }) -join "`n" | Set-Clipboard
```

Paste the results here. The two Chaos prices are the biggest unresolved variables. All calculations above use accessible HeneFM snapshots and modeled repeatable prices, not synchronized authenticated quotes. The DP is exact within a restricted 1k-grid, one-active-item and parked-fallback model; it does not establish a global inventory optimum. No actual purchases or production engine modifications.

[Post-save metadata omitted.]
