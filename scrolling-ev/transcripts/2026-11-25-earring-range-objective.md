# Earring scroll family audit and range objective — 2026-11-25

## User

also check all earrings scrolls for damage increase. remember the end goal is highest range increase

## Assistant

## All 24 earring scrolls checked

There are six earring scroll families, each with four tiers. There are **no weapon attack, magic attack or critical rate earring scrolls** in the currently documented Classic World catalogue.

| Scroll family | Lesser 100% | Intermediate 60% | Greater 10% | Chaos 10% |
|---|---:|---:|---:|---:|
| LUK | +1 | +2 | +3 | +4 |
| DEX | +1 | +2 | +3 | +4 |
| STR | +1 | +2 | +3 | +4 |
| INT | +1 | +2 | +3 | +4 |
| Crit damage | +1% | +2% | +3% | +4% |
| Evasion | +1 | +2 | +3 | +4 |

Chaos also carries a 45% unconditional destruction probability under the documented 50%-on-failure mechanic.

## Important distinction: damage range versus actual damage

I checked the current MeowDB combat formulas. **Critical damage does not increase your displayed character-window damage range.** It increases the damage of critical hits, but those are excluded from the stat window.

Since your end goal is the highest range increase, we'll prioritize that metric and report actual Lucky Seven combat damage separately. This also means we should no longer rank earrings using natural crit damage as a bonus to displayed range.

## Damage contribution of every scroll family

Using our previous illustrative level-50 Assassin model (53 total weapon attack, including throwing stars):

| Added stat | Maximum displayed range gain per point | Average Lucky Seven damage gain per cast |
|---|---:|---:|
| LUK | +1.325 | +3.726 |
| DEX converted to LUK AP | +1.325 | +3.726 |
| DEX without AP conversion | +0.530 | +1.656 |
| STR | +0.530 | +1.656 |
| Critical damage (1 percentage point) | 0 | +2.095 |
| INT | 0 | 0 |
| Evasion | 0 | 0 |

These are pre-rounding, pre-defense estimates under the previous build assumptions, not measured results for your character.

## Updated priority

1. LUK and convertible DEX: primary targets.
2. STR and excess DEX: investigate as cheap secondary-stat fillers. For displayed maximum range, each point is worth 40% of a LUK point.
3. Critical damage: valuable for actual combat, not for displayed range.
4. INT and Evasion: exclude from the damage-range objective.

Our current 1m NPC-recovery model gives an expected +7.925 effective LUK, or approximately +10.50 maximum displayed range at 53 weapon attack. It remains optimal within the previously modeled LUK-equivalent scroll choices, not necessarily across all mixed-stat strategies.

The immediate next improvement is to add STR and nonconvertible DEX to the exact budget optimizer, using their actual range contributions and current HeneFM prices. We will retain the fixed 30k Pansy base.

[Post-save verification notice omitted.]

## Archive note
Visible text preserved; citations and formatting flattened. Research commit a1178f2a6acbe8cd4608622e728cad1c9ccf84d4. Mechanical audit of all 24 tiers, not a synchronized price scan or mixed-stat DP rerun.
