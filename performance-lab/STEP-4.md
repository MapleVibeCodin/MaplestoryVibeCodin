# Performance Lab — Step 4: passive transition observations

Base: Step 3 branch head d895c942a3edd733e13875cc005cffad4aa18eff. This isolated branch does not change main, pre-optimized, calibrations, screenshots, or archived logs. Recorder tag 24.63.4-lab4 is not a production desktop release.

## Implemented
- Existing GUI gate observations feed a one-second bounded heartbeat; no new capture, OCR worker, input automation or navigation logic. Unknown/unavailable states invalidate stale evidence. An explicit interruption is logged when the existing black sampler detects a long sample gap.
- Offline export pairs black starts/ends conservatively within the same observation segment. Preserves incomplete records and valid black intervals even if destination state is missing. Durations must agree within 1 ms. Source state older than 1.25 s is not used; destination evidence must arrive within 3 s. These are proposed thresholds, not benchmark results.
- Observed entrance-to-room, room-to-entrance, same-scene, unknown; these are detector-level observations, not proof of portal use, actual movement path, channel identity, or server readiness. Channel-shortcut association is a hint only. Existing detector coverage is limited (especially no eligible target/unlocked entrance); cached detector results and GUI scheduling can affect timings. No-target cases remain unknown.
- Export adds transition_observations per segment and visual_loading_ms / black_to_observed_scene_ms summary distributions.
- Offline transition_dashboard.html imports a report locally, separates version/scope, counts incomplete observations and missing destinations, and shows nearest-rank percentiles. No network requests or production deployment.

## Verification
11/11 copied Python pure reducer tests executed in isolation (not the exact repository full suite); 13 tests staged in the repository, including heartbeat and export integration. 12/12 JavaScript reducer tests executed with synthetic fixtures. Saved files read back from GitHub. No live Windows run, browser rendering check, full historical replay, real report import, or overhead measurement performed. Page connector unavailable during this step; standalone dashboard saved as fallback. Existing purchase detector remains disabled pending evidence qualification.

## Next
Step 5 data integrity and failure handling. Before deployment, qualify actual source/destination observations, validate native video labels and Windows capture behavior, test missing segments and dropped events, and measure overhead.
