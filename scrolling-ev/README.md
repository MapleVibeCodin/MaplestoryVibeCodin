# Universal Scrolling EV Optimizer v1.0

Open `scrolling_ev_optimizer.html` locally in a browser (standalone, offline). The reusable JavaScript engine is `scrolling_ev_engine.js`.

## Permanent calculation standard
- Use 100% scrolls as the guaranteed stat-per-meso benchmark.
- Enter equipment price, natural stats, available slots, and each scroll's price, success probability, stat bonus and unconditional destruction probability.
- Use HeneFM credible current asking prices and Cozy Market completed transactions; distinguish stale sales, active listings, and unavailable stock. Prices in presets are illustrative November 25, 2026 snapshots; refresh before market decisions.
- Optimize both expected net cost per accepted item and expected net cost per retained added stat. The latter is a ratio of expectations, not an average of individual ratios.
- Evaluate every legal scroll action after each outcome using finite-slot dynamic programming and renewal/fractional optimization. Include fresh-base and same-base opener retries, mixed tiers, adaptive switching, selective abandonment, destruction, salvage, and stopping early.
- Compare finished targets, probability distribution, expected scroll and base consumption, and 100% benchmark efficiency. For arbitrage, compare actual production cost with credible finished-equipment resale values net of fees.

## Regression example
Five slots, base 3,000 mesos; 100% +1 at 39,000, 60% +2 at 90,000, 10% +3 at 13,000. Target +7: fresh-base 10% opener then four guaranteed scrolls, expected cost 316,000. Target +6: retry failed opener once on same base, then restart if both fail; after success use three guaranteed scrolls, expected cost about 262,789.

## Limits
Version 1.0 models one additive stat, independent scroll outcomes, constant salvage for discarded surviving bases, and fixed prices. No slot restoration, protection, market slippage, or automated market fetching. The UI supports 1–20 slots; use realistic input ranges. Actual individual results can differ substantially from expectation.

For future ChatGPT/Codex sessions: reuse this engine and update inputs instead of rebuilding the math. Keep this folder separate from unrelated projects.

## Current research and next-session handoff
Read [RESEARCH_HANDOFF.md](RESEARCH_HANDOFF.md) for AP-aware DEX/LUK equivalence, damage calculations, hard-budget earring-only constraints, crafting assumptions, current regression cases and future research logging conventions. This documents new requirements; it does not change the v1.0 engine implementation.

## Resume protocol for ChatGPT and Codex
Read this README, [RESEARCH_HANDOFF.md](RESEARCH_HANDOFF.md), and [CATALYST_RESEARCH.md](CATALYST_RESEARCH.md) from current main (not a pinned old commit). Read the latest dated sections first for superseding decisions; consult earlier sections for supporting evidence. Inspect existing engine files if implementation is requested. Continue the user's latest instruction without requiring them to restate documented constraints. Treat the repository as the durable project checkpoint, not a complete chat transcript. At the end of substantive project work, update relevant research/implementation files and verify the commit; keep new findings, decisions, inputs, provenance, calculation limitations, unresolved questions, and next steps. Never claim unsaved messages are automatically synchronized. Avoid private/account-specific information in this public repository.

Current active project checkpoint (2026-11-25): catalyst crafting resale and liquidity comparison, 50 crafts. Exclude Shoes Jump from this comparison. Default production 75% Intermediate /20% Greater /5% Chaos, provisional, sensitivity 1–10% Chaos. HeneFM only for market pricing: arithmetic mean of lowest, 24h sold average and recent sold-unit sample median; separate lowest-price liquidation case. Latest user-provided output snapshots are in CATALYST_RESEARCH.md, material input costs are older. At 67.933k catalyst, 3% fee, 50 crafts: Gloves Crit 5.915m cost, 1.361m representative profit, 1.130m lowest profit; Shoes Speed 4.191m,616k,470k; Earring LUK 5.144m,568k,264k. Conditional full clearance at 50% demand capture 19.8/5.9/13.3h, not measured mean. Previous suggested allocation 25 glove+25 speed, 5.053m investment, ~800k profit at lowest, conditional 9.9h clearance. No actual user craft outcomes reported yet. Next steps when requested: refresh materials and catalyst bulk acquisition costs; incorporate actual craft results; refine liquidity using listing-level observations, not invented capture rates. Update this checkpoint after substantial changes. Engine remains v1.0; catalyst calculations documented but not integrated into engine.
