# FIX-001-Focused-Mouse-Lock: Mouse cannot move while game has focus

Status: **Implemented; live pending**

Source-level cause: direct focused pointer movement may be rejected by the game. Earlier proven design releases scanner focus on explicit shortcut and waits for game focus release before attempting one move. Source: https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/a80a9ffbcc2a4a1616b5cfdc8c91b35c430df8fb/Scanner%20Nov%2020/fm_rush.py (move_pointer_to_target); current wrapper: https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/456b90748e6440870b4f0ea9cbc475210c8b5c0e/The%20ultimate%20beast/fm_sprint.py. Historical regression: [FOCUS-REGRESSION.md](../../research/FOCUS-REGRESSION.md), [test_focus_release.py](../../research/test_focus_release.py). Mandatory check: explicit request only, cancel stale target or stop, no blind retries; observed live successful pointer placement and cancellation must be verified separately. Do not introduce a second controller or force a pointer past app restrictions. Live trial had failed automatic handoffs; this does not prove the explicit path works on every attempt.

Update this record with each recurrence, actual check results, and the new commit. Never overwrite historical evidence.
