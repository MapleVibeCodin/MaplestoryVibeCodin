import http.client
import json
import queue
import unittest
from henefm_bridge import BrowserBridge, HOST, PORT, parse_browser_deal
from item_price_lookup import url_for_item

OK={
    'cc':30, 'fm':5, 'item':'Blue Starlight', 'ign':'Hyperborean',
    'stats':'W.DEF 57 · M.DEF 66 · INT 9+1 · 10 slots',
    'buy_mesos':65000, 'profit_mesos':30000, 'profit_percent':34.0
}

class TestBrowserBridge(unittest.TestCase):
    def test_strict_browser_filter(self):
        d=parse_browser_deal(OK)
        self.assertIsNotNone(d)
        self.assertEqual(d.buy_label,'BUY AT: 65,000 MESOS')
        self.assertEqual((d.cc,d.fm,d.ign),(30,5,'Hyperborean'))
        for field,val in [('profit_mesos',14999),('profit_percent',14.9),('buy_mesos',0),('cc',41),('fm',21)]:
            self.assertIsNone(parse_browser_deal({**OK,field:val}),field)
        self.assertIsNone(parse_browser_deal({**OK,'ign':'bad name'}))
        self.assertIsNone(parse_browser_deal({'cc':30,'fm':5}))

    def test_cheap_exception(self):
        raw={**OK, 'profit_mesos':8600, 'profit_percent':819, 'unusually_cheap':True}
        self.assertIsNotNone(parse_browser_deal(raw))
        self.assertIsNone(parse_browser_deal({**raw,'unusually_cheap':'true'}))
        self.assertIsNone(parse_browser_deal({**raw,'buy_mesos':0}))
        self.assertIsNone(parse_browser_deal({**raw,'profit_percent':float('nan')}))
        self.assertIsNotNone(parse_browser_deal({**OK,'profit_percent':15}))

    def test_bridge_http_accept_and_reject(self):
        events=queue.Queue()
        server=BrowserBridge(events)
        server.start()
        try:
            c=http.client.HTTPConnection(HOST,PORT,timeout=2)
            c.request('GET','/health')
            r=c.getresponse()
            self.assertEqual(r.status,200)
            r.read();c.close()
            valid_headers={'Content-Type':'application/json','X-FM-Rush-Bridge':'v17-browser-view','Origin':'chrome-extension://test'}
            c=http.client.HTTPConnection(HOST,PORT,timeout=2)
            c.request('POST','/deal',json.dumps(OK),headers=valid_headers)
            r=c.getresponse()
            self.assertEqual(r.status,200)
            r.read();c.close()
            self.assertEqual(events.get_nowait()[1].ign,'Hyperborean')
            bad_origin={**valid_headers,'Origin':'https://evil.example'}
            c=http.client.HTTPConnection(HOST,PORT,timeout=2)
            c.request('POST','/deal',json.dumps(OK),headers=bad_origin)
            r=c.getresponse();self.assertEqual(r.status,403);r.read();c.close()
            self.assertTrue(events.empty())
            below={**OK,'profit_mesos':8000}
            c=http.client.HTTPConnection(HOST,PORT,timeout=2)
            c.request('POST','/deal',json.dumps(below),headers=valid_headers)
            r=c.getresponse();self.assertEqual(r.status,422);r.read();c.close()
            self.assertTrue(events.empty())
        finally:
            server.stop()

    def test_single_item_query(self):
        self.assertEqual(url_for_item('1082000','stats.crit_rate=3'),
                         'https://henefm.com/api/public/v1/items/1082000/price?stats.crit_rate=3')
        with self.assertRaises(ValueError):url_for_item('notanid')
        with self.assertRaises(ValueError):url_for_item('1082000','api/getAll=1')

if __name__=='__main__':unittest.main()
