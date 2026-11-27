"""Requalify historical pinned-scanner fixtures against the current Exact contract.

Original pinned suite results are recorded separately; these adapters don't
edit any pinned source or historical test file.
"""
import os
import sys
import types
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
PINNED=Path(os.environ['BEAST_PINNED_SCANNER'])
sys.path.insert(0,str(ROOT))
sys.path.insert(1,str(PINNED))

def replace_once(src,old,new):
    if src.count(old)!=1:raise RuntimeError('Unexpected historical fixture: '+old)
    return src.replace(old,new,1)

def load(path):
    source=path.read_text(encoding='utf-8')
    if path.name=='test_inventory_hover.py':
        # Old mocks predate the base's name-only branch. Reuse the actual
        # current exact-price scan method; retain the capture and row fixtures.
        source=replace_once(source,
            't=ShopInventoryTracker.__new__(ShopInventoryTracker)',
            'from beast_inventory import InventoryFallbackMixin\n        class ExactTracker(InventoryFallbackMixin,ShopInventoryTracker):pass\n        t=ExactTracker.__new__(ExactTracker)')
        source=replace_once(source,
            't._ocr=SimpleNamespace(recognize=unexpected_ocr)',
            't._ocr=SimpleNamespace(recognize=lambda *args,**kwargs:lines)')
        # Old policy allowed a partial tooltip/name-only candidate. Current
        # user requires visible, complete item and verified exact price.
        source=replace_once(source,
            "if 'Scroll' in item:self.assertEqual(t._latest['hits'],[])\n                else:\n                    self.assertTrue(t._latest['hits'],t._latest)\n                    self.assertEqual(t._latest['hits'][0][0],'ROW_CHECK')",
            "self.assertEqual(t._latest['hits'],[])")
    elif path.name=='test_shop_inventory.py':
        # _find_anchor now reads the full observation, not the old 85x53
        # standalone gate; insert identical native signature pixels in it.
        old="""w,h=85,53;stride=w*3
        b=bytearray(stride*h)
        for dy,pattern in ((0,GREEN),(31,ORANGE),(51,ORANGE)):
            at=dy*stride+5*3"""
        new="""w,h=220,334;stride=w*3
        b=bytearray(stride*h)
        for dy,pattern in ((0,GREEN),(31,ORANGE),(51,ORANGE)):
            at=(dy+1)*stride+140*3"""
        source=replace_once(source,old,new)
        source=replace_once(source,"capture.assert_called_once_with((573,234,85,53),allow_crop=True)",
            "capture.assert_called_once_with((438,233,220,334),allow_crop=True)")
    module=types.ModuleType('requalified_'+path.stem)
    module.__file__=str(path)
    sys.modules[module.__name__]=module
    exec(compile(source,str(path),'exec'),module.__dict__)
    return unittest.defaultTestLoader.loadTestsFromModule(module)

if __name__=='__main__':
    suite=unittest.TestSuite()
    for path in sorted(PINNED.glob('test_*.py')):
        suite.addTests(load(path))
    print('Pinned historical fixtures, current contract:',suite.countTestCases(),flush=True)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
