# Valley of Death endpoint analysis and map reference — 2026-11-28

Eight user-provided screenshots were inspected at native resolution and enlarged inventory crops. Raw images, personal identifiers, character progression, wallet balances and item holdings are not redistributed to this public repository. This is a technical method/reference note, not a verbatim personal-data transcript.

## Source reference
https://meowdb.com/msclassic/maps/010006031 — The Valley of Death, checked 2026-11-28. 26 potential spawn points, mob rate 0.8, modeled solo cap 9, 7.56s tick, default realistic 952 mobs/hr and 83,226 base EXP/hr at 40% uptime; ceiling 374,175 EXP/hr. Additional capacity after five combat players at 0.75 each rounded down. Model, not measured live server behavior.
- Zombie Mushroom: 6 points, level 24, 436 HP, 45 EXP.
- Jr. Boogie 1: 3 points, level 35, 1395 HP, 69 EXP.
- Zombie Lupin: 7 points, level 41, 1774 HP, 89 EXP.
- Rafflesia: 10 points, level 47, 2285 HP, 117 EXP.

## Method and evidence limitations
Match Use-tab endpoint timestamps for EXP and wallet rates (not nominal test duration). Match Etc stacks by icon across scroll states. A stack on an omitted starting page must remain unknown, not zero. A pet-linked consumable shown in Use and Deco must not be counted twice; visible partial Use stacks may not sum to full pet-linked quantity. Net inventory changes are not gross consumption or gross pickup. Separate wallet delta, known NPC liquidation value, cost to replace consumed stock and actual purchases. No exact kill count from mixed-species EXP when curse, party or buffs may change received EXP. One additional player visible in ending scene does not prove total or sustained map population. Rope attack failure and curse warnings are directly visible; timing, sustained density, TTK and spawn pressure need continuous timestamped evidence. Missing initial inventory middle page is a coverage gap. No raw overlay logs or continuous session supplied. No runtime change or tests executed.
NPC prices checked: https://mesos.guide/guides/selling-drops (Cursed Doll 40, Charm of the Undead 24, Rafflesia Petal 47, Jr. Boogie Horn 35); https://meowdb.com/msclassic/item-db/376 (horn 35); https://ms-classic.com/shops (Orange Potion 150 purchase, White 350, Blue 220). Icon identifications are visual candidates unless tooltip or template validates. No automatic inventory reconciliation implemented by this note.
