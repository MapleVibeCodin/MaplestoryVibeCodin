"""Section 3: exact first, qualified visual second, batched OCR last."""
from dataclasses import dataclass
from time import perf_counter_ns


@dataclass(frozen=True)
class ScanTelemetry:
    raw_hits: int
    visual_hits: int
    signature_attempts: int
    rejected: int
    ocr_rows: int
    ocr_calls: int
    elapsed_ns: int
    provenance: tuple


class HybridCache:
    def __init__(self, exact, bank, signature):
        self.exact = exact
        self.bank = bank
        self.signature = signature
        self.last_scan = None

    def recognize(self, frame, rows, ocr, *, allow_visual=False, visual_eligible=()):
        # Caller must establish visibility, strict-scroll policy and target freshness.
        # Default is baseline-only, not implicit visual permission.
        self.last_scan = None
        start = perf_counter_ns()
        rows = tuple(sorted(set(rows)))
        names, keys, paths = {}, {}, {}
        raw_hits = visual_hits = attempts = rejected = 0
        for row in rows:
            key = self.exact.fingerprint(frame, row)
            keys[row] = key
            value = self.exact.lookup(key)
            if value is not None:
                names[row] = value
                paths[row] = 'raw_ocr_cache'
                raw_hits += 1
        missing = [row for row in rows if row not in names]
        if missing and allow_visual is True and self.bank:
            eligible = frozenset(visual_eligible)
            for row in missing:
                if row not in eligible:
                    rejected += 1
                    continue
                attempts += 1
                key = self.signature(frame, row)
                review = self.bank.lookup(key, eligible=True)
                if review is None:
                    rejected += 1
                    continue
                names[row] = review.name
                paths[row] = 'verified_visual'
                visual_hits += 1
        missing = [row for row in missing if row not in names]
        if missing:
            fresh = self.exact.read_missing(frame, missing, ocr)
            for row in missing:
                value = fresh[row]
                names[row] = value
                paths[row] = 'ocr' if value else 'ocr_blank'
                # Visual answers never enter the exact OCR cache, nor does OCR
                # enter the reviewed visual bank. Keep origin and invalidation separate.
                self.exact.store(keys[row], value)
            self.exact.evict()
        self.last_scan = ScanTelemetry(raw_hits, visual_hits, attempts, rejected,
            len(missing), int(bool(missing)), perf_counter_ns()-start,
            tuple(sorted(paths.items())))
        return names, raw_hits + visual_hits, len(missing), bool(missing)
