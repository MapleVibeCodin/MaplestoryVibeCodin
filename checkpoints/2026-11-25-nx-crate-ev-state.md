# NX Fashion Crate — HeneFM EV checkpoint
Saved: 2026-11-25 (Taipei context). Repo: MapleVibeCodin/MaplestoryVibeCodin (main).
Scope: THIS NX crate discussion only, not the separate FM Rush and scrolling EV programs.

## Continuation files
- 2026-11-25-nx-crate-ev-chat.md: all six accessible user messages verbatim, and the assistant's visible response text, tables and numbers. Note that rendered interactive widget implementation code and hidden messages are not available in a verbatim export.
- 2026-11-25-nx-crate-items.csv: 50 names, HeneFM IDs/links, last-reported asking prices, claimed item probabilities, 44K modeled values.

## Hard constraints / user preferences
- Use HeneFM rather than Cozy; refresh the actual lowest active asking price for **all 50 new crate NX items** if asked for a new scan. Cached snapshots must be labeled as such.
- Model any item below **44,000 mesos as 44,000** minimum; explicitly a user-requested valuation assumption, not a guaranteed exit price.
- Assumed palette conversion: any 5 low-value NX -> 1 Mystery Palette Exchange Coupon; model price 220,000 mesos, hence 44K each. If palette price changes, update threshold to coupon_price/5; for finite simulations convert full groups of five and price leftovers individually or carry forward.
- Apply 3% sale fee on realized individual/palette proceeds.
- Assumed bundle: 11 crates / 35K NX; modeled NX:meso ratio 1:20 => 700K cost per 11 and 7M cost per 110. This is an opportunity cost, not a transaction guarantee.
- Simulate independent 110-crate weighted random pulls and report every item count, sales strategy, leftovers, fees, ROI and gain/loss; run actual reproducible code rather than inventing RNG output.

## Verified arithmetic (locally recomputed from conversation's 50 rows)
- Probability weights add to 100%, 50 distinct products. Source authority of drop weights NOT independently verified in this checkpoint.
- Net EV with individual sales: 63,787.20 mesos per crate.
- Net EV with 44K floor / palettes: **66,916.42 per crate**; for 11 crates 736,080.62; for 110 crates 7,360,806.20.
- At ratio 1:20, expected profit = 36,080.62 per 11; 360,806.20 per 110; break-even conversion about 21.03 mesos per NX.
- Mass of prices >44K = 20% of pulls, expected high-value items out of 110 = 22; other 88 at salvage floor.
- EV formulas: sum_i [P_i * max(lowest_ask_i, palette_price/5) * 0.97]; 110 profit = 110*EV - 7,000,000. Fractional-floor EV assumes large-volume carry-forward of scraps.

## Prior assistant-reported 110-pull scenarios (NOT RNG-verified)
Run 1: 25 individual items, 85 palette items => 17 coupons. Individual gross 3,708,800; palette gross 3,740,000; total gross 7,448,800; net 7,225,336; profit +225,336; ROI +3.22%. Tania Sword ×1, Dragonfly Wings ×1, Yo Yo ×0. Claimed seed 20261123, not independently checked.

Run 2: 15 individual items, 95 palette items => 19 coupons. Individual gross 2,151,000; palette gross 4,180,000; total gross 6,331,000; net 6,141,070; profit −858,930; ROI −12.27%. Tania Sword ×0, Dragonfly Wings ×2, Yo Yo ×1. Claimed NumPy seed 2026112302, not independently checked.

Both reported scenarios combined −633,594. These are *conversation-recorded outputs*, not actual observed crate openings or independently reproducible simulations. Next run: use a real RNG, verify each item's drop weight, count totals, sums, and conversion groups.

## Staleness / evidence
Market prices were various HeneFM pages with mixed cache ages during an earlier response (some reported as old as November 21). The 50 asking prices should NOT be labeled current for November 25.
Palette page: https://henefm.com/items/2430045
Unopened crate page: https://henefm.com/items/5222000
Earlier low unopened asking ~63.6K and 24-hour sold average ~82.2K were reported, not guaranteed realizable; previous assistant concluded unopened sales above ~69K after trading fees can outperform opening.
Item-by-item links stored in CSV. No HeneFM market refresh or new 110-pull simulation was performed during this checkpoint.

## Resume instruction
"Resume my NX crate EV analysis from https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/checkpoints/2026-11-25-nx-crate-ev-state.md. Read the accompanying transcript and CSV, respect the 44K floor and 3% fee, then execute my next request without making me restate the model."
