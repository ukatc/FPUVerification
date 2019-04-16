from __future__ import print_function, division, absolute_import

from ImageAnalysisFuncs.base import ImageAnalysisError
import camera_calibration


class CorrectionError(ImageAnalysisError):
    pass


def correct(x, y, calibration_pars=None):
    if (calibration_pars == None) or (calibration_pars["algorithm"] == "identity"):
        return x, y
    elif calibration_pars["algorithm"] == "scale":
        return (
            x * calibration_pars["scale_factor"],
            y * calibration_pars["scale_factor"],
        )
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
        config =  camera_calibration.Config.from_dict(calibration_pars["config"])
        x_corr, y_corr = camera_calibration.correct_point( (x, y), config, level)
        print("Distortion correction: (%7.2f, %7.2f) --> (%6.3f, %6.3f)" % (x, y, x_corr, y_corr))
        return x_corr, y_corr

    raise CorrectionError("unknown algorithm")
