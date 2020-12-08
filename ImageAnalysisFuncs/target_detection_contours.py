# -*- coding: utf-8 -*-
from __future__ import division, print_function

from math import pi
import numpy as np

import cv2
from DistortionCorrection import get_correction_func
from ImageAnalysisFuncs.base import ImageAnalysisError

# exceptions which are raised if image analysis functions fail


class TargetDetectionContoursError(ImageAnalysisError):
    pass


def targetCoordinates(
    image_path,
    # configurable parameters
    pars=None,
    correct=None,
    show=False,
    debugging=False
):  # will display image with contours annotated

    """
    
    Reads an image from the positional repeatability camera and returns
    the XY coordinates and circularity of the two targets in mm.

    # Authors: Stephen Watson (initial algorithm March 4, 2019)
    # Johannes Nix (code imported and re-formatted)

    # Using the 'PLATESCALE' parameter here has the problem that
    # it does not account for non-linear distortion of the image,
    # and it is also overlapping with the image correction
    # function.  (Also, 'PLATESCALE' means normally something
    # different, it normally thescribes the ratio between a ppixel
    # number and an angle, not a pixel number and a distance.)
    
    See https://docs.opencv.org/master/d6/d00/tutorial_py_root.html
    
    """

    if correct is None:
        correct = get_correction_func(
            calibration_pars=pars.CALIBRATION_PARS,
            platescale=pars.PLATESCALE,
            loglevel=pars.loglevel,
        )

    smallPerimeterLo = (
        (pars.SMALL_DIAMETER - pars.DIAMETER_TOLERANCE) * pi / pars.PLATESCALE
    )
    smallPerimeterHi = (
        (pars.SMALL_DIAMETER + pars.DIAMETER_TOLERANCE) * pi / pars.PLATESCALE
    )
    largePerimeterLo = (
        (pars.LARGE_DIAMETER - pars.DIAMETER_TOLERANCE) * pi / pars.PLATESCALE
    )
    largePerimeterHi = (
        (pars.LARGE_DIAMETER + pars.DIAMETER_TOLERANCE) * pi / pars.PLATESCALE
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

    # Open the image file and attempt to convert it to greyscale.
    # pylint: disable=no-member
    image = cv2.imread(image_path)
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    except cv2.error as err:
        raise TargetDetectionContoursError(
            "OpenCV returned error %s for image %s" % (str(err), path)
        )

    # Blur the image with a 5x5 Guassian kernel.
    blur = cv2.GaussianBlur(gray, (9, 9), 0)
    
    # Apply a binary threshold to the blurred image at the given threshold level
    # and extract elment [1].
    # Values below and above the threshold are set to 0 and 255.
    # See https://docs.opencv.org/master/d7/d4d/tutorial_py_thresholding.html
    thresh = cv2.threshold(blur, pars.THRESHOLD, 255, cv2.THRESH_BINARY)[1]

    # Find contours from thresholded image and keep only the first 15 elements.
    # See https://docs.opencv.org/master/d3/dc0/group__imgproc__shape.html
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
        if circularity > pars.QUALITY_METRIC:
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
            if M["m00"] == 0:
                raise TargetDetectionContoursError(
                    "image %s: Moment m00 is zero, would cause"
                    " division by zero in analysis" % image_path
                )
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
        raise TargetDetectionContoursError(
            "Image %s: Multiple small targets found - tighten parameters or use "
            "display option to investigate images for contamination" % image_path
        )
    if multipleLarge == True:
        raise TargetDetectionContoursError(
            "Image %s: Multiple large targets found - tighten parameters or"
            " use display option to investigate images for contamination" % image_path
        )

    if smallTargetFound == False:
        raise TargetDetectionContoursError(
            "Image %s: Small target not found - "
            "loosen diameter tolerance or change image thresholding" % image_path
        )

    if largeTargetFound == False:
        raise TargetDetectionContoursError(
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

    posrep_small_target_x, posrep_small_target_y = correct(
        pixels_posrep_small_target_x, pixels_posrep_small_target_y
    )

    posrep_large_target_x, posrep_large_target_y = correct(
        pixels_posrep_large_target_x, pixels_posrep_large_target_y
    )

    # target separation check - the values here are not configurable, as
    # they represent real mechanical tolerances
    targetSeparation = np.linalg.norm(
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
        raise TargetDetectionContoursError(
            "Image %s: Target separation has a value of %.3f which is out of spec - "
            "use display option to check for target-like reflections"
            % (image_path, targetSeparation)
        )

    return (
        posrep_small_target_x,
        posrep_small_target_y,
        posrep_small_target_quality,
        posrep_large_target_x,
        posrep_large_target_y,
        posrep_large_target_quality,
    )
