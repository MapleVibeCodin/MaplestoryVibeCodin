# Catalyst inventory and range-target rerun — 2026-11-25

## User

great. now run the test again with all the variables and use github to refresh all knowledge up to right now

## Assistant

## Latest result: catalyst crafting barely improves your earrings

I've reloaded the latest GitHub research and rerun the model with NPC recovery, self-crafted Lesser scrolls, and your fixed **75% Intermediate / 20% Greater / 5% Chaos** catalyst production rates.

The new model allows you to observe a crafted scroll's tier, hold it for a later earring, apply it, or—in a separate scenario—sell it and reuse the proceeds.

| | |
|---|---:|
| Starting capital | 1,000,000 |
| Fixed Pansy base | 30,000 |
| NPC recovery | 13,500 |
| Catalyst-assisted craft | 99,779 |

## 1. Scrolling strategy comparison

| Strategy | Expected added LUK equivalent | Expected maximum range increase* |
|---|---:|---:|
| Adaptive scrolling with NPC recovery | 7.9252 | +10.501 |
| Add catalyst crafting for personal use | 7.9252 | +10.501 |
| Add catalyst crafting and immediate FM resale | **7.9371** | **+10.517** |

*Using our illustrative 53 total weapon attack build. Catalyst model permits up to two crafts, holding one unused crafted scroll at a time.*

Even under favorable assumptions for resale, adding catalysts improves the expected maximum range by only approximately **0.016**.

For making your own earring, buying the appropriate scroll directly remains substantially simpler, with essentially the same modeled result.

## 2. Top three targets with catalyst crafting included

Each row uses a separate policy optimized specifically for that target.

| Target | Added max range | Without catalysts | Craft for self-use | Craft + sell outputs |
|---|---:|---:|---:|---:|
| **+8** | **+10.60** | 78.46% | 78.46% | 78.78% |
| +9 | +11.93 | 57.59% | 57.59% | 58.23% |
| +10 | +13.25 | 33.29% | 33.30% | 33.75% |

The catalyst resale column assumes completed sales at our previous prices, with the 3% fee deducted. It is not guaranteed immediate liquidity.

I also extended the resale model to allow up to five catalyst crafts. The expected added stat increases to **7.949**, or approximately +10.53 maximum range. Still not a meaningful improvement over buying scrolls.

## 3. Why crafting with catalysts isn't better

| Catalyst output | Probability | Replacement purchase cost |
|---|---:|---:|
| Intermediate | 75% | 90,000 |
| Greater | 20% | 18,888 |
| Chaos | 5% | 310,000 |

The expected replacement value is only **86,778 mesos**, versus the crafting cost of 99,779. That is a disadvantage of approximately 13k per craft for personal use.

LUK scrolls can sell at a premium over DEX scrolls, which explains the slight advantage when resale is permitted.

## 4. Other improvements tested

| Method | Result |
|---|---|
| Cheaper STR Greater scrolls | Negligible improvement |
| INT, Evasion and Crit Damage | No displayed range increase |
| NPC failed earrings | Significant improvement |
| FM resale of failed four-slot earrings | Potentially better than NPC |
| Retaining the best finished earring | Included |
| Self-crafted 100% Lesser scrolls | Included |

I found STR Greater listings around 13.3–14k on HeneFM. Even at 14k, allowing these as secondary-stat fillers improved the expected maximum range by less than 0.001 in a separate mixed-stat calculation.

## 5. FM resale is a more promising opportunity

We previously found a failed four-slot Pansy selling for 20k. If you can consistently sell such earrings for that amount and reinvest the proceeds, the model improves more than catalyst crafting does.

[Chart flattened: +8 NPC 78.46%, conditional FM 81.88%; +9 NPC 57.59%, conditional FM 61.40%; +10 NPC 33.29%, conditional FM 36.01%.]

This scenario uses 19k net recovery for failed four-slot bases after conservatively rounding down the 19.4k proceeds. It assumes sales settle before additional attempts.

## 6. The actual strategy I would use

Start by buying one clean Pansy and applying DEX Greater.

**Pansy 30k + Greater 18,888**

**Success:** +3 stat, 4 slots. Apply Intermediate.

**Failure:** Recover 13.5k. NPC and restart.

The new calculation establishes a useful stopping point: under the maximum-expected-range policy, after **14 consecutive failed openers**, with approximately 503k remaining in the rounded model, switch to a 60% opener instead of continuing to gamble.

**My recommendation remains to target +8 effective LUK**, purchase Greater and Intermediate scrolls, craft Lesser when needed, and avoid spending significant capital on catalysts for this particular objective.

## Limitations

This is the most comprehensive comparison so far, not a proof of the unrestricted global optimum. Catalyst inventory is limited to one held scroll at a time; STR and FM failed-base recovery were tested separately rather than jointly with catalysts. Prices are the latest recorded HeneFM inputs, not a fresh synchronized private API scan. NPC value after scrolling, market depth and DEX conversion remain assumptions. The 53 attack range example is illustrative, not a measured character stat.

[Post-save verification notice omitted.]

## Archive note

User-visible prose and data reproduced; rendered components and citations flattened. Research commit 49c4a6f8cbd986c852ae891f9414104c0cdb3efb. No raw provider responses or secrets.
