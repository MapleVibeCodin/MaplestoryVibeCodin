# Fresh market analysis responses — 2026-11-25

Archive metadata: manually copied original assistant response prose and Markdown tables following the three user-pasted HeneFM market snapshots, in order. User-provided recent-sale rows are in 2026-11-25-henefm-sales-excerpts.txt. Interactive UI, citation widgets and tool records excluded; omissions are labeled. This is not a full conversation export.

## Assistant response to Gloves Crit Rate market snapshot

This fresh HeneFM data is particularly useful because **Pangio is already selling the exact scrolls we intend to manufacture in bulk.** We can use his actual sales as a benchmark rather than relying entirely on market-wide demand.

## 1. Updated Gloves Crit prices

I calculated the quantity-weighted median of the 25 visible sold units for each tier.

| Scroll | Lowest | 24h average | Sample median | Our representative price |
|---|---:|---:|---:|---:|
| Lesser | 50k | 59k | 56.8k | **55.27k** |
| Intermediate | 185k | 191.7k | 190k | **188.90k** |
| Greater | 20k | 32.9k | 32.2k | **28.37k** |
| Chaos | 50k | 55.4k | 55k | **53.47k** |

The 20k Greater listing is a single scroll. The next four cheapest listings are all 30k, making 29.9–30k a more reasonable bulk selling price.

## 2. Updated 50-craft EV

Using our established 75/20/5 production model, 67.93k catalyst price, 50.36k base crafting cost and 3% selling fee.

[Rendered summary cards omitted.]

| Selling strategy | Intermediate | Greater | Chaos | Expected profit |
|---|---:|---:|---:|---:|
| Representative prices | 188.9k | 28.37k | 53.47k | **1.361m** |
| Strict FM lowest | 185k | 20k | 50k | 1.130m |
| Competitive bulk prices | 185k | 30k | 50k | **1.227m** |
| Pangio-style pricing | 188.9k | 30k | 55k | **1.381m** |

There is little reason to price all ten expected Greater scrolls at 20k because of one unusually cheap competitor.

## 3. Pangio's actual selling speed

Pangio has 13 Intermediate scrolls remaining at 188.9k.

His recorded sales:

| Time before your snapshot | Price |
|---|---:|
| 2h 21m | 188.9k |
| 1h 43m | 188.9k |
| 1h 22m | 188.9k |
| 1m | 188.9k |

That's approximately **one sale every 47 minutes** between observed transactions, without being the cheapest seller.

Extrapolating his observed sales pace, it would take approximately **22–29 hours** to sell 38 Intermediate scrolls.

## 4. Expected liquidation time at FM lowest

| Demand captured | Intermediate | Greater | Chaos | Entire batch |
|---|---:|---:|---:|---:|
| 25% | 39.6h | 9.9h | 26 min | 39.6h |
| 50% | 19.8h | 4.9h | 13 min | 19.8h |
| 75% | 13.2h | 3.3h | 9 min | 13.2h |
| 100% | 9.9h | 2.5h | 7 min | 9.9h |

These are modeled scenarios, not guaranteed selling times.

**I would budget approximately 20–30 hours for the entire batch**, based on Pangio's observed selling pace. Maintaining the lowest price could improve that.

## 5. What about crafting without catalysts?

Your fresh Lesser price data also shows a small guaranteed-output arbitrage.

| 50 Lesser crafts | Amount |
|---|---:|
| Production cost | 2.518m |
| Representative selling price | 55.27k |
| Revenue after fees | 2.680m |
| **Expected profit** | **162k** |
| ROI | 6.45% |

However, at the current FM lowest of 50k, normal crafting is unprofitable.

## 6. Updated maximum catalyst purchase price

| Target | Maximum catalyst price |
|---|---:|
| Break-even at representative prices | 95.16k |
| Break-even at strict FM lowest | 90.53k |
| Earn 1m per 50 crafts at competitive bulk prices | **72.47k** |
| Earn 500k per 50 crafts at competitive bulk prices | 82.47k |

**My preferred execution prices:**

- Buy catalysts: 70k or below.
- Sell Intermediate: 184.9k.
- Sell Greater: 29.9k.
- Sell Chaos: 49.9k.

At these prices, 50 crafts generate approximately **1.119m expected profit**, using our provisional probability distribution.

The freshest output prices are now incorporated, but material and catalyst acquisition costs still use our earlier HeneFM estimates.

[Updated calculations saved to GitHub](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/scrolling-ev/CATALYST_RESEARCH.md). Commit `44be81d`.

## Assistant response to Earring LUK market snapshot

