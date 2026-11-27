# FIX-003-Logitech-Shortcuts: Shop/channel commands stopped working after jitter fix

Status: **Source correction; live pending**

Passive Stability disabled user-triggered pointer shortcuts, an unacceptable regression. Smooth Shortcuts restores the exact SoftLock override and delegates to one inherited handler; Ctrl+Alt+J/M shop, Ctrl+Alt+C channel, Shift+1/2 lock/unlock. No G HUB changes. Implementation https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/456b90748e6440870b4f0ea9cbc475210c8b5c0e/The%20ultimate%20beast/fm_sprint.py; historical source https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/11931bde19b10ed680bcd5a106efa10d64b6edea/The%20ultimate%20beast/fm_sprint.py; base registrations https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/a80a9ffbcc2a4a1616b5cfdc8c91b35c430df8fb/Scanner%20Nov%2020/trade_hotkeys.py. Regression: verify explicit controller remains wired, passive actions remain non-dispatched, F12 guard remains; manual Windows observation needed. Never solve jitter by removing these shortcuts.

Update this record with each recurrence, actual check results, and the new commit. Never overwrite historical evidence.


## Spatial iteration
Runtime 4b1635d4b85dfc183fc6f0ac2f3d2e61380a436c. Existing registered shortcuts, F12 stop guard and single explicit inherited controller logic preserved. New mixin adapts the pinned handler solely for correlation and stale-projection checks; no automatic cursor movement or clicks added. Static source verified; live registration and timing remain pending.
