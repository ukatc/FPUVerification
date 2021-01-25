from __future__ import absolute_import, division, print_function

import unittest
import numpy.testing as npt

from ImageAnalysisFuncs.analyze_positional_repeatability import posrepCoordinates
from vfr.conf import DATUM_REP_ANALYSIS_PARS

VERBOSE_TESTS = True
DEBUGGING = False

class TestDatRepImageAnalysis(unittest.TestCase):
    def test_expected(self):

        cases = [
            (
                "../TestImages/PT11e_datum-repeatability_2019-05-14T14-44-06.239BST_datumed-003.bmp",
                14.427,
                10.283,
                0.4,
                12.752,
                8.644,
                0.4,
            ),
            (
                "../TestImages/PT13e_datum-repeatability_2019-05-14T14-44-06.239BST_moved+datumed-006.bmp",
                15.4455,
                9.863,
                0.4,
                13.89,
                8.138,
                0.4,
            ),
            (
                "../TestImages/PT19e_datum-repeatability_2019-05-14T14-44-06.239BST_datumed-002.bmp",
                14.732,
                10.512,
                0.4,
                12.994,
                8.9768,
                0.4,
            ),
            (
                "../TestImages/PT25e_datum-repeatability_2019-05-14T14-44-06.239BST_moved+datumed-005.bmp",
                13.9977,
                10.285,
                0.4,
                12.2935,
                8.7014,
                0.4,
            ),
            (
                "../TestImages/PT26e_datum-repeatability_2019-05-14T14-44-06.239BST_datumed-001.bmp",
                14.771,
                10.337,
                0.4,
                13.086,
                8.699,
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
                test_image, pars=DATUM_REP_ANALYSIS_PARS, debugging=DEBUGGING
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
