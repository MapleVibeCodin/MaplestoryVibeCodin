import unittest
from dataclasses import replace
from fm_sprint_core import *
from fm_sprint import header

class FlowTests(unittest.TestCase):
    def test_no_actions_without_entrance(self):
        f=Lifecycle()
        self.assertEqual(f.step('x',Scene(black=True),navigate=True),[])
        self.assertEqual(f.step('x',Scene(black=True),navigate=True),[])
        self.assertEqual(f.stage,'route')
    def test_complete_navigation(self):
        f=Lifecycle();f.step('a',Scene(entrance=True),navigate=True)
        self.assertEqual(f.step('a',Scene(black=True),navigate=True),[])
        self.assertEqual(f.step('a',Scene(black=True),navigate=True),['park_channel'])
        self.assertEqual(f.step('a',Scene(room=True),navigate=True),[])
        self.assertEqual(f.step('a',Scene(room=True,menu=True),navigate=True),['select_channel'])
        self.assertEqual(f.step('a',Scene(room=True,menu=True),navigate=True),[])
        self.assertEqual(f.step('a',Scene(room=True,menu=True,selected=True,confirm=False),navigate=True),[])
        self.assertEqual(f.step('a',Scene(room=True,menu=True,selected=True,confirm=True),navigate=True),['confirm_channel'])
        self.assertEqual(f.step('a',Scene(room=True,menu=True,selected=True,confirm=True),navigate=True),[])
        self.assertEqual(f.step('a',Scene(black=True,pin=True),navigate=True),[])
        self.assertEqual(f.step('a',Scene(black=True,pin=True),navigate=True),['park_shop_cc'])
        self.assertEqual(f.step('a',Scene(room=True,pin=True),navigate=True),['open_projected_shop'])
        self.assertEqual(f.step('a',Scene(room=True,pin=True),navigate=True),[])
        self.assertEqual(f.step('a',Scene(room=True,shop=True),navigate=True),['park_clear'])
        self.assertEqual(f.step('a',Scene(room=True,shop=True,hit=True),navigate=True),[])
        self.assertEqual(f.stage,'item_ready')
    def test_same_channel(self):
        f=Lifecycle();f.step('x',Scene(entrance=True),same_channel=True)
        self.assertEqual(f.step('x',Scene(room=True,pin=True),same_channel=True),['park_shop_normal'])
        self.assertEqual(f.stage,'shop')
    def test_focus_interrupts_black(self):
        f=Lifecycle();f.step('a',Scene(entrance=True));f.step('a',Scene(black=True))
        self.assertEqual(f.step('a',Scene(black=True,focus=False)),[])
        self.assertEqual(f.step('a',Scene(black=True)),[])
        self.assertEqual(f.step('a',Scene(black=True)),['park_channel'])
    def test_cancel_generation(self):
        f=Lifecycle();f.step('a',Scene(entrance=True));f.step('a',Scene(black=True))
        self.assertEqual(f.step('b',Scene(black=True),navigate=True),[])
        self.assertEqual(f.step('b',Scene(black=True),navigate=True),[])
        self.assertEqual(f.stage,'route')
    def test_stop(self):
        f=Lifecycle();f.step('a',Scene(entrance=True));f.stop()
        self.assertEqual(f.step('a',Scene(room=True,pin=True),navigate=True),[])
    def test_no_click_by_default(self):
        f=Lifecycle();f.step('a',Scene(entrance=True));f.step('a',Scene(room=True))
        self.assertEqual(f.step('a',Scene(room=True,menu=True)),[])
        self.assertEqual(f.step('a',Scene(room=True,menu=True,selected=True,confirm=True)),[])
    def test_no_blind_cc_fade(self):
        f=Lifecycle();f.step('a',Scene(entrance=True));f.step('a',Scene(room=True))
        f.step('a',Scene(black=True,pin=True));self.assertEqual(f.step('a',Scene(black=True,pin=True)),[])
        self.assertEqual(f.stage,'channel')
    def test_no_shop_pin(self):
        f=Lifecycle();f.step('a',Scene(entrance=True),same_channel=True);f.step('a',Scene(room=True),same_channel=True)
        self.assertEqual(f.step('a',Scene(room=True),navigate=True),[])
    def test_stop_latched_across_geometry_changes(self):
        f=Lifecycle();self.assertEqual(f.bind('a',('old',)), 'new');f.stop()
        self.assertEqual(f.bind('a',('new',)), 'context_changed')
        self.assertEqual(f.bind('a',('old',)), 'same')
        self.assertEqual(f.stage,'stopped')
        self.assertEqual(f.step('a',Scene(entrance=True,room=True),navigate=True),[])
        self.assertEqual(f.bind('b',('new',)), 'new');self.assertEqual(f.stage,'route')
    def test_initial_window_missing_then_available(self):
        f=Lifecycle();f.bind('a',None);f.bind('a',('window',));self.assertEqual(f.stage,'route')
        self.assertEqual(f.bind('a',None),'context_changed');self.assertEqual(f.stage,'stopped')
    def test_item_ready_requires_current_hit(self):
        f=Lifecycle();f.step('a',Scene(entrance=True),same_channel=True)
        f.step('a',Scene(room=True,shop=True,hit=True),same_channel=True)
        self.assertEqual(f.stage,'item_ready')
        f.step('a',Scene(room=True,shop=True,hit=False));self.assertEqual(f.stage,'scan')
    def test_inventory_fresh_identity_and_sold_rejection(self):
        key=(1,(0,0,1366,768),'id','seller','item',100,0,1)
        result={'hits':[('ROW_CHECK',(1,2,3,4))]}
        self.assertEqual(fresh_inventory(result,key,key[:6],1.,1.1),(True,True))
        self.assertEqual(fresh_inventory(result,key,key[:6],1.,1.36),(False,False))
        self.assertEqual(fresh_inventory(result,key,key[:5]+(200,),1.,1.1),(False,False))
        self.assertEqual(fresh_inventory({'hits':[('SOLD',(1,2,3,4))]},key,key[:6],1.,1.1),(True,False))
        self.assertEqual(fresh_inventory(result,key,key[:6],None,1.1),(False,False))
    def test_f9_channel_only_and_release(self):
        f=Lifecycle();f.step('a',Scene(entrance=True),channel_request=True)
        f.step('a',Scene(black=True),channel_request=True)
        self.assertEqual(f.step('a',Scene(black=True),channel_request=True),['park_channel'])
        f.step('a',Scene(room=True),channel_request=True)
        self.assertEqual(f.step('a',Scene(room=True,menu=True),channel_request=True),['select_channel'])
        self.assertEqual(f.step('a',Scene(room=True,menu=True,selected=True,confirm=True)),[])
        self.assertEqual(f.step('a',Scene(room=True,menu=True,selected=True,confirm=True),channel_request=True),['confirm_channel'])
        self.assertEqual(f.step('a',Scene(room=True,menu=True,selected=True,confirm=True),channel_request=True),[])
        f.step('a',Scene(black=True,pin=True),channel_request=True)
        self.assertEqual(f.step('a',Scene(black=True,pin=True),channel_request=True),['park_shop_cc'])
        self.assertEqual(f.step('a',Scene(room=True,pin=True),channel_request=True),[])
    def test_failed_channel_rearms_only_after_release(self):
        f=Lifecycle();f.step('a',Scene(entrance=True));f.step('a',Scene(room=True))
        m=Scene(room=True,menu=True)
        self.assertEqual(f.step('a',m,channel_request=True),['select_channel']);f.channel_failed('select_channel')
        self.assertEqual(f.step('a',m,channel_request=True),[])
        self.assertEqual(f.step('a',m),[])
        self.assertEqual(f.step('a',m,channel_request=True),['select_channel'])
    def test_route_map_all_rooms(self):
        for room in range(1,21):
            nodes,path,cue=mini_route(room)
            self.assertEqual(set(nodes),set(range(1,21)));self.assertEqual(path[-1],nodes[room]);self.assertEqual(path[0],(80,77))
            self.assertTrue(all(0<x<160 and 0<y<185 for x,y in path));self.assertEqual(len(cue),2)
        self.assertIn('WARP',mini_route(1)[2][0]);self.assertIn('CLIMB',mini_route(20)[2][0])
    def test_f9_explicit_release_recovers_unregistered_click(self):
        f=Lifecycle();f.step('a',Scene(entrance=True));f.step('a',Scene(room=True))
        m=Scene(room=True,menu=True)
        self.assertEqual(f.step('a',m,channel_request=True),['select_channel'])
        self.assertEqual(f.step('a',m,channel_request=True),[])
        self.assertEqual(f.step('a',m),[])
        self.assertEqual(f.step('a',m,channel_request=True),['select_channel'])
    def test_f9_never_clicks_on_focus_loss(self):
        f=Lifecycle();f.step('a',Scene(entrance=True));f.step('a',Scene(room=True))
        self.assertEqual(f.step('a',Scene(room=True,menu=True,focus=False),channel_request=True),[])
    def test_auto_mode_failure_does_not_loop(self):
        f=Lifecycle();f.step('a',Scene(entrance=True));f.step('a',Scene(room=True))
        m=Scene(room=True,menu=True)
        self.assertEqual(f.step('a',m,navigate=True),['select_channel']);f.channel_failed('select_channel')
        self.assertEqual(f.step('a',m,navigate=True),[])
    def test_grid_points(self):
        self.assertEqual(channel_points(1),((437,353),(837,473)))
        self.assertEqual(channel_points(40),((927,441),(837,473)))
        self.assertIsNone(channel_points(41));self.assertIsNone(channel_points(1,(1280,720)))
    def test_purchase_all_gates_required(self):
        values={k:True for k in PurchaseProof.__dataclass_fields__};values['quantity']=1
        p=PurchaseProof(**values);self.assertTrue(purchase_ready(p))
        for k in values:
            self.assertFalse(purchase_ready(replace(p,**{k:0 if k=='quantity' else False})),k)
        self.assertFalse(purchase_ready(replace(p,quantity=2)))

