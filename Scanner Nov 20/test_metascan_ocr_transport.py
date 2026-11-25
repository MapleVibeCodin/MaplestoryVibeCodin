import base64
from pathlib import Path
import unittest
from unittest.mock import Mock
from shop_inventory import WindowsOCR, ShopInventoryTracker

class TransportTests(unittest.TestCase):
    def test_memory_success_uses_no_file(self):
        worker=WindowsOCR()
        worker._exchange=Mock(return_value={'ok':True,'lines':[{'text':'ok'}]})
        self.assertEqual(worker.recognize(b'PNG'),[{'text':'ok'}])
        self.assertEqual(worker._exchange.call_args.args[0],{'png':base64.b64encode(b'PNG').decode('ascii')})
    def test_handled_memory_error_falls_back_and_stays_on_file(self):
        worker=WindowsOCR()
        calls=[]
        def exchange(request):
            calls.append(request)
            if isinstance(request,dict):return {'ok':False,'error':'memory unsupported'}
            self.assertEqual(Path(request).read_bytes(),b'PNG')
            return {'ok':True,'lines':[]}
        worker._exchange=exchange
        self.assertEqual(worker.recognize(b'PNG'),[])
        self.assertEqual(worker.recognize(b'PNG'),[])
        self.assertEqual(len(calls),3)
        self.assertIsInstance(calls[0],dict)
        self.assertTrue(all(isinstance(v,str) for v in calls[1:]))
        self.assertFalse(worker._memory_png)
    def test_highlight_notification_only_on_change(self):
        import threading
        t=ShopInventoryTracker.__new__(ShopInventoryTracker)
        t._lock=threading.Lock();t._key='current';t._latest=None
        t._notify=Mock()
        t._publish('current',{'hits':[]})
        t._notify.assert_not_called()
        t._publish('current',{'hits':[('MATCH',(1,2,3,4))]})
        t._publish('current',{'hits':[('MATCH',(1,2,3,4))]})
        t._publish('old',None)
        self.assertEqual(t._notify.call_count,1)
        t._publish('current',None)
        self.assertEqual(t._notify.call_count,2)

if __name__=='__main__':unittest.main()
