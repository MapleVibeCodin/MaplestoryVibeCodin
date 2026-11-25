# Fixed Pansy base assumption and updated status — 2026-11-25

## User

ok until otherwise speificed, always use base pansy earrings costing 30k. easy to save. update memory and update github and give me summary of where we're at

## Assistant

**New permanent assumption: clean Pansy Earrings cost 30,000 mesos each**, until you specify otherwise. We'll use the 3% natural crit damage, five-unused-slot variant as our standard base and stop refreshing its price for every calculation.

## 1. Current earring optimization inputs

| Item | Cost | Success | Stat gain |
|---|---:|---:|---:|
| Pansy Earrings | **30,000** | — | 3% CD |
| Self-crafted Lesser | 34,780 | 100% | +1 |
| Purchased Lesser | 38,500 | 100% | +1 |
| DEX Intermediate | 90,000 | 60% | +2 |
| DEX Greater | 20,000 | 10% | +3 |
| LUK Chaos | 310,000 | 10% | +4 |

Scroll and ingredient prices are carried forward from our last HeneFM research, not freshly retrieved.

## 2. Updated optimization — 1 million mesos

I've rerun our hard-budget model using the new 30k base price.

| | |
|---|---:|
| Expected added effective LUK | +7.67 |
| Chance of +8 or better | 63.69% |
| Chance of +10 or better | 19.25% |
| Expected expenditure | 963,986 |

| Method | Expected added stat |
|---|---:|
| Buy all scrolls | +7.655 |
| Craft cheaper Lesser scrolls | **+7.673** |
| Guaranteed five Lesser scrolls | +5 |

The guaranteed +5 route costs **203,900 mesos**.

## 3. Important strategy change

With the base price increased to 30k, the optimal opening scroll changes from Greater to Intermediate.

Clean Pansy — 30k

Apply Intermediate — 90k

Success (60%): +2 stat, 4 slots left. Apply another Intermediate.

Failure (40%): +0 stat, 4 slots left. Apply Greater.

Don't automatically discard the first failed base anymore. Further actions depend on remaining budget, slots and your best retained earring.

## 4. Where we stand

- Earrings: fixed 30k Pansy base, 1m hard budget, self-scroll only, all other equipment clean.
- Scroll sourcing: buy Intermediate/Greater, craft Lesser when cheaper. DEX and LUK are equivalent only when DEX can replace base AP.
- Catalyst experiment: 12 Shoes Speed crafts yielded 9 Intermediate, 2 Greater, 1 Chaos; projected profit 79,520, not realized. Retain provisional 75/20/5 model.
- Pricing: HeneFM only. The normal-ChatGPT clipboard workflow works; direct automatic retrieval remains unresolved.

The latest model assumes repeatable prices, rounds costs up to the nearest 1k for the budget calculation, and predicts added stats rather than verified character damage. The modeled chance of finishing below +5 is 2.05%.

[Post-save verification notice omitted.]

## Archive note

Visible wording reconstructed with cards/diagram flattened; no secrets or raw market payloads. Research commit eb40d6118b54de1821c1f92ce3aa24af44e216b1.
