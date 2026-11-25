# Screenshot regression coverage — v24.56.0

Historical tree abac54c3d3a20f25c4b0bb416b81d983a67ddae5: 127 image paths, 116 distinct blobs. Current main has no raw images. The manifest references existing Git history, not copied assets. Earlier nameplate OCR tests have different semantics from the current fixed-coordinate scanner.

Three unique current-chat images (four attachments including duplicate) were tested offline using copied current detector and PNG preprocessing routines: Euphye gate (585,256), second row sold; GoreMagala gate (585,256), second row sold while target Cat's Eye is active row five; closed FM18 screenshot no gate. Both PNGs decoded at 486×804. These are pixel/preprocessing checks, not Windows OCR or end-to-end passes. The original HeneFM CSS pin for the FM18 marker is unavailable. No live latency or full alignment claim.

Historical image references have been indexed, not replayed. Existing legacy expected target coordinates are recorded for nine regression samples plus Mora badge. Unlabeled screenshots need expected target, room/channel and map pin/crop metadata. Thirteen named later chat screenshots and additional unnamed attachment references lack original pixels in the active environment. FM8 remains unresolved.

Run the separate offline suite with Pillow and the original image directory. On Windows it also invokes the same WinRT OCR worker. Optional history retrieval downloads unique blobs into a local test cache, outside the normal update. The suite exits nonzero for any failed or incomplete case; it never counts image integrity or a legacy expectation as current behavior passing. Do not claim all screenshots passed until each relevant image has a current expectation and a recorded successful replay.
