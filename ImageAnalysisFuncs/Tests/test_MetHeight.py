from __future__ import print_function, division, absolute_import
from ImageAnalysisFuncs.analyze_metrology_height import methtHeight

import unittest

from vfr.conf import MET_HEIGHT_ANALYSIS_PARS


class TestMetHeightImageAnalysis(unittest.TestCase):
    def test_expected(self):
        cases = [
            ("../TestImages/PT25_metht_1_001.bmp", 0.076, 0.055),
            ("../TestImages/PT25_metht_1_002.bmp", 0.074, 0.058),
            ("../TestImages/PT25_metht_1_003.bmp", 0.073, 0.060),
            ("../TestImages/PT25_metht_1_004.bmp", 0.071, 0.055),
            ("../TestImages/PT25_metht_1_005.bmp", 0.070, 0.055),
        ]

        for (test_image, small_ht, large_ht) in cases:
            print("Testing methtHeight with image %s.." % test_image)

            (sh, lh) = methtHeight(test_image, pars=MET_HEIGHT_ANALYSIS_PARS)

            ht_limit = 0.01  # millimeter

            self.assertTrue(abs(small_ht - sh) < ht_limit)

            self.assertTrue(abs(large_ht - lh) < ht_limit)


if __name__ == "__main__":
    unittest.main()