# Updated Earring LUK crafting analysis

Your fresh HeneFM data confirms that **Earring LUK is significantly more liquid than Gloves Crit Rate for Intermediate scrolls, but much less profitable when selling at FM lowest.**

## 1. Updated representative prices

Using our established formula: (lowest + 24h average + sample median) ÷ 3.

| Scroll | Lowest | Average | Median | Representative |
|---|---:|---:|---:|---:|
| Lesser | 38k | 39.3k | 39k | **38.77k** |
| Intermediate | 120k | 131.7k | 129k | **126.90k** |
| Greater | 30k | 35.9k | 35k | **33.63k** |
| Chaos | 310k | 322k | 320k | **317.33k** |

The sample medians use 25 recent sold units for Lesser, Intermediate and Greater, and all nine sales within 24 hours for Chaos.

## 2. Updated 50-craft profitability

Using 67.93k per catalyst, 34.95k regular recipe cost, 75/20/5 probabilities and a 3% selling fee.

[Rendered summary cards omitted.]

| Selling strategy | Intermediate | Greater | Chaos | Expected profit | Modeled loss risk |
|---|---:|---:|---:|---:|---:|
| Representative | 126.9k | 33.63k | 317.33k | **568k** | 6.43% |
| Competitive bulk | 124.9k | 32.9k | 309.9k | **470k** | 10.16% |
| FM lowest | 120k | 30k | 310k | 264k | 27.95% |
| Undercut lowest | 119.9k | 29.9k | 309.9k | 259k | 27.95% |

I prefer the competitive bulk prices. There are only two Intermediate scrolls at 120k before the price jumps to 125k, so pricing all 38 expected Intermediate scrolls at 120k unnecessarily sacrifices revenue.

## 3. How quickly can you sell 50 crafted scrolls?

| Scroll | Daily sales | FM stock | Expected production |
|---|---:|---:|---:|
| Intermediate | **593** | 541 | 37.5 |
| Greater | **293** | 134 | 10 |
| Chaos | 9 | **2** | 2.5 |
| Lesser | 96 | 503 | — |

The Intermediate market is extremely active: your snapshot shows 25 sales within just 33 minutes.

### Estimated liquidation time at FM lowest

| Scroll | Capturing 25% of demand | Capturing 50% |
|---|---:|---:|
| Intermediate | 6h 4m | **3h 2m** |
| Greater | 3h 17m | **1h 38m** |
| Chaos | 26h 40m | 13h 20m |

Chaos is the bottleneck, but Intermediate and Greater sales should recover most of your capital considerably earlier.

At FM lowest, expected revenue from Intermediate and Greater alone is **4.656m after fees**, leaving approximately 488k of your initial investment to recover from Chaos sales.

## 4. Direct comparison with Gloves Crit Rate

Both calculations now use your freshly pasted HeneFM data.

| Metric | Gloves Crit Rate | Earring LUK |
|---|---:|---:|
| Investment | 5.915m | **5.144m** |
| Representative EV profit | **1.361m** | 568k |
| FM lowest profit | **1.130m** | 264k |
| Representative ROI | **23.0%** | 11.0% |
| Loss risk at FM lowest | **1.11%** | 27.95% |
| Intermediate daily sales | 91 | **593** |
| Intermediate clearance at 50% demand | 19.8h | **3.0h** |
| Break-even catalyst price at lowest | **90.53k** | 73.21k |

## 5. Sensitivity to Chaos production probability

Expected profit from 50 crafts at representative prices:

[Rendered chart omitted.]

Earring LUK becomes significantly more attractive if the actual Chaos production rate exceeds our 5% assumption. There is still a **7.69% probability of producing zero Chaos scrolls in 50 crafts** under that model.

## 6. Maximum catalyst purchase price

| Catalyst price | Representative profit | FM lowest profit |
|---|---:|---:|
| 60k | 964k | 660k |
| 65k | 714k | 410k |
| 70k | 464k | 160k |
| 75k | 214k | −90k |
| 80k | −36k | −340k |

**I would only craft Earring LUK with catalysts purchased at 65k or below** if rapid liquidation is the objective.

Gloves Crit Rate remains the stronger profit opportunity. Earring LUK is better for quickly recovering most of your capital, but its dependence on Chaos production adds risk.

All calculations use your new output prices and our previously established material costs. Liquidation times are conditional estimates, not measured average selling times.

[Updated research saved to GitHub](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/scrolling-ev/CATALYST_RESEARCH.md) — commit `93598c7`.

## Assistant response to Shoes Speed market snapshot

# Updated Shoes Speed crafting analysis

