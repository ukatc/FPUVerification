from __future__ import print_function, division, absolute_import

import logging
from functools import partial

from ImageAnalysisFuncs.base import ImageAnalysisError
import camera_calibration
from numpy import array
import logging

class CorrectionError(ImageAnalysisError):
    pass


def get_correction_func(calibration_pars=None, platescale=1.0, loglevel=0):
    """This returns a closure which applies the selected distortion
    correction or scaling to pairs of coordinates.

    Computing this closure outside of loops has the goal to make
    the correction faster.
    """
    # get default scaling function
    if calibration_pars is None:
        calibration_pars = {
            "algorithm": "scale",
            "scale_factor": platescale,
        }

    log = partial(logging.getLogger(__name__).log, loglevel)

    if calibration_pars["algorithm"] == "identity":
        def f(x,y):
            return x, y
        return f

    elif calibration_pars["algorithm"] == "scale":
        platescale = calibration_pars["scale_factor"]

        def f(x, y):
            if loglevel > 0:
                log("Distortion correction: (%7.2f, %7.2f) --> (%6.3f, %6.3f), platescale = %f" % (
                    x, y, x * platescale, y * platescale, platescale
                ))

            return (x * platescale, y * platescale)

        return f


    elif calibration_pars["algorithm"] == "al/201904/multistage":
        # Use Alexander Lay's multi-stage distortion correction.
        level = camera_calibration.Correction.lens_keystone_and_real_coordinates
        config = camera_calibration.Config.from_dict(calibration_pars["config"])
        x_0, y_0 = camera_calibration.correct_point((0.0, 0.0), config, level)

        def f(x, y):
            x_corr, y_corr = camera_calibration.correct_point(array([x, y],dtype=float), config, level)
            if loglevel > 0:
                try:
                    x_scale = (x_corr - x_0) / float(x)
                    y_scale = (y_corr - y_0) / float(y)
                except ZeroDivisionError:
                    x_scale = float("NaN")
                    y_scale = float("NaN")
                log(
                    "Distortion correction: (%7.2f, %7.2f) --> (%6.3f, %6.3f), platescale = %f/%f"
                    % (x, y, x_corr, y_corr, x_scale, y_scale)
                )
            return x_corr, y_corr

        return f


    elif calibration_pars["algorithm"] == "al/20190429/chessboard":
        # using single-stage correction with chessboard,
        # for pupil alignment correction
        level = camera_calibration.Correction.lens_keystone_and_real_coordinates
        config = camera_calibration.Config.from_dict(calibration_pars["config"])
        points0 = array([0.0, 0.0], dtype=float)
        x_0, y_0 = camera_calibration.correct_point(points0, config, level)

        def f(x, y):

            points = array([x, y], dtype=float)
            x_corr, y_corr = camera_calibration.correct_point(points, config, level)
            if loglevel > 0:
                try:
                    x_scale = (x_corr - x_0) / float(x)
                    y_scale = (y_corr - y_0) / float(y)
                except ZeroDivisionError:
                    x_scale = float("NaN")
                    y_scale = float("NaN")
                log(
                    "Distortion correction: (%7.2f, %7.2f) --> (%6.3f, %6.3f), platescale = %f/%f"
                    % (x, y, x_corr, y_corr, x_scale, y_scale)
                )
            return x_corr, y_corr

        return f

    raise CorrectionError("unknown algorithm")
