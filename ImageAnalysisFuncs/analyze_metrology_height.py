from __future__ import division, print_function

import cv2
from ImageAnalysisFuncs.base import ImageAnalysisError
from matplotlib import pyplot as plt
from numpy import float32, std, sqrt  # pylint: disable=no-name-in-module
from numpy.polynomial import Polynomial

# version number for analysis algorithm
# (each different result for the same data
# should yield a version number increase)

METROLOGY_HEIGHT_ANALYSIS_ALGORITHM_VERSION = (1,0,0)


# exceptions which are raised if image analysis functions fail


class MetrologyHeightAnalysisError(ImageAnalysisError):
    pass


def methtHeight(
    image_path, pars=None  # configurable parameters
):  # will thresholded image

    """reads an image from the metrology height camera and
        returns the heights and quality metric of the two targets in mm"""

    # Authors: Stephen Watson (initial algorithm March 4, 2019)
    # Johannes Nix (code imported and re-formatted)

    # image processing
    # pylint: disable=no-member
    image = cv2.imread(image_path)
    blur = cv2.GaussianBlur(image, (pars.METHT_GAUSS_BLUR, pars.METHT_GAUSS_BLUR), 0)
    gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
    gray = float32(gray)

    tval, thresh = cv2.threshold(gray, pars.METHT_THRESHOLD, 255, 0, cv2.THRESH_BINARY)

    # find location of beta arm
    betaScan = thresh[pars.METHT_SCAN_HEIGHT, :]
    betaSide = 0
    for i in range(0, len(betaScan) - 1):
        if (betaScan[i + 1] - betaScan[i]) < 0:
            betaSide = i
            if pars.verbosity > 5:
                print(
                    "Image %s: Beta arm side is at x-coordinate %i"
                    % (image_path, betaSide)
                )

    if betaSide == 0:
        raise MetrologyHeightAnalysisError(
            "Image %s: Beta arm side not found - consider changing scan height"
            % image_path
        )

    threshcrop = thresh[1750:2700, betaSide - 100 : betaSide + 1500]
    if pars.display == True:
        plt.imshow(threshcrop)
        plt.title("Thresholded image, thresholdVal = %i" % pars.METHT_THRESHOLD)
        plt.show()

    # estimation of noise in thresholded image
    threshblur = cv2.GaussianBlur(threshcrop, (3, 3), 0)
    threshave, threshstd = cv2.meanStdDev(threshcrop)
    threshblurave, threshblurstd = cv2.meanStdDev(threshblur)
    noiseMetric = (threshstd - threshblurstd) / threshblurstd * 100

    if pars.verbosity > 5:
        print(
            "Image %s: Noise metric in thresholded image is %.2f"
            % (image_path, noiseMetric)
        )

    # pixel distances from side of beta arm to measurement points
    # these parameters could be made configurable but shouldn't need to be changed
    armSurfaceX = [60, 320, 760, 980, 1220]
    smallTargetX = [100, 180, 260]
    largeTargetX = [380, 530, 680]

    # fills lists with pixel values at X coordinates defined above
    armSurfacePix, smallTargetPix, largeTargetPix = [], [], []
    for i in range(0, 5):
        armSurfacePix.append(thresh[:, betaSide + armSurfaceX[i]])
    for i in range(0, 3):
        smallTargetPix.append(thresh[:, betaSide + smallTargetX[i]])
        largeTargetPix.append(thresh[:, betaSide + largeTargetX[i]])

    # looks for pixel transitions indicating surfaces
    armSurfaceY, smallTargetY, largeTargetY = [None] * 5, [None] * 3, [None] * 3
    for i in range(0, 5):
        for p in range(0, len(thresh) - 1):
            if abs(armSurfacePix[i][p + 1] - armSurfacePix[i][p]) > 0:
                armSurfaceY[i] = p
                break
    for i in range(0, 3):
        for p in range(0, len(thresh) - 1):
            if abs(smallTargetPix[i][p + 1] - smallTargetPix[i][p]) > 0:
                smallTargetY[i] = p
                break
    for i in range(0, 3):
        for p in range(0, len(thresh) - 1):
            if abs(largeTargetPix[i][p + 1] - largeTargetPix[i][p]) > 0:
                largeTargetY[i] = p
                break

    if pars.verbosity > 5:
        print("Image %s:" % image_path)
        print("Arm surface points found - x:%s y:%s" % (armSurfaceX, armSurfaceY))
        print("Small target points found - x:%s y:%s" % (smallTargetX, smallTargetY))
        print("Large target points found - x:%s y:%s" % (largeTargetX, largeTargetY))

    # best fit straight line through 5 beta arm surface points
    try:
        armSurfaceDom = Polynomial.fit(armSurfaceX, armSurfaceY, 1, domain=(-1, 1))
        armSurface = armSurfaceDom.convert().coef
    except TypeError as err:
        raise MetrologyHeightAnalysisError(
            "Image %s: Polynomial fit failed with TypeError exception (message %s)"
            % (image_path, str(err))
        )

    # calculates normal distance from points on targets to beta arm surface
    # D = |a*x_n + b*y_n + c|/sqrt(a^2 + b^2) where line is defined as ax + by + c = 0
    a = armSurface[1]
    b = -1
    c = armSurface[0]
    smallTargetHeights, largeTargetHeights = [None] * 3, [None] * 3
    for i in range(0, 3):
        smallTargetHeights[i] = (a * smallTargetX[i] + b * smallTargetY[i] + c) / sqrt(
            a ** 2 + b ** 2
        )
        largeTargetHeights[i] = (a * largeTargetX[i] + b * largeTargetY[i] + c) / sqrt(
            a ** 2 + b ** 2
        )

    # calculates standard deviation of heights to see how level the targets are
    stdSmallTarget = std(smallTargetHeights) * pars.METHT_PLATESCALE
    stdLargeTarget = std(largeTargetHeights) * pars.METHT_PLATESCALE
    if pars.verbosity > 5:
        print(
            "Image %s: Standard deviations of small/large target heights are %.3f and %.3f"
            % (image_path, stdSmallTarget, stdLargeTarget)
        )

    # exceptions
    if stdSmallTarget > pars.METHT_STANDARD_DEV:
        raise MetrologyHeightAnalysisError(
            "Image %s: Small target points have high standard deviation"
            " - target may not be sitting flat" % image_path
        )

    if stdLargeTarget > pars.METHT_STANDARD_DEV:
        raise MetrologyHeightAnalysisError(
            "Image %s: Large target points have high standard deviation"
            " - target may not be sitting flat" % image_path
        )

    #if noiseMetric > pars.METHT_NOISE_METRIC:
    #    raise MetrologyHeightAnalysisError(
    #        "Image %s: Image noise excessive - consider "
    #        "changing Gaussian blur value" % image_path
    #    )

    metht_small_target_height = (
        sum(smallTargetHeights) / len(smallTargetHeights) * pars.METHT_PLATESCALE
    )
    metht_large_target_height = (
        sum(largeTargetHeights) / len(largeTargetHeights) * pars.METHT_PLATESCALE
    )

    return metht_small_target_height, metht_large_target_height
