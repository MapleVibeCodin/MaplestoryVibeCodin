"""Platform-independent integration checks against the actual nested App methods."""
import ast,copy,importlib.util,socket,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from fm_sprint import target_context,live_target_matches
from fm_sprint_core import Lifecycle
from beast_feedback import build_report
from run_beast import check_bridge_available,check_source

ROOT=Path(__file__).resolve().parent
if not (ROOT/'fm_sprint.py').is_file():ROOT=ROOT.parent
SRC=(ROOT/'fm_sprint.py').read_text()
TREE=ast.parse(SRC)
APP=next(n for n in ast.walk(TREE) if isinstance(n,ast.ClassDef) and n.name=='App')

def load_app(base,**env):
    methods={'cancel_pending_pointers','set_chase_locked','complete_deal','move_pointer_to_target','current_target_valid','at','release_and_park'}
    node=copy.deepcopy(APP);node.bases=[ast.Name(id='Base',ctx=ast.Load())];node.body=[n for n in node.body if isinstance(n,ast.FunctionDef) and n.name in methods]
    ns={'Base':base,'target_context':target_context,'live_target_matches':live_target_matches,**env}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<actual App>','exec'),ns)
    return ns['App']

def deal(**updates):
    d=dict(cc=20,fm=1,item='Ribbon',buy_mesos=999,listing_id='id',ign='seller',shop_position=(1,2),sold=False);d.update(updates);return SimpleNamespace(**d)

class Tests(unittest.TestCase):
    def setUp(self):
        self.client=(0,0,1366,768);self.d=deal();self.ctx=target_context(self.d,1,self.client);self.current=('key',self.d)
    def test_same_key_metadata_change_cancels(self):
        for k,v in dict(cc=21,fm=2,item='Other',buy_mesos=1000,listing_id='other',ign='other',shop_position=(2,3),sold=True).items():
            with self.subTest(k=k):self.assertFalse(live_target_matches(('key',deal(**{k:v})),True,'key',self.ctx,1,self.client))
        self.assertTrue(live_target_matches(self.current,True,'key',self.ctx,1,self.client))
        self.assertFalse(live_target_matches(self.current,False,'key',self.ctx,1,self.client))
        self.assertFalse(live_target_matches(self.current,True,'key',self.ctx,2,self.client))
    def make_app(self,**env):
        class Base:
            def set_chase_locked(self,locked):self.archive.chase_locked=locked
            def complete_deal(self):self.skipped=True
            def move_pointer_to_target(self,*a,**kw):self.inherited_called=True
        user=Mock();user.GetAsyncKeyState.return_value=0
        app=load_app(Base,user=user,**env)();app.flow=Lifecycle();app.flow.bind('key',self.ctx);app._park_serial=4;app._pointer_serial=8;app._pointer_pending=object();app.status=Mock();app.archive=SimpleNamespace(lock=threading.Lock(),current=lambda:self.current,chase_locked=True);return app,user
    def test_unlock_cancels_both_paths_even_if_relocked(self):
        a,_=self.make_app();a.set_chase_locked(False);a.set_chase_locked(True);self.assertEqual((a._park_serial,a._pointer_serial),(5,9));self.assertIsNone(a._pointer_pending);self.assertIsNone(a.flow.key)
    def test_skip_cancels_both_paths(self):
        a,_=self.make_app();a.complete_deal();self.assertTrue(a.skipped);self.assertEqual((a._park_serial,a._pointer_serial),(5,9));self.assertIsNone(a.flow.key)
    def test_stopped_inherited_shortcut_blocked(self):
        a,u=self.make_app();a.flow.stop();a.move_pointer_to_target('shop');self.assertFalse(hasattr(a,'inherited_called'));self.assertIsNone(a._pointer_pending)
    def test_f12_inherited_shortcut_blocked(self):
        a,u=self.make_app();u.GetAsyncKeyState.return_value=0x8000;a.move_pointer_to_target('channel');self.assertFalse(hasattr(a,'inherited_called'))
    def test_focused_click_aborts_changed_target(self):
        a,u=self.make_app(window_at_point=lambda *x:1,cursor_screen_position=lambda:(5,5),move_cursor_on_screen=Mock());a.safe=lambda *x:True;a.f9_down=lambda:True
        self.current=('key',deal(buy_mesos=123));self.assertFalse(a.at(1,self.client,(5,5),click=True,require_f9=True));u.mouse_event.assert_not_called()
    def test_focused_click_rechecks_after_move(self):
        a,u=self.make_app(window_at_point=lambda *x:1,cursor_screen_position=lambda:(5,5));a.safe=Mock(side_effect=[True,False]);a.f9_down=lambda:True
        self.assertFalse(a.at(1,self.client,(5,5),click=True,require_f9=True));u.mouse_event.assert_not_called()
    def test_port_occupied_detected(self):
        with socket.socket() as s:
            s.bind(('127.0.0.1',0));s.listen();port=s.getsockname()[1]
            with self.assertRaises(SystemExit):check_bridge_available(port=port)
    def test_port_free(self):check_bridge_available(port=0)
    def test_source_shadow_detected(self):
        with patch('run_beast.importlib.util.find_spec',return_value=SimpleNamespace(origin='/tmp/rogue.py')):
            with self.assertRaises(SystemExit):check_source(Path('/tmp/pinned'))
    def test_feedback_pointer_summary(self):
        r=build_report([dict(event='beast_pointer_handoff',t=1,ok=True,reason='moved',total_ms=10),dict(event='beast_pointer_handoff',t=2,ok=False,reason='focus_timeout',total_ms=75)])
        self.assertEqual(r['pointer_handoffs']['count'],2);self.assertEqual(r['pointer_handoffs']['succeeded'],1);self.assertEqual(r['pointer_handoffs']['reasons']['focus_timeout'],1)
    def test_no_automatic_movement_text(self):
        self.assertIn("self.status.set('LOCKED · Shift+2 to unlock')",SRC)
        self.assertEqual(SRC.count('self.status.set(self._message)'),1)
    def test_no_capture_worker(self):
        text=(ROOT/'run_beast.py').read_text();self.assertIn('super().__init__(folder)',text);self.assertIn('base.ShopScreenshotRecorder = NoScreenshots',text)

if __name__=='__main__':unittest.main()
