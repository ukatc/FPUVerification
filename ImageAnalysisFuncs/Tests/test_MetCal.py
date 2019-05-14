from __future__ import absolute_import, division, print_function

import unittest
import numpy.testing as npt

from ImageAnalysisFuncs.analyze_metrology_calibration import (
    MetrologyAnalysisFibreError,
    MetrologyAnalysisTargetError,
    metcalFibreCoordinates,
    metcalTargetCoordinates,
)
from vfr.conf import MET_CAL_TARGET_ANALYSIS_PARS


class TestMetCalImageAnalysis(unittest.TestCase):
    def test_expected(self):
        cases = [
            (
                "../TestImages/PT25_metcal_1_001.bmp",
                15.461,
                10.267,
                0.874,
                13.771,
                8.620,
                0.892,
            ),
            (
                "../TestImages/PT25_metcal_1_002.bmp",
                15.463,
                10.265,
                0.862,
                13.771,
                8.618,
                0.892,
            ),
            (
                "../TestImages/PT25_metcal_1_003.bmp",
                15.463,
                10.265,
                0.862,
                13.771,
                8.618,
                0.892,
            ),
            (
                "../TestImages/PT25_metcal_1_004.bmp",
                14.789,
                10.260,
                0.860,
                13.112,
                8.598,
                0.894,
            ),
            (
                "../TestImages/PT25_metcal_1_005.bmp",
                14.788,
                10.260,
                0.872,
                13.112,
                8.598,
                0.892,
            ),
        ]

        for (test_image, small_x, small_y, small_q, large_x, large_y, large_q) in cases:
            print("Testing metcalTargetCoordinates with image %s.." % test_image)

            (sx, sy, sq, lx, ly, lq) = metcalTargetCoordinates(
                test_image, pars=MET_CAL_TARGET_ANALYSIS_PARS
            )

            pos_limit = 0.01  # millimeter
            q_limit = 0.05  # dimensionless

            npt.assert_almost_equal(sx, small_x, pos_limit)
            npt.assert_almost_equal(sy, small_y, pos_limit)
            npt.assert_almost_equal(sq, small_q, q_limit)

            npt.assert_almost_equal(lx, large_x, pos_limit)
            npt.assert_almost_equal(ly, large_y, pos_limit)
            npt.assert_almost_equal(lq, large_q, q_limit)

    # def test_notFound(self):
    #     cases = ["../TestImages/PT25_metcal_1_002.bmp"]
    # 
    #     with self.assertRaises(MetrologyAnalysisTargetError):
    #         for test_image in cases:
    # 
    #             print("Testing metcalTargetCoordinates with image %s.." % test_image)
    # 
    #             (sx, sy, sq, lx, ly, lq) = metcalTargetCoordinates(
    #                 test_image, pars=MET_CAL_TARGET_ANALYSIS_PARS
    #             )


if __name__ == "__main__":
    unittest.main()
