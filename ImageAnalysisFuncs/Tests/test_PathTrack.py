from __future__ import absolute_import, division, print_function

import unittest
import numpy.testing as npt

from ImageAnalysisFuncs.analyze_positional_repeatability import posrepCoordinates
from vfr.conf import POS_REP_ANALYSIS_PARS

#from ImageAnalysisFuncs.analyze_pupil_alignment import pupilCoordinates
#from vfr.conf import PUP_ALGN_ANALYSIS_PARS
#PUP_ALGN_ANALYSIS_PARS.MIN_RADIUS = 0.5
#PUP_ALGN_ANALYSIS_PARS.MAX_RADIUS = 10.0

VERBOSE_TESTS = True
DEBUGGING = True

class TestPosRepImageAnalysis(unittest.TestCase):
    def test_expected(self):
        cases = [
            (
                "../TestImages/path-tracking-test1.bmp",
                45.62,
                30.55,
                0.4,
                43.88,
                28.97,
                0.4,
            ),
            (
                "../TestImages/path-tracking-test256.bmp",
                45.62,
                30.55,
                0.4,
                43.88,
                28.97,
                0.4,
            ),
        ]

        for (test_image, small_x, small_y, small_q, large_x, large_y, large_q) in cases:
            print("Testing path tracking with image %s.." % test_image)

            (sx, sy, sq, lx, ly, lq) = posrepCoordinates(
                test_image, pars=POS_REP_ANALYSIS_PARS, debugging=DEBUGGING
            )
            print("Returned:", sx, sy, sq, lx, ly, lq)

#            (px, py, pq) = pupilCoordinates(
#                test_image, pars=PUP_ALGN_ANALYSIS_PARS, debugging=DEBUGGING
#            )
#            print("Returned:", px, py, pq)

            pos_limit = 2.15  # roughly equal to the old 0.01  # millimeter
            q_limit = 1.475  # roughly equal to the old 0.05  # dimensionless

#            npt.assert_almost_equal(
#                sx, small_x, pos_limit, "small x failed", VERBOSE_TESTS
#            )
#            npt.assert_almost_equal(
#                sy, small_y, pos_limit, "small y failed", VERBOSE_TESTS
#            )
#            npt.assert_almost_equal(
#                sq, small_q, q_limit, "small qual failed", VERBOSE_TESTS
#            )
#
#            npt.assert_almost_equal(
#                lx, large_x, pos_limit, "large x failed", VERBOSE_TESTS
#            )
#            npt.assert_almost_equal(
#                ly, large_y, pos_limit, "large y failed", VERBOSE_TESTS
#            )
#            npt.assert_almost_equal(
#                lq, large_q, q_limit, "large q failed", VERBOSE_TESTS
#            )


if __name__ == "__main__":
    unittest.main()
