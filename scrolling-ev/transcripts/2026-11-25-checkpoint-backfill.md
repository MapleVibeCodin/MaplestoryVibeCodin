# 2026-11-25 checkpoint backfill

Archive metadata: manually copied accessible user-visible text. Speaker/section labels and omission notices are editorial. This supplements, rather than replaces, the earlier partial transcript and sales excerpt archives. Rendered interactive controls, internal tool messages, and citation widgets are omitted. Not a complete exported transcript.

## Assistant response to "no need to explort. just copy paste the words"

I've directly copied the original conversation text and market data into GitHub. **No export required.**

Both archive files have been committed and verified.

| Archive | Contents |
|---|---|
| [Verbatim conversation excerpts](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/scrolling-ev/transcripts/2026-11-25-partial-verbatim.md) | Original requests, selected responses and decisions |
| [Raw HeneFM sales data](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/scrolling-ev/transcripts/2026-11-25-henefm-sales-excerpts.txt) | Original recent-sale records across all 12 scroll tiers |
| [Research documentation](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/scrolling-ev/CATALYST_RESEARCH.md) | Calculations, findings and methodology |
| [Master README](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/scrolling-ev/README.md) | Continuation instructions and archive index |

**28,384 characters of original text archived.** These are partial verbatim archives: some earlier messages, responses and full market listing tables remain omitted.

Moving forward, the documented workflow is to preserve original conversation text alongside research summaries, not replace the original with summaries.

## Your permanent continuation prompt

Resume everything from https://github.com/MapleVibeCodin/MaplestoryVibeCodin/tree/main/scrolling-ev. Read the latest README, research documents and verbatim conversation archives. Continue from our latest checkpoint. Preserve new conversation text verbatim alongside research findings, and commit updates to GitHub.

Latest verified commit: `ef60fc6`.

## Earlier assistant reply backfill: "ok how to reproduce the glove crit? i can make 50"

To make **50 Gloves Crit Rate scrolls using catalysts**, you need **Arcforge level 9** and a character of at least level 45.

## 1. Exact shopping list for 50 crafts

