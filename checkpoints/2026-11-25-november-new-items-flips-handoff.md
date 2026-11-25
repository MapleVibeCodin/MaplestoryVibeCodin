# Checkpoint — MapleStory Classic World new-item flipping, November 1–25, 2026

**Checkpoint date:** 2026-11-25 (Taipei).  
**Repository:** https://github.com/MapleVibeCodin/MaplestoryVibeCodin, `main`.  
**Chat topic:** Research new *ETC/USE items added after November 1, 2026*, looking for Turkey Egg-like practical utility, high transaction volume, and profitable real HeneFM underpricing.

## Priority and hard constraints
- **Only items introduced after 2026-11-01**; exclude preexisting ores, fragments, ordinary consumables and scrolls even if their spreads are better.
- Primary venue: **https://henefm.com/flips/deals**. Examine actual deal rows, actual current buyable price/quantity and recent sold data; cross-check item pages and item utility. `https://henefm.com/flips/craft` is supplemental.
- Prefer **ETC or USE** that players *actually consume/open/use/exchange repeatedly*; reject collectible trash or high-priced fashion gear. High turnover, inexpensive entry cost, a reliable executable margin and inventory stackability matter more than headline ROI.
- User's demonstrated baseline: **Turkey Eggs bought at 500 mesos and sold at 1,000**; with an assumed 3% shop fee this yields **470 mesos net per egg / 94% net ROI**. This result is based on the user's actual reported trades, unlike most public market snapshots.
- **Do not claim a trade is executable** merely because 24-hour mean sale > cheapest ask. Check live listing exists, quantity, age, number of sales, fees, competitive price and whether sold counts represent units or disappearance events.
- Distinguish *verified current*, *observed past*, *database claim*, and *hypothesis*. New event notes and item-database tradeability flags conflict: check the live FM/client before recommending pumpkin-ingredient or buff trades.
- Deliver a concrete ranked shortlist with shop/channel when visible and **real buy thresholds and feasible resale prices**, not hypothetical items with no completed sales. No generic 'try testing it' instead of doing the research.
- Working style: execute; independently follow evidence; search fresh and deep; don't recycle rejected ideas; minimize follow-up questions.

## Research scope covered in this chat
Previous assistants expanded the Nov 18–25 coverage to:
1. Thanksgiving: Turkey Egg; Pumpkin Piece, Pie Flour, Milk Jug; Pumpkin Pie, Roasted Turkey, Gravy, Turkey Leg, Cranberry Sauce; Autumn Leaf Wreath; Roast Turkey Platter, Harvest Feast Table, Harvest Hay Bale, Pumpkin Harvest Wagon.
2. Moon Bunny PQ: Moon Bunny Hat, Moon Bunny Statue, Moon Bunny's Rice Cake, Flower Rice Cake, Fullmoon Rice Cake.
3. Forgotten Hollow: new weapons, ingredients, recipes, scrolls, return scroll, Sylka's Brew, Hollow Extract, Rotten Mushmom Cap, Nyroth's Mystery Deco Box, and Black Sack: Mano/Stumpy.
4. November 4 and November 18 NX cosmetic rotations and November 23 Aurora Stamp coupons. These are **not preferred for this ETC/USE use-case**, although a 191-item spreadsheet was reported earlier in the chat.

