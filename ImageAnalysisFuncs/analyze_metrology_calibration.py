# -*- coding: utf-8 -*-
from __future__ import division, print_function

from math import asin, pi, sqrt

import cv2
from ImageAnalysisFuncs.base import ImageAnalysisError
from numpy import array, cross
from numpy.linalg import norm

# version number for analysis algorithm
# (each different result for the same data
# should yield a version number increase)

METROLOGY_ANALYSIS_ALGORITHM_VERSION = 0.1


# exceptions which are raised if image analysis functions fail


class MetrologyAnalysisTargetError(ImageAnalysisError):
    pass


class MetrologyAnalysisFibreError(ImageAnalysisError):
    pass


def metcalTargetCoordinates(image_path, pars=None):

    """reads an image from the metrology calibration camera and returns
        the XY coordinates and circularity of the two targets in mm"""

    # Authors: Stephen Watson (initial algorithm March 4, 2019)
    # Johannes Nix (code imported and re-formatted)

    smallPerimeterLo = (
        (pars.MET_CAL_SMALL_DIAMETER - pars.MET_CAL_DIAMETER_TOLERANCE)
        * pi
        / pars.MET_CAL_PLATESCALE
    )
    smallPerimeterHi = (
        (pars.MET_CAL_SMALL_DIAMETER + pars.MET_CAL_DIAMETER_TOLERANCE)
        * pi
        / pars.MET_CAL_PLATESCALE
    )
    largePerimeterLo = (
        (pars.MET_CAL_LARGE_DIAMETER - pars.MET_CAL_DIAMETER_TOLERANCE)
        * pi
        / pars.MET_CAL_PLATESCALE
    )
    largePerimeterHi = (
        (pars.MET_CAL_LARGE_DIAMETER + pars.MET_CAL_DIAMETER_TOLERANCE)
        * pi
        / pars.MET_CAL_PLATESCALE
    )

    if pars.verbosity > 5:
        print(
            "Image %s:"
            "Lower/upper perimeter limits of small & large targets in mm: %.2f / %.2f ; %.2f / %.2f"
            % (
                image_path,
                smallPerimeterLo,
                smallPerimeterHi,
                largePerimeterLo,
                largePerimeterHi,
            )
        )

    centres = {}

    # pylint: disable=no-member
    image = cv2.imread(image_path)

    # image processing
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (pars.MET_CAL_GAUSS_BLUR, pars.MET_CAL_GAUSS_BLUR), 0)
    thresh = cv2.threshold(blur, pars.MET_CAL_THRESHOLD, 255, cv2.THRESH_BINARY)[1]

    # find contours from thresholded image
    cnts = sorted(
        cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[1],
        key=cv2.contourArea,
        reverse=True,
    )[:15]

    largeTargetFound, smallTargetFound, multipleSmall, multipleLarge = (
        False,
        False,
        False,
        False,
    )

    # filter through contours on size and circularity
    for i, c in enumerate(cnts):
        perimeter = cv2.arcLength(c, True)
        area = cv2.contourArea(c)
        if area > 0 and perimeter > 0:
            circularity = 4 * pi * (area / (perimeter * perimeter))
        if pars.verbosity > 5:
            print(
                "Image %s:"
                "ContourID - %i; perimeter - %.2f; circularity - %.2f"
                % (image_path, i, perimeter, circularity)
            )
        if circularity > pars.MET_CAL_QUALITY_METRIC:
            if perimeter > smallPerimeterLo and perimeter < smallPerimeterHi:
                if smallTargetFound == True:
                    multipleSmall = True
                circle = "Small Target"
                smallTargetFound = True
            elif perimeter > largePerimeterLo and perimeter < largePerimeterHi:
                if largeTargetFound == True:
                    multipleLarge = True
                circle = "Large Target"
                largeTargetFound = True
            else:
                circle = "N" + str(i)

            # finds contour moments, which can be used to derive centre of mass
            M = cv2.moments(c)
            cX = M["m10"] / M["m00"]
            cY = M["m01"] / M["m00"]
            centres[circle] = (cX, cY, circularity, i)

            if pars.display == True:
                cv2.drawContours(image, cnts, -1, (0, 255, 0), 2)
                label = (
                    str(i)
                    + ", "
                    + str(round(perimeter, 1))
                    + ", "
                    + str(round(circularity, 2))
                    + " = "
                    + circle
                )
                cv2.putText(
                    image,
                    label,
                    (int(cX), int(cY)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    2,
                    (255, 255, 255),
                    2,
                    1,
                )
                cv2.imshow("image", cv2.resize(image, (0, 0), fx=0.3, fy=0.3))
                cv2.waitKey(100)
                raw_input("Press enter to continue")

    if multipleSmall == True:
        raise MetrologyAnalysisTargetError(
            "Image %s: Multiple small targets found - tighten"
            " parameters or investigate images for contamination" % image_path
        )

    if multipleLarge == True:
        raise MetrologyAnalysisTargetError(
            "Image %s: Multiple large targets found - tighten "
            "parameters or investigate images for contamination" % image_path
        )

    if smallTargetFound == False:
        raise MetrologyAnalysisTargetError(
            "Image %s: Small target not found - loosen diameter"
            " tolerance or change image thresholding" % image_path
        )

    if largeTargetFound == False:
        raise MetrologyAnalysisTargetError(
            "Image %s: Large target not found - loosen diameter"
            " tolerance or change image thresholding" % image_path
        )

    if pars.verbosity > 5:
        print(
            "Image %s: Contour %i = small target, contour %i = large target"
            % (image_path, centres["Small Target"][3], centres["Large Target"][3])
        )

    metcal_small_target_x = centres["Small Target"][0] * pars.MET_CAL_PLATESCALE
    metcal_small_target_y = centres["Small Target"][1] * pars.MET_CAL_PLATESCALE
    metcal_small_target_quality = centres["Small Target"][2]
    metcal_large_target_x = centres["Large Target"][0] * pars.MET_CAL_PLATESCALE
    metcal_large_target_y = centres["Large Target"][1] * pars.MET_CAL_PLATESCALE
    metcal_large_target_quality = centres["Large Target"][2]

    # target separation check - the values here are not configurable,
    # as they represent real mechanical tolerances
    targetSeparation = sqrt(
        (metcal_small_target_x - metcal_large_target_x) ** 2
        + (metcal_small_target_y - metcal_large_target_y) ** 2
    )

    if pars.verbosity > 5:
        print(
            "Image %s: Target separation is %.3f mm.  Specification is 2.375 +/- 0.1 mm."
            % (image_path, targetSeparation)
        )

    if targetSeparation > 2.475 or targetSeparation < 2.275:
        raise MetrologyAnalysisTargetError(
            "Image %s: Target separation is out of spec - use display option "
            "to check for target-like reflections" % image_path
        )

    return (
        metcal_small_target_x,
        metcal_small_target_y,
        metcal_small_target_quality,
        metcal_large_target_x,
        metcal_large_target_y,
        metcal_large_target_quality,
    )


def metcalFibreCoordinates(image_path, pars=None):  # configurable parameters

    MET_CAL_PLATESCALE = pars.MET_CAL_PLATESCALE
    MET_CAL_QUALITY_METRIC = pars.MET_CAL_QUALITY_METRIC
    verbosity = pars.verbosity
    display = pars.display

    """reads an image from the metrology calibration camera and returns the
        XY coordinates and Gaussian fit quality of the backlit fibre in mm"""

    # Authors: Stephen Watson (initial algorithm March 4, 2019)
    # Johannes Nix (code imported and re-formatted)

    # pylint: disable=no-member
    image = cv2.imread(image_path)

    # image processing
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    metcal_fibre_x = 0
    metcal_fibre_y = 0
    metcal_fibre_quality = 0

    # exceptions: MetrologyAnalysisFibreError()

    return metcal_fibre_x, metcal_fibre_y, metcal_fibre_quality


def fibre_target_distance(big_target_coords, small_target_coords, fibre_coords):
    """
    takes coordinates of the big metrology target, the small metrology target,
    and the distance in millimeter, and returns

    1) the distance between the large  metrology target and the fibre aperture in millimeter.
    2) the distance between the small  metrology target and the fibre aperture in millimeter.
    3) the angle of ∠(large target - fibre - small target), in degrees.
    """

    # Authors: Stephen Watson (initial algorithm March 4, 2019)

    v_big = array(big_target_coords)
    v_small = array(small_target_coords)

    v_f = array(fibre_coords)

    va = v_f - v_big
    metcal_fibre_large_target_distance = norm(va)

    vb = v_f - v_small
    metcal_fibre_small_target_distance = norm(vb)

    metcal_target_vector_angle = asin(cross(va, vb) / (norm(va) * norm(vb))) * (
        180.0 / pi
    )

    return (
        metcal_fibre_large_target_distance,
        metcal_fibre_small_target_distance,
        metcal_target_vector_angle,
    )
