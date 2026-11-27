# FIX-006-SoftLock-Stale-Target: Click next listing without manual unlock; stale pointer work

Status: **Implemented; live pending**

SoftLock permits explicit replacement under archive RLock; passive feed must not steal current lock; old listing pending and invalid selection must retain lock. New target cancels pending pointer generations before refresh. Source: https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/456b90748e6440870b4f0ea9cbc475210c8b5c0e/The%20ultimate%20beast/run_beast.py and https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/456b90748e6440870b4f0ea9cbc475210c8b5c0e/The%20ultimate%20beast/fm_sprint.py. Existing [test_soft_lock.py](../../research/test_soft_lock.py) covers 10 cases including concurrency, invalid selection, save failure, old pending cancellation. SoftLock historical 70/70 offline passed at 11931bde19b10ed680bcd5a106efa10d64b6edea; later 15 static checks only. Regression: run original relevant tests and confirm current revision preserves explicit replacement, unlock/skip and cancellation. No live browser confirmation.

Update this record with each recurrence, actual check results, and the new commit. Never overwrite historical evidence.
