"""Cash-first local accounting. No capture, network, game input or market estimates."""
import csv
import math
import time
import uuid
from pathlib import Path

NPC = {"Lupin's Banana":37, "Green Mushroom Cap":14, "Raffle Petal":40,
       "Glowing Mushroom Spore":39, "Golden Stirge Wing":42, "Aqumander Tail":43,
       "Echopus Leg":44, "Duskmander Tail":49, "Rafflesia Petal":47, "Curse Eye Tail":33, "Evil Eye Tail":27,
       "Jr. Boogie Horn":35, "Cursed Doll":40, "Horny Mushroom Cap":22,
       "Charm of the Undead":24, "Stirge Wing":20, "Wooden Board":23, "Slate":24}

def rate(value, seconds):
    return round(value * 3600 / seconds) if seconds >= 60 else None

class CashLedger:
    def __init__(self):
        self.segment = uuid.uuid4().hex
        self.map = None
        self.seconds = 0.0
        self.raw = 0
        self.npc = 0
        self.unknown = {}
        self.messages = 0
        self.last = None
        self.active = False
        self.wallet_start = self.wallet_end = None
        self.wallet_at = None

    def tick(self, now, active, name):
        if self.last is not None and now < self.last:
            return
        if self.last is not None and self.active and active and name == self.map:
            # Do not silently count long UI stalls, suspended machines or unknown map time.
            delta = now - self.last
            if delta <= 3:
                self.seconds += delta
        self.last = now
        self.active = bool(active and name)
        if self.map is None and name:
            self.map = name

    def add(self, found, prices):
        if not self.active:
            return
        for p in found:
            if len(p) == 2 and p[0] == "mesos" and type(p[1]) is int and p[1] > 0:
                self.raw += p[1]
                self.messages += 1
            elif len(p) == 4 and p[0] == "item":
                _, name, qty, tab = p
                if not isinstance(name, str) or type(qty) is not int or qty <= 0:
                    continue
                # Temporary user policy: consumables are count-only, never NPC-valued.
                if str(tab).casefold() in ("cash","use"):
                    continue
                self.messages += 1
                price = prices.get(name.casefold())
                if type(price) is int and price >= 0:
                    self.npc += qty * price
                else:
                    self.unknown[name] = self.unknown.get(name, 0) + qty

    def wallet(self, value, seen, now):
        # One confirmed balance per timestamp, only while actively on the known map.
        if not self.active or type(value) is not int or value < 0 or seen is None:
            return
        if not 0 <= now - seen <= 3 or (self.wallet_at is not None and seen <= self.wallet_at):
            return
        if self.wallet_start is None:
            self.wallet_start = value
        self.wallet_end = value
        self.wallet_at = seen

    def snapshot(self):
        return {"segment":self.segment, "map":self.map or "", "active_seconds":round(self.seconds, 2),
                "observed_raw":self.raw if self.messages else None,
                "known_npc_value":self.npc if self.messages else None,
                "unknown_units":sum(self.unknown.values()),
                "raw_hr":rate(self.raw,self.seconds) if self.messages else None,
                "raw_plus_known_npc_hr":rate(self.raw+self.npc,self.seconds) if self.messages else None,
                "wallet_change":None if self.wallet_start is None else self.wallet_end-self.wallet_start}

def append_snapshot(path, ledger, **extra):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {"timestamp":time.strftime("%Y-%m-%dT%H:%M:%S%z"), **ledger.snapshot(), **extra}
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if f.tell() == 0:
            w.writeheader()
        w.writerow(row)
