from __future__ import print_function, division, absolute_import

from ImageAnalysisFuncs.base import ImageAnalysisError
import camera_calibration


class CorrectionError(ImageAnalysisError):
    pass


def correct(x, y, calibration_pars=None):
    if (calibration_pars == None) or (calibration_pars["algorithm"] == "identity"):
        return x, y
    elif calibration_pars["algorithm"] == "scale":
        platescale = calibration_pars["scale_factor"]
        #print("Distortion correction: (%7.2f, %7.2f) --> (%6.3f, %6.3f), platescale = %f" % (
        #    x, y, x * platescale, y * platescale, platescale
        #))

        return (
            x * platescale,
            y * platescale,
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
        x_0, y_0 = camera_calibration.correct_point( (0.0, 0.0), config, level)
        x_corr, y_corr = camera_calibration.correct_point( (x, y), config, level)
        x_scale = (x_corr - x_0) / float(x)
        y_scale = (y_corr - y_0) / float(y)
        print("Distortion correction: (%7.2f, %7.2f) --> (%6.3f, %6.3f), platescale = %f/%f" % (
            x, y, x_corr, y_corr, x_scale, y_scale
        ))
        return x_corr, y_corr

    raise CorrectionError("unknown algorithm")
