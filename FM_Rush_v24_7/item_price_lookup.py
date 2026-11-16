"""HeneFM's permitted one-item-at-a-time pricing API lookup.

Never scans/compares shop listings, never makes a background/batch request,
never stores the user's bearer key. Use only for manual reference pricing.
"""
from __future__ import annotations
import json
import re
import threading
import tkinter as tk
from tkinter import ttk
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = 'https://henefm.com/api/public/v1/items/'


def url_for_item(item_id: str, stats: str='') -> str:
    if not re.fullmatch(r'\d{3,12}', item_id.strip()):
        raise ValueError('Item ID must be numeric (3–12 digits)')
    params = []
    for part in stats.strip().split('&') if stats.strip() else []:
        if '=' not in part: raise ValueError('Each stat needs key=value')
        key, val = part.strip().split('=', 1)
        key=key.strip(); val=val.strip()
        if not re.fullmatch(r'(?:stats|min)\.[a-z0-9_.]{1,40}',key):
            raise ValueError('Stat key must look like stats.crit_rate or min.crit_rate')
        if not re.fullmatch(r'[-+]?\d+(?:\.\d+)?',val):
            raise ValueError('Stat value must be numeric')
        params.append((key,val))
    query = '?' + urlencode(params) if params else ''
    return f'{API}{item_id.strip()}/price{query}'


class Lookup(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('FM Rush — Single-Item Price Lookup (HeneFM API)')
        self.geometry('770x550')
        self.minsize(520,400)
        self.config(bg='#0b1422')
        self.key=tk.StringVar()
        self.item=tk.StringVar()
        self.stats=tk.StringVar()
        self.status=tk.StringVar(value='One item per click. Your API key is never saved.')
        for label, var, shown in [
            ('HeneFM API key',self.key,'•'),
            ('Item ID',self.item,None),
            ('Optional stat query, e.g. stats.crit_rate=3',self.stats,None),
        ]:
            line=tk.Frame(self,bg='#0b1422')
            line.pack(fill='x',padx=15,pady=4)
            tk.Label(line,text=label,bg='#0b1422',fg='#b9d1e8',width=40,anchor='w').pack(side='left')
            ent=tk.Entry(line,textvariable=var,show=shown or '',bg='#183149',fg='white',insertbackground='white')
            ent.pack(side='left',fill='x',expand=True,ipady=5)
        bar=tk.Frame(self,bg='#0b1422');bar.pack(fill='x',padx=15,pady=10)
        self.go=tk.Button(bar,text='LOOK UP THIS ITEM',command=self.lookup,bg='#20d1a0',fg='#001b17',font=('Segoe UI',11,'bold'))
        self.go.pack(side='left')
        tk.Label(bar,textvariable=self.status,bg='#0b1422',fg='#ffe48d',wraplength=530,justify='left').pack(side='left',padx=12)
        tk.Label(self,text='Returns HeneFM’s raw usual-price response. This is not a deal scanner or automatic shop comparison.',
                 bg='#0b1422',fg='#afc3da',wraplength=720).pack(fill='x',padx=15,pady=(0,8))
        frame=tk.Frame(self,bg='#0b1422');frame.pack(fill='both',expand=True,padx=15,pady=(0,15))
        self.output=tk.Text(frame,bg='#102238',fg='#ebf9ff',font=('Consolas',10),wrap='word')
        scroll=ttk.Scrollbar(frame,orient='vertical',command=self.output.yview)
        self.output.configure(yscrollcommand=scroll.set)
        self.output.pack(side='left',fill='both',expand=True);scroll.pack(side='right',fill='y')

    def lookup(self):
        key=self.key.get().strip()
        if not key or len(key)<8:
            self.status.set('Enter your private API key (only on your own computer).')
            return
        try: url=url_for_item(self.item.get(),self.stats.get())
        except ValueError as exc:
            self.status.set(str(exc));return
        self.go.config(state='disabled')
        self.status.set('Looking up one item…')
        def worker():
            try:
                request=Request(url,headers={'Authorization':'Bearer '+key,'User-Agent':'FM-Rush-Personal-Item-Price-Lookup/1.0',
                          'Accept':'application/json'})
                with urlopen(request,timeout=12) as res:
                    body=res.read(131072)
                parsed=json.loads(body.decode('utf-8'))
                rendered=json.dumps(parsed,indent=2,ensure_ascii=False)
                status='Item returned. No other requests were made.'
            except HTTPError as exc:
                rendered='HTTP '+str(exc.code)+'\n'+exc.reason
                status='Lookup failed. Check the item ID, key and rate limit.'
            except (URLError,ValueError,OSError) as exc:
                rendered=str(exc)
                status='Lookup failed.'
            def done():
                if not self.winfo_exists(): return
                self.go.config(state='normal')
                self.status.set(status)
                self.output.delete('1.0','end')
                self.output.insert('1.0',rendered)
            try:self.after(0,done)
            except RuntimeError:pass
        threading.Thread(target=worker,daemon=True).start()

if __name__=='__main__':
    Lookup().mainloop()
