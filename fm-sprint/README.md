# FM Sprint dual-engine prototype — 2026-11-27

Separate branch from Step 13 checkpoint a80a9ffbcc2a4a1616b5cfdc8c91b35c430df8fb. Production main and prior lab branches unchanged.

## Start and launch
Use START_FM_SPRINT.ps1 with -Engine runescape or -Engine maplestory. The installer creates a separate pinned checkout and Python environment. Close other FM Rush instances first. Default is pointer assist; -Navigate adds experimental, bounded channel-selection/confirmation and one projected shop click. Windows execution and complete lifecycle timing are unverified. Start at CH20, row 3, base of the rope between FM14 and FM15. -StartChannel changes the assumed starting channel; this is not independently detected. F8 repeats the route. F12 stops the run; Shift+2 unlocks. Walking, teleporting, opening the channel menu, and buying remain manual.

## Implemented
Existing HeneFM feed, automatic lock, route plan, overlays, native inventory gate, strict scroll path, and screenshot/performance components are reused. Common lifecycle prepositions the cursor during observed black frames, validates the channel menu header and selected-cell color before experimental clicks, projects the first-return shop sign, and parks the cursor outside the inventory on shop-open detection. A projected shop location is not proven seller identity. No blind click loops; no anti-cheat bypass, network injection, or game memory access.

RuneScape engine: native exact name bitmap and sprite signature cache learned from OCR, with fallback and conflict abstention. MapleStory engine: existing compact text-band OCR with exact row cache. No reuse of the OBS crop coordinates as native geometry. Both are experimental live adapters.

## Tests and blockers
19 offline pure Python tests passed. Channel menu template tested on 241 sampled frames from 04-39-52; six positive matches at 445,965,970,975,980,985, correlations 0.99910–0.99931; max remaining score 0.24766. This is one recording, not independent exhaustive validation. Prior Step 12/13 latency results do not apply to the new live wrapper. No verified Windows execution or full end-to-end latency.

PurchaseProof and acceptance tests exist, but no live purchase dispatch: receipt, quantity, actual channel identity and statless classification are not verified. Empty stats do not prove an item is statless. F8 is a route cue, not an automatic movement macro; prior FM1 V5 remains unqualified. Automated gameplay may violate Nexon's terms. The full downloadable ZIP (including BAT files and README) SHA256 is 08053743f895c2e9cd707c0f631c2e0ff2eae2a256eaed005745c499c443cada. Raw private media not uploaded.
