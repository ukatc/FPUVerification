from __future__ import print_function, division
import cv2
from math import pi, sqrt
from numpy.polynomial import Polynomial
from matplotlib import pyplot as plt
from numpy import NaN, float32, mean, std
from numpy.linalg import norm


from ImageAnalysisFuncs.base import ImageAnalysisError

# version number for analysis algorithm
# (each different result for the same data
# should yield a version number increase)

METROLOGY_HEIGHT_ANALYSIS_ALGORITHM_VERSION = 0.1


# exceptions which are raised if image analysis functions fail


class MetrologyHeightAnalysisError(ImageAnalysisError):
    pass


def methtHeight(
    image_path,  # configurable parameters
    METHT_PLATESCALE=0.00668,  # mm per pixel
    METHT_THRESHOLD=150,  # 0-255
    METHT_SCAN_HEIGHT=2000,  # pixels
    METHT_GAUSS_BLUR=1,  # pixels - MUST BE AN ODD NUMBER
    METHT_STANDARD_DEV=0.04,  # mm
    METHT_NOISE_METRIC=0.25,  # dimensionless
    verbosity=0,  # a value > 5 will write relevant parameters to the terminal
    display=False,
):  # will thresholded image

    """reads an image from the metrology height camera and 
        returns the heights and quality metric of the two targets in mm"""

    # Authors: Stephen Watson (initial algorithm March 4, 2019)
    # Johannes Nix (code imported and re-formatted)

    # image processing
    image = cv2.imread(image_path)
    blur = cv2.GaussianBlur(image, (METHT_GAUSS_BLUR, METHT_GAUSS_BLUR), 0)
    gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
    gray = float32(gray)

    tval, thresh = cv2.threshold(gray, METHT_THRESHOLD, 255, 0, cv2.THRESH_BINARY)

    # find location of beta arm
    betaScan = thresh[METHT_SCAN_HEIGHT, :]
    betaSide = 0
    for i in range(0, len(betaScan) - 1):
        if (betaScan[i + 1] - betaScan[i]) < 0:
            betaSide = i
            if verbosity > 5:
                print ("Beta arm side is at x-coordinate %i" % betaSide)

    if betaSide == 0:
        raise MetrologyHeightAnalysisError(
            "Beta arm side not found - consider changing scan height"
        )

    threshcrop = thresh[1750:2700, betaSide - 100 : betaSide + 1500]
    if display == True:
        plt.imshow(threshcrop)
        plt.title("Thresholded image, thresholdVal = %i" % thresholdVal)
        plt.show()

    # estimation of noise in thresholded image
    threshblur = cv2.GaussianBlur(threshcrop, (3, 3), 0)
    threshave, threshstd = cv2.meanStdDev(threshcrop)
    threshblurave, threshblurstd = cv2.meanStdDev(threshblur)
    noiseMetric = (threshstd - threshblurstd) / threshblurstd * 100

    if verbosity > 5:
        print ("Noise metric in thresholded image is %.2f" % noiseMetric)

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

    if verbosity > 5:
        print ("Arm surface points found - x:%s y:%s" % (armSurfaceX, armSurfaceY))
        print ("Small target points found - x:%s y:%s" % (smallTargetX, smallTargetY))
        print ("Large target points found - x:%s y:%s" % (largeTargetX, largeTargetY))

    # best fit straight line through 5 beta arm surface points
    armSurfaceDom = Polynomial.fit(armSurfaceX, armSurfaceY, 1, domain=(-1, 1))
    armSurface = armSurfaceDom.convert().coef

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
    stdSmallTarget = std(smallTargetHeights) * METHT_PLATESCALE
    stdLargeTarget = std(largeTargetHeights) * METHT_PLATESCALE
    if verbosity > 5:
        print (
            "Standard deviations of small/large target heights are %.3f and %.3f"
            % (stdSmallTarget, stdLargeTarget)
        )

    # exceptions
    if stdSmallTarget > METHT_STANDARD_DEV:
        raise MetrologyHeightAnalysisError(
            "Small target points have high standard deviation"
            " - target may not be sitting flat"
        )

    if stdLargeTarget > METHT_STANDARD_DEV:
        raise MetrologyHeightAnalysisError(
            "Large target points have high standard deviation"
            " - target may not be sitting flat"
        )

    if noiseMetric > METHT_NOISE_METRIC:
        raise MetrologyHeightAnalysisError(
            "Image noise excessive - consider " "changing Gaussian blur value"
        )

    metht_small_target_height = (
        sum(smallTargetHeights) / len(smallTargetHeights) * METHT_PLATESCALE
    )
    metht_large_target_height = (
        sum(largeTargetHeights) / len(largeTargetHeights) * METHT_PLATESCALE
    )

    return metht_small_target_height, metht_large_target_height


def eval_met_height_inspec(
    metht_small_target_height, metht_large_target_height, METHT_HEIGHT_TOLERANCE=0.01
):
    if (
        (metht_small_target_height > 0)
        and (metht_small_target_height <= MET_HEIGHT_TOLERANCE)
        and (metht_large_target_height > 0)
        and (metht_large_target_height <= MET_HEIGHT_TOLERANCE)
    ):

        return True
    else:
        return False
