from ImageAnalysisFuncs.analyze_metrology_height import methtHeight

import unittest

class TestPosRepImageAnalysis(unittest.TestCase):

    def test_expected(self):
        cases = [("PT25_metht_1_001.bmp", 0.076,  0.055),
                 ("PT25_metht_1_002.bmp", 0.074,  0.058),
                 ("PT25_metht_1_003.bmp", 0.073,  0.060),
                 ("PT25_metht_1_004.bmp", 0.071,  0.055),
                 ("PT25_metht_1_005.bmp", 0.070,  0.055),]

        for (test_image, small_ht, large_ht) in cases:
            (sh, lh) = methtHeight(test_image)

            ht_limit = 0.01 # millimeter
            
            self.assertTrue(abs(small_ht - sh) < ht_limit)

            self.assertTrue(abs(large_ht - lh) < ht_limit)
                        

            
if __name__ == '__main__':
    unittest.main()