| Material | Per craft | Buy |
|---|---:|---:|
| [Black Crystal](https://henefm.com/items/4020108) | 3 | **150** |
| [Fragment of Magic](https://henefm.com/items/4000063) | 45 | **2,250** |
| [Processed Parchment](https://henefm.com/items/4003009) | 1 | **50** |
| [Scroll Crafting Catalyst](https://henefm.com/items/4130003) | 1 | **50** |
| Crafting fee | 30,000 | **1.5m mesos** |

The current recipe is confirmed by several crafting databases. Older guides incorrectly list ten magic fragments and a 20k fee.

You can buy 150 Black Crystal **Ore** instead of refined crystals and refine them yourself if that works out cheaper.

## 2. Total investment

Using our HeneFM three-price valuation methodology:

| Material | Quantity | Target unit price | Total |
|---|---:|---:|---:|
| Black Crystal Ore | 150 | 3.1k | 465k |
| Refining fee | 150 | 1.2k | 180k |
| Fragment of Magic | 2,250 | 155 | 348.75k |
| Processed Parchment | 50 | 500 | 25k |
| Catalyst | 50 | 67.93k | 3,396.65k |
| Crafting fee | 50 | 30k | 1,500k |
| **Total** | | | **5.915m** |

## 3. Where to buy materials in bulk

These sellers appeared in the latest accessible HeneFM snapshots.

| Material | Seller | Location | Price | Stock |
|---|---|---|---:|---:|
| Black Crystal Ore | [Likefire](https://henefm.com/shops/Likefire) | CC25 FM14 | 3,199 | 102 |
| Black Crystal Ore | [Murchmellow](https://henefm.com/shops/Murchmellow) | CC29 FM7 | 3,200 | 106 |
| Parchment | [ixcherries](https://henefm.com/shops/ixcherries) | CC8 FM6 | 480 | 100 |
| Magic Fragment | [AcalaK](https://henefm.com/shops/AcalaK) | CC39 FM2 | 168 | 200 |
| Magic Fragment | [DAmimi38e](https://henefm.com/shops/DAmimi38e) | CC40 FM2 | 165 | 153 |

**Catalysts are the bottleneck.** There were 187 listed, but many shops only had one each. I'd target an average acquisition price of **75k or less**.

[All catalyst listings sorted by price](https://henefm.com/items/4130003)

## 4. How to craft them

1. Open your Arcforge crafting interface.
2. Refine 150 Black Crystal Ore into 150 Black Crystals.
3. Select **Gloves Crit. Rate Scroll: Lesser**.
4. Add a Scroll Crafting Catalyst in the optional catalyst slot.
5. Craft, ensuring a catalyst is included in every attempt.

Do not select Gloves Attack or Gloves Accuracy. The Lesser Crit Rate recipe is the one that generates higher-tier Crit Rate scrolls with catalysts.

## 5. Expected results from 50 crafts

[Rendered outcome chart and summary cards omitted.]

## 6. Realistic profit depending on your catalyst buying price

I calculated the exact multinomial distribution for all possible outcomes across 50 crafts.

| Average catalyst cost | Total investment | Expected profit | Modeled loss probability |
|---:|---:|---:|---:|
| 67.93k | 5.915m | **1.526m** | 0.10% |
| 75k | 6.268m | **1.172m** | 0.78% |
| 80k | 6.518m | **922k** | 2.77% |
| 90k | 7.018m | 422k | 16.61% |
| 98.45k | 7.440m | Break-even EV | — |

These loss probabilities assume our provisional 75/20/5 distribution is correct, outcomes are independent, and selling prices remain unchanged. Actual risk is higher if those assumptions are wrong.

## 7. Track your actual 50-craft results

[Interactive tracker omitted.]

Your 50 crafts would increase our existing community dataset from 30 to 80 observations. That would be extremely useful for improving our probability estimates.

**Before buying all 50 catalysts, check the [Intermediate selling price](https://henefm.com/items/2040813?back=/shops/cooperm).** The accessible Intermediate snapshot was stale, unlike the more recent Greater and Chaos snapshots. I'd want Intermediate selling around 190k and catalysts averaging no more than 75k.

[50-craft calculations saved to GitHub](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/scrolling-ev/CATALYST_RESEARCH.md).

## Earlier assistant reply backfill: "do the 50 craft calculation for all the other profitable items."

# 50-craft profitability comparison

**Shoes Jump remains the most profitable per catalyst, but Gloves Crit Rate and Shoes Speed are easier to sell in bulk.**

I refreshed the accessible HeneFM prices. Shoes Jump Intermediate has dropped from 186.35k to approximately 169.47k using our three-price valuation method.

## 1. Expected profit for 50 crafts each

[Rendered chart omitted.]

| 50 crafts | Investment | Net revenue | Net profit |
|---|---:|---:|---:|
| **Shoes Jump** | 4.042m | 6.208m | **2.166m** |
| Gloves Crit Rate | 5.915m | 7.440m | **1.526m** |
| Shoes Speed | 4.191m | 4.872m | **681k** |
| Earring LUK | 5.144m | 5.726m | **582k** |

Assumptions: 67.93k average catalyst cost, 3% selling fee, 75% Intermediate / 20% Greater / 5% Chaos production. The catalyst's current HeneFM snapshot shows a 64k lowest listing, 69.8k average sale and 70k sample median.

## 2. Exact shopping lists

All three recipes are significantly less material-intensive than Gloves Crit Rate, which requires 2,250 magic fragments per 50 crafts.

| Material | Shoes Jump | Shoes Speed | Earring LUK |
|---|---:|---:|---:|
| Arcforge required | Lv. 6 | Lv. 6 | Lv. 8 |
| Aquamarine | 150 | — | — |
| Amethyst | — | 150 | — |
| Black Crystal | — | — | 150 |
| Fragment of Magic | 500 | 500 | 500 |
| Processed Parchment | 50 | 50 | 50 |
| Scroll Crafting Catalyst | 50 | 50 | 50 |
| Crafting fees | 500k | 500k | 1m |

Recipes verified against current crafting data.

### Total material cost breakdown

| Expense | Jump | Speed | LUK |
|---|---:|---:|---:|
| Raw ores | 12.6k | 42k | 465k |
| Refining fees | 30k | 150k | 180k |
| Magic Fragments | 77.35k | 77.35k | 77.35k |
| Parchment | 25k | 25k | 25k |
| Catalysts | 3.397m | 3.397m | 3.397m |
| Crafting fees | 500k | 500k | 1m |
| **Total** | **4.042m** | **4.191m** | **5.144m** |

Material costs use our previous HeneFM estimates; catalyst and major output prices were rechecked.

## 3. Expected scroll production

Each batch of 50 produces the following expected distribution:

| Output | Expected quantity | Jump price | Speed price | LUK price |
|---|---:|---:|---:|---:|
| Intermediate | 37.5 | 169.47k | 130.17k | 127.30k |
| Greater | 10 | 4.5k | 6.7k | 33.63k |
| Chaos | 2.5 | Unverified | 29.6k | 317.33k |

Shoes Jump Chaos contributes zero revenue in this conservative model because its price remains unverified. Its production probability remains 5%.

## 4. Profit depending on catalyst acquisition price

| Catalyst cost | Shoes Jump | Shoes Speed | Earring LUK |
|---|---:|---:|---:|
| **67.93k** | **+2.166m** | +681k | +582k |
| 75k | **+1.813m** | +327k | +229k |
| 80k | **+1.563m** | +77k | −21k |
| 90k | **+1.063m** | −423k | −521k |
| Break-even catalyst price | **111.26k** | 81.54k | 79.58k |

Shoes Jump is much more resilient to rising catalyst prices.

## 5. Probability of losing money on 50 crafts

Calculated using the exact multinomial distribution.

| Average catalyst cost | Shoes Jump | Shoes Speed | Earring LUK |
|---|---:|---:|---:|
| 67.93k | 0.003% | 3.03% | 6.43% |
| 75k | 0.037% | 17.62% | 29.16% |
| 80k | 0.102% | 39.21% | 55.77% |
| 90k | 1.43% | 88.95% | 89.16% |

These are modeled crafting-outcome risks, not total business risks. They exclude changing prices, unsold inventory and uncertainty in the actual catalyst probabilities.

## 6. The biggest problem: liquidity

[Rendered chart omitted.]

Producing 38 Intermediate Shoes Jump scrolls would introduce nearly **four days of currently observed market demand**.

That's why I wouldn't put all 50 catalysts into Shoes Jump, despite its outstanding theoretical ROI.

## 7. My recommended allocation of 50 catalysts

| Recipe | Crafts | Investment | Expected profit |
|---|---:|---:|---:|
| Shoes Jump | 15 | 1.212m | 650k |
| Gloves Crit Rate | 35 | 4.140m | 1.068m |
| **Total** | **50** | **5.352m** | **1.718m** |

**Expected ROI: 32.1%.**

This balances high profit per catalyst with better market liquidity. It assumes you have unlocked Arcforge level 9.

## 8. Interactive batch planner

[Interactive planner omitted.]

## 9. Direct market links

| Item | HeneFM |
|---|---|
| Catalysts | [Buy](https://henefm.com/items/4130003) |
| Magic Fragments | [Buy](https://henefm.com/items/4000063) |
| Processed Parchment | [Buy](https://henefm.com/items/4003009) |
| Shoes Jump Intermediate | [Check price](https://henefm.com/items/2040701) |
| Shoes Speed Intermediate | [Check price](https://henefm.com/items/2040705) |
| Earring LUK Intermediate | [Check price](https://henefm.com/items/2040313) |
| Gloves Crit Rate Intermediate | [Check price](https://henefm.com/items/2040813) |

All calculations have been saved to [our GitHub catalyst research](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/scrolling-ev/CATALYST_RESEARCH.md), commit `2470242`.

## Earlier assistant reply backfill: "find out average time to offload those scrolls if listed at fm lowest"

# Estimated time to sell 50 crafted scrolls at FM lowest

I checked HeneFM's individual shop histories, including how long listings were open before selling, rather than relying solely on daily sales volume.

**Shoes Speed offers the fastest modeled full-batch liquidation. Gloves Crit Rate offers the highest profit, but takes longer to unload in bulk.**

## 1. Estimated batch clearance time

Assuming 50 crafts per recipe, producing an expected 37.5 Intermediate, 10 Greater and 2.5 Chaos scrolls.

| Recipe | 50% of market demand captured | 25% captured |
|---|---:|---:|
| Shoes Speed | **5.9 hours** | 11.9 hours |
| Earring LUK | 13.3 hours | 26.7 hours |
| Gloves Crit Rate | 20 hours | 40 hours |

These are conditional sell-through estimates, not measured averages. Matching the lowest FM price does not guarantee that your shop captures 25% or 50% of buyers.

## 2. Latest HeneFM market data

| Scroll | FM lowest | Daily sales | Current stock |
|---|---:|---:|---:|
| Gloves Crit Intermediate | 185k | 90 | 73 |
| Gloves Crit Greater | 30k | 97 | 76 |
| Gloves Crit Chaos | 50k | 553 | 187 |
| Shoes Speed Intermediate | 125k | 303 | 107 |
| Shoes Speed Greater | 4.8k | 1,005 | 687 |
| Shoes Speed Chaos | 27.8k | 390 | 128 |
| Earring LUK Intermediate | 120k | 591 | 550 |
| Earring LUK Greater | 30k | 291 | 135 |
| Earring LUK Chaos | 310k | **9** | 2 |

## 3. Actual observed time to sell

These are real examples from HeneFM shop histories, at or near the lowest observed price.

| Scroll | Sale price | Time listed |
|---|---:|---:|
| Gloves Crit Intermediate | 185k | 18 min |
| Gloves Crit Intermediate | 181k | 50 min |
| Shoes Speed Intermediate | 125k | 0 min* |
| Shoes Speed Intermediate | 125k | 68 min |
| Shoes Speed Intermediate | 120k | 38 min |
| Earring LUK Intermediate | 120k | 22 min |
| Earring LUK Intermediate | 124k | 37 min |
| Earring LUK Chaos | 300k | 21 min |
| Earring LUK Chaos | 315k | 0 min* |
| Earring LUK Chaos | 320k | 19h 44m |

*Zero minutes means HeneFM recorded no elapsed time between observations, not necessarily an instantaneous sale.

The small sample of successfully sold Intermediate listings averages approximately 34 minutes for Gloves Crit, 35 minutes for Shoes Speed and 30 minutes for Earring LUK. This is not a representative market-wide mean because it excludes unsold listings.

A particularly relevant example is [Pangio's shop](https://henefm.com/shops/Pangio): it still had 22 Gloves Crit Intermediate scrolls at 188.9k after nearly four hours of listing.

Bulk selling clearly requires more time than selling individual scrolls.

## 4. Profit when selling at FM lowest

Our earlier EV used representative market prices. Selling at the absolute lowest reduces profit but should improve liquidity.

| 50 crafts | Normal EV profit | FM lowest profit | ROI at lowest |
|---|---:|---:|---:|
| **Gloves Crit Rate** | 1.526m | **1.227m** | **20.7%** |
| Shoes Speed | 681k | **470k** | 11.2% |
| Earring LUK | 582k | **264k** | 5.1% |

Includes all previous crafting expenses and the 3% selling fee.

## 5. Best recipe for repeatedly reinvesting capital

[Interactive calculator omitted.]

**My recommendation:**
- Highest total profit: Gloves Crit Rate.
- Fastest capital turnover: Shoes Speed.
- Least attractive at FM lowest: Earring LUK, especially because Chaos has relatively few buyers.

[Research and liquidation methodology saved to GitHub](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/scrolling-ev/CATALYST_RESEARCH.md).
