# FIX-002-Cursor-Jitter: Mouse flies across screen; unwanted shop clearing

Status: **Source correction; live pending**

SoftLock emitted automatic park_channel, park_shop_normal, park_shop_cc and park_clear in addition to inherited shortcuts. In 3 trial reports, 19 automatic action emissions, 10 automatic handoff outcomes (0 successful), two displacements 539.8 and 1158.6 px coincident with park_clear (<1 ms). Source-level cause confirmed; not every physical jump attributable. Smooth Shortcuts suppresses scene dispatch, park/at no-op, no F9 automated clicks. Source: https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/456b90748e6440870b4f0ea9cbc475210c8b5c0e/The%20ultimate%20beast/fm_sprint.py. Regression: no scene-to-input dispatch, no cursor move without explicit command; preserve FIX-003. Existing live diagnostic evidence: checkpoint b531ba456321aa5416de9d5a55fa33db677e9f33. Do not claim jitter eliminated until live verified.

Update this record with each recurrence, actual check results, and the new commit. Never overwrite historical evidence.


## Centered live evidence
2026-11-27 Centered: all 17 recorded passive action batches dispatched=false; three completed shop pointer watches recorded zero outside displacement. This supports suppression of unsolicited scene actions, but cannot establish all cursor behavior or correct target placement. No runtime changes.
