"""Pure recognition guards: no capture, input, or platform dependencies."""
import re

MAX_HIGHLIGHT_AGE = 0.35
_NUMBER = r'(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)'
_PRICE = re.compile(rf'(?:({_NUMBER})\s+)?for\s+({_NUMBER})\s+mesos', re.I | re.ASCII)

def parse_price_line(text):
    """Do not silently repair malformed grouping or look-alike characters."""
    m = _PRICE.fullmatch(text.strip())
    if not m:
        return None
    quantity, amount = m.groups()
    if quantity is not None and int(quantity.replace(',', '')) <= 0:
        return None
    return int(amount.replace(',', ''))

def highlight_expired(result, observed_at, now):
    """An old positive result is not evidence of the current screen."""
    return bool(result and result.get('hits') and
                (observed_at is None or not 0 <= now-observed_at <= MAX_HIGHLIGHT_AGE))

def revalidate_changed_hits(hits, before, after, strict):
    """Changed frame cannot retain green; exact scrolls require full recheck."""
    if strict or -1 not in before or before[-1] != after.get(-1):
        return []
    stable = [(i, 'SOLD_CHECK' if mode in ('SOLD', 'SOLD_CHECK') else 'ROW_CHECK' if mode == 'MATCH' else mode)
              for i, mode in hits if i in before and before[i] == after.get(i)
              and mode in ('MATCH', 'PRICE_CHECK', 'ROW_CHECK', 'SOLD', 'SOLD_CHECK')]
    return stable if len(stable) == 1 else []
