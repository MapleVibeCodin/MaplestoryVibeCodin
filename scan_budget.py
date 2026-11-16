"""Small, deterministic scheduling rules for a CPU-safe shop-name scanner."""
from __future__ import annotations

# Target is first seen as soon as practical, but a constantly animated game must
# not force a full-frame neural OCR inference on every frame.
CAPTURE_PERIOD_S = 0.085      # <= ~12 fps (also enforced inside the capture callback)
SEARCH_OCR_PERIOD_S = 0.45   # <= ~2.2 searches per second while moving
STATIC_RETRY_S = 1.6        # no need to rescan an unchanging screen 2x/s
VERIFY_PERIOD_S = 2.2       # less expensive visual-template tracking once found
LOST_OCR_PERIOD_S = 0.7     # when template following failed, seek a fresh match
PREVIEW_PERIOD_S = 0.2      # <= 5 UI preview updates / second


def should_ocr(now: float, last: float, image_changed: bool,
               tracking_good: bool, ever_found: bool) -> bool:
    """Bound OCR workload even on animated screenshots; never skip initial pass."""
    if last <= 0:
        return True
    elapsed = now - last + 1e-9  # guard floating-point boundary rounding
    if tracking_good:
        return elapsed >= VERIFY_PERIOD_S
    if ever_found:
        return elapsed >= (LOST_OCR_PERIOD_S if image_changed else STATIC_RETRY_S)
    return elapsed >= (SEARCH_OCR_PERIOD_S if image_changed else STATIC_RETRY_S)


class ScanDutyBudget:
    """Limit sustained search CPU time to a fraction of one logical processor.

    A scan may burst immediately. Its measured thread CPU time buys a cooldown;
    target changes and manual retries must share the same budget.
    """
    def __init__(self, fraction=.35):
        if not 0 < fraction <= 1:
            raise ValueError('CPU fraction must be in (0, 1]')
        self.fraction=fraction
        self.ready_at=0.

    def remaining(self, now):
        return max(0., self.ready_at-now)

    def charge(self, cpu_seconds, now):
        cooldown=max(0.,cpu_seconds)*(1/self.fraction-1)
        self.ready_at=max(now,self.ready_at)+cooldown
