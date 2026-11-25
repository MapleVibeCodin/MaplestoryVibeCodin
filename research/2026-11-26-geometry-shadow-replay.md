# FM Rush v24.63.1 — fresh checkpoint replay and geometry shadow experiment

Baseline 44d0aeb54a5377b3979a67f91effbb1c4cbccedc; runtime 68b8b7a1cbe75d805ab78314458f8ff1c72a1ed5, browser 24.56.0. Ten static continuity areas recovered from live source and checkpoint. Read source audit, research continuation, final continuation and pipeline audit. Runtime unchanged. Complete private Library archive materialized, ZIP CRC passed: 10 MP4, 42 PNG, 5 JSONL; 109961754 bytes. All recordings decoded, 5777 frames, 199 half-second detector samples at assumed native top-left 1366x768, 42 PNGs searched, 2914 JSONL events parsed. Copied equivalent room and exact shop gate logic executed, not full Windows scanner. The archived replay_summary.json clarifies the previous 188 scored title samples: 140 room, 48 nonroom, 11 ambiguous excluded. Reproduced 140 room detections, zero exact shop video anchors, ten exact shop PNG anchors. Five copied pure vision guard test methods freshly passed. Full Windows staged suite not executed. No private raw media published.

## Geometry experiment
Original offline prototype vision_shop_geometry_shadow.py, source commit 4668bebe8ac18ec98e770f83893df110f8d58625. Minerva-inspired repeated 40px inventory geometry and Simba-inspired multiple spatial color landmarks. Research only, numpy/OpenCV not runtime dependencies. Search video region x535:615 y185:250; 24px green strip, orange strips at +31/+51 with small independent offset. Recognize normal/sold/selected backgrounds with tolerances. First experiment used right margin only and had 46 detections: missed frame 480 of 03-38-05 because four right margins obscured; recovered earlier 03-46-13 frame 990 where third button changed. Second experiment checks four spaced columns (-100,-55,-10,+54 relative to candidate), requires at least two columns in a row; require 3 rows with both orange strips or 4 with one; reject spatially competing clusters.

| Clip | Samples | Prior labeled open | Multi-column detections |
|---|---:|---:|---:|
| 03-14-15 | 13 | 0 | 0 |
| 03-14-30 | 14 | 0 | 0 |
| 03-14-46 | 13 | 0 | 0 |
| 03-15-01 | 12 | 0 | 0 |
| 03-38-05 | 25 | 10 | 10 |
| 03-42-22 | 18 | 2 | 2 |
| 03-46-13 | 40 | 6 | 6 |
| 03-55-12 | 16 | 10 | 10 |
| 03-56-42 | 20 | 11 | 11 |
| 03-58-13 | 28 | 8 | 8 |
| total | 199 | 47 | 47 |

Detected frame indices (zero based): 03-38-05 450,480,510,540,570,600,630,660,690,720; 03-42-22 420,450; 03-46-13 840,870,900,930,960,990; 03-55-12 180 through 450 every 30; 03-56-42 270 through 570 every 30; 03-58-13 540 through 750 every 30. Counts match prior open-shop labels per recording; no independent per-frame label adjudication in this session. Do not claim independently verified 100% recall or zero false positives; 141 previous closed samples and 11 ambiguous, labels aggregate. All ten known native anchor PNGs also return shadow evidence using ROI around known exact anchor; other 32 PNGs not shadow-tested. The returned shadow x is approximately two pixels left of exact native anchor, so NOT suitable as inventory crop origin. This and held-out testing block promotion. The experiment is tuned on existing recordings, not held-out. No live integration, no automatic inputs.

## Next steps
Use native screenshots and GDI rasterization to identify actual shop font, then build and test packed glyph atlas with independent competitor margin, price-width checks, background evidence and strict scroll identity. Retain exact gate as native fast path. Test alignment/crop offsets and negative cases, empty and heavily occluded shops, 1280x720 and 1366x768, held-out whole sessions, all 116 historical unique PNGs and full seller/name/price/publish pipeline. No source release or updater changes. Direct network unavailable in container; GitHub connector used to read exact refs, copied logic used for offline execution. Do not claim source test suite or fresh Windows performance measured. Preserve all old files.
