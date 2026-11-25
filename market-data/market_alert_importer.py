#!/usr/bin/env python3
"""Offline importer for manually supplied market alerts. No network access."""
import argparse, csv, hashlib, json, re, sqlite3
from decimal import Decimal
from pathlib import Path

MONEY = r'([\d,.]+\s*[KM]?)'

def amount(s):
    s=s.replace(',','').replace(' ','').upper()
    scale={'K':1000,'M':1000000}.get(s[-1],1)
    return int(Decimal(s[:-1] if scale!=1 else s)*scale)

def parse(text, date=None):
    rows=[]; rejected=[]; stamp=None
    for block in re.split(r'henefm\.com/flips(?:/deals)?',text,flags=re.I):
        lines=[l.strip() for l in block.splitlines() if l.strip()]
        for l in lines:
            m=re.search(r'\b(\d{1,2}:\d{2}\s*[AP]M)\b',l,re.I)
            if m: stamp=m[1]
        lines=[l for l in lines if l not in ('HeneFM','APP') and not re.match(r'^—\s*\d{1,2}:\d{2}',l)]
        if 'Buy' not in lines:
            if lines: rejected.append({'reason':'missing Buy','text':'\n'.join(lines)})
            continue
        try:
            bi=lines.index('Buy'); ri=lines.index('Resell at'); si=lines.index('Sells in'); wi=lines.index('Where')
            prefix=lines[:bi]; name=prefix[0]; stats=' · '.join(l for l in prefix[1:] if 'risk:' not in l.lower())
            buy=re.match(MONEY+r'\s+each(?:\s*[×x]\s*(\d+))?',lines[bi+1],re.I)
            resale=re.match(MONEY+r'\s*\(([^)]*)\)',lines[ri+1],re.I)
            loc=re.match(r'CH\s+(\d+)\s*·\s*FM\s+(\d+)\s*·\s*(.+)',lines[wi+1])
            if not all((buy,resale,loc)): raise ValueError('unrecognized buy/resale/location')
            qty=int(buy[2] or 1); b=amount(buy[1]); s=amount(resale[1]); cost=b*qty
            turnover=lines[si+1]; daily=re.search(r'([\d,]+) sold a day',turnover)
            if not daily: raise ValueError('missing daily sales')
            estimated_net=round(s*qty*.97,2); profit=round(estimated_net-cost,2)
            row=dict(source_date=date or '',source_time=stamp or '',item=name,stats=stats,buy_each=b,quantity=qty,resell_each=s,resale_basis=resale[2],estimated_first_sale=turnover.split('·')[0].strip(),daily_sales=int(daily[1].replace(',','')),channel=int(loc[1]),fm=int(loc[2]),seller=loc[3],risk='; '.join(l for l in lines if 'risk:' in l.lower() or 'unusually cheap' in l.lower()),cost=cost,estimated_net=estimated_net,estimated_profit=profit,roi_pct=round(100*profit/cost,4) if cost else None)
            fingerprint={k:v for k,v in row.items() if k not in ('estimated_net','estimated_profit','roi_pct')}
            row['alert_id']=hashlib.sha256(json.dumps(fingerprint,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:24]
            rows.append(row)
        except (ValueError,IndexError,AttributeError,ArithmeticError) as e:
            rejected.append({'reason':str(e),'text':'\n'.join(lines)})
    return rows,rejected

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('input',type=Path); ap.add_argument('--date',help='Source date YYYY-MM-DD; not inferred'); ap.add_argument('--out',type=Path,default=Path.home()/'Documents'/'Market Alert Data'); args=ap.parse_args()
    rows,rejected=parse(args.input.read_text(encoding='utf-8-sig'),args.date)
    args.out.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(args.out/'alerts.sqlite3') as db:
        db.execute('CREATE TABLE IF NOT EXISTS alerts (alert_id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        before=db.total_changes
        db.executemany('INSERT OR IGNORE INTO alerts VALUES (?,?)',[(r['alert_id'],json.dumps(r,ensure_ascii=False)) for r in rows]); added=db.total_changes-before
        allrows=[json.loads(r[0]) for r in db.execute('SELECT payload FROM alerts ORDER BY rowid')]
    if allrows:
        with (args.out/'alerts.csv').open('w',encoding='utf-8-sig',newline='') as fp:
            writer=csv.DictWriter(fp,fieldnames=list(allrows[0]));writer.writeheader();writer.writerows(allrows)
    (args.out/'alerts.json').write_text(json.dumps(allrows,ensure_ascii=False,indent=2),encoding='utf-8')
    (args.out/'rejected.json').write_text(json.dumps(rejected,ensure_ascii=False,indent=2),encoding='utf-8')
    result=dict(parsed=len(rows),added=added,rejected=len(rejected),total_stored=len(allrows),units=sum(r['quantity'] for r in rows),sample_cost=sum(r['cost'] for r in rows),sample_estimated_profit=round(sum(r['estimated_profit'] for r in rows),2),note='Advertised estimates, not actual purchases or sales. Source date/time may be missing. Fingerprints deduplicate identical records, not confirmed listing identity.')
    print(json.dumps(result,indent=2));print('Saved to',args.out)

if __name__=='__main__': main()
