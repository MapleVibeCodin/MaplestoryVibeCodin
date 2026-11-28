"""Cash Overlay v1: offline extension of the pinned Javipen overlay."""
import os
import sys
import time
from pathlib import Path
from cash_core import CashLedger, NPC, append_snapshot

os.environ["MAPLE_EXP_DATA"] = str(Path(os.environ["LOCALAPPDATA"]) / "MapleCashOverlayV1")
import maple_exp as base

base.WINDOW_TITLE = "Maple Cash Overlay"
base.OLD_TITLES = ()
base.VERSION = "Cash 1.0"
base.DEFAULTS.update(hud_layout="full", hud_repot=False, hud_scale=0.45,
                     hud_theme="steel", hotkeys_on=False, gap_seconds=120)
base.LOGGING = True
base.LOOT_PRICES.update(NPC)
OriginalApp = base.App

def fmt(v):
    return "—" if v is None else f"{v:,}"

class CashApp(OriginalApp):
    def __init__(self, root, templates):
        self.cash = CashLedger()
        self.last_export = 0.0
        self.last_signature = None
        super().__init__(root, templates)
        self._original_show = self.hud.show
        self.hud.show = self._show_cash
        root.title(base.WINDOW_TITLE)

    def _export(self, force=False):
        if self.cash.map is None or not (self.cash.seconds or self.cash.messages):
            return
        now = time.monotonic()
        if not force and now - self.last_export < 30:
            return
        s = self.cash.snapshot()
        sig = tuple(s.values())
        if sig == self.last_signature:
            return
        try:
            append_snapshot(base.DATA_DIR / "cash-sessions.csv", self.cash,
                            exp_gained=getattr(self.tracker,"gained",None),
                            level=getattr(self,"level",None), party=getattr(self,"party",None))
            self.last_export, self.last_signature = now, sig
        except OSError as e:
            base.log_error("saving cash snapshots", e)

    def _state_cash(self, now):
        name = self.session.map
        here = self.session.here
        active = bool(self.tracker.running and name and name == here
                      and not self.in_town and not self.map_hidden)
        if name and self.cash.map and name != self.cash.map:
            self._export(True)
            self.cash = CashLedger()
            self.last_signature = None
        self.cash.tick(now, active, name)
        self.cash.wallet(self.meso.value, self.meso.seen_at, now)

    def _pickups(self, found, when):
        now = time.monotonic()
        self._state_cash(now)
        # Reject delayed queued messages rather than assigning them to a later map.
        if 0 <= now-when <= 2:
            prices = {k.casefold():v for k,v in base.LOOT_PRICES.items()}
            prices.update({k.casefold():v for k,v in (self.cfg.get("loot_prices") or {}).items()})
            self.cash.add(found, prices)
        super()._pickups(found, when)

    def _update_display(self):
        self._state_cash(time.monotonic())
        super()._update_display()
        self._export()

    def _show_cash(self, rect, content):
        s = self.cash.snapshot()
        c = dict(content)
        c.update(mesos_rate=fmt(s["raw_hr"]), net_label="RAW + NPC / HR",
                 mesos_net=fmt(s["raw_plus_known_npc_hr"]),
                 mesos_gained=fmt(s["observed_raw"]),
                 mesos_spent=fmt(s["wallet_change"]),
                 rate_label="OBS. MESOS / HR", gain_label="OBS. PICKUPS",
                 spent_label="WALLET CHANGE")
        # Never silently call an estimated or partially observed amount net profit.
        if s["unknown_units"]:
            c["net_label"] = "RAW + NPC* / HR"
        return self._original_show(rect, c)

    def reset(self):
        self._export(True)
        self.cash = CashLedger()
        self.last_signature = None
        super().reset()

    def close(self):
        self._export(True)
        super().close()

if __name__ == "__main__":
    base.App = CashApp
    base.main()
