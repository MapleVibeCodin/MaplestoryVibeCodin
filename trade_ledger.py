"""Local purchase-to-sale ledger. No game actions and no inferred sales."""
from dataclasses import asdict
from decimal import Decimal, ROUND_FLOOR
import json
import hashlib
from pathlib import Path
import re
import sqlite3
import threading
import time
import uuid


def amount(text):
    m=re.fullmatch(r'\s*(\d[\d,]*(?:\.\d+)?)\s*([kmb]?)\s*',str(text),re.I)
    if not m:raise ValueError('Use a mesos amount such as 25000, 25K or 2M.')
    result=Decimal(m[1].replace(',',''))*{'':1,'k':1000,'m':1000000,'b':1000000000}[m[2].lower()]
    if result!=result.to_integral_value() or result<0 or result>10**12:raise ValueError('Invalid mesos amount.')
    return int(result)


def quote(raw):
    """Read explicit resale and time fields; never reconstruct price from profit."""
    lines=[re.sub(r'\s+',' ',line).strip() for line in (raw or '').splitlines() if line.strip()]
    text=' '.join(lines)
    money=r'(\d[\d,]*(?:\.\d+)?\s*[KMB]?)'
    resell=re.search(r'\bResell at\s*:?\s*'+money+r'\b',text,re.I)
    price=amount(resell[1]) if resell else None
    eta=re.search(r'\bTime to resell\s*:?\s*(?:about\s+|under\s+)?(?:an?\s+)?(\d+(?:\.\d+)?)?\s*(h(?:ours?)?|d(?:ays?)?|minutes?|mins?)\b',text,re.I)
    hours=None
    if eta:
        value=float(eta[1] or 1);unit=eta[2].lower()
        hours=value*(24 if unit.startswith('d') else 1/60 if unit.startswith('m') else 1)
    qty=re.search(r'\b(\d+)\s+items?\s*[·•-]\s*'+money+r'\s+total\b',text,re.I)
    lot=re.search(r'\ball\s+\d+\s*:\s*(?:about\s+|under\s+)?(?:an?\s+)?(\d+(?:\.\d+)?)?\s*(h(?:ours?)?|d(?:ays?)?|minutes?|mins?)\b',text,re.I)
    lot_hours=None
    if lot:
        value=float(lot[1] or 1);unit=lot[2].lower()
        lot_hours=value*(24 if unit.startswith('d') else 1/60 if unit.startswith('m') else 1)
    return {'list_price':price,'eta_hours':hours,'lot_eta_hours':lot_hours,'offered_quantity':int(qty[1]) if qty else None,
            'source':'HeneFM displayed estimate' if price is not None else 'Listing price not read; enter it once'}


def net_estimate(price,quantity,tax_percent):
    if price is None:return None
    return int((Decimal(price)*quantity*(Decimal(100)-Decimal(str(tax_percent)))/100).to_integral_value(rounding=ROUND_FLOOR))


def required_slots(deal,quantity):
    text=' '.join((deal.raw_text or '').split())
    return 1 if re.search(r'\bUse\s*[·•]?\s*Consumable\b|\bEtc\s*[·•]',text,re.I) else quantity


