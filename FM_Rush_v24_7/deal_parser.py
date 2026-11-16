"""Parse only the information needed for an HeneFM flip alert.

The parser never guesses a Buy At price from resale or profit values.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from route_logic import parse_alert
from profit_filter import filter_profit, parse_mesos, ProfitDecision

# HeneFM embeds have multiple columns and Discord OCR may put column labels
# together on one line and their values on the next.
MONEY = r'(?P<price>\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(?P<suffix>[KMBkmb]?)'
MONEY_RE = re.compile(MONEY, re.I)
CC_FM_RE = re.compile(r'\b(?:CH|CC|CHANNEL)\s*[.:#\-]?\s*[0-9OIl]{1,2}\b.{0,45}?\bFM\s*[.:#\-]?\s*[0-9OIl]{1,2}\b', re.I)
STATS_RE = re.compile(r'(?i)\b(?:W\.DEF|M\.DEF|W\.ATK|M\.ATK|STR|DEX|INT|LUK|ACC|ATK|SPEED|JUMP|HP|MP|slots?|crit|CDMG)\b')
HEADER_RE = re.compile(r'^(?:henefm|buy\b|resell\b|profit\b|sells?\s+in\b|where\b|under\b|https?://|www\.)', re.I)

@dataclass(frozen=True)
class Deal:
    cc: int
    fm: int
    item: str
    stats: str
    ign: str
    buy_mesos: int | None
    profit: ProfitDecision

    @property
    def buy_label(self) -> str:
        if self.buy_mesos is None:
            return 'BUY AT: —'
        return f'BUY AT: {self.buy_mesos:,} MESOS'


def _number(text: str) -> int | None:
    found = MONEY_RE.search(text)
    if not found:
        return None
    val = (found.group('price') + found.group('suffix')).replace(' ', '')
    return parse_mesos(val)


def buy_price(text: str) -> int | None:
    """Purchase cost from explicit Buy field, not resale estimate.

    Handles `Buy 30K each`, `Buy at: 30,000`, and multi-column
    `Buy  Resell at  Profit\n30K each 38.9K ... +7.7K (26%)`.
    """
    lines = [re.sub(r'\s+', ' ', l).strip() for l in text.replace('\r', '\n').split('\n')]
    for i, line in enumerate(lines):
        found = re.search(r'\bBuy(?:\s+at)?\b\s*[:=]?\s*', line, re.I)
        if not found:
            continue
        tail = line[found.end():]
        # Don't mistake `Resell at 38K` or `Profit +10K` in the header for Buy.
        if re.match(r'(?:Resell|Profit|Price|each|$)', tail, re.I):
            # A standard column header: first value on the next useful line.
            for next_line in lines[i+1:i+4]:
                if not next_line:
                    continue
                if re.search(r'^(?:Where|Sells in|CH|CC|FM|henefm)', next_line, re.I):
                    break
                val = _number(next_line)
                if val is not None and not next_line.lstrip().startswith('+'):
                    return val
            continue
        # Sometimes buy price is in the same line after other labels.
        if (m := MONEY_RE.match(tail)) is not None:
            return parse_mesos((m.group('price')+m.group('suffix')).strip())
        if (m := re.search(r'(?<!\w)(?:price\s*)?'+MONEY, tail, re.I)) is not None:
            return parse_mesos((m.group('price')+m.group('suffix')).strip())
    return None


def get_ign(text: str) -> str:
    labeled = re.search(r'(?i)\b(?:IGN|Seller|Owner)\s*[:=]\s*([A-Za-z0-9_]{3,24})', text)
    if labeled:
        return labeled.group(1)
    for line in re.split(r'[\r\n]', text):
        found = CC_FM_RE.search(line)
        if not found:
            continue
        tail = line[found.end():]
        # The HeneFM Where field appends seller name after CH/FM.
        tail = re.sub(r'^[^A-Za-z0-9]+', '', tail)
        m = re.search(r'([A-Za-z][A-Za-z0-9_]{2,23})\s*$', tail)
        if m and m.group(1).lower() not in ('where','profit','resell'):
            return m.group(1)
    return ''


def parse_details(text: str) -> tuple[str, str, str]:
    raw = re.sub(r'\s*[·•|]\s*', ' · ', text.replace('\r', '\n'))
    lines = [re.sub(r'\s+', ' ', line).strip() for line in raw.split('\n')]
    stats=''; item=''
    for line in lines:
        if len(STATS_RE.findall(line)) >= 2 or (STATS_RE.search(line) and 'slots' in line.casefold()):
            stats=line[:130]
            break
    for line in lines:
        if not line or HEADER_RE.search(line) or CC_FM_RE.search(line) or line==stats:
            continue
        if 'AM' in line or 'PM' in line:
            if re.search(r'\b\d{1,2}:\d{2}\s*(?:AM|PM)\b',line, re.I):
                continue
        if line.lower().startswith(('30k each','buy','resell','profit')):
            continue
        # Skip value-only lines, including the multi-column metrics.
        if re.match(r'^[+\-]?\d+(?:\.\d+)?\s*[KMBkmb]?\b',line):
            continue
        if 'henefm.com/' in line.casefold() or 'cheapest other ask' in line.casefold():
            continue
        if len(line)>2:
            item=line[:80]
            break
    return item,stats,get_ign(text)


def parse_deal(text: str) -> Deal | None:
    cc_fm = parse_alert(text)
    if cc_fm is None:
        return None
    item, stats, ign = parse_details(text)
    return Deal(*cc_fm,item=item,stats=stats,ign=ign,buy_mesos=buy_price(text),profit=filter_profit(text))
