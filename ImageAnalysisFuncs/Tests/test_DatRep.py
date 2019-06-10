from __future__ import absolute_import, division, print_function

import unittest
import numpy.testing as npt

from ImageAnalysisFuncs.analyze_positional_repeatability import posrepCoordinates
from vfr.conf import DATUM_REP_ANALYSIS_PARS

VERBOSE_TESTS = True


class TestDatRepImageAnalysis(unittest.TestCase):
    def test_expected(self):

        cases = [
            (
                "../TestImages/PT11e_datum-repeatability_2019-05-14T14-44-06.239BST_datumed-003.bmp",
                15.12,
                10.77,
                0.4,
                13.36,
                9.06,
                0.4,
            ),
            (
                "../TestImages/PT13e_datum-repeatability_2019-05-14T14-44-06.239BST_moved+datumed-006.bmp",
                16.19,
                10.33,
                0.4,
                14.56,
                8.52,
                0.4,
            ),
            (
                "../TestImages/PT19e_datum-repeatability_2019-05-14T14-44-06.239BST_datumed-002.bmp",
                15.44,
                11.01,
                0.4,
                13.62,
                9.41,
                0.4,
            ),
            (
                "../TestImages/PT25e_datum-repeatability_2019-05-14T14-44-06.239BST_moved+datumed-005.bmp",
                14.67,
                10.78,
                0.4,
                12.88,
                9.12,
                0.4,
            ),
            (
                "../TestImages/PT26e_datum-repeatability_2019-05-14T14-44-06.239BST_datumed-001.bmp",
                15.47,
                10.84,
                0.4,
                13.71,
                9.11,
                0.4,
            ),
        ]

        for (test_image, small_x, small_y, small_q, large_x, large_y, large_q) in cases:
            print("Testing posrepCoordinates with image %s.." % test_image)

            (sx, sy, sq, lx, ly, lq) = posrepCoordinates(
                test_image, pars=DATUM_REP_ANALYSIS_PARS
            )

            pos_limit = 2.15  # roughly equal to the old 0.01  # millimeter
            q_limit = 1.475  # roughtly equal to the old 0.05  # dimensionless

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
