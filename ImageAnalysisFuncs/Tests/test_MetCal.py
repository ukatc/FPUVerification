from __future__ import absolute_import, division, print_function

import unittest
import numpy.testing as npt

from ImageAnalysisFuncs.analyze_metrology_calibration import (
    MetrologyAnalysisFibreError,
    MetrologyAnalysisTargetError,
    metcalFibreCoordinates,
    metcalTargetCoordinates,
)
from vfr.conf import MET_CAL_TARGET_ANALYSIS_PARS, MET_CAL_FIBRE_ANALYSIS_PARS

VERBOSE_TESTS = True
DEBUGGING = False

class TestMetCalImageAnalysis(unittest.TestCase):
    def test_expected(self):
        target_cases = [
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
        fibre_cases = [
            (
                "../TestImages/PT24_metcal_fibre_2019-04-09.bmp",
                0.072,
                0.041,
                0.8,
            ),
        ]

        pos_limit = 0.01  # millimeter
        q_limit = 0.05  # dimensionless

        for (test_image, small_x, small_y, small_q, large_x, large_y, large_q) in target_cases:
            print("Testing metcalTargetCoordinates with image %s.." % test_image)

            (sx, sy, sq, lx, ly, lq) = metcalTargetCoordinates(
                test_image, pars=MET_CAL_TARGET_ANALYSIS_PARS, debugging=DEBUGGING
            )

            if VERBOSE_TESTS:
                print("Small: Expecting (%.4f,%.4f). Measured (%.4f,%.4f)." % \
                    (small_x, small_y, sx, sy) )
                print("Large: Expecting (%.4f,%.4f). Measured (%.4f,%.4f)." % \
                    (large_x, large_y, lx, ly) )

            npt.assert_almost_equal(sx, small_x, pos_limit)
            npt.assert_almost_equal(sy, small_y, pos_limit)
            npt.assert_almost_equal(sq, small_q, q_limit)

            npt.assert_almost_equal(lx, large_x, pos_limit)
            npt.assert_almost_equal(ly, large_y, pos_limit)
            npt.assert_almost_equal(lq, large_q, q_limit)

        pos_limit = 0.005  # millimeter
        q_limit = 0.05  # dimensionless

        for (test_image, fibre_x, fibre_y, fibre_q) in fibre_cases:
            print("Testing metcalFibreCoordinates with image %s.." % test_image)
            
            (fx, fy, fq) = metcalFibreCoordinates(
                test_image, pars=MET_CAL_FIBRE_ANALYSIS_PARS, debugging=DEBUGGING
            )
            if VERBOSE_TESTS:
                print("Fibre: Expecting (%.4f,%.4f). Measured (%.4f,%.4f)." % \
                    (fibre_x, fibre_y, fx, fy) )
            
            npt.assert_almost_equal(fx, fibre_x, pos_limit)
            npt.assert_almost_equal(fy, fibre_y, pos_limit)
            npt.assert_almost_equal(fq, fibre_q, q_limit)

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
