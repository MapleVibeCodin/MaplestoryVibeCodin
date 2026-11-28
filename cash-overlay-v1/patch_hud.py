"""Verify expected upstream HUD layout and add labels without changing recognition code."""
from pathlib import Path
p=Path(__file__).with_name("hud.py")
s=p.read_text(encoding="utf-8")
for old,new in [
 ('"MESOS / HR", c.get("mesos_rate"', 'c.get("rate_label", "MESOS / HR"), c.get("mesos_rate"'),
 ('"MESOS GAINED", c.get("mesos_gained"', 'c.get("gain_label", "MESOS GAINED"), c.get("mesos_gained"'),
 ('"MESOS SPENT", c.get("mesos_spent"', 'c.get("spent_label", "MESOS SPENT"), c.get("mesos_spent"')]:
    if s.count(old)!=1:
        raise SystemExit("Upstream HUD mismatch; stopping without writing")
    s=s.replace(old,new,1)
from map_reader_fix import patch_reader_source
reader=p.with_name("maple_exp.py")
reader_source=patch_reader_source(reader.read_text(encoding="utf-8"))
reader.write_text(reader_source,encoding="utf-8")
p.write_text(s,encoding="utf-8")
