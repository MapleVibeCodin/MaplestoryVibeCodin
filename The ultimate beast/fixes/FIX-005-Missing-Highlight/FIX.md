# FIX-005-Missing-Highlight: Shop item fails to highlight or name mismatches

Status: **Open**

250 inventory timing records: all fallback geometry/name-only; 129 OCR scans, one candidate-bearing locked attempt, no verified unique match. Exact cause unknown (wrong shop, OCR mismatch, tooltip, sold row, room/focus loss). Status diagnostics added in https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/456b90748e6440870b4f0ea9cbc475210c8b5c0e/The%20ultimate%20beast/fm_sprint.py and feedback; do not infer exact OCR names from status. Existing scanner gates https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/a80a9ffbcc2a4a1616b5cfdc8c91b35c430df8fb/Scanner%20Nov%2020/shop_inventory.py and https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/a80a9ffbcc2a4a1616b5cfdc8c91b35c430df8fb/Scanner%20Nov%2020/fm_rush.py. Regression: native labeled shop evidence, exact target/name comparison, no stale/wrong item highlight, maintain strict scroll guards. Historical 70 tests do not prove live highlighting. No verified fix; use future actual diagnostic evidence, do not rerun unchanged research.

Update this record with each recurrence, actual check results, and the new commit. Never overwrite historical evidence.
