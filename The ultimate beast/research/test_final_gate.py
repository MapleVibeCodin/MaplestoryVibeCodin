"""Final gate: actual ZIP launcher and browser-side cancellation paths."""
import ast, copy, re, sys, subprocess, tempfile, time, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from fm_sprint_core import Lifecycle

ROOT=Path(__file__).resolve().parent.parent
SRC=(ROOT/'fm_sprint.py').read_text()
class FinalGate(unittest.TestCase):
    def test_browser_unlock_before_throttle(self):
        node=next(n for n in ast.walk(ast.parse(SRC)) if isinstance(n,ast.ClassDef) and n.name=='App')
        node=copy.deepcopy(node);node.bases=[ast.Name(id='Base',ctx=ast.Load())]
        node.body=[n for n in node.body if isinstance(n,ast.FunctionDef) and n.name in ('refresh_overlays','cancel_pending_pointers')]
        class Base:
            def refresh_overlays(self,current):pass
        user=Mock();user.GetAsyncKeyState.return_value=0
        ns={'Base':Base,'user':user,'time':time}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<actual App>','exec'),ns)
        a=ns['App']();a.flow=Lifecycle();a.flow.bind('key',('context',));a._f12=False;a._last_tick=time.perf_counter();a._pointer_serial=8;a._park_serial=4;a._pointer_pending=object();a.archive=SimpleNamespace(chase_locked=False);a.show_route_mini=Mock();a.refresh_overlays(('key',object()))
        self.assertEqual((a._pointer_serial,a._park_serial),(9,5));self.assertIsNone(a._pointer_pending);self.assertIsNone(a.flow.key)
    def test_powershell_native_python_arguments(self):
        # Windows PowerShell itself is unavailable; inspect and execute the exact
        # compile argument without embedded double quotes that native PS can strip.
        launcher=(ROOT/'START.ps1').read_text();codes=re.findall(r'-c "([^"\n]+)"',launcher)
        self.assertEqual(len(codes),3)
        for code in codes:compile(code,'<launcher>','exec')
        compile_code=next(c for c in codes if 'read_bytes' in c)
        p=subprocess.run([sys.executable,'-c',compile_code,str(ROOT)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        with tempfile.TemporaryDirectory(prefix='beast folder ') as d:
            for name in ('run_beast.py','beast_feedback.py','fm_sprint.py','fm_sprint_core.py'):
                (Path(d)/name).write_bytes((ROOT/name).read_bytes())
            p=subprocess.run([sys.executable,'-c',compile_code,d],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
    def test_final_build_identity(self):
        self.assertIn('The ultimate beast FINAL',SRC)
        self.assertIn('Trial FINAL',(ROOT/'START.ps1').read_text())
    def test_automatic_recovery_preserves_old_paths(self):
        s=(ROOT/'START.ps1').read_text()
        self.assertIn("-Filter 'pinned-source-*'",s);self.assertIn("-Filter 'venv-*'",s)
        self.assertNotIn('Remove-Item',s);self.assertNotIn('Rename-Item',s)
    def test_feedback_error_not_hidden(self):
        src=(ROOT/'run_beast.py').read_text();self.assertIn("os.environ.pop('FM_RUSH_WEB_ONLY',None)",src)
        node=ast.parse(src)
        self.assertTrue(any(isinstance(n,ast.ExceptHandler) and any(isinstance(x,ast.Raise) for x in n.body) for n in ast.walk(node)))
        self.assertIn('$RunCode -eq 0 -and',(ROOT/'START.ps1').read_text())

if __name__=='__main__':unittest.main()
