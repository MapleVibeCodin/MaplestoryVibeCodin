# NPC recovery and methodology audit — 2026-11-25

## User

is it possible to get better outcome with starting with 10% then NPCing the failed?

## Assistant

**Yes. Factoring in NPC resale actually changes our optimal opening scroll from 60% to 10%.**

Pansy Earrings have a documented NPC sell value of **13,500 mesos**, which significantly reduces the cost of restarting after a failed scroll.

## 1. Actual cost of a failed 10% opener

| Item | Cost |
|---|---:|
| Clean Pansy | 30,000 |
| DEX Greater (10%) | 18,888 |
| NPC recovery | −13,500 |
| **Net cost per failed attempt** | **35,388** |

On average, obtaining a Pansy with +3 stat and four remaining slots through repeated 10% openers costs **367,380 mesos**.

## 2. Rerun of the 1m budget model

| Strategy | Expected stat | Chance of +8 or better | Chance of below +5 |
|---|---:|---:|---:|
| Previous optimal, no NPC recovery | 7.675 | 63.75% | 2.05% |
| Always open 10%, NPC failures | 7.602 | 53.69% | 7.40% |
| **Adaptive with NPC recovery** | **7.925** | 55.71% | **1.36%** |

The adaptive strategy produces the highest expected stat, although the old strategy has a higher probability of reaching +8 specifically. Strictly forcing every replacement base to start with a 10% scroll is less efficient than adapting as the budget decreases.

## 3. New recommended opening strategy

**30k Pansy + 18,888 Greater**

**10% success**

+3 stat · 4 slots

Apply 60% Intermediate

**90% failure**

Recover 13,500

NPC and restart

As your remaining budget decreases, switch to the optimal affordable scroll rather than repeatedly gambling on 10%.

**NPC recovery is worth incorporating into all future scrolling calculations.** The model assumes failed earrings retain their documented NPC sell value of 13,500, which we haven't independently confirmed in-game.

[Updated mathematical model and findings saved and verified on GitHub](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/commit/f7e2fd822869be8c0877d4ac9b458486ae160905). The research update is saved; the separate verbatim transcript has not yet been updated.

## User

great discovery. bhow come this wasnt part of the methology and is there any other untested methods?

## Assistant

**NPC recovery should have been included from the beginning.** Our original optimizer actually supported a salvage-value input, but we left it at zero when developing the hard-budget earring model. I failed to investigate the actual NPC resale value of each clean base.

That was a methodological oversight. On a 30k Pansy, recovering 13.5k means getting back **45% of the base cost** after a failed scroll. That's too significant to ignore.

Going forward, every equipment-scrolling calculation should account for the full lifecycle: acquisition, scrolling, failed-item recovery, destruction, successful-item retention and potential resale—not just scroll costs and success rates.

## 1. Another improvement: optimize for your desired outcome, not just average stats

I reran the model with NPC recovery and several different objectives.

| Strategy | Expected added stat | Chance of +8 or better | Chance of +10 or better | Chance of below +5 |
|---|---:|---:|---:|---:|
| Maximize average stats | **7.93** | 55.71% | 16.11% | 1.36% |
| Target +8 specifically | 7.15 | **78.46%** | 5.40% | 16.75% |
| Target +10 specifically | 5.39 | 34.00% | **33.29%** | 52.18% |
| Make guaranteed +5 fallback first | 7.56 | 49.44% | 12.70% | **0%** |

[Chart omitted; values in table.]

All four strategies respect the 1m hard budget under our current assumptions.

This is a meaningful distinction: maximizing the chance of a godly earring is not the same as maximizing expected damage. We should retain both objectives in our optimizer.

## 2. Sell failed earrings in FM instead of NPCing them

I found a HeneFM record of a 3% CD Pansy with four remaining slots and no added stats selling for 20,000 mesos. Another identical damage variant was still listed after more than six hours.

| Recovery method | Net recovery | Net failed 10% attempt cost |
|---|---:|---:|
| NPC | 13,500 | 35,388 |
| FM at 20k, after 3% fee | 19,400 | 29,488 |

That saves another 5,900 per failed attempt if you can actually sell it. The drawback is delayed capital recovery.

## 3. Other methods we still need to investigate

| Method | Status |
|---|---|
| State-dependent resale of successful but inferior earrings | High priority; not modeled |
| Keeping several partially scrolled candidates | Not modeled |
| Mixing DEX, LUK and crit damage scrolls using actual combat damage | Not fully modeled |
| Crafting a pool of scrolls before selecting which to apply | Not modeled |
| Quest rewards, drops and alternate acquisition routes | Not fully costed |
| Slot restoration and protection | Not verified for Classic; exclude for now |

Crit damage scrolls exist, but the observed Lesser and Greater prices are higher than their DEX equivalents while our earlier damage model values each CD point at only about 0.56 effective LUK. They look inferior when DEX is fully convertible, but this must be revisited with actual AP limits and combat formulas.

**My next priority would be state-dependent FM resale.** We have only treated every discarded surviving earring as worth 13.5k. A partially successful earring may recover significantly more, which could fund additional attempts without increasing the original 1m budget.

[Post-save verification notice omitted.]

## Archive note
Visible wording reconstructed; citations and rendered chart/diagram omitted; no raw provider payloads. Methodology and calculations recorded in RESEARCH_HANDOFF.md commit 0c3731438ef4d6affdc7ce93582113809a3dd8c0. Target optimization uses a small expected-stat tie-break, not proven exact lexicographic optimization.
