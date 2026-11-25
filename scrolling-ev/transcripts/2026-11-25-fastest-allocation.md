# Fastest 20-catalyst allocation

## User

what about mesos per hour? fastest

## Assistant

**4 Gloves Crit Rate + 16 Shoes Speed** is the fastest allocation for your 20 catalysts.

I optimized all 231 possible combinations, accounting for actual integer crafting outcomes rather than just average scroll quantities.

| Allocation (Gloves / Speed / LUK) | Expected profit | Modeled clearance | Mesos/hour |
|---|---:|---:|---:|
| **4 / 16 / 0** | **241k** | **1.97h** | **122.3k** |
| 5 / 15 / 0 | 254k | 2.12h | 119.6k |
| 10 / 10 / 0 | 320k | 3.97h | 80.7k |
| 0 / 20 / 0 | 188k | 2.35h | 80.1k |
| 20 / 0 / 0 | 452k | 7.91h | 57.1k |
| 0 / 0 / 20 | 105k | 5.80h | 18.2k |

## Buy these materials

- 12 Black Crystals
- 48 Amethysts
- 340 Fragments of Magic
- 20 Processed Parchments
- 20 catalysts
- 280k crafting fees

**Total estimated investment: 1.814m.**

At FM lowest, list Gloves Crit Intermediate at 185k and Shoes Speed Intermediate at 125k, with Greater/Chaos at their respective lowest prices.

The 122.3k/hour figure assumes 50% of market demand captured, 67.93k catalysts, the previous HeneFM prices, a 3% selling fee and provisional 75/20/5 craft odds. At 25% capture it drops to 61.1k/hour. Including 30 minutes of procurement and crafting gives about 97.5k/hour at 50% capture. Modeled loss probability is 15.5%; neither selling speed nor profit is guaranteed.

If procurement and crafting take a full hour per batch, 5 Gloves Crit + 15 Shoes Speed becomes the modeled best allocation instead.

[Optimization saved and verified on GitHub](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/scrolling-ev/CATALYST_RESEARCH.md).
