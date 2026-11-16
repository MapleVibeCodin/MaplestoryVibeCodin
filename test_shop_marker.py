import unittest
from shop_pin import ShopPin

class Canvas:
    def __init__(self):self.calls=[]
    def delete(self,*args):self.calls=[]
    def create_rectangle(self,*args,**kwargs):self.calls.append(('rect',args,kwargs));return len(self.calls)
    def create_line(self,*args,**kwargs):self.calls.append(('line',args,kwargs));return len(self.calls)
    def create_text(self,*args,**kwargs):self.calls.append(('text',args,kwargs));return len(self.calls)
    def bbox(self,*args):return (10,10,150,30)
    def tag_lower(self,*args):pass

class MarkerTests(unittest.TestCase):
    def test_multiple_sellers_have_large_red_boxes_and_arrows(self):
        pin=ShopPin.__new__(ShopPin);pin.canvas=Canvas()
        pin.draw_markers(1280,720,1280,720,{
            'Mora':{'box':(200,300,240,315),'mode':'EXACT'},
            'Oral':{'box':(600,500,640,515),'mode':'CONFUSABLE'}})
        reds=[args for kind,args,style in pin.canvas.calls if kind=='rect' and style.get('outline')=='#ff1744']
        self.assertEqual(len(reds),2)
        self.assertTrue(all(r-l>=110 and b-t>=110 for l,t,r,b in reds))
        arrows=[style for kind,_,style in pin.canvas.calls if kind=='line' and style.get('fill')=='#ff1744']
        self.assertEqual(len(arrows),2)
        labels=[style['text'] for kind,_,style in pin.canvas.calls if kind=='text']
        self.assertIn('Mora · HERE',labels);self.assertIn('Oral · CHECK NAME',labels)

    def test_top_row_marker_has_valid_bounds(self):
        pin=ShopPin.__new__(ShopPin);pin.canvas=Canvas()
        pin.draw_markers(1280,720,1280,720,{'Top':{'box':(200,2,250,15),'mode':'EXACT'}})
        for kind,args,style in pin.canvas.calls:
            if kind=='rect' and style.get('outline')=='#ff1744':
                l,t,r,b=args
                self.assertLess(t,b);self.assertGreaterEqual(t,0);self.assertLessEqual(b,720)

    def test_two_names_at_one_location_show_one_check_marker(self):
        pin=ShopPin.__new__(ShopPin);pin.canvas=Canvas()
        pin.draw_markers(1280,720,1280,720,{
            'IamNotty':{'box':(200,300,260,315),'mode':'EXACT'},
            'lamNotty':{'box':(201,300,261,315),'mode':'CONFUSABLE'}})
        reds=[args for kind,args,style in pin.canvas.calls if kind=='rect' and style.get('outline')=='#ff1744']
        self.assertEqual(len(reds),1)
        labels=[style['text'] for kind,_,style in pin.canvas.calls if kind=='text']
        self.assertEqual(labels,['IamNotty / lamNotty · CHECK NAME'])

    def test_stationary_markers_do_not_repaint_on_every_follow_tick(self):
        from types import SimpleNamespace
        from unittest.mock import Mock,patch
        pin=ShopPin.__new__(ShopPin);pin.window=Mock();pin.canvas=Canvas()
        pin.ready=True;pin.closed=False;pin.visible=False;pin.drawn=None;pin.last_rect=None;pin.hwnd=999
        pin.data=(123,(1280,720),{'Mora':{'box':(200,300,240,315),'mode':'EXACT'}})
        user=SimpleNamespace(IsIconic=lambda hwnd:False,GetForegroundWindow=lambda:123,SetWindowPos=Mock())
        with patch('shop_pin.ctypes.windll',SimpleNamespace(user32=user),create=True), \
             patch('shop_pin.window_rect',return_value=(0,0,1280,720)), \
             patch.object(pin,'draw_markers',wraps=pin.draw_markers) as draw:
            pin.follow(schedule=False);pin.follow(schedule=False)
            self.assertEqual(draw.call_count,1)
            pin.data[2]['Mora']['mode']='CONFUSABLE'
            pin.follow(schedule=False)
            self.assertEqual(draw.call_count,2)
