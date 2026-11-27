import random
import unittest
import time
import statistics
import pinned_excerpt as old
from exact_cache import ExactRowCache


def frame(values, price=0, stride=620):
    buf = bytearray([227]) * (stride * 263)
    for row, value in enumerate(values):
        y = 26 + 40 * row
        buf[y * stride + 40 * 3] = value
        buf[y * stride + 201 * 3] = price
    return bytes(buf), 204, 263, stride


def prepare(frame, rows):
    return tuple(frame[0][(26+40*r)*frame[3]+120] for r in rows), dict(enumerate(rows))


class OCR:
    def __init__(self):
        self.calls = []
    def recognize(self, values):
        self.calls.append(values)
        return [line for slot, val in enumerate(values) if val != 0
                for line in ({'y': slot*84+3,'text': ' Item '},
                             {'y': slot*84+12,'text': str(val)},
                             {'y': slot*84+66,'text': 'ignored gap'})]


def pair(limit=512):
    old.prepare_name_ocr = prepare
    return old.NameOCRCache(limit), ExactRowCache(old.name_row_fingerprint, prepare, limit=limit), OCR(), OCR()


class DifferentialTests(unittest.TestCase):
    def check_scan(self, p, f, rows):
        a,b,oa,ob=p
        x=a.recognize(f, rows, oa)
        y=b.recognize(f, rows, ob)
        self.assertEqual(x,y)
        self.assertEqual(list(x[0]),list(y[0]))
        self.assertEqual(list(a.entries.items()),list(b.entries.items()))
        self.assertEqual(oa.calls,ob.calls)
        return y

    def test_cold_warm_and_price(self):
        p=pair(); f=frame([1,2,3,4,5,6])
        self.assertEqual(self.check_scan(p,f,range(6))[1:],(0,6,True))
        self.assertEqual(self.check_scan(p,frame([1,2,3,4,5,6],8),range(6))[1:],(6,0,False))

    def test_blank_retry(self):
        p=pair(); f=frame([0,1,2,3,4,5])
        for _ in range(3):
            self.assertEqual(self.check_scan(p,f,[0])[0],{0:''})
        self.assertFalse(p[1].entries)

    def test_same_content_multiple_rows(self):
        p=pair(); f=frame([7,7,7,0,1,1])
        self.assertEqual(self.check_scan(p,f,[2,0,1,2])[1:],(0,3,True))
        self.assertEqual(self.check_scan(p,f,[0,1,2])[1:],(3,0,False))

    def test_empty_and_eviction(self):
        for limit in (0,1,2,512):
            p=pair(limit)
            self.check_scan(p,frame([1,2,3,4,5,6]),[])
            for seq in ([1,2,3,4,5,6],[6,5,4,3,2,1],[3,3,4,0,2,6]):
                self.check_scan(p,frame(seq),range(6))
                self.assertLessEqual(len(p[1].entries),limit)

    def test_row_identity_and_padding(self):
        p=pair(); self.check_scan(p,frame([1,2,3,4,5,6]),[0])
        self.assertEqual(self.check_scan(p,frame([8,1,7,0,2,5],stride=640),[1])[1:],(1,0,False))

    def test_normalized_duplicate_truncation(self):
        self.assertEqual(old.exact_name_rows({0:'  Ｉtem   1'},'item 1'),[0])
        self.assertEqual(old.exact_name_rows({0:'Item 1',1:'item 1'},'item 1'),[])
        self.assertEqual(old.exact_name_rows({0:'Very Long Item Name',1:'Very Long Item...'},'Very Long Item Name'),[])
        self.assertEqual(old.exact_name_rows({0:'Item 1'},'item 1',[0]),[])

    def test_random_differential(self):
        rng=random.Random(3301)
        for limit in (0,1,5,512):
            p=pair(limit)
            for _ in range(300):
                f=frame([rng.randrange(10) for _ in range(6)],rng.randrange(255))
                self.check_scan(p,f,[rng.randrange(6) for _ in range(rng.randrange(9))])


def benchmark():
    p=pair(); f=frame([1,2,3,4,5,6]); rows=range(6)
    for engine,ocr in ((p[0],p[2]),(p[1],p[3])):
        engine.recognize(f,rows,ocr)
    samples=[[],[]]
    for i in range(3000):
        for j in (i%2,1-i%2):
            t=time.perf_counter_ns();p[j].recognize(f,rows,p[j+2]);samples[j].append((time.perf_counter_ns()-t)/1000)
    for name,times in zip(('pinned','extracted'),samples):
        print(name,'median_us',round(statistics.median(times),3),'p95_us',round(sorted(times)[2849],3),'n',len(times))


if __name__=='__main__':
    unittest.main(exit=False)
    benchmark()
