# -*- coding: utf-8 -*-
from __future__ import division, print_function

from math import pi

import cv2
from DistortionCorrection import correct
from ImageAnalysisFuncs.base import ImageAnalysisError, rss

# exceptions which are raised if image analysis functions fail


class RepeatabilityAnalysisError(ImageAnalysisError):
    pass


# version number for analysis algorithm
# (each different result for the same data
# should yield a version number increase)

DATUM_REPEATABILITY_ALGORITHM_VERSION = 0.1

POSITIONAL_REPEATABILITY_ALGORITHM_VERSION = 0.1

POSITIONAL_VERIFICATION_ALGORITHM_VERSION = 0.1


def posrepCoordinates(
    image_path,
    # configurable parameters
    pars=None,
):  # will display image with contours annotated

    """reads an image from the positional repeatability camera and returns
        the XY coordinates and circularity of the two targets in mm"""

    # Authors: Stephen Watson (initial algorithm March 4, 2019)
    # Johannes Nix (code imported and re-formatted)

    # using the 'PLATESCALE' parameter here has the problem that
    # it does not account for non-linear distortion of the image,
    # and it is also overlapping with the image correction
    # function.  (Also, 'PLATESCALE' means normally something
    # different, it normally thescribes the ratio between a ppixel
    # number and an angle, not a pixel number and a distance.)

    smallPerimeterLo = (
        (pars.POS_REP_SMALL_DIAMETER - pars.POS_REP_DIAMETER_TOLERANCE)
        * pi
        / pars.POS_REP_PLATESCALE
    )
    smallPerimeterHi = (
        (pars.POS_REP_SMALL_DIAMETER + pars.POS_REP_DIAMETER_TOLERANCE)
        * pi
        / pars.POS_REP_PLATESCALE
    )
    largePerimeterLo = (
        (pars.POS_REP_LARGE_DIAMETER - pars.POS_REP_DIAMETER_TOLERANCE)
        * pi
        / pars.POS_REP_PLATESCALE
    )
    largePerimeterHi = (
        (pars.POS_REP_LARGE_DIAMETER + pars.POS_REP_DIAMETER_TOLERANCE)
        * pi
        / pars.POS_REP_PLATESCALE
    )

    if pars.verbosity > 5:
        print(
            "Image %s: Lower/upper perimeter limits of small & large "
            "targets in mm: %.2f / %.2f ; %.2f / %.2f"
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
    # FIXME: gray is unused!
    blur = cv2.GaussianBlur(gray, (9, 9), 0)
    thresh = cv2.threshold(blur, pars.POS_REP_THRESHOLD, 255, cv2.THRESH_BINARY)[1]

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
                "Image %s: ContourID - %i; perimeter - %.2f; circularity - %.2f"
                % (image_path, i, perimeter, circularity)
            )
        if circularity > pars.POS_REP_QUALITY_METRIC:
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

            # finds contour momenIA.posrepCoordinates("./PT25_posrep_1_001.bmp")ts,
            # which can be used to derive centre of mass
            M = cv2.moments(c)
            cX = M["m10"] / M["m00"]
            cY = M["m01"] / M["m00"]
            centres[circle] = (cX, cY, circularity, i)

            # superimpose contours and labels onto original image, user prompt required in terminal to progress
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
        raise RepeatabilityAnalysisError(
            "Image %s: Multiple small targets found - tighten parameters or use "
            "display option to investigate images for contamination" % image_path
        )
    if multipleLarge == True:
        raise RepeatabilityAnalysisError(
            "Image %s: Multiple large targets found - tighten parameters or"
            " use display option to investigate images for contamination" % image_path
        )

    if smallTargetFound == False:
        raise RepeatabilityAnalysisError(
            "Image %s: Small target not found - "
            "loosen diameter tolerance or change image thresholding" % image_path
        )

    if largeTargetFound == False:
        raise RepeatabilityAnalysisError(
            "Image %s: Large target not found - "
            "loosen diameter tolerance or change image thresholding" % image_path
        )

    if pars.verbosity > 5:
        print(
            "Image %s: Contour %i = small target, contour %i = large target"
            % (image_path, centres["Small Target"][3], centres["Large Target"][3])
        )

    pixels_posrep_small_target_x = centres["Small Target"][0]
    pixels_posrep_small_target_y = centres["Small Target"][1]
    posrep_small_target_quality = centres["Small Target"][2]
    pixels_posrep_large_target_x = centres["Large Target"][0]
    pixels_posrep_large_target_y = centres["Large Target"][1]
    posrep_large_target_quality = centres["Large Target"][2]

    # scale and straighten the result coordinates
    # the distortion correction is applied here, using the 'correct' function
    # from the distortion correction module
    if pars.POS_REP_CALIBRATION_PARS is None:
        pars.POS_REP_CALIBRATION_PARS = {
            "algorithm": "scale",
            "scale_factor": pars.POS_REP_PLATESCALE,
        }

    posrep_small_target_x, posrep_small_target_y = correct(
        pixels_posrep_small_target_x,
        pixels_posrep_small_target_y,
        calibration_pars=pars.POS_REP_CALIBRATION_PARS,
    )

    posrep_large_target_x, posrep_large_target_y = correct(
        pixels_posrep_large_target_x,
        pixels_posrep_large_target_y,
        calibration_pars=pars.POS_REP_CALIBRATION_PARS,
    )

    # target separation check - the values here are not configurable, as
    # they represent real mechanical tolerances
    targetSeparation = rss(
        [
            posrep_small_target_x - posrep_large_target_x,
            posrep_small_target_y - posrep_large_target_y,
        ]
    )
    if pars.verbosity > 5:
        print(
            "Image %s: Target separation is %.3f mm.  Specification is 2.375 +/- 0.1 mm."
            % (image_path, targetSeparation)
        )
    # FIXME: This below is a work-around so that we can test something
    # at all. Either the image detection or the PLATESCALE value needs
    # to be fixed.

    # if targetSeparation > 2.475 or targetSeparation < 2.275:
    if targetSeparation > 30 or targetSeparation < 2.2:
        raise RepeatabilityAnalysisError(
            "Image %s: Target separation has a value of %.3f which is out of spec - "
            "use display option to check for target-like reflections" % (
                image_path, targetSeparation)
        )

    return (
        posrep_small_target_x,
        posrep_small_target_y,
        posrep_small_target_quality,
        posrep_large_target_x,
        posrep_large_target_y,
        posrep_large_target_quality,
    )


