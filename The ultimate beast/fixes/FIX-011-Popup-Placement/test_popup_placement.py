"""Source-level geometry regression, no GUI or Windows dependency."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

class PopupPlacementTests(unittest.TestCase):
    def test_centered_popup_and_visibility(self):
        source = Path(__file__).resolve().parents[2] / "fm_sprint.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        method, = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "show_route_mini"]
        scope = {"window_rect": lambda hwnd: window}
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), "exec"), scope)
        show = scope["show_route_mini"]
        for client, window in [
            ((0,0,1366,768),(0,0,1366,768)),
            ((8,31,1280,720),(0,0,1296,759)),
            ((108,231,1366,768),(100,200,1382,807)),
            ((-1912,31,1365,768),(-1920,0,1381,807)),
            ((8,31,184,209),(0,0,200,248)),
        ]:
            with self.subTest(client=client, window=window):
                calls = []
                pin = SimpleNamespace(show_many=lambda *args: calls.append(args), hide=lambda: calls.append("hide"))
                app = SimpleNamespace(_route_mini=pin, _route_mini_key=None)
                deal = SimpleNamespace(cc=20, fm=15)
                show(app, 1, client, deal)
                box = calls[0][2]["20:15"]["box"]
                x,y,r,b = box
                self.assertEqual((r-x,b-y),(160,185))
                self.assertEqual(y,client[1]-window[1]+12)
                self.assertLessEqual(abs(x+80-(client[0]-window[0]+client[2]/2)),.5)
                show(app, 1, client, deal)
                self.assertEqual(len(calls),1)
                show(app)
                self.assertEqual(calls[-1],"hide")
                self.assertIsNone(app._route_mini_key)

if __name__ == "__main__":
    unittest.main()
