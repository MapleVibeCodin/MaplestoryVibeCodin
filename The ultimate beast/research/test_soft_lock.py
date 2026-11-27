"""Soft-lock tests using the pinned archive source with stub deal types."""
import ast,copy,hashlib,sys,tempfile,threading,time,types,unittest
from dataclasses import dataclass,field
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from run_beast import soft_lock_archive_type
from fm_sprint_core import Lifecycle

ROOT=Path(__file__).resolve().parent.parent
PIN=ROOT/'research'/'pinned'/'deal_archive.py'
PIN_SHA='3d0835989beb5091bdd63f52b745c837350221e1'
@dataclass
class ProfitDecision:
    label:str='example'
@dataclass
class Deal:
    listing_id:str
    ign:str='seller'
    cc:int=20
    fm:int=1
    item:str='Ribbon'
    stats:str=''
    buy_mesos:int=999
    sold:bool=False
    raw_text:str=''
    shop_position:object=None
    profit:ProfitDecision=field(default_factory=ProfitDecision)

def load_archive():
    b=PIN.read_bytes()
    assert hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()==PIN_SHA
    parser=types.ModuleType('deal_parser');parser.Deal=Deal
    profit=types.ModuleType('profit_filter');profit.ProfitDecision=ProfitDecision
    ns={'__name__':'pinned_archive_fixture'}
    with patch.dict(sys.modules,{'deal_parser':parser,'profit_filter':profit}):exec(compile(b,str(PIN),'exec'),ns)
    return ns['DealArchive']

class SoftLockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=load_archive()
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.a=soft_lock_archive_type(self.base)(Path(self.tmp.name)/'archive.db',manual_selection=True,auto_lock=True)
        self.addCleanup(self.a.close)
        self.deals=[Deal(c,fm=i+1) for i,c in enumerate('ABC')]
        self.a.apply_visible(self.deals,'page',1)
        self.keys=[self.a.record(d)[0] for d in self.deals]
    def test_click_replaces_lock_and_old_remains_pending(self):
        a=self.a;x,y,z=self.keys
        self.assertEqual(a.focus,x);self.assertTrue(a.chase_locked)
        self.assertTrue(a.choose(y));self.assertEqual(a.focus,y);self.assertTrue(a.chase_locked)
        self.assertEqual(a._setting('focus'),y);self.assertFalse(a.records[x]['done'])
        self.assertTrue(a.choose(z));self.assertTrue(a.choose(x));self.assertEqual(a.focus,x)
    def test_passive_feed_does_not_steal(self):
        a=self.a;a.choose(self.keys[1]);a.apply_visible([Deal('new'),self.deals[0]],'page',2)
        self.assertEqual(a.focus,self.keys[1]);self.assertTrue(a.chase_locked)
        a.preview_latest();self.assertEqual(a.focus,self.keys[1])
        self.assertFalse(a.apply_visible([Deal('older')],'page',1));self.assertEqual(a.focus,self.keys[1])
    def test_invalid_choice_retains_lock(self):
        a=self.a;self.assertFalse(a.choose('missing'));self.assertEqual(a.focus,self.keys[0]);self.assertTrue(a.chase_locked)
    def test_completed_non_skipped_rejected(self):
        a=self.a;a.mark_bought(self.keys[1],'receipt');self.assertFalse(a.choose(self.keys[1]));self.assertEqual(a.focus,self.keys[0]);self.assertTrue(a.chase_locked)
    def test_skipped_can_reopen_explicitly(self):
        a=self.a;a.skip(self.keys[1]);self.assertTrue(a.choose(self.keys[1]));self.assertFalse(a.records[self.keys[1]]['done']);self.assertTrue(a.chase_locked)
    def test_failure_does_not_release_lock(self):
        a=self.a
        with patch.object(a,'_save',side_effect=RuntimeError('disk')):
            with self.assertRaises(RuntimeError):a.choose(self.keys[1])
        self.assertTrue(a.chase_locked);self.assertEqual(a.focus,self.keys[0])
    def test_concurrent_feed_cannot_see_temporary_unlock(self):
        a=self.a;entered=threading.Event();release=threading.Event();done=threading.Event();orig=a.select
        def select(key):entered.set();release.wait(2);return orig(key)
        with patch.object(a,'select',side_effect=select):
            t=threading.Thread(target=lambda:a.choose(self.keys[1]));t.start();self.assertTrue(entered.wait(2))
            def feed():a.apply_visible([Deal('new')],'page',2);done.set()
            f=threading.Thread(target=feed);f.start();self.assertFalse(done.wait(.03));release.set();t.join(2);f.join(2)
        self.assertTrue(done.is_set());self.assertEqual(a.focus,self.keys[1]);self.assertTrue(a.chase_locked)
    def test_unlock_and_skip_unchanged(self):
        a=self.a;a.choose(self.keys[1]);a.unlock();self.assertFalse(a.chase_locked);self.assertEqual(a.focus,self.keys[0]);a.choose(self.keys[2]);a.skip(self.keys[2]);self.assertFalse(a.chase_locked)
    def test_original_base_stays_hard_locked(self):
        base=self.base(Path(self.tmp.name)/'original.db',manual_selection=True,auto_lock=True)
        try:
            base.apply_visible(self.deals,'page',1);self.assertFalse(base.choose(self.keys[1]));self.assertEqual(base.focus,self.keys[0])
        finally:base.close()
    def test_replacement_cancels_pending_before_base_refresh(self):
        src=(ROOT/'fm_sprint.py').read_text();tree=ast.parse(src);node=copy.deepcopy(next(n for n in ast.walk(tree) if isinstance(n,ast.ClassDef) and n.name=='App'));node.bases=[ast.Name(id='Base',ctx=ast.Load())];node.body=[n for n in node.body if isinstance(n,ast.FunctionDef) and n.name in ('refresh_overlays','cancel_pending_pointers')]
        class Base:
            def refresh_overlays(self,current):
                assert self._pointer_pending is None and self.flow.key is None
        user=Mock();user.GetAsyncKeyState.return_value=0
        ns={'Base':Base,'user':user,'time':time};exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<actual App>','exec'),ns)
        app=ns['App']();app.flow=Lifecycle();app.flow.bind('old',('context',));app._park_serial=3;app._pointer_serial=4;app._pointer_pending=object();app._f12=False;app._identity='old';app.archive=SimpleNamespace(chase_locked=True);app.show_route_mini=Mock();app.refresh_overlays(('new',SimpleNamespace(cc=20,fm=1,sold=True)))
        self.assertEqual((app._park_serial,app._pointer_serial),(4,5));self.assertIsNone(app._pointer_pending);self.assertIsNone(app._identity)

if __name__=='__main__':unittest.main()
