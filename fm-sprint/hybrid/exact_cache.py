"""Section 1: exact row cache, injected pinned capture/OCR functions."""
from collections import OrderedDict


class ExactRowCache:
    def __init__(self, fingerprint, prepare, *, scale=3, slot=28, height=20, limit=512):
        if limit < 0:
            raise ValueError('negative cache limit')
        self.fingerprint = fingerprint
        self.prepare = prepare
        self.scale, self.slot, self.height = scale, slot, height
        self.limit = limit
        self.entries = OrderedDict()

    def lookup(self, key):
        if key not in self.entries:
            return None
        self.entries.move_to_end(key)
        return self.entries[key]

    def store(self, key, value):
        # Trim after the batch, matching pinned NameOCRCache ordering.
        if value:
            self.entries[key] = value
            self.entries.move_to_end(key)

    def evict(self):
        while len(self.entries) > self.limit:
            self.entries.popitem(last=False)

    def read_missing(self, frame, rows, ocr):
        png, layout = self.prepare(frame, rows)
        raw = ocr.recognize(png)
        grouped = {row: [] for row in rows}
        for line in raw:
            yy = float(line.get('y', -100)) / self.scale
            slot = int(yy // self.slot)
            if slot in layout and yy - slot * self.slot < self.height:
                text = str(line.get('text', '')).strip()
                if text:
                    grouped[layout[slot]].append(text)
        return {row: ' '.join(grouped[row]) for row in rows}

    def recognize(self, frame, rows, ocr):
        rows = tuple(sorted(set(rows)))
        names, keys = {}, {}
        for row in rows:
            key = self.fingerprint(frame, row)
            keys[row] = key
            value = self.lookup(key)
            if value is not None:
                names[row] = value
        missing = [row for row in rows if row not in names]
        if missing:
            fresh = self.read_missing(frame, missing, ocr)
            for row in missing:
                value = fresh[row]
                names[row] = value
                self.store(keys[row], value)
            self.evict()
        return names, len(rows) - len(missing), len(missing), bool(missing)
