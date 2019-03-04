from ImageAnalysisFuncs.analyze_positional_repeatability import posrepCoordinates

import unittest

class TestPosRepImageAnalysis(unittest.TestCase):

    def test_expected(self):
        cases = [("PT25_posrep_1_001.bmp", 45.833,  30.703,  0.892,  44.083,  29.115,  0.904),
                 ("PT25_posrep_1_002.bmp", 45.830,  30.699,  0.886,  44.081,  29.111,  0.899),
                 ("PT25_posrep_1_003.bmp", 45.831,  30.700,  0.895,  44.080,  29.111,  0.898),
                 ("PT25_posrep_1_004.bmp", 45.156,  30.715,  0.894,  43.419,  29.113,  0.898),
                 ("PT25_posrep_1_005.bmp", 45.152,  30.717,  0.888,  43.418,  29.112,  0.903),]

        for (test_image, small_x, small_y, small_q, large_x, large_y, large_q) in cases:
            (sx, sy, sq, lx, ly, lq) = posrepCoordinates(test_image)

            pos_limit = 0.01 # millimeter
            q_limit = 0.05 # dimensionless
            
            self.assertTrue(abs(small_x - sx) < pos_limit)
            self.assertTrue(abs(small_y - sy) < pos_limit)
            self.assertTrue(abs(small_q - sq) < q_limit)
            
            self.assertTrue(abs(large_x - lx) < pos_limit)
            self.assertTrue(abs(large_y - ly) < pos_limit)
            self.assertTrue(abs(large_q - lq) < q_limit)
            
            

            
if __name__ == '__main__':
    unittest.main()