class TradeLedger:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock();self.db=sqlite3.connect(self.path,check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS trade_items (id TEXT PRIMARY KEY,source_key TEXT UNIQUE,data TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS trade_settings (key TEXT PRIMARY KEY,data TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS trade_events (id TEXT PRIMARY KEY,kind TEXT,amount INTEGER,store TEXT,at REAL,data TEXT)')
        self.db.commit()

    def settings(self):
        with self.lock:
            row=self.db.execute("SELECT data FROM trade_settings WHERE key='setup'").fetchone()
            return json.loads(row[0]) if row else {'buyer':'Unfkabe','stores':['fkable','unfkable'],
                'existing_slots':[None,None],'tax_percent':3,'reserve_mesos':500000,'max_item_percent':20}

    def configure(self,cash,stores,existing_slots,tax_percent=3,reserve_mesos=500000,max_item_percent=20):
        if len(stores)!=2 or len(set(s.casefold() for s in stores))!=2 or any(not s.strip() for s in stores):raise ValueError('Enter two different seller names.')
        if len(existing_slots)!=2 or any(n is not None and (isinstance(n,bool) or not isinstance(n,int) or not 0<=n<=18) for n in existing_slots):raise ValueError('Existing shop slots must be 0–18, or blank if unknown.')
        if not 0<=float(tax_percent)<100 or not 0<=float(max_item_percent)<=100:raise ValueError('Check tax and per-item percentages.')
        cash=amount(cash);reserve_mesos=amount(reserve_mesos)
        setup=dict(buyer='Unfkabe',stores=[s.strip() for s in stores],existing_slots=existing_slots,tax_percent=float(tax_percent),reserve_mesos=reserve_mesos,max_item_percent=float(max_item_percent))
        with self.lock,self.db:
            previous=self.db.execute('SELECT COALESCE(SUM(amount),0) FROM trade_events').fetchone()[0]
            old_stores=self.settings()['stores']
            rename=dict(zip(old_stores,setup['stores']))
            for item in self.items():
                if item['target_store'] in rename:
                    item['target_store']=rename[item['target_store']]
                    if item['owner'] in rename:item['owner']=rename[item['owner']]
                    self._write(item)
            self.db.execute("INSERT OR REPLACE INTO trade_settings VALUES ('setup',?)",(json.dumps(setup),))
            self._event('cash_reconcile',cash-(previous or 0),None,{'note':'User-entered currently spendable cash'})

    def _event(self,kind,value,store,data):
        self.db.execute('INSERT INTO trade_events VALUES (?,?,?,?,?,?)',(uuid.uuid4().hex,kind,value,store,time.time(),json.dumps(data)))

    def _write(self,item):
        self.db.execute('INSERT INTO trade_items VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data',
            (item['id'],item['source_key'],json.dumps(item,ensure_ascii=False)))

    def items(self):
        with self.lock:return [json.loads(row[0]) for row in self.db.execute('SELECT data FROM trade_items ORDER BY rowid DESC')]

    def get(self,key):
        with self.lock:
            row=self.db.execute('SELECT data FROM trade_items WHERE id=?',(key,)).fetchone()
            if row is None:raise ValueError('Select an inventory item.')
            return json.loads(row[0])

    def cash(self):
        with self.lock:
            if not self.db.execute("SELECT 1 FROM trade_events WHERE kind='cash_reconcile' LIMIT 1").fetchone():return None
            return self.db.execute('SELECT COALESCE(SUM(amount),0) FROM trade_events').fetchone()[0]

    def purchase(self,source_key,deal,quantity=1,unit_cost=None):
        if isinstance(quantity,bool) or not isinstance(quantity,int) or not 1<=quantity<=999:raise ValueError('Quantity must be 1–999.')
        cost=deal.buy_mesos if unit_cost is None else amount(unit_cost)
        if cost is None:raise ValueError('Purchase price is missing. Enter the price paid before logging the purchase.')
        cost=amount(cost);pricing=quote(deal.raw_text)
        holding=pricing['lot_eta_hours'] if quantity>1 and quantity==pricing['offered_quantity'] and pricing['lot_eta_hours'] is not None else pricing['eta_hours']
        with self.lock,self.db:
            old=self.db.execute('SELECT id FROM trade_items WHERE source_key=?',(source_key,)).fetchone()
            if old and self.get(old[0])['status']!='void':return self.get(old[0]),False
            item=dict(id=old[0] if old else uuid.uuid4().hex,source_key=source_key,item=deal.item,stats=deal.stats,seller=deal.ign,
                quantity=quantity,slots=required_slots(deal,quantity),unit_cost=cost,list_price=pricing['list_price'],eta_hours=holding,
                pricing_source=pricing['source'],cost_source='alert price; user purchase confirmation' if unit_cost is None else 'user-entered paid price',
                owner='Unfkabe',target_store=None,status='to_list',bought_at=time.time(),first_listed_at=None,
                last_listed_at=None,sold_at=None,sale_net=None,collected=False,screenshot=None,
                snapshot=asdict(deal))
            for store,report in self.stores().items():
                if report['known'] and report['planned_slots']+item['slots']<=18:
                    item['target_store']=store;break
            self._write(item);self._event('purchase',-cost*quantity,None,{'item_id':item['id']})
            return item,True

    def correct_purchase(self,key,quantity,unit_cost):
        cost=amount(unit_cost)
        if not isinstance(quantity,int) or not 1<=quantity<=999:raise ValueError('Quantity must be 1–999.')
        with self.lock,self.db:
            item=self.get(key)
            if item['status']!='to_list':raise ValueError('Correct purchase details before confirming it listed.')
            old=(item['unit_cost'] or 0)*item['quantity']
            stackable=item.get('slots',item['quantity'])==1 and item['quantity']>1
            slots=1 if stackable else quantity
            if item['target_store'] and self.stores()[item['target_store']]['planned_slots']-item.get('slots',item['quantity'])+slots>18:
                raise ValueError('Correct the assigned shop before increasing this quantity.')
            item.update(quantity=quantity,slots=slots,unit_cost=cost,cost_source='user-corrected paid price')
            self._write(item);self._event('purchase_correction',0 if item.get('historical') else old-cost*quantity,None,{'item_id':key})

    def review(self,item,now=None):
        now=time.time() if now is None else now
        age=None if item['first_listed_at'] is None else max(0,(now-item['first_listed_at'])/3600)
        eta=item['eta_hours']
        stale=item['status']=='listed' and age is not None and age>=max(12,(eta or 6)*2)
        net=net_estimate(item['list_price'],item['quantity'],self.settings()['tax_percent'])
        return {'listed_hours':age,'review_due':stale,
            'estimated_profit':None if net is None or item['unit_cost'] is None else net-item['unit_cost']*item['quantity'],
            'note':'Review at next planned shop visit; no automatic price cut' if stale else ''}

    def void_purchase(self,key):
        with self.lock,self.db:
            item=self.get(key)
            if item['status']=='void':return False
            if item['status']!='to_list' and not (item.get('historical') and item['status']=='listed'):raise ValueError('Only an unlisted purchase can be voided. Reconcile listed/sold inventory explicitly.')
            item.update(status='void',voided_at=time.time())
            self._write(item);self._event('purchase_void',0 if item.get('historical') else item['unit_cost']*item['quantity'],None,{'item_id':key})
            return True

    def import_existing(self,rows):
        """One-time owned-stock import; historical purchases never debit current cash."""
        parsed=[];setup=self.settings();occurrences={}
        for row in rows:
            item=str(row.get('item','')).strip();seller=str(row.get('seller','')).strip()
            if not item:raise ValueError('Every stock row needs an item name.')
            if seller and seller not in setup['stores']:raise ValueError('Seller must be fkable/unfkable, or blank for buyer inventory.')
            quantity=int(row.get('quantity') or 1)
            if not 1<=quantity<=999:raise ValueError('Invalid existing-stock quantity.')
            cost=amount(row['unit_cost']) if str(row.get('unit_cost','')).strip() else None
            price=amount(row['list_price']) if str(row.get('list_price','')).strip() else None
            hours=float(row['listed_hours']) if str(row.get('listed_hours','')).strip() else None
            if hours is not None and not 0<=hours<=100000:raise ValueError('Invalid listed hours.')
            slots=int(row.get('slots') or quantity)
            if not 1<=slots<=18:raise ValueError('Existing stock slots must be 1–18. Use one slot for one consumable stack/listing.')
            digest=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()
            occurrence=occurrences.get(digest,0);occurrences[digest]=occurrence+1
            source='existing:'+str(row.get('stock_id') or (digest+':'+str(occurrence)))
            parsed.append((row,item,seller,quantity,slots,cost,price,hours,source))
        imported=0
        with self.lock,self.db:
            for row,name,seller,quantity,slots,cost,price,hours,source in parsed:
                if self.db.execute('SELECT 1 FROM trade_items WHERE source_key=?',(source,)).fetchone():continue
                if seller:
                    n=setup['stores'].index(seller);baseline=setup['existing_slots'][n]
                    if baseline is not None:setup['existing_slots'][n]=max(0,baseline-slots)
                    tracked=sum(i.get('slots',i['quantity']) for i in self.items() if i['target_store']==seller and i['status'] in ('to_list','listed'))
                    if tracked+(setup['existing_slots'][n] or 0)+slots>18:raise ValueError('Imported stock exceeds 18 slots on '+seller)
                now=time.time();first=now-hours*3600 if seller and hours is not None else None
                entry=dict(id=uuid.uuid4().hex,source_key=source,item=name,stats=row.get('stats',''),seller='historical',
                    quantity=quantity,slots=slots,unit_cost=cost,list_price=price,eta_hours=None,
                    pricing_source='user-imported current stock',cost_source='historical paid cost; current cash unchanged',
                    owner=seller or setup['buyer'],target_store=seller or None,status='listed' if seller else 'to_list',
                    bought_at=None,first_listed_at=first,last_listed_at=first,sold_at=None,sale_net=None,
                    collected=False,screenshot=None,snapshot=None,historical=True)
                self._write(entry);self._event('historical_import',0,seller,{'item_id':entry['id']});imported+=1
            self.db.execute("INSERT OR REPLACE INTO trade_settings VALUES ('setup',?)",(json.dumps(setup),))
        return imported

    def attach_screenshot(self,key,path):
        with self.lock,self.db:
            item=self.get(key);item['screenshot']=str(path);self._write(item)

    def assign(self,key,store):
        setup=self.settings()
        if store not in setup['stores']:raise ValueError('Choose a configured shop.')
        with self.lock,self.db:
            item=self.get(key)
            if item['status']!='to_list':raise ValueError('Only unlisted inventory can be assigned.')
            report=self.stores();entry=report[store]
            if item['target_store']!=store and entry['planned_slots']+item.get('slots',item['quantity'])>18:raise ValueError('That shop would exceed 18 planned equipment slots.')
            item['target_store']=store;self._write(item)

    def listed(self,key,store,price):
        price=amount(price)
        if price<=0:raise ValueError('Listing price must be positive.')
        with self.lock,self.db:
            item=self.get(key)
            if item['status'] not in ('to_list','listed'):raise ValueError('Only active purchased inventory can be listed.')
            if store not in self.settings()['stores']:raise ValueError('Choose a configured shop.')
            report=self.stores()[store]
            already=item['target_store']==store
            if report['planned_slots']+(0 if already else item.get('slots',item['quantity']))>18:raise ValueError('This exceeds 18 planned equipment slots. Reconcile existing slots if needed.')
            now=time.time();first=item['first_listed_at']
            if item['status']=='to_list' and first is None:first=now
            item.update(status='listed',owner=store,target_store=store,list_price=price,
                first_listed_at=first,last_listed_at=now)
            self._write(item)

    def sold(self,key,net_received,estimated=False):
        value=amount(net_received)
        with self.lock,self.db:
            item=self.get(key)
            if item['status']=='sold':return False
            if item['status']!='listed':raise ValueError('Confirm the item was listed first.')
            item.update(status='sold',sold_at=time.time(),sale_net=value,collected=False,net_source='listed-price estimate' if estimated else 'confirmed net proceeds');self._write(item)
            # Sales stay in the shop; spendable cash changes only on collection.
            return True

    def collect(self,store,fee=0,actual_received=None):
        fee=amount(fee)
        if store not in self.settings()['stores']:raise ValueError('Choose a configured seller.')
        with self.lock,self.db:
            rows=[item for item in self.items() if item['status']=='sold' and item['target_store']==store and not item['collected']]
            total=sum(item['sale_net'] for item in rows)
            if not rows and not fee and (actual_received is None or amount(actual_received)==0):return 0
            for item in rows:item['collected']=True;self._write(item)
            received=total if actual_received is None else amount(actual_received)
            self._event('collection',received-fee,store,{'items':[i['id'] for i in rows],'fee':fee,'estimated_items_total':total})
            return received-fee

    def stores(self):
        with self.lock:
            setup=self.settings();items=self.items();result={}
            for n,store in enumerate(setup['stores']):
                stock=[item for item in items if item['target_store']==store and item['status'] in ('to_list','listed')]
                baseline=setup['existing_slots'][n]
                result[store]=dict(known=baseline is not None,planned_slots=(baseline or 0)+sum(i.get('slots',i['quantity']) for i in stock),
                    listed_slots=(baseline or 0)+sum(i.get('slots',i['quantity']) for i in stock if i['status']=='listed'),
                    ready=sum(i['quantity'] for i in stock if i['status']=='to_list'),
                    collectable=sum(i['sale_net'] for i in items if i['status']=='sold' and i['target_store']==store and not i['collected']))
            return result

    def recommendation(self,deal,quantity=None):
        pricing=quote(deal.raw_text)
        quantity=quantity if quantity is not None else (pricing['offered_quantity'] or 1)
        if quantity>1 and quantity==pricing['offered_quantity'] and pricing['lot_eta_hours'] is not None:pricing['eta_hours']=pricing['lot_eta_hours']
        cash=self.cash();setup=self.settings();cost=None if deal.buy_mesos is None else deal.buy_mesos*quantity
        net=net_estimate(pricing['list_price'],quantity,setup['tax_percent'])
        gain=None if net is None or cost is None else net-cost
        notes=[]
        if quantity>1 and pricing['lot_eta_hours'] is None:notes.append('Whole-lot holding time unknown')
        if cash is None:notes.append('Set current spendable cash')
        elif cost is not None:
            if cost>cash:notes.append('Over available cash')
            elif cash-cost<setup['reserve_mesos']:notes.append('Uses cash reserve')
            if cost>max(cash,0)*setup['max_item_percent']/100:notes.append('Large share of available cash')
        if pricing['eta_hours'] is None:notes.append('Holding time not read')
        elif pricing['eta_hours']>6:notes.append('Slow turnover estimate')
        if gain is None:notes.append('Price/profit estimate incomplete')
        elif gain<=0:notes.append('No estimated profit after planning tax')
        hours=pricing['eta_hours']
        return dict(cost=cost,net_profit=gain,list_price=pricing['list_price'],hours=hours,
            profit_per_hour=gain/hours if gain is not None and hours else None,notes=notes)

    def export(self,path):
        with self.lock:
            data={'settings':self.settings(),'estimated_spendable_cash':self.cash(),'inventory':self.items(),
                'events':[dict(id=r[0],kind=r[1],amount=r[2],store=r[3],at=r[4],data=json.loads(r[5])) for r in self.db.execute('SELECT * FROM trade_events ORDER BY at')]}
            Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    def close(self):
        with self.lock:self.db.close()
