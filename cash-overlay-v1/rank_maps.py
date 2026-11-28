"""Offline MCWO archive ranking, without fetching or submitting anything."""
import argparse
import json
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("archive",type=Path)
    p.add_argument("--level",type=int,default=45)
    p.add_argument("--party",choices=["solo","party"],default="solo")
    p.add_argument("--early",action="store_true")
    a=p.parse_args()
    data=json.loads(a.archive.read_text(encoding="utf-8"))
    for q in data["results"]:
        if q["level"]==a.level and q["party"]==a.party:
            rows=[r for r in q["rows"] if r[1] is not None and (a.early or r[6])]
            for r in sorted(rows,key=lambda r:-r[1]):
                print(f"{r[1]:>8,}  {r[0]}  (n={r[3]} EXP contributors; {'ranked' if r[6] else 'early'})")
            return
    raise SystemExit("No matching query")
if __name__=="__main__":
    main()
