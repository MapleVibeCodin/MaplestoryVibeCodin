import unittest
import numpy as np
from minimap_tracker import viewport,observe
class MiniTests(unittest.TestCase):
    def frame(self):
        im=np.zeros((230,519,3),np.uint8)
        im[71,4:208]=255;im[176,4:208]=255;im[71:177,4]=255;im[71:177,207]=255
        im[130:135,100:105]=(34,238,255);im[100:105,120:125]=(0,0,238)
        return im
    def test_markers(self):
        im=self.frame();b=viewport(im);self.assertIsNotNone(b)
        r=observe(im,b);self.assertEqual(r['status'],'candidate');self.assertEqual(len(r['red_xy']),1)
    def test_ambiguous(self):
        im=self.frame();im[120:125,140:145]=(34,238,255)
        self.assertEqual(observe(im,viewport(im))['status'],'ambiguous_self')
    def test_no_viewport(self):
        im=np.zeros((230,519,3),np.uint8);self.assertIsNone(viewport(im))
        self.assertIsNone(observe(im,None)['red_xy'])
if __name__=='__main__':unittest.main()
