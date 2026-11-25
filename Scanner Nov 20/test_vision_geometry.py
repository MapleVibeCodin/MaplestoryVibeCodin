import unittest
from vision_geometry import WIDTH, HEIGHT, AX, AY, geometry_present, conservative_hits


def fixture(rows=6, orange=(31,51), occluded=(), shift=0):
    stride=(WIDTH*3+3)&~3
    buf=bytearray(stride*HEIGHT)
    def set_pixel(x,y,color):
        i=y*stride+x*3;buf[i:i+3]=bytes(color)
    for dy,c in [(0,(70,222,208))]+[(dy,(130,163,215)) for dy in orange]:
        for x in range(AX+shift,AX+shift+24):set_pixel(x,AY+dy,c)
    for row in range(rows):
        color=((227,216,204),(248,243,242),(40,152,230))[row%3]
        y=AY+93+row*40
        for dx in (-100,-55,-10,54):
            for yy in range(y+4,y+36):set_pixel(AX+dx,yy,(124,75,70) if (row,dx) in occluded else color)
    return buf,WIDTH,HEIGHT,stride


class GeometryTests(unittest.TestCase):
    def test_valid_and_occluded(self):
        self.assertTrue(geometry_present(fixture()))
        self.assertTrue(geometry_present(fixture(orange=(31,),occluded=tuple((i,54) for i in range(6)))))
    def test_reject_missing_geometry(self):
        for f in (fixture(rows=0),fixture(rows=2),fixture(orange=()),fixture(rows=3,orange=(31,)),fixture(shift=12),None,(b'',WIDTH,HEIGHT,WIDTH*3)):
            with self.subTest(f=f is None):self.assertFalse(geometry_present(f))
    def test_dark_border_required(self):
        f=fixture();b,w,h,s=f
        for x in range(AX+2,AX+24):b[x*3:x*3+3]=bytes((220,220,220))
        self.assertFalse(geometry_present(f))
    def test_fail_closed_candidates(self):
        self.assertEqual(conservative_hits([(2,'MATCH')],False),[(2,'ROW_CHECK')])
        self.assertEqual(conservative_hits([(2,'SOLD')],False),[(2,'SOLD_CHECK')])
        self.assertEqual(conservative_hits([(2,'PRICE_CHECK')],False),[(2,'PRICE_CHECK')])
        self.assertEqual(conservative_hits([(2,'MATCH')],True),[])
        self.assertEqual(conservative_hits([(1,'MATCH'),(2,'MATCH')],False),[])
        self.assertEqual(conservative_hits([],False),[])
        self.assertEqual(conservative_hits([(1,'unknown')],False),[])

if __name__=='__main__':unittest.main()
