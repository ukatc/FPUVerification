from ImageAnalysisFuncs.analyze_metrology_calibration import metcalTargetCoordinates, metcalFibreCoordinates

import unittest
            

class TestMetCalImageAnalysis(unittest.TestCase):

    
    def test_expected(self):
        cases = [("PT25_metcal_1_001.bmp", 15.461,  0.874,  13.771,  8.620,  0.892),
                 ("PT25_metcal_1_003.bmp", 15.463,  0.862,  13.771,  8.618,  0.892),
                 ("PT25_metcal_1_004.bmp", 14.789,  0.860,  13.112,  8.598,  0.894),
                 ("PT25_metcal_1_005.bmp", 14.788,  0.872,  13.112,  8.598,  0.892),]

        for (test_image, small_x, small_y, small_q, large_x, large_y, large_q) in cases:
            (sx, sy, sq, lx, ly, lq) = metcalTargetCoordinates(test_image)



            pos_limit = 0.01 # millimeter
            q_limit = 0.05 # dimensionless
            
            self.assertTrue(abs(small_x - sx) < pos_limit)
            self.assertTrue(abs(small_y - sy) < pos_limit)
            self.assertTrue(abs(small_q - sq) < q_limit)
            
            self.assertTrue(abs(large_x - lx) < pos_limit)
            self.assertTrue(abs(large_y - ly) < pos_limit)
            self.assertTrue(abs(large_q - lq) < q_limit)
            
            
    def test_notFound(self):
        cases = ["PT25_metcal_1_002.bmp"]

        with self.assertRaises(MetrologyAnalysisTargetError):
            for (test_image, small_x, small_y, small_q, large_x, large_y, large_q) in cases:
                (sx, sy, sq, lx, ly, lq) = metcalTargetCoordinates(test_image)

            
if __name__ == '__main__':
    unittest.main()