With your latest HeneFM data, we now have comparable fresh snapshots for all three recipes.

**Shoes Speed is the strongest candidate for rapid capital turnover.** Its Intermediate scrolls have relatively low inventory, strong daily demand, and both secondary outputs are easy to liquidate.

## 1. Updated representative prices

| Scroll | Lowest | 24h average | Sample median | Representative |
|---|---:|---:|---:|---:|
| Lesser | 14.4k | 15.6k | 16.5k | **15.50k** |
| Intermediate | 125k | 130.4k | 130k | **128.47k** |
| Greater | 4.8k | 7.5k | 7k | **6.43k** |
| Chaos | 27.8k | 31k | 30k | **29.60k** |

Calculated using the 25 most recent sold units for each tier, with duplicate pasted pages excluded.

## 2. Expected profit from 50 crafts

Using our existing material costs, 67.93k per catalyst, 75/20/5 production probabilities and 3% selling fees.

[Rendered summary cards omitted.]

| Selling strategy | Intermediate | Greater | Chaos | Profit | Modeled loss risk |
|---|---:|---:|---:|---:|---:|
| Representative | 128.47k | 6.43k | 29.6k | **616k** | 4.76% |
| Competitive bulk | 127.9k | 6.9k | 28.9k | **598k** | 4.76% |
| FM lowest | 125k | 4.8k | 27.8k | 470k | 8.79% |
| Undercut lowest | 124.9k | 4.7k | 27.7k | 465k | 9.37% |

Competitive bulk pricing is particularly attractive here. There is only one Intermediate at 125k and one at 128k before most sellers begin at 130k.

## 3. Estimated time to offload 50 crafts

| Scroll | Daily sales | Current stock | Expected production |
|---|---:|---:|---:|
| Intermediate | 307 | 105 | 37.5 |
| Greater | **1,007** | 633 | 10 |
| Chaos | 388 | 129 | 2.5 |

| Scroll | Capturing 25% of demand | Capturing 50% |
|---|---:|---:|
| Intermediate | 11h 44m | **5h 52m** |
| Greater | 57 min | 29 min |
| Chaos | 37 min | 19 min |

The Intermediate tier determines how quickly you can reinvest your capital.

SinZilla recorded three Intermediate sales at 130k within 67 minutes, with nine remaining. This demonstrates demand even above FM lowest, although it does not establish the average selling time for an entire batch.

## 4. Final comparison — all three updated

Using your freshly pasted HeneFM data for every output.

| Metric | Gloves Crit | Shoes Speed | Earring LUK |
|---|---:|---:|---:|
| Investment | 5.915m | **4.191m** | 5.144m |
| Representative profit | **1.361m** | 616k | 568k |
| FM lowest profit | **1.130m** | 470k | 264k |
| Representative ROI | **23.0%** | 14.7% | 11.0% |
| FM lowest ROI | **19.1%** | 11.2% | 5.1% |
| FM lowest loss risk | **1.11%** | 8.79% | 27.95% |
| Intermediate daily sales | 91 | 307 | **593** |
| Intermediate stock | 62 | 105 | 541 |
| Full batch clearance* | 19.8h | **5.9h** | 13.3h |

*Assuming 50% market demand capture.

## 5. Expected profit per liquidation hour

[Rendered chart omitted.]

## 6. Catalyst price sensitivity

Profit per 50 crafts when selling at representative prices:

| Catalyst cost | Gloves Crit | Shoes Speed | Earring LUK |
|---|---:|---:|---:|
| 60k | **1.758m** | 1.013m | 964k |
| 65k | **1.508m** | 763k | 714k |
| 70k | **1.258m** | 513k | 464k |
| 75k | **1.008m** | 263k | 214k |
| 80k | **758k** | 13k | −36k |
| Break-even | **95.16k** | 80.26k | 79.29k |

## 7. Optimal allocation calculator

[Interactive calculator omitted.]

## My preferred strategy

For your first 50 catalysts, I'd split them evenly:

| Recipe | Crafts | Profit at FM lowest |
|---|---:|---:|
| Gloves Crit Rate | 25 | 565k |
| Shoes Speed | 25 | 235k |
| **Total** | **50** | **800k** |

Investment: **5.053m**. Modeled clearance: approximately **9.9 hours** at 50% demand capture.

This balances profitability and capital turnover without relying heavily on rare Chaos outcomes.

All three updated datasets are now [saved to GitHub](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/scrolling-ev/CATALYST_RESEARCH.md). Input material costs remain from earlier snapshots, and the actual catalyst probabilities and market capture rates remain unverified.
