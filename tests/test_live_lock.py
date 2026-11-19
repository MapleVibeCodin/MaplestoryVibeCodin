import ast, queue, time, json, threading, urllib.request, urllib.error
from pathlib import Path
import sys,tempfile,unittest
from dataclasses import replace
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deal_archive import DealArchive
from deal_parser import Deal
from profit_filter import ProfitDecision
from route_logic import plan,arrows

A=Deal(13,3,'Black Sack: Stumpy','','SellerA',100000,ProfitDecision(True,16400,16),'stumpy')
B=Deal(14,11,'Moon and Sun Cape','','SellerB',60000,ProfitDecision(True,347400,579),'cape')
C=replace(B,ign='SellerC',listing_id='new',cc=2,fm=20)
class Var:
 def __init__(self):self.value=''
 def set(self,v):self.value=v
 def get(self):return self.value
# Exercise actual GUI state methods without a Windows display/capture engine.
source=ast.parse((Path(__file__).resolve().parents[1]/'fm_rush.py').read_text())
cls=next(x for x in source.body if isinstance(x,ast.ClassDef) and x.name=='FMApp')
names={'sync_archive','set_target','toggle_chase','select_archived','pump'}
module=ast.Module(body=[x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name in names],type_ignores=[])
ns={'plan':plan,'arrows':arrows,'queue':queue,'time':time};exec(compile(module,'fm_rush.py','exec'),ns)
class UI:
 pass
for name in names:setattr(UI,name,ns[name])
class LiveLock(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.a=DealArchive(Path(self.tmp.name)/'a.db',manual_selection=True)
 def tearDown(self):self.a.close();self.tmp.cleanup()
 def page(self,deals,rev):self.a.apply_visible(deals,'test',rev)
 def test_initial_top_card_and_next_popup(self):
  self.page([A,B],1);self.assertEqual(self.a.current()[1],A)
  self.page([C,A,B],2);self.assertEqual(self.a.current()[1],C)
 def test_hard_lock_then_unlock_latest(self):
  self.page([A,B],1);self.assertTrue(self.a.choose(self.a.focus))
  self.page([C,B],2);self.assertEqual(self.a.current()[1],A)
  self.assertEqual(self.a.selected_names(),('SellerA',))
  other=self.a.record(B)[0];self.assertFalse(self.a.choose(other));self.a.select(other)
  self.assertEqual(self.a.current()[1],A)
  self.a.unlock();self.assertFalse(self.a.chase_locked);self.assertEqual(self.a.current()[1],C)
 def test_stale_snapshot_does_not_override(self):
  self.page([C],2);self.assertFalse(self.a.apply_visible([A],'test',1));self.assertEqual(self.a.current()[1],C)
 def test_backlog_records_dont_override_preview(self):
  self.page([A],1);self.a.record(B);self.assertEqual(self.a.current()[1],A)
 def test_empty_page_clears_preview_but_not_lock(self):
  self.page([A],1);self.page([],2);self.assertIsNone(self.a.current())
  self.page([A],3);self.a.choose(self.a.focus);self.page([],4);self.assertEqual(self.a.current()[1],A)
 def test_completed_lock_requires_unlock(self):
  self.page([A,B],1);self.a.choose(self.a.focus);self.a.complete_current()
  self.page([C,B],2);self.assertIsNone(self.a.current());self.assertTrue(self.a.chase_locked)
  self.a.unlock();self.assertEqual(self.a.current()[1],C)
 def test_skip_not_purchase_and_skipped_top_is_not_reselected(self):
  self.page([A,B],1);key=self.a.focus;self.a.skip(key);self.page([A,B],2)
  self.assertEqual(self.a.current()[1],B);self.assertTrue(self.a.records[key]['skipped']);self.assertNotIn('bought_at',self.a.records[key])
 def test_gui_route_item_and_scan_target_follow_then_lock(self):
  ui=UI();ui.archive=self.a;ui.conf={'start_channel':20};ui.shop=None;ui.map=None;ui.grid=None
  ui.displayed_listing=None;ui.scan_names=();ui.current_cc=20;ui.current_fm=13;ui.opened=0
  for name in ['ccfm','keys','item','stats','ign','profit','buy','buy_quantity','status','chase_label']:setattr(ui,name,Var())
  ui.accepted_ign=lambda name:setattr(ui,'shop_target',name)
  ui.open_map=lambda:setattr(ui,'opened',ui.opened+1)
  self.page([A,B],1);ui.sync_archive()
  self.assertEqual((ui.current_cc,ui.current_fm),(13,3));self.assertIn('Stumpy',ui.item.get());self.assertEqual(ui.opened,1)
  ui.toggle_chase();self.page([C],2);ui.sync_archive()
  self.assertEqual((ui.current_cc,ui.current_fm),(13,3));self.assertEqual(ui.scan_names,('SellerA',))
  ui.set_target(1,1);self.assertEqual(ui.current_fm,3)
  ui.toggle_chase();self.assertEqual((ui.current_cc,ui.current_fm),(2,20));self.assertEqual(ui.shop_target,'SellerC')

 def test_http_chase_ack_reject_override_and_unlock(self):
  import henefm_bridge as bridge
  bridge.PORT=0
  ui=UI();ui.archive=self.a;ui.events=queue.Queue();ui.shop_events=queue.Queue();ui.shop_running=False;ui.scan_names=()
  ui.status=Var();ui.sync_archive=lambda:None;ui.retry_shop_once=lambda:None;ui.schedule=lambda *args:None
  server=bridge.BrowserBridge(ui.events,self.a);server.start()
  url='http://127.0.0.1:'+str(server.server.server_port)
  stop=threading.Event()
  def pump():
   while not stop.wait(.002):ui.pump()
  thread=threading.Thread(target=pump);thread.start()
  def post(endpoint,data):
   req=urllib.request.Request(url+endpoint,data=json.dumps(data).encode(),headers={'Content-Type':'application/json','X-FM-Rush-Bridge':'v17-browser-view'})
   try:
    with urllib.request.urlopen(req) as response:return response.status,json.load(response)
   except urllib.error.HTTPError as error:return error.code,json.load(error)
  def payload(deal,rev):
   return dict(cc=deal.cc,fm=deal.fm,item=deal.item,ign=deal.ign,buy_mesos=deal.buy_mesos,listing_id=deal.listing_id,_choice_session='clicks',_choice_revision=rev)
  try:
   self.page([A,B],1)
   self.assertEqual(post('/select',payload(A,1))[0],200)
   self.page([C,B],2)
   self.assertEqual(post('/select',payload(B,2))[0],409)
   self.assertEqual(self.a.current()[1].ign,'SellerA')
   self.assertEqual(post('/unlock',{'_choice_session':'clicks','_choice_revision':3})[0],200)
   self.assertEqual(self.a.current()[1],C)
   self.assertEqual(post('/unlock',[])[0],422)
   self.assertEqual(post('/select',payload(A,1))[0],409)
  finally:
   stop.set();thread.join();server.stop()
if __name__=='__main__':unittest.main()

