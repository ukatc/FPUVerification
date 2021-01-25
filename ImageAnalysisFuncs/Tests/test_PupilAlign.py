from __future__ import absolute_import, division, print_function

import unittest
import numpy.testing as npt

from ImageAnalysisFuncs.analyze_pupil_alignment import pupilCoordinates
from vfr.conf import PUP_ALGN_ANALYSIS_PARS

VERBOSE_TESTS = True
DEBUGGING = False

class TestPupilAlignImageAnalysis(unittest.TestCase):
    def test_expected(self):

        cases = [
#            (
#                "../TestImages/PT24_pupil-alignment_2019-04-08_+010.000_-080.000.bmp",
#                380.15,
#                308.08,
#                0.6,
#            ),
            (
                "../TestImages/pupil-alignment_2019-10-03T00.00.00.00.bmp",
                641.36,
                345.42,
                0.6,
            ),
            (
                "../TestImages/pupil-alignment_2020-10-19T11.18.45.96.bmp",
                760.17,
                340.24,
                0.6,
            ),
#            (
#                "NoSuchImage.bmp",
#                0.0,
#                0.0,
#                0.6,
#            ),
        ]

        for (test_image, pupil_x, pupil_y, pupil_q) in cases:
            print("Testing pupilCoordinates with image %s.." % test_image)

            (px, py, pq) = pupilCoordinates(
                test_image, pars=PUP_ALGN_ANALYSIS_PARS, debugging=DEBUGGING
            )

            pos_limit = 2.15  # roughly equal to the old 0.01  # millimeter
            q_limit = 1.475  # roughly equal to the old 0.05  # dimensionless

            if VERBOSE_TESTS:
                print("Pupil blob: Expecting (%.4f,%.4f). Measured (%.4f,%.4f)." % \
                    (pupil_x, pupil_y, px, py) )

            if not DEBUGGING:
                npt.assert_almost_equal(
                    px, pupil_x, pos_limit, "pupil x failed", VERBOSE_TESTS
                )
                npt.assert_almost_equal(
                    py, pupil_y, pos_limit, "pupil y failed", VERBOSE_TESTS
                )
                npt.assert_almost_equal(
                    pq, pupil_q, q_limit, "pupil q failed", VERBOSE_TESTS
                )


if __name__ == "__main__":
    unittest.main()
