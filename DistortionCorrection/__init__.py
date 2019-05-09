from __future__ import print_function, division, absolute_import

import logging
from functools import partial

from ImageAnalysisFuncs.base import ImageAnalysisError
import camera_calibration
from numpy import array
import logging

class CorrectionError(ImageAnalysisError):
    pass


def correct(x, y, calibration_pars=None, loglevel=5):
    log = partial(logging.getLogger(__name__).log, loglevel)

    if (calibration_pars == None) or (calibration_pars["algorithm"] == "identity"):
        return x, y
    elif calibration_pars["algorithm"] == "scale":
        platescale = calibration_pars["scale_factor"]
        # log("Distortion correction: (%7.2f, %7.2f) --> (%6.3f, %6.3f), platescale = %f" % (
        #    x, y, x * platescale, y * platescale, platescale
        # ))

        return (x * platescale, y * platescale)

    elif calibration_pars["algorithm"] == "al/201904/multistage":
        # Use Alexander Lay's multi-stage distortion correction.
        #
        # Note: It isn't ideal to generate the config again and again
        # for each single point. We do that here so that we reduce
        # merge conflicts with Alan O'Brien's parallel work on image
        # analysis. After merging, we can simply transform to
        # equivalent code which passes a reference to the correciton
        # function.
        level = camera_calibration.Correction.lens_keystone_and_real_coordinates
        config = camera_calibration.Config.from_dict(calibration_pars["config"])
        x_0, y_0 = camera_calibration.correct_point((0.0, 0.0), config, level)
        x_corr, y_corr = camera_calibration.correct_point((x, y), config, level)
        x_scale = (x_corr - x_0) / float(x)
        y_scale = (y_corr - y_0) / float(y)
        log(
            "Distortion correction: (%7.2f, %7.2f) --> (%6.3f, %6.3f), platescale = %f/%f"
            % (x, y, x_corr, y_corr, x_scale, y_scale)
        )
        return x_corr, y_corr


    elif calibration_pars["algorithm"] == "al/20190429/chessboard":
        # using single-stage correction with chessboard,
        # for pupil alignment correction
        level = camera_calibration.Correction.lens_keystone_and_real_coordinates

        config = camera_calibration.Config.from_dict(calibration_pars["config"])
        points0 = array([0.0, 0.0], dtype=float)
        x_0, y_0 = camera_calibration.correct_point(points0, config, level)
        points = array([x, y], dtype=float)
        x_corr, y_corr = camera_calibration.correct_point(points, config, level)
        x_scale = (x_corr - x_0) / float(x)
        y_scale = (y_corr - y_0) / float(y)
        log(
            "Distortion correction: (%7.2f, %7.2f) --> (%6.3f, %6.3f), platescale = %f/%f"
            % (x, y, x_corr, y_corr, x_scale, y_scale)
        )
        return x_corr, y_corr

    raise CorrectionError("unknown algorithm")
