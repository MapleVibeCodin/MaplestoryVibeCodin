"""Pure route and alert parsing logic. No input injection, network, or game access."""
from __future__ import annotations
import re
from dataclasses import dataclass

CHANNELS = 40
COLUMNS = 8
ROOMS = 20
START_CHANNEL = 20

# Updated FM schematic based on user correction:
# four rows: 1–6, 7–12, 13–16, 17–20
# rope spine aligned between 3–4, 9–10, 14–15, and 18–19.
ROW_Y = {
    'ROW4': 48,   # FM 17–20
    'ROW3': 114,  # FM 13–16
    'ROW2': 180,  # FM 7–12
    'ROW1': 246,  # FM 1–6
}
PORTALS = {
    **{n: (130 + (n - 1) * 102, ROW_Y['ROW1'], 'ROW1') for n in range(1, 7)},
    **{n: (130 + (n - 7) * 102, ROW_Y['ROW2'], 'ROW2') for n in range(7, 13)},
    **{n: (232 + (n - 13) * 102, ROW_Y['ROW3'], 'ROW3') for n in range(13, 17)},
    **{n: (232 + (n - 17) * 102, ROW_Y['ROW4'], 'ROW4') for n in range(17, 21)},
}
# User-selected waiting position: halfway up the upper rope between rows 3 and 4.
# Schematic coordinate only; not a measured in-game pixel coordinate.
START_POINT = (385, (ROW_Y["ROW4"] + ROW_Y["ROW3"]) // 2)
ROPE_X = 385
BOTTOM_WARP = ((705, ROW_Y['ROW2']), (705, ROW_Y['ROW1']))
ROPE_POINTS = {
    'ROW4': (ROPE_X, ROW_Y['ROW4']),
    'ROW3': (ROPE_X, ROW_Y['ROW3']),
    'ROW2': (ROPE_X, ROW_Y['ROW2']),
    'ROW1': (ROPE_X, ROW_Y['ROW1']),
}

@dataclass(frozen=True)
class Plan:
    channel: int
    fm: int
    channel_keys: tuple[str, ...]
    tier: str
    ordinal: int
    ordinal_total: int
    direction: str
    route_text: str
    waypoints: tuple[tuple[int, int], ...]


def parse_alert(text: str) -> tuple[int, int] | None:
    """Parse channel+FM even when other numbers (prices) appear in an alert."""
    if not text:
        return None
    text = text.replace('\u200b', '').replace('\ufeff', '').replace('＃', '#')
    # OCR often merges two nearby fields: `CC 1FM 13`. Split that boundary.
    text = re.sub(r'(?<=\d)(?=F\s*M\b)', ' ', text, flags=re.I)
    cpat = r'(?<![A-Z0-9])(?:C\s*C|C\s*H|CHANNEL|CHNL)\s*(?:[.:#=\-]|NO\.?|NUMBER)?\s*([0-9OIl]{1,2})(?!\d)'
    fpat = r'(?<![A-Z0-9])(?:F\s*M|FREE\s*MARKET)\s*(?:[.:#=\-]|ROOM)?\s*([0-9OIl]{1,2})(?!\d)'
    x = re.search(cpat, text, flags=re.I)
    y = re.search(fpat, text, flags=re.I)
    if not x or not y:
        return None
    fix = lambda s: int(s.upper().replace('O', '0').replace('I', '1').replace('L', '1'))
    try:
        cc, fm = fix(x.group(1)), fix(y.group(1))
    except ValueError:
        return None
    if 1 <= cc <= CHANNELS and 1 <= fm <= ROOMS:
        return cc, fm
    return None


def channel_keys(cc: int, start: int = START_CHANNEL) -> tuple[str, ...]:
    if not (1 <= cc <= CHANNELS and 1 <= start <= CHANNELS):
        raise ValueError('Channel must be between 1 and 40')
    sr, sc = divmod(start - 1, COLUMNS)
    tr, tc = divmod(cc - 1, COLUMNS)
    vertical = ('UP',) * max(0, sr - tr) + ('DOWN',) * max(0, tr - sr)
    horizontal = ('LEFT',) * max(0, sc - tc) + ('RIGHT',) * max(0, tc - sc)
    return vertical + horizontal + ('ENTER',)


def _row_route(fm: int) -> tuple[int, int, str, str, tuple[tuple[int, int], ...]]:
    x, y, tier = PORTALS[fm]
    side = 'LEFT' if x < ROPE_X else 'RIGHT'
    if 1 <= fm <= 6:
        ordinal, total = fm, 6
        direction = 'LEFT'
        rt = f'DROP to ROW 2 → RIGHT to DOWN-WARP → ROW 1 → LEFT to FM {fm} ({ordinal}/6)'
        route = (START_POINT, ROPE_POINTS['ROW3'], ROPE_POINTS['ROW2'],
                 BOTTOM_WARP[0], BOTTOM_WARP[1], (x, y))
    elif 7 <= fm <= 12:
        ordinal, total = fm - 6, 6
        direction = side
        rt = f'DROP to ROW 2 → {side} to FM {fm} ({ordinal}/6)'
        route = (START_POINT, ROPE_POINTS['ROW3'], ROPE_POINTS['ROW2'], (x, y))
    elif 13 <= fm <= 16:
        ordinal, total = fm - 12, 4
        direction = side
        rt = f'DROP to ROW 3 → {side} to FM {fm} ({ordinal}/4)'
        route = (START_POINT, ROPE_POINTS['ROW3'], (x, y))
    else:
        ordinal, total = fm - 16, 4
        direction = side
        rt = f'CLIMB to ROW 4 → {side} to FM {fm} ({ordinal}/4)'
        route = (START_POINT, ROPE_POINTS['ROW4'], (x, y))
    return ordinal, total, direction, rt, route


def plan(cc: int, fm: int, start_channel: int = START_CHANNEL) -> Plan:
    if not 1 <= fm <= ROOMS:
        raise ValueError('FM must be between 1 and 20')
    keys = channel_keys(cc, start_channel)
    _, _, tier = PORTALS[fm]
    ordinal, total, direction, rt, route = _row_route(fm)
    return Plan(cc, fm, keys, tier, ordinal, total, direction, rt, route)


def arrows(keys: tuple[str, ...]) -> str:
    values = {'UP': '↑', 'DOWN': '↓', 'LEFT': '←', 'RIGHT': '→', 'ENTER': '↵'}
    return ' '.join(values[k] for k in keys)
