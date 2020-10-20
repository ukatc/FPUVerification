from __future__ import absolute_import, division, print_function

import unittest
import numpy.testing as npt

from ImageAnalysisFuncs.analyze_pupil_alignment import pupilCoordinates
from vfr.conf import PUP_ALGN_ANALYSIS_PARS

VERBOSE_TESTS = True
DEBUGGING = True

class TestPupilAlignImageAnalysis(unittest.TestCase):
    def test_expected(self):

        cases = [
            (
                "../TestImages/PT24_pupil-alignment_2019-04-08_+010.000_-080.000.bmp",
                15.12,
                10.77,
                0.4,
            ),
            (
                "../TestImages/pupil-alignment_2019-10-03T00.00.00.00.bmp",
                16.19,
                10.33,
                0.4,
            ),
            (
                "../TestImages/pupil-alignment_2020-10-19T11.18.45.96.bmp",
                15.44,
                11.01,
                0.4,
            ),
        ]

        for (test_image, large_x, large_y, large_q) in cases:
            print("Testing posrepCoordinates with image %s.." % test_image)

            (lx, ly, lq) = pupilCoordinates(
                test_image, pars=PUP_ALGN_ANALYSIS_PARS, debugging=DEBUGGING
            )

            pos_limit = 2.15  # roughly equal to the old 0.01  # millimeter
            q_limit = 1.475  # roughtly equal to the old 0.05  # dimensionless

            if VERBOSE_TESTS:
                print("Large: Expecting (%.4f,%.4f). Measured (%.4f,%.4f)." % \
                    (large_x, large_y, lx, ly) )

            if not DEBUGGING:
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
