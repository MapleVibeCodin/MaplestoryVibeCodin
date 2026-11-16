import os
import json
import http.client
import unittest
from fm_rush import FMApp
from henefm_bridge import HOST,PORT

@unittest.skipIf(os.name!='nt' and not os.environ.get('DISPLAY'),'No GUI display available')
class TestBrowserToApp(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        for field,path in [('ARCHIVE_DIR',Path(self.temp.name)/'archives'),('CONFIG',Path(self.temp.name)/'config.json')]:
            patcher=patch('fm_rush.'+field,path);patcher.start();self.addCleanup(patcher.stop)

    def test_browser_deal_updates_bottom_and_target(self):
        app=FMApp()
        try:
            good=dict(cc=30,fm=5,item='Blue Starlight',ign='Hyperborean',
                      stats='W.DEF 57 · INT 9+1',profit_mesos=22300,profit_percent=34,buy_mesos=65000)
            conn=http.client.HTTPConnection(HOST,PORT,timeout=3)
            conn.request('POST','/deal',json.dumps(good),headers={'Content-Type':'application/json',
                       'X-FM-Rush-Bridge':'v17-browser-view','Origin':'chrome-extension://test'})
            result=conn.getresponse()
            self.assertEqual(result.status,200)
            result.read();conn.close()
            app.pump()
            self.assertEqual((app.current_cc,app.current_fm),(30,5))
            self.assertEqual(app.shop_target,'Hyperborean')
            self.assertEqual(app.buy.get(),'BUY AT: 65,000 MESOS')
            self.assertIn('+22,300',app.profit.get())
            self.assertIn('Blue Starlight',app.item.get())
        finally:app.close()

if __name__=='__main__':unittest.main()
