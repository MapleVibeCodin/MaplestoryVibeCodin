"""Section 2: explicitly reviewed visual signatures, never OCR self-training."""
from collections import OrderedDict
from dataclasses import dataclass
import unicodedata


def normalized(name):
    return ' '.join(unicodedata.normalize('NFKC', name).casefold().split())


@dataclass(frozen=True)
class Review:
    name: str
    source_id: str
    review_id: str
    method: str = 'manual-independent'
    native: bool = False
    complete: bool = False
    unobscured: bool = False


class VerifiedVisualBank:
    def __init__(self, limit=2048, conflict_limit=2048):
        if limit < 1 or conflict_limit < 1:
            raise ValueError('positive limits required')
        self.limit = limit
        self.conflict_limit = conflict_limit
        self.entries = OrderedDict()
        self.conflicts = set()
        self.disabled = False

    @staticmethod
    def valid_key(key):
        return isinstance(key, bytes) and len(key) == 20

    @staticmethod
    def valid_review(review):
        if not isinstance(review, Review) or not all(isinstance(x, str) for x in
                (review.name, review.source_id, review.review_id, review.method)):
            return False
        name = normalized(review.name)
        return (review.method == 'manual-independent' and review.native is True
                and review.complete is True and review.unobscured is True
                and bool(name) and not name.endswith(('...', '…'))
                and '\ufffd' not in name and not any(ord(c) < 32 for c in review.name)
                and 0 < len(review.name) <= 256
                and 0 < len(review.source_id.strip()) <= 128
                and 0 < len(review.review_id.strip()) <= 128)

    def __bool__(self):
        return not self.disabled and bool(self.entries)

    def invalidate(self, key):
        if not self.valid_key(key):
            return
        self.entries.pop(key, None)
        if key in self.conflicts:
            return
        if len(self.conflicts) >= self.conflict_limit:
            # Never silently forget a conflict to admit a later positive.
            self.disabled = True
            self.entries.clear()
            return
        self.conflicts.add(key)

    def qualify(self, key, review):
        if (self.disabled or not self.valid_key(key) or key in self.conflicts
                or not self.valid_review(review)):
            return False
        existing = self.entries.get(key)
        if existing is not None and normalized(existing.name) != normalized(review.name):
            self.invalidate(key)
            return False
        # Keep the first independent evidence for this signature; no OCR promotion.
        if existing is None:
            self.entries[key] = review
        self.entries.move_to_end(key)
        while len(self.entries) > self.limit:
            self.entries.popitem(last=False)
        return True

    def lookup(self, key, *, eligible):
        if self.disabled or eligible is not True or not self.valid_key(key):
            return None
        value = self.entries.get(key)
        if value is not None:
            self.entries.move_to_end(key)
        return value
