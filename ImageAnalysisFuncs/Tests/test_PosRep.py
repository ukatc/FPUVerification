from __future__ import absolute_import, division, print_function

import unittest
import numpy.testing as npt

from ImageAnalysisFuncs.analyze_positional_repeatability import posrepCoordinates
from vfr.conf import POS_REP_ANALYSIS_PARS


class TestPosRepImageAnalysis(unittest.TestCase):
    def test_expected(self):
        cases = [
            (
                "../TestImages/PT25_posrep_1_001.bmp",
                45.833,
                30.703,
                0.892,
                44.083,
                29.115,
                0.904,
            ),
            (
                "../TestImages/PT25_posrep_1_002.bmp",
                45.830,
                30.699,
                0.886,
                44.081,
                29.111,
                0.899,
            ),
            (
                "../TestImages/PT25_posrep_1_003.bmp",
                45.831,
                30.700,
                0.895,
                44.080,
                29.111,
                0.898,
            ),
            (
                "../TestImages/PT25_posrep_1_004.bmp",
                45.156,
                30.715,
                0.894,
                43.419,
                29.113,
                0.898,
            ),
            (
                "../TestImages/PT25_posrep_1_005.bmp",
                45.152,
                30.717,
                0.888,
                43.418,
                29.112,
                0.903,
            ),
            (
                "../TestImages/PT24_posrep_selftest.bmp",
                45.152,
                30.717,
                0.888,
                43.418,
                29.112,
                0.903,
            ),
        ]

        for (test_image, small_x, small_y, small_q, large_x, large_y, large_q) in cases:
            print("Testing posrepCoordinates with image %s.." % test_image)

            (sx, sy, sq, lx, ly, lq) = posrepCoordinates(
                test_image, pars=POS_REP_ANALYSIS_PARS
            )

            pos_limit = 2.15  # roughly equal to the old 0.01  # millimeter
            q_limit = 1.475  # roughtly equal to the old 0.05  # dimensionless

            npt.assert_almost_equal(sx, small_x, pos_limit)
            npt.assert_almost_equal(sy, small_y, pos_limit)
            npt.assert_almost_equal(sq, small_q, q_limit)

            npt.assert_almost_equal(lx, large_x, pos_limit)
            npt.assert_almost_equal(ly, large_y, pos_limit)
            npt.assert_almost_equal(lq, large_q, q_limit)


if __name__ == "__main__":
    unittest.main()
