"""Two-seller inventory and cash controls inside the existing FM Rush window."""
import time
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from trade_ledger import amount,net_estimate


def money(value):return '—' if value is None else f'{value:,.0f}'

class TradePanels:
    def __init__(self,app,notebook):
        self.app=app;self.ledger=app.ledger;self.stamp=None
        self.inventory=ttk.Frame(notebook);self.shops=ttk.Frame(notebook)
        notebook.add(self.inventory,text='Inventory & listing');notebook.add(self.shops,text='Shops & cash')
        self.summary=tk.StringVar();ttk.Label(self.inventory,textvariable=self.summary).pack(fill='x',padx=8,pady=8)
        ttk.Label(self.inventory,text='Ctrl+Alt+B = confirm purchase of selected deal. Records the alert Buy price. Quantity uses the displayed lot count when read, otherwise 1; verify it.').pack(fill='x',padx=8)
        controls=ttk.Frame(self.inventory);controls.pack(fill='x',padx=8,pady=6)
        self.quantity=app.buy_quantity
        ttk.Button(controls,text='Correct cost / qty',command=self.correct).pack(side='left',padx=5)
        ttk.Button(controls,text='Undo mistaken buy',command=self.void).pack(side='left',padx=5)
        self.show_history=tk.BooleanVar(value=False)
        ttk.Checkbutton(controls,text='Show sold history',variable=self.show_history,command=self.refresh).pack(side='left')
        ttk.Button(controls,text='Export ledger',command=self.export).pack(side='right')
        columns=('item','stats','qty','cost','list','shop','status','age','review')
        self.table=ttk.Treeview(self.inventory,columns=columns,show='headings',selectmode='extended',height=10)
        for name,label,width in zip(columns,['Item','Exact displayed stats','Qty','Paid / unit','List / unit','Seller','Status','Listed age','Review'],[145,210,35,90,90,80,75,80,180]):
            self.table.heading(name,text=label);self.table.column(name,width=width,minwidth=35)
        self.table.pack(fill='both',expand=True,padx=8,pady=6)
        self.table.bind('<Double-1>',self.details)
        row=ttk.Frame(self.inventory);row.pack(fill='x',padx=8,pady=8)
        ttk.Button(row,text='Copy listing details',command=self.copy).pack(side='left')
        ttk.Button(row,text='Copy numeric price',command=self.copy_price).pack(side='left',padx=5)
        ttk.Button(row,text='Assign seller',command=self.assign).pack(side='left',padx=5)
        ttk.Button(row,text='Confirm LISTED / repriced',command=self.listed).pack(side='left',padx=5)
        ttk.Button(row,text='Confirm SOLD at list price',command=self.sold).pack(side='left',padx=5)
        self.cash_info=tk.StringVar();ttk.Label(self.shops,textvariable=self.cash_info,wraplength=900,justify='left').pack(fill='x',padx=10,pady=10)
        ttk.Button(self.shops,text='Set current buyer cash / shop setup',command=self.setup).pack(anchor='w',padx=10)
        imports=ttk.Frame(self.shops);imports.pack(fill='x',padx=10,pady=4)
        ttk.Button(imports,text='Import current stock CSV (one-time)',command=self.import_stock).pack(side='left')
        ttk.Button(imports,text='Save blank CSV template',command=self.stock_template).pack(side='left',padx=6)
        self.shop_info=tk.StringVar();ttk.Label(self.shops,textvariable=self.shop_info,wraplength=1000,justify='left').pack(fill='x',padx=10,pady=12)
        self.shop_buttons=ttk.Frame(self.shops);self.shop_buttons.pack(fill='x',padx=10)
        ttk.Button(self.shops,text='Open old Bought screenshots (optional)',command=app.open_bought_folder).pack(anchor='w',padx=10,pady=5)
        ttk.Button(self.shops,text='Export scanner timing',command=app.export_latency).pack(anchor='w',padx=10,pady=5)
        self.notice=tk.StringVar(value='Records replace screenshot sorting. Game purchases, listings and transfers remain manual confirmations.')
        ttk.Label(self.shops,textvariable=self.notice,wraplength=1000).pack(fill='x',padx=10,pady=12)
        self.refresh()

    def selected(self):
        keys=self.table.selection()
        if not keys:raise ValueError('Select inventory rows first.')
        return [self.ledger.get(key) for key in keys]

    def safe(self,fn):
        try:fn();self.refresh()
        except (ValueError,OSError) as exc:messagebox.showerror('Trade desk',str(exc))

    def refresh(self):
        rows=self.ledger.items();cash=self.ledger.cash();stores=self.ledger.stores()
        self.summary.set('Buyer Unfkabe · estimated spendable cash '+money(cash)+' mesos · '+str(sum(r['status'] in ('to_list','listed') for r in rows))+' tracked lots')
        existing=set(self.table.get_children())
        for item in rows:
            if not self.show_history.get() and item['status'] not in ('to_list','listed'):continue
            review=self.ledger.review(item)
            age='—' if review['listed_hours'] is None else f"{review['listed_hours']:.1f} h"
            values=(item['item'],item['stats'],item['quantity'],money(item['unit_cost']),money(item['list_price']),
                    item['target_store'] or 'Unassigned',item['status'],age,'Review next visit' if review['review_due'] else '')
            if item['id'] in existing:self.table.item(item['id'],values=values);existing.remove(item['id'])
            else:self.table.insert('','end',iid=item['id'],values=values)
        for key in existing:self.table.delete(key)
        setup=self.ledger.settings()
        self.cash_info.set('Spendable cash: '+money(cash)+' mesos. This is a ledger estimate—reconcile to Unfkabe\'s actual balance when needed.\n'
            +'Cash reserve: '+money(setup['reserve_mesos'])+' · per-item warning: '+str(setup['max_item_percent'])+'% of cash · planning tax: '+str(setup['tax_percent'])+'%.\n'
            +'A confirmed sale stays at the seller until you confirm its cash reached Unfkabe. Existing stock is unknown until entered or counted; no inventory is inferred from old screenshots.')
        lines=[]
        for store,s in stores.items():
            slots=str(s['planned_slots'])+'/18 planned slots' if s['known'] else str(s['planned_slots'])+' tracked slots; old occupancy unknown'
            lines.append(f"{store}: {slots}; {s['ready']} ready to list; {money(s['collectable'])} sale proceeds awaiting transfer to buyer")
            ready=[r for r in rows if r['target_store']==store and r['status']=='to_list']
            if ready:lines.append('  Transfer batch Unfkabe → '+store+': '+', '.join(str(r['quantity'])+' × '+r['item'] for r in ready))
        available=[(s['collectable'],name) for name,s in stores.items() if s['collectable']>0]
        if available and cash is not None and cash<setup['reserve_mesos']:
            lines.append('Cash is low: collect/transfer from '+max(available)[1]+' first; do not restart both shops automatically.')
        else:lines.append('Group transfers and listings into a shop visit. A stale timer is a review reminder, not an automatic price cut.')
        self.shop_info.set('\n\n'.join(lines))
        for widget in self.shop_buttons.winfo_children():widget.destroy()
        for store in setup['stores']:ttk.Button(self.shop_buttons,text='Cash received from '+store,command=lambda s=store:self.collect(s)).pack(side='left',padx=5)

    def setup(self):
        settings=self.ledger.settings();dialog=tk.Toplevel(self.shops);dialog.title('Buyer cash and two seller shops')
        fields=[]
        def field(label,value):
            row=ttk.Frame(dialog);row.pack(fill='x',padx=10,pady=4);ttk.Label(row,text=label,width=38).pack(side='left')
            var=tk.StringVar(value=str(value));ttk.Entry(row,textvariable=var,width=20).pack(side='right');fields.append(var);return var
        cash=field('Current spendable cash on Unfkabe',self.ledger.cash() if self.ledger.cash() is not None else '2M')
        names=[];slots=[]
        for i in range(2):
            names.append(field('Seller '+str(i+1)+' name',settings['stores'][i]))
            slots.append(field('Old stock slots NOT in this ledger (0–18)',settings['existing_slots'][i] if settings['existing_slots'][i] is not None else ''))
        tax=field('Planning sale tax % (estimate)',settings['tax_percent'])
        reserve=field('Cash reserve warning',settings['reserve_mesos']);cap=field('Per-purchase cash warning %',settings['max_item_percent'])
        ttk.Label(dialog,text='Blank old-stock occupancy means unknown. Equipment uses a slot per unit; explicit consumable lots use one slot.').pack(padx=10,pady=5)
        def save():
            try:
                self.ledger.configure(cash.get(),[n.get() for n in names],[int(n.get()) if n.get().strip() else None for n in slots],
                    float(tax.get()),amount(reserve.get()),float(cap.get()))
                dialog.destroy();self.refresh()
            except (ValueError,OSError) as exc:messagebox.showerror('Setup',str(exc),parent=dialog)
        ttk.Button(dialog,text='Confirm current balance and save',command=save).pack(pady=10)
        dialog.transient(self.shops.winfo_toplevel())

    def copy(self):
        def run():
            item=self.selected()[0]
            text=f"{item['item']}\n{item['stats']}\nQty {item['quantity']} · paid {money(item['unit_cost'])} each\nList at {money(item['list_price'])} each ({item['pricing_source']})"
            self.inventory.clipboard_clear();self.inventory.clipboard_append(text)
        self.safe(run)

    def copy_price(self):
        def run():
            item=self.selected()[0]
            if item['list_price'] is None:raise ValueError('No listing price is recorded for this item.')
            self.inventory.clipboard_clear();self.inventory.clipboard_append(str(item['list_price']))
        self.safe(run)

    def details(self,event=None):
        def run():
            item=self.selected()[0]
            messagebox.showinfo(item['item'],f"{item['stats']}\nPaid {money(item['unit_cost'])} × {item['quantity']}\nHeneFM list estimate {money(item['list_price'])}\nExpected sale time: {item['eta_hours'] if item['eta_hours'] is not None else 'unknown'} h\nCost source: {item['cost_source']}\n{self.ledger.review(item)['note']}")
        self.safe(run)

    def void(self):
        def run():
            item=self.selected()[0]
            if not messagebox.askyesno('Undo mistaken purchase','Confirm you did not buy this item. This reverses its cash debit and reopens the deal.',parent=self.inventory):return
            self.ledger.void_purchase(item['id'])
            self.app.archive.reopen(item['source_key']);self.app.sync_archive()
        self.safe(run)

    def correct(self):
        def run():
            item=self.selected()[0]
            price=simpledialog.askstring('Actual paid price','Price paid per unit:',initialvalue=str(item['unit_cost']),parent=self.inventory)
            if price is None:return
            qty=simpledialog.askinteger('Bought quantity','Actual quantity bought:',initialvalue=item['quantity'],minvalue=1,maxvalue=999,parent=self.inventory)
            if qty is not None:self.ledger.correct_purchase(item['id'],qty,price)
        self.safe(run)

    def assign(self):
        def run():
            items=self.selected();names=self.ledger.settings()['stores']
            store=simpledialog.askstring('Seller','Choose seller: '+', '.join(names),initialvalue=items[0]['target_store'] or names[0],parent=self.inventory)
            if store is None:return
            for item in items:self.ledger.assign(item['id'],store)
        self.safe(run)

    def listed(self):
        def run():
            items=self.selected()
            if len(items)==1 and (items[0]['list_price'] is None or items[0]['status']=='listed'):
                value=simpledialog.askstring('Listing price','Enter the actual price you listed/relisted at (no automatic markdown):',parent=self.inventory)
                if value is None:return
                items[0]['list_price']=amount(value)
            if any(i['list_price'] is None or i['target_store'] is None for i in items):raise ValueError('Assign a seller and listing price to each item first.')
            if not messagebox.askyesno('Confirm actual listing','Have you transferred and listed these '+str(len(items))+' lots in the specified shops at the displayed prices?',parent=self.inventory):return
            for item in items:self.ledger.listed(item['id'],item['target_store'],item['list_price'])
        self.safe(run)

    def sold(self):
        def run():
            items=self.selected()
            if any(i['status']!='listed' for i in items):raise ValueError('Select only listed items that you verified sold.')
            if not messagebox.askyesno('Confirm verified sales','Confirm these items actually sold at the listed price. Net proceeds will be estimated using the planning tax; cash is not credited yet.',parent=self.inventory):return
            for item in items:self.ledger.sold(item['id'],net_estimate(item['list_price'],item['quantity'],self.ledger.settings()['tax_percent']),estimated=True)
        self.safe(run)

    def collect(self,store):
        def run():
            current=self.ledger.stores()[store]['collectable']
            value=simpledialog.askstring('Cash physically received by Unfkabe','Enter the actual mesos transferred from '+store+' to Unfkabe. Do this only after receiving it; estimated pending proceeds '+money(current)+'.',initialvalue=str(current),parent=self.shops)
            if value is not None:
                self.ledger.collect(store,actual_received=amount(value))
                self.notice.set('Cash receipt recorded. Reconcile buyer balance if untracked old stock also sold.')
        self.safe(run)

    def stock_template(self):
        import csv
        path=filedialog.asksaveasfilename(defaultextension='.csv',initialfile='FM_Rush_Existing_Stock.csv')
        if path:
            with open(path,'w',newline='',encoding='utf-8-sig') as file:
                csv.writer(file).writerow(['stock_id','item','stats','quantity','unit_cost','list_price','seller','listed_hours','slots'])

    def import_stock(self):
        import csv
        path=filedialog.askopenfilename(title='Import only items you still own',filetypes=[('CSV stock file','*.csv')])
        if not path:return
        def run():
            with open(path,newline='',encoding='utf-8-sig') as file:rows=list(csv.DictReader(file))
            if not messagebox.askyesno('Confirm current owned stock','Import '+str(len(rows))+' rows as CURRENTLY OWNED stock? This does not debit cash. Leave unknown paid costs or listed hours blank.',parent=self.shops):return
            count=self.ledger.import_existing(rows);self.notice.set('Imported '+str(count)+' existing lots. Current buyer cash was not changed.')
        self.safe(run)

    def export(self):
        path=filedialog.asksaveasfilename(defaultextension='.json',initialfile='FM_Rush_Trading_Ledger.json')
        if path:self.safe(lambda:self.ledger.export(path))
