from __future__ import absolute_import, division, print_function

import unittest
import numpy.testing as npt

from ImageAnalysisFuncs.analyze_positional_repeatability import posrepCoordinates
from vfr.conf import POS_REP_ANALYSIS_PARS

VERBOSE_TESTS = True
DEBUGGING = False

class TestPosRepImageAnalysis(unittest.TestCase):
    def test_expected(self):
        cases = [
            (
                "../TestImages/PT13d_positional-repeatability_2019-05-14T11-42-32.168BST_i001-j000-k001.bmp",
                62.59,
                41.74,
                0.4,
                64.65,
                42.74,
                0.4,
            ),
            (
                "../TestImages/PT26e_positional-repeatability_2019-05-14T15-03-15.999BST_i000-j000-k016.bmp",
                28.58,
                30.00,
                0.4,
                26.25,
                29.78,
                0.4,
            ),
            (
                "../TestImages/PT19e_positional-repeatability_2019-05-14T15-03-15.999BST_i001-j001-k024.bmp",
                60.79,
                44.80,
                0.4,
                62.60,
                46.18,
                0.4,
            ),
            (
                "../TestImages/PT13e_positional-repeatability_2019-05-14T15-03-15.999BST_i001-j000-k001.bmp",
                62.53,
                41.75,
                0.4,
                64.59,
                42.74,
                0.4,
            ),
            (
                "../TestImages/PT25_posrep_1_001.bmp",
                45.63,
                30.557,
                0.4,
                43.88,
                28.98,
                0.4,
            ),
            (
                "../TestImages/PT25_posrep_1_002.bmp",
                45.62,
                30.55,
                0.4,
                43.88,
                28.97,
                0.4,
            ),
#            (
#                "../TestImages/PT25_posrep_1_003.bmp",
#                45.62,
#                30.55,
#                0.4,
#                43.88,
#                28.97,
#                0.4,
#            ),
#            (
#                "../TestImages/PT25_posrep_1_004.bmp",
#                44.95,
#                30.56,
#                0.4,
#                43.22,
#                28.97,
#                0.4,
#            ),
            (
                "../TestImages/PT25_posrep_1_005.bmp",
                44.95,
                30.57,
                0.4,
                43.22,
                28.97,
                0.4,
            ),
            (
                "../TestImages/PT24_posrep_selftest.bmp",
                41.12,
                30.51,
                0.4,
                39.46,
                28.85,
                0.4,
            ),
#            (
#                "NoSuchImage.bmp",
#                0.0,
#                0.0,
#                0.4,
#                0.0,
#                0.0,
#                0.4,
#            ),
        ]

        for (test_image, small_x, small_y, small_q, large_x, large_y, large_q) in cases:
            print("Testing posrepCoordinates with image %s.." % test_image)

            (sx, sy, sq, lx, ly, lq) = posrepCoordinates(
                test_image, pars=POS_REP_ANALYSIS_PARS, debugging=DEBUGGING
            )

            pos_limit = 2.15  # roughly equal to the old 0.01  # millimeter
            q_limit = 1.475  # roughtly equal to the old 0.05  # dimensionless

            if VERBOSE_TESTS:
                print("Small: Expecting (%.4f,%.4f). Measured (%.4f,%.4f)." % \
                    (small_x, small_y, sx, sy) )
                print("Large: Expecting (%.4f,%.4f). Measured (%.4f,%.4f)." % \
                    (large_x, large_y, lx, ly) )

            if not DEBUGGING:
                npt.assert_almost_equal(
                    sx, small_x, pos_limit, "small x failed", VERBOSE_TESTS
                )
                npt.assert_almost_equal(
                    sy, small_y, pos_limit, "small y failed", VERBOSE_TESTS
                )
                npt.assert_almost_equal(
                    sq, small_q, q_limit, "small qual failed", VERBOSE_TESTS
                )

                npt.assert_almost_equal(
                    lx, large_x, pos_limit, "large x failed", VERBOSE_TESTS
                )
                npt.assert_almost_equal(
                    ly, large_y, pos_limit, "large y failed", VERBOSE_TESTS
                )
                npt.assert_almost_equal(
                    lq, large_q, q_limit, "large q failed", VERBOSE_TESTS
                )


if __name__ == "__main__":
    unittest.main()
