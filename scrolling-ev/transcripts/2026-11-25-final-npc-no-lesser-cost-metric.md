# Latest standing constraints, cost questions and chat-switch exchange — 2026-11-25

This archive backfills accessible user-visible wording since the catalyst inventory rerun. The intervening 100-base simulation exchange is already preserved in [triple Greater experiment](2026-11-25-triple-greater-100.md). Rendered components are flattened. No raw private provider payloads or credentials.

## User

no need to explore the npc vs resell. always NPC 4 slot failed scroll earrings.

## Assistant

**Permanent rule: always NPC Pansy Earrings after a failed first scroll, leaving four slots and zero added stats.**

- Fixed clean Pansy cost: 30,000
- NPC recovery: 13,500
- Greater scroll: 18,888
- Net failed attempt cost: **35,388 mesos**

Exclude FM resale of these failed earrings from all future optimizations. No waiting for buyers or repricing.

[Updated GitHub and verified the permanent rule](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/commit/0d2fa0ff053475cf62d1e90d3951e82f64603901).

Future calculations will enforce this as a **hard constraint**, not an optional strategy.

## Intervening exchange

See [100-base triple Greater experiment](2026-11-25-triple-greater-100.md).

## User

how much did that cost?

## Assistant

**3,949,008 mesos net** for the entire 100-earring simulation.

| Expense | Cost |
|---|---:|
| 100 Pansy Earrings | 3,000,000 |
| 116 Greater scrolls | 2,191,008 |
| NPC recovery | −1,242,000 |
| **Total** | **3,949,008** |

You ended up with six +3 earrings and two +6 earrings, each with two slots remaining.

Finishing one +6 earring with two guaranteed Lesser scrolls brings the total expenditure to **4,018,568 mesos** for the batch, including one finished +8 earring.

## User

so this is much more expensive than other methods?

## Assistant

**Yes, significantly more expensive if your goal is one strong finished earring.** The problem is applying two additional 10% scrolls after the initial successful opener.

| Strategy | Expected cost | Outcome |
|---|---:|---|
| Five guaranteed 100% scrolls | 203,900 | +5 guaranteed |
| Successful 10% opener, then four 100% | 506,500 | +7 upon completion |
| Previous adaptive +8 target strategy | Budget of 1m | 78.46% chance of +8* |
| Triple 10% strategy — 100 bases | ~4.05m | Only 9.52% chance of producing a +9 with two slots left |

The second strategy is particularly attractive: once you land that first 10%, you can guarantee another four stats for just 139,120 mesos.

## Why the triple 10% strategy is inefficient

| Scroll | Expected stat gain per slot |
|---|---:|
| 100% Lesser | 1.0 |
| 60% Intermediate | **1.2** |
| 10% Greater | 0.3 |

The first 10% is worthwhile because you can NPC failures without sacrificing a successful earring. Subsequent 10% attempts consume valuable slots on an already successful base.

**Use 10% to establish a strong base, then use a mixture of 60% and 100% to finish it.**

*The previous 78.46% calculation allowed retaining some failed openers. It needs recalculation under your new mandatory NPC rule. All costs assume our previously recorded prices, and the +7 method's cost is an average, not a guaranteed spending cap.*

## User

what if i dont want to use 100%'s at all? Only part of the calculation due to that being baseline

## Assistant

**Absolutely. We'll use 100% Lesser scrolls strictly as a benchmark, never as an actual scrolling option.**

I've rerun the 1m budget model with:

- 30k Pansy base.
- 10% Greater, 60% Intermediate and 10% Chaos only.
- Mandatory NPC disposal of failed first-scroll earrings.
- 13.5k NPC recovery.
- Highest displayed damage range as the objective.

## New results without 100% scrolls

Expected added effective LUK: +7.70
Expected max range increase: +10.20
Expected expenditure: 943,623
Chance of +7 or better: 73.50%

## Top three targets

| Target | Added max range | Target-optimized success chance |
|---|---:|---:|
| +8 | +10.60 | **66.75%** |
| +9 | +11.93 | 49.73% |
| +10 | +13.25 | 25.86% |

Each target has its own optimized policy. Range figures use our previous illustrative 53 total weapon attack.

## User

great, can you also add the metric of cost per additional stat? such as +8 stat earring costing 800k = 100k per +1 stat

## Assistant

Yes. **Cost per additional stat will now be a standard metric in every scrolling calculation.** All failed attempts and NPC recoveries will be included in the net cost.

## Updated efficiency comparison

Using the new rule of no 100% scrolls and mandatory NPC disposal of failed openers:

| Strategy | Average net cost | Expected added stat | Cost per +1 stat |
|---|---:|---:|---:|
| 100% benchmark only | 203,900 | 5.00 | 40,780 |
| **Maximum expected range** | 943,623 | **7.70** | **122,524** |
| Target +8 | 945,117 | 6.77 | 139,574 |
| Target +9 | 941,026 | 5.76 | 163,300 |
| Target +10 | 959,497 | 4.43 | 216,673 |

These figures include unsuccessful runs, so they reflect the true long-run efficiency of each strategy.

## Cost efficiency when the target is achieved

| Target | Success chance | Average cost of successful runs | Cost per actual added stat* |
|---|---:|---:|---:|
| +8 or better | 66.75% | 931,299 | 107,077 |
| +9 or better | 49.73% | 910,736 | 95,028 |
| +10 or better | 25.86% | 924,760 | 91,886 |

*Conditional average expenditure divided by conditional average retained stat, including outcomes exceeding the target. Failed runs are excluded from this table only.*

The higher targets look cheaper per stat when they succeed, but their much higher failure rates make them considerably more expensive overall.

### Catalyst crafting impact

With 100% scrolls excluded, allowing up to two catalyst crafts for personal use changes expected added stats from 7.70156 to 7.70162. Still negligible.

### Permanent reporting metrics

Every future comparison will include total net cost, added stat, added damage range, cost per additional stat and target success probability.

The costs above use our previously recorded prices and the purchase-only scrolling model.

[Updated methodology and calculations saved and verified on GitHub](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/commit/c247f8202abfc765e45567739095918154c10182).

## User

awesome save all of this onto github and whats the command or paste into chat gpt for new chat?

## Assistant

## Copy and paste this into any new ChatGPT conversation

Resume from https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/checkpoints/LATEST.md. Read the latest project state, research files, methodology, and chronological conversation archives. Continue immediately using my latest rules and calculations. Newer instructions override older ones. Do not restart completed research. Preserve subsequent conversations word for word on GitHub and verify every checkpoint.

You can reuse this same prompt indefinitely. It points to the latest checkpoint rather than a specific historical version.

## Saved project state

- Pansy base: 30k; 1m budget; NPC failed four-slot openers immediately for assumed 13.5k.
- No 100% scroll applications; benchmark only.
- Catalyst production: fixed 75% Intermediate / 20% Greater / 5% Chaos.
- Highest displayed range objective; report net cost, added stat, added range, cost per stat and target probability.
- Latest expected-stat result: +7.70156, +10.20 illustrative maximum range, 943,623 expected net cost, 122,524 per retained stat.
- All accessible unsaved dialogue backfilled, with rendered UI flattened; earlier archives retained.

[Post-save verification metadata omitted.]