## HeneFM leads already inspected — historical snapshots, NOT current quotes
- **Turkey Egg:** user buy 500 / sell 1,000 repeatedly; HeneFM was previously quoted ~9,750 24h shop-sale observations and 882 average, but data should be freshly read. Inventory stack size previously claimed 10; recheck.
- **Black Sack: Mano** (`https://henefm.com/items/2100010`): historical ~125–135K ask; ~145K average sale; ~128 reported sales/day; buy target <=100K for resale ~130K (hypothetical, not a live offer).
- **Black Sack: Stumpy** (`https://henefm.com/items/2100011`): historical ~120K ask; ~129K average sale; ~149/day; hypothetical buy <=95K, sell ~120K. Source may be time-limited; a prior assistant claimed Kerning PQ source was temporarily removed Nov 20.
- **Return Scroll to Forgotten Hollow** (`https://henefm.com/items/2030007`): historical 799–899 asks / ~1,100 mean / ~199/day; NPC reportedly sells at 800. At a 799 ask, **no guaranteed resale spread**; buy target <=600 for 999 resale is *not confirmed available*.
- **Rotten Mushmom Cap** (`https://henefm.com/items/4000065`): ETC, prior listing nine at 25K and ~39.8K mean; declining and a boss drop, weak fit vs Turkey Egg repeated-utility requirement.
- **Nyroth's Mystery Deco Box** (`https://metacw.com/price-check/2430001`): reportedly bought from Nyroth NPC for 5,000 and listed in FM at 6,999 or 10,000; *zero verified completed trades* in checked snapshot. Theoretical NPC arbitrage **unvalidated**.
- **Sylka's Brew:** NPC potion reportedly 1,000 / 1,499 observed trade with just two observations; poor volume.
- **Gloves Crit. Rate Scroll: Lesser:** historical ~54K ask / ~54.7K sale, likely loss after fees at prevailing price; not Turkey Egg-like.
- **Fragment of Magic** was suggested earlier but explicitly rejected because it is **not new** after Nov 1.
- **Turkey Leg, Cranberry Sauce, Pumpkin Pie, Roasted Turkey, pumpkin ingredients:** assistant found contradictory trading flags; some event notes say world-tradeable, item data account-shared/untradeable; HeneFM completed sales not verified. Do not label them executable until checked.
- **Hollow Extract**: no observed FM sales in prior snapshot.
- **Wild Glowshrooms**: actual HeneFM deal feed had 7 priced 1,400, sale average 2,480, around 10/day; furniture setup rather than frequent-use ETC/USE, so poor fit.
- **Elixir** was excluded because older listings predate Nov 1.

## Last active research outcome
Prior assistant inspected the HeneFM deal feed snapshot and reported **63 detected / 44 sold**; no visible Turkey Egg/Pumpkin Piece/Pie Flour/Turkey Leg deal rows. This is *one snapshot*, not proof they cannot flip.
The last assistant concluded there was **no verified second newly-released, low-cost ETC/USE item with Turkey Egg-level liquidity and immediately buyable doubling spread**; the only observable active alternatives were Mano/Stumpy sacks and the Forgotten Hollow return scroll, with caveats above. **User rejected superficial answers and wants a much deeper actual-deals-driven scan.** Resume by retrieving live `/flips/deals` and paging/filtering the new ETC/USE deals, not repeating this shortlist.

## Resume execution plan
1. Pull the live HeneFM flips list, including sold/hidden rows and shop coordinates where supported. If blocked, say so precisely and use fresh HeneFM item pages and relevant market records; do **not** pretend to have read live feed.
2. Construct the canonical list of all tradeable USE/ETC added after Nov 1 via patch diff and item database (date check per item).
3. Match *every* candidate against HeneFM listing count, price, 24h recent sales and underpricing; calculate net resale **(0.97 * feasible sell price) - purchase price**, and resale sell-through.
4. Separate consumable/summon/teleport/crafting inputs that create repeat demand from one-time decorations and cosmetic speculation.
5. Return top **immediately purchasable** opportunities with seller/CH/FM/quantity/timestamp when supplied, **not** mere target bids. Admit when none qualify.

## Other current repository state / non-changes
- This request is *research only*. Do not change scanner code, browser extension, auto-pull settings, FM Rush installation scripts, or the universal scrolling optimizer.
- The existing root `AGENTS.md` is specifically the FM Rush engineering handoff, and remains authoritative for FM Rush. Do not overwrite it with a market-research transcript.
- Universal scrolling EV optimizer exists under `scrolling-ev/` in this repo (separate project; not modified here).
- The prior assistant offered `MapleStory_Classic_New_Items_Nov_2026_Price_Audit.xlsx` in the chat and said 191 items. **Workbook bytes are not archived in GitHub.** A container check in this checkpoint verified that `/mnt/data/MapleStory_Classic_New_Items_Nov_2026_Price_Audit.xlsx` exists (25,107 bytes; SHA-256 `ef8dbd81df4333b40320fa72fcda0ff41b7b9f86055d74edd46e87d96530d60b`). The file is available as a current-chat sandbox artifact, but **not** as a GitHub asset; do not claim it is part of this commit.
- All market figures are **past assistant observations**, not live rechecks performed during this GitHub checkpoint.
- This handoff is not a ChatGPT transcript. The separate transcript file in `checkpoints/transcripts/` records accessible conversation utterances and its coverage limits.

## New-chat prompt
> Resume November 2026 MapleStory ETC/USE flipping research from https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/checkpoints/2026-11-25-november-new-items-flips-handoff.md . Read the accompanying conversation archive and do a fresh scan of https://henefm.com/flips/deals . Only new items introduced after November 1; seek genuinely useful cheap consumables with high volume and verified executable flips like buying Turkey Eggs 500 and selling 1000. No old items, cosmetics, unverified asking prices, or theoretical margins.
