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
