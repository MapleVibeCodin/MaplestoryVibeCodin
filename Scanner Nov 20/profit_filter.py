"""Strict, profit gate for pasted HeneFM alerts.

A pasted alert is accepted only when a LOCAL profit amount and percentage
belong to the same price statement and both thresholds are reached.
If either value is missing/uncertain, fail closed instead of showing it.
"""
from __future__ import annotations
from dataclasses import dataclass
import re

MIN_MESOS = 15_000
MIN_PERCENT = 15.0
FILTER_LABEL = 'FILTER ON: PROFIT ≥15% AND ≥15,000 MESOS'

# Numeric forms from HeneFM and OCR: +10K, +10,000, +0.01M, +10000 mesos.
_NUMBER = r'[+-]?\s*(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?\s*[KMBkmb]?'
_PERCENT = r'[+-]?\s*\d+(?:[.,]\d+)?\s*%'
_AMOUNT_PERCENT = re.compile(r'(?<![\w.%])(?P<amount>' + _NUMBER + r')(?![\d.,%])\s*(?:mesos?)?\s*[\(\[]?\s*(?P<percent>' + _PERCENT + r')\s*[\)\]]?', re.I)
_PERCENT_AMOUNT = re.compile(r'(?<![\w])(?P<percent>' + _PERCENT + r')\s*[\)\]]?\s*(?:profit|mesos?)?\s*[:=]?\s*(?P<amount>' + _NUMBER + r')(?![\d.,])', re.I)
_LABEL = re.compile(r'\b(?:profit|gain|earnings?|flips?\s+profit)\b\s*[:=]?\s*', re.I)


@dataclass(frozen=True)
class ProfitDecision:
    accepted: bool
    mesos: int | None = None
    percent: float | None = None
    reason: str = ''

    @property
    def label(self):
        if self.mesos is None or self.percent is None:
            return 'PROFIT: —'
        return ('UNUSUALLY CHEAP · ' if self.reason == 'unusually cheap' else '') + f'PROFIT: {self.mesos:+,} MESOS  ({self.percent:g}%)'


def parse_mesos(value: str) -> int | None:
    value = value.replace(' ', '').replace(',', '')
    found = re.fullmatch(r'([+-]?)(\d+(?:\.\d+)?)([KMBkmb]?)', value)
    if not found:
        return None
    sign, quantity, suffix = found.groups()
    multiple = {'': 1, 'K': 1_000, 'M': 1_000_000, 'B': 1_000_000_000}[suffix.upper()]
    number = float(quantity) * multiple
    if number < 0 or sign == '-':
        return None
    return round(number)


def parse_percentage(value: str) -> float | None:
    cleaned = value.replace(' ', '').replace(',', '.').rstrip('%')
    try:
        number = float(cleaned)
    except ValueError:
        return None
    return number if 0 <= number <= 1000 else None


def _pairs(segment: str):
    for pattern in (_AMOUNT_PERCENT, _PERCENT_AMOUNT):
        for found in pattern.finditer(segment):
            amount_text = found.group('amount').strip()
            percent_text = found.group('percent').strip()
            mesos = parse_mesos(amount_text)
            percent = parse_percentage(percent_text)
            if mesos is None or percent is None:
                continue
            # Absurd values are an OCR failure; don't show them.
            if mesos > 1_000_000_000_000:
                continue
            yield found.start(), mesos, percent


def filter_profit(text: str, min_mesos: int = MIN_MESOS,
                  min_percent: float = MIN_PERCENT) -> ProfitDecision:
    if not text:
        return ProfitDecision(False, reason='empty OCR')
    clean = text.replace('\u200b', '').replace('\ufeff', '').replace('\r', '\n')
    clean = re.sub(r'[\u2212\u2013\u2014]', '-', clean)
    # Tesseract occasionally reads the decimal in HeneFM's '+12.7K' as
    # '+12-7K'. Reconstruct that specific signed currency notation only.
    clean = re.sub(r'\+\s*(\d+)\s*-\s*(\d{1,2})(?=\s*[KMB]\b)',
                   r'+\1.\2', clean, flags=re.I)
    # Common pasted alert variants: "+10,000 (15%)", "+10K (15%)".
    labels = list(_LABEL.finditer(clean))
    if labels:
        # Prefer pairs near the literal Profit label, allowing HeneFM's multi-column layout.
        # There may be "Buy / Resell at / Profit" followed by values on the next line.
        candidates = []
        for label in labels:
            tail = clean[label.end():label.end()+280]
            for offset, mesos, percent in _pairs(tail):
                candidates.append((offset, mesos, percent))
        if not candidates:
            return ProfitDecision(False, reason='profit amount/percent missing')
        _, mesos, percent = min(candidates, key=lambda v: v[0])
    else:
        # No label: accept only an explicit +amount-and-percent pair, not a random
        # item stat like +2% or a plain purchase price.
        candidates = []
        for offset, mesos, percent in _pairs(clean):
            snippet=clean[offset:offset+45].lstrip()
            if snippet.startswith('+'):
                candidates.append((offset,mesos,percent))
        if not candidates:
            return ProfitDecision(False, reason='no trustworthy profit pair')
        _, mesos, percent = candidates[0]
    eligible = mesos >= min_mesos and percent >= min_percent
    return ProfitDecision(eligible, mesos=mesos, percent=percent,
                          reason='passed' if eligible else 'below minimum')