class VisionTests(unittest.TestCase):
    def test_conflict(self):
        b=VisualBank();b.learn(b'x','Name');self.assertEqual(b.get(b'x'),'Name')
        b.learn(b'x','Other');self.assertIsNone(b.get(b'x'));b.learn(b'x','Name');self.assertIsNone(b.get(b'x'))
    def test_ellipsis_not_learned(self):
        b=VisualBank();b.learn(b'x','Abc...');self.assertIsNone(b.get(b'x'))
    def test_blank_not_learned(self):
        b=VisualBank();b.learn(b'x','');self.assertIsNone(b.get(b'x'))
    def test_visual_key_price_independent(self):
        a=np.full((263,204,3),[227,217,205],dtype=np.uint8)
        a[30:37,42:60]=0;a[30:42,8:18]=[25,5,180]
        frame=lambda a:(a.tobytes(),204,263,612)
        k=visual_key(frame(a),0);self.assertIsNotNone(k)
        a[49:58,45:80]=0;self.assertEqual(visual_key(frame(a),0),k)
        a[31:35,64:70]=0;self.assertNotEqual(visual_key(frame(a),0),k)
    def test_blank_visual_key(self):
        a=np.full((263,204,3),[227,217,205],dtype=np.uint8)
        self.assertIsNone(visual_key((a.tobytes(),204,263,612),0))
    def test_rune_cache_reuse(self):
        class Base:
            def __init__(self):self.calls=0
            def recognize(self,frame,rows,ocr):self.calls+=1;return {r:'Test Item' for r in rows},0,len(rows),True
        a=np.full((263,204,3),[227,217,205],dtype=np.uint8);a[30:37,42:60]=0;a[30:42,8:18]=[25,5,180]
        frame=(a.tobytes(),204,263,612);base=Base();cache=RuneCache(base)
        self.assertEqual(cache.recognize(frame,[0],None)[0],{0:'Test Item'})
        self.assertEqual(cache.recognize(frame,[0],None),({0:'Test Item'},1,0,False));self.assertEqual(base.calls,1)
    def test_menu_header(self):
        a=np.zeros((200,565,3),np.uint8);a[:51,:164]=header()[:,:,None]
        a[131:135,10:22]=[220,168,55];a[185:189,387:399]=[229,144,34]
        self.assertEqual(menu_evidence((a.tobytes(),565,200,1695),header(),25)[:3],(True,True,True))
    def test_black_not_menu(self):
        a=np.zeros((200,565,3),np.uint8)
        self.assertEqual(menu_evidence((a.tobytes(),565,200,1695),header(),25)[:3],(False,False,False))
if __name__=='__main__':unittest.main(verbosity=2)
