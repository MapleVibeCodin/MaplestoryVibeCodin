# HeneFM research — next-chat handoff, November 27, 2026

## Read this first
User's precise latest objectives, quoted word for word:
> i dont really care about room speeds. i want to be at the correct channel for the next deal before it's announced. thats the goal
> also just being in the right place at right time. using our predictive model. if i can be 1 second faster, its better
> channel needs to be exact because change channel time takes the same amount of time. aprox fm location is good beacuse where i am relative to fm room the closer i am (instead of a central spot) is best.
> ok now move everything to new chat. preserve EVERYTHING WORD FOR WORD.
> no i dont want to download...everything goes in our github.
> no its fine do everything

Goal: exact channel before a profitable alert, approximate physically closer FM position, maximize expected seconds saved including wrong predictions and CC cost. One second improvement counts. Do not substitute conditional FM accuracy or scanner-count estimation for this objective. Do not use future timestamp/channel in operational prediction. Use passive observations, no runtime changes requested. Current fitting uses Nov26–27 only; older data remains archived.

## Data and chronology
[Raw original data archive](raw/2026-11-27/README.md): six exports, all byte-exact verified against source git hashes, including full 7970-record historical export and latest 2052-record export. Latest header 20:35:18.868 +08, last record20:35:05.774. Prior tested cutoff20:29:52.486; 81 new records in latest export still unscored. Retrieve the original files from GitHub; do not ask user to re-download/re-upload. Do not edit originals. Screenshot binary not transferred yet; exact UI wording and hash recorded in raw archive README. Earlier tests used selected filename download timestamps, not verified actual alert arrival/scan timestamps.

## All research
[Complete historical scanner research index](2026-11-27-scanner-research-LATEST.md) contains earlier tests and links. Read:
- [Controlled CH1 experiment](2026-11-27-ch1-requested-scan-experiment.md)
- [Full recent reanalysis](2026-11-27-full-recent-reanalysis-after-ch1.md)
- [Next-deal channel objective](2026-11-27-next-deal-channel-objective.md)
- [Exact channel, approximate position](2026-11-27-exact-channel-approximate-position.md)

Original route 1,7,17,18,19,20,16,15,14,13,8,9,10,11,12,6,5,4,3,2; original 7s, weak FM12/20 positions. Recurrence prefit855s, exploratory840s. Fleet size remains unverified; 7 conditional on full sweep interpretation, not fact. Requested channel scans confirmed by UI; caller cooldown30min; CH1 reported complete20:29. Fixed schedules and room-only forecasts did not yield reliable next-channel prediction.
Raw event prediction 58/187 equals persistence; actionable 10s/15s exact21/131 vs persistence19/131. Conditional positioning mean .541 floor vs .844 central baseline (36% distance reduction), not measured travel seconds. Prior visible assistant also reported simulation on135 held-out observations assuming2s CC: already correct >=1s early5.9% reactive vs11.1% predictive; average reach2.21s vs1.87s, CC85 vs17; gains>=1s29/135, losses6, ~46s net saved. The simulation's full implementation/independent reproduction is not available in the checkpoint; treat these as prior reported results rather than verified fresh benchmark. Reproduce before relying on them.
Next action: score latest 81 new observations without retuning; use exact-channel lead-time and expected time-saved metrics, compare against persistence and reactive baseline. Use physical FM movement cost, not numerical room distance. Keep predictions and test results separate; archive implementation, parameters, test fixtures and errors.

## Transcript archive status
[Part 1](transcripts/2026-11-27-scanner-validation-accessible-dialogue-part-1.md) and [part 2](transcripts/2026-11-27-scanner-validation-accessible-dialogue-part-2.md) preserve accessible messages and key exact user instructions. Part 2 is explicitly partial; prior assistant responses not fully captured, interactive widgets not preserved exactly, compacted earlier content unavailable. These are not a complete verbatim platform export. Do not claim otherwise. Original raw exports are stored byte-for-byte at user's explicit request in public repository; unrelated private information/credentials remain excluded.

## Continuity
Read root AGENTS.md and checkpoints/LATEST.md; run the ten applicable continuity checks, distinguish static documentation verification from executed tests, consult prior fixes, preserve historical files, append and verify updates. No runtime edits in this checkpoint. User requires one-command PowerShell workflows where applicable and no Work/Codex suggestions.
