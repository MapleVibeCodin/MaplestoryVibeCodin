"""Game-only location regressions from the latest uploaded screenshots."""
from pathlib import Path
import unittest
import cv2
from name_finder import NameFinder

ROOT=Path(__file__).parent
CASES=[
('162357',(107,34,1475,802),'Bums',(1453,628)),
('162456',(110,51,1054,719),'oHunt',(648,398)),
('174245',(0,40,1305,808),'vlex',(1122,449)),
('174330',(0,40,1305,808),'williamcc',(300,394)),
('175543',(0,40,1305,808),'ShroomFarmer',(751,582)),
('185546',(57,83,1425,851),'loshop',(998,190)),
('185751',(57,83,1425,851),'Fadenz',(864,584)),
('190224',(2,48,1368,816),'Ivane',(468,168)),
('191120',(2,48,1368,816),'francoftw',(195,400)),
('191702',(3,45,1370,813),'Doromamoo',(390,314)),
('195150',(3,45,1370,813),'languishwisp',(548,183)),
('204232',(2,45,1370,813),'bayyoo',(412,697)),
('205756',(0,0,1368,576),'Bleu',(205,158)),
('212444',(3,45,1370,809),'AddeHD',(990,634)),
('212549',(3,45,1370,806),'AdriChan',(695,634)),
('212708',(3,45,1370,813),'jr0geroge',(300,657)),
('213139',(0,0,463,560),'daboiboi',(50,103)),
]

class UploadedReaderNames(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cv2.setNumThreads(1)
        cls.finder=NameFinder()

    def read(self,stamp,crop,name):
        image=cv2.imread(str(ROOT/f'Screenshot 2026-11-16 {stamp}.png'))
        self.assertIsNotNone(image)
        x,y,r,b=crop
        game=image[y:b,x:r]
        return self.finder.scan(game,name,quick_only=True) or self.finder.scan(game,name)

    def test_uploaded_targets_locate_the_game_name_label(self):
        uncertain={'vlex','ShroomFarmer','loshop','Ivane','francoftw','jr0geroge'}
        for stamp,crop,name,(x,y) in CASES:
            with self.subTest(name=name):
                hit=self.read(stamp,crop,name)
                self.assertIsNotNone(hit,self.finder.last_diagnostic)
                l,t,r,b=hit.box
                self.assertTrue(l<=x-crop[0]<=r and t<=y-crop[1]<=b,hit)
                if name in uncertain:self.assertNotEqual(hit.mode,'EXACT',hit)

    def test_browser_sellers_and_wrong_full_names_are_rejected(self):
        for index,name in [(13,'Dolve'),(13,'Waku'),(14,'AdriChann'),
                           (15,'j0rgeorge'),(15,'jr0gerogeX'),(16,'daboi'),
                           (5,'loshopp'),(3,'villiamcc'),(2,'vlexx')]:
            stamp,crop,_,_=CASES[index]
            with self.subTest(name=name):self.assertIsNone(self.read(stamp,crop,name))
