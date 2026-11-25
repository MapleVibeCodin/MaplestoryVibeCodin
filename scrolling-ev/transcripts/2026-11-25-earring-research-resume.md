# Earring research resumed — 2026-11-25

## User

ok now lets get back to our original question of making earrings the best for my level 50 character. pull up all the data from github on previous comversation

## Assistant

I've recovered our original earring optimization research from GitHub. We were solving a very specific problem: **maximize your level 50 Assassin's damage through self-made earrings with a hard budget of 1 million mesos.**

## 1. Original constraints

- All other equipment remains clean.
- Only the earring slot receives upgrades.
- No buying partially scrolled or finished earrings.
- DEX and LUK are equivalent when DEX replaces base AP that can be reassigned to LUK.
- No AP reset expense.
- Compare self-crafted scrolls against purchased scrolls.
- Use HeneFM exclusively for market prices.
- Optimize the actual outcome within the 1m budget, not just an unlimited-budget expected cost.

[Original research handoff](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/scrolling-ev/RESEARCH_HANDOFF.md)

## 2. Previously researched scroll prices

These are the saved November 25 price observations, not newly refreshed quotes.

| Scroll tier | Success | Stat gain | DEX | LUK |
|---|---:|---:|---:|---:|
| Lesser | 100% | +1 | 38.5k | 38k |
| Intermediate | 60% | +2 | 95k | 120k |
| Greater | 10% | +3 | 18k | 30k |
| Chaos | 10% | +4 | Unavailable | 310k |

The Chaos model also includes a 45% unconditional destruction probability.

Our previous approach was to buy the cheapest equivalent DEX or LUK scroll at each tier, rather than restrict ourselves to LUK scrolls.

## 3. Top three clean earrings

**Pansy Earrings**

Best modeled combat damage

3% natural crit damage · 5 slots

15,000 mesos

**Star Earrings**

Best expected raw stat gain

2% natural crit damage · 5 slots

4,000 mesos

**Emerald Earrings**

Alternative inexpensive base

2% natural crit damage · 5 slots

5,000 mesos

We also investigated higher natural crit damage variants, but the historical prices were significantly more expensive: 165k for 3% Emerald and 250k for 4% Pansy.

## 4. Best self-scrolling results under 1m

Our last hard-budget optimization included all four scroll tiers, fresh-base retries, retaining the best earring, and crafting cheaper Lesser scrolls.

| Base | Expected added effective LUK | Modeled average Lucky Seven cast damage |
|---|---:|---:|
| Pansy 3% CD | 8.004 | **1,199.063** |
| Star 2% CD | **8.427** | 1,198.487 |
| Emerald 2% CD | 8.384 | 1,198.326 |

The difference in expected damage is extremely small. Pansy won in the historical model because its additional natural crit damage compensated for its slightly lower expected LUK gain.

These are previously calculated expectations, not guaranteed outcomes or independently verified in-game damage measurements.

## 5. Making our own scrolls

The saved Arcforge level 8 recipe for Earring DEX/LUK Lesser is:

| Ingredient | Quantity | Previous cost |
|---|---:|---:|
| Black Crystal Ore | 3 | 9,000 |
| Refining fees | 3 | 3,600 |
| Fragment of Magic | 10 | 1,690 |
| Processed Parchment | 1 | 488 |
| Crafting fee | — | 20,000 |
| **Total** | | **34,778** |

Using five self-crafted Lesser scrolls on a 15k Pansy gives a guaranteed +5 stat earring for **188,890 mesos**.

## 6. What our new catalyst experiment adds

We now have more empirical evidence than when we originally calculated the earring strategy.

[Chart flattened: Intermediate community 80%, our batch 75%; Greater community 20%, our batch 16.67%; Chaos community 0%, our batch 8.33%.]

Community sample: 30 reported crafts. Our Shoes Speed sample: 12 crafts.

Combining both samples descriptively gives 33 Intermediate, 8 Greater and 1 Chaos across 42 crafts. However, these are different recipes and small samples, so I would retain our provisional 75/20/5 probability model for now.

## 7. Where we left off

The next optimization should compare three routes: buying scrolls directly, crafting guaranteed Lesser scrolls, and catalyst-assisted production with random outputs.

My starting choice remains **clean 3% crit damage Pansy Earrings**, assuming the earlier price is still available. The 1m cap remains a hard constraint.

The existing JavaScript optimizer is v1.0 and implements expected renewal cost, not the full hard-budget AP-aware model. Our previous hard-budget results are documented separately; the original standalone step-by-step earring HTML guide was not located in the repository. I have not rerun the optimizer or refreshed the market prices in this retrieval turn.

[Post-save verification notice omitted.]
