# Spatial research source catalog
User verbatim: now look up github. all similar style code. minic and learn. get exact github links and tell me. just google search can find tons

Scope: passive screenshot analysis, map quality and anonymous actor observation. No automation/input modules to be imported. New search extends existing 99-repository tracker catalog, overlaps are intentional references, no claim of exhaustive coverage.

## Verified commits, tree listings and files inspected
- [neiamo/D4MXD](https://github.com/neiamo/D4MXD/tree/e50471e95028ba7c87cb4346d21a8c8954b0160f) — license metadata unconfirmed. Files read: [maple_v2/stitch.py](https://github.com/neiamo/D4MXD/blob/e50471e95028ba7c87cb4346d21a8c8954b0160f/maple_v2/stitch.py), [maple_v2/templates.py](https://github.com/neiamo/D4MXD/blob/e50471e95028ba7c87cb4346d21a8c8954b0160f/maple_v2/templates.py)
- [weihouang/maplestory](https://github.com/weihouang/maplestory/tree/c6f0839ef95b9a4074f2f0375747eda3a5a25fb1) — license metadata unconfirmed. Files read: [src/motion.py](https://github.com/weihouang/maplestory/blob/c6f0839ef95b9a4074f2f0375747eda3a5a25fb1/src/motion.py), [src/tracker.py](https://github.com/weihouang/maplestory/blob/c6f0839ef95b9a4074f2f0375747eda3a5a25fb1/src/tracker.py)
- [Amit-Singh-P/Game-Vision](https://github.com/Amit-Singh-P/Game-Vision/tree/50a5b476116fdd6812330f35d506ffdf4b08f805) — license metadata MIT. Files read: [src/gamevision/events/detector.py](https://github.com/Amit-Singh-P/Game-Vision/blob/50a5b476116fdd6812330f35d506ffdf4b08f805/src/gamevision/events/detector.py), [src/gamevision/analytics/event_metrics.py](https://github.com/Amit-Singh-P/Game-Vision/blob/50a5b476116fdd6812330f35d506ffdf4b08f805/src/gamevision/analytics/event_metrics.py), [src/gamevision/visualization/heatmap.py](https://github.com/Amit-Singh-P/Game-Vision/blob/50a5b476116fdd6812330f35d506ffdf4b08f805/src/gamevision/visualization/heatmap.py)
- [Yufy1114/Gameplay_Event_Detection](https://github.com/Yufy1114/Gameplay_Event_Detection/tree/78c91601a8504fe3ff84c70e18a2a6785c37ee64) — license metadata unconfirmed. Files read: [src/event_engine.py](https://github.com/Yufy1114/Gameplay_Event_Detection/blob/78c91601a8504fe3ff84c70e18a2a6785c37ee64/src/event_engine.py)
- [tanjeffreyz/auto-maple](https://github.com/tanjeffreyz/auto-maple/tree/5d88510e582784d6992ef72e8664e7df88d392ff) — license metadata unconfirmed. Files read: [src/modules/capture.py](https://github.com/tanjeffreyz/auto-maple/blob/5d88510e582784d6992ef72e8664e7df88d392ff/src/modules/capture.py)
- [ra1nty/DXcam](https://github.com/ra1nty/DXcam/tree/1e595ff55e57263c4b5d0414828f74104afa86f4) — license metadata MIT. Files read: [dxcam/core/capture_loop.py](https://github.com/ra1nty/DXcam/blob/1e595ff55e57263c4b5d0414828f74104afa86f4/dxcam/core/capture_loop.py)
- [NiiightmareXD/windows-capture](https://github.com/NiiightmareXD/windows-capture/tree/6ab0086703e83fde0685c07becd7ff04ab004dbb) — license metadata MIT. Tree inspected, no source file read.
- [roboflow/trackers](https://github.com/roboflow/trackers/tree/642d6bfab1959b6f4410dd9747417ab5a9b1bbe9) — license metadata Apache-2.0. Files read: [src/trackers/core/botsort/cmc.py](https://github.com/roboflow/trackers/blob/642d6bfab1959b6f4410dd9747417ab5a9b1bbe9/src/trackers/core/botsort/cmc.py), [src/trackers/utils/cmc.py](https://github.com/roboflow/trackers/blob/642d6bfab1959b6f4410dd9747417ab5a9b1bbe9/src/trackers/utils/cmc.py)
## Additional public search results (not audited or pinned this turn)
- https://github.com/vinmorel/MapleWrapper
- https://github.com/Dashadower/MS-Visionify
- https://github.com/gmh5225/MapleStoryAutoLevelUp-
- https://github.com/sychen6192/maplebot
- https://github.com/NecturaLabs/MapleStory-MVP-Detector
- https://github.com/itechify/minerva
- https://github.com/jcsoutherland/maple-exp-tracker
- https://github.com/CabbageCanFly/msxp
- https://github.com/NirAharon/BoT-SORT
- https://github.com/onuralpszr/trackforge
- https://github.com/Geekgineer/motcpp
- https://github.com/ZelZahid/Hunters_Eye
- https://github.com/naxastudio/game-map-stitcher
- https://github.com/tryolabs/norfair
- https://github.com/lovettchris/wincam
- https://github.com/glpc/BetterCam
- https://github.com/phoboslab/qoi
- https://github.com/TanishqSanduja/lila-player-journey-explorer
- https://github.com/DracoShivam/lila-player-viz
- https://github.com/sripentakota/player-analytics-service
- https://github.com/skadistats/clarity
## Findings
- D4MXD stitch: phase correlation, dense optical flow, adaptive thresholds, ORB/RANSAC affine, incremental canvas. Unknown license and external JYMOKUAI dependency; do not copy. Template code mixes action queues; only study vision design, not game control.
- weihouang motion: downscaled grayscale, phase correlation, warp previous frame, absdiff, threshold/median/dilate/contour. Excess shift reset may create false motion; stationary mobs missed. CSRT tracker requires contrib OpenCV, only single object in inspected tracker. Unknown license; use as conceptual reference.
- Game-Vision: temporal confirmations, track lifecycle and region transitions, CSV/JSON event export, simple grid heatmap. Do not treat every newly confirmed track as spawn or every aged-out track as kill; add visibility, motion, EXP and animation evidence, time-based dwell weighting, per-map coordinate alignment and unknown state. MIT metadata; retain license if reused.
- Yufy event engine: consecutive-seen and last-seen state, dedup. Frame-count thresholds should be elapsed-time-aware at varying capture intervals. Unknown license.
- Roboflow CMC shim deprecated, actual utils/cmc.py supports ORB/SIFT/sparse flow/ECC, robust affine, detection masks, track coordinate updates. Apache-2.0 metadata; preserve notices. Start with translation only for side scrolling; reject parallax and low overlap.
- DXcam capture loop reserves slots, captures with frame ticks, commits buffer under lock; bounded asynchronous producer/consumer pattern. MIT metadata. At 1 Hz actual previous bottleneck was lossless WebP encoding, not established capture backend. Compare Windows capture with current MSS only after hybrid encoder integration; do not claim speed increase.
- Existing Minerva static spawn data and MCWO/Javipen pickups remain important. Need real labeled game captures for calibration, no arbitrary ML performance claims. Further search results for telemetry heatmaps take structured data as input, not pixel inference; cannot create missing observations.
- No code changes, no upstream code redistributed, no runtime or benchmark tests this turn. Exact upstream references and source-level review only. Existing archive and history retained.
