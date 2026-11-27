# Section 0 — recovery and baseline freeze
2026-11-27. Resume request: Resume FM Sprint Hybrid from checkpoint de9c508; read plan, relevant source, transcripts, benchmarks and tests; start at section 0, execute sequentially, prioritize first-correct-highlight and human alert-to-item, checkpoint each message, preserve originals, no Work/Codex.

Verified source branch fm-sprint/dual-engine is identical to de9c50897729417a9f13ff8409d543def3f4d0d0. Created isolated fm-sprint/hybrid at that exact SHA. R3 aeb991dafc99ac335d8a2726419e7dbfca4bc50d to de9c508 comparison: 11 documentation-only commits, five added files, no runtime modifications. All seven package file blob hashes match NEXT-CHAT.md:
- README.md e1fbfd1a553f3f72f94d7f4075d572842ae19c79
- START_FM_SPRINT.ps1 c6d0643fed254930ddbf8a6d7694182830bf5391
- START_MAPLESTORY.bat 8ac0b6f5db4ff43d35b2715e17bc28396469f2d7
- START_RUNESCAPE.bat d4bc1782d8276456b9e194f7cf556f199839b6b4
- fm_sprint.py f3e224ba6c14d1c93d07f5598b4d99a85f871e34
- fm_sprint_core.py d8f6e0ff4071b36db9ea84ad266a79c44eb141af
- test_fm_sprint.py 14f044495e40163579d4a8b2166a5741bead032c

Read pinned Scanner Nov 20/shop_inventory.py at a80a9ffbcc2a4a1616b5cfdc8c91b35c430df8fb (blob f9e561509ffb60c9c1188f0a492b85a7a3d59c56). NameOCRCache contract: sorted unique rows; exact 16-byte BLAKE2b of native BGR name pixels x40:198, y26+40*row through 20 rows, price excluded; target-independent LRU 512; batch OCR misses only; trimmed text lines grouped by compact slot; blank returned but never cached; eviction after whole batch. Name matching downstream uses NFKC/casefold/whitespace normalization and rejects duplicate/ambiguous truncated candidates. Preserve that boundary.

Recovered R3 source/core/tests, launcher, prior replay report, transcript excerpts, root and performance-lab handoff. Prior 27-video replay is retained, not rerun. Private replay ZIP not present in current container; recover only when required for section 5. No new Windows/live tests or latency claim. Section 0 complete for source recovery, next section 1: extract exact lookup/store API and differential test; no integration yet.
