from __future__ import print_function

import math

import numpy as np
import cv2

from DistortionCorrection import get_correction_func
from ImageAnalysisFuncs.base import ImageAnalysisError
from Crypto.SelfTest.Hash.test_SHA256 import LargeSHA256Test


class OtsuFibreFindingError(ImageAnalysisError):
    pass


def find_largest_bright_circle(path,
                        min_radius,
                        max_radius,
                        threshold=60,
                        quality=0.4,
                        show=False,
                        debugging=False):
    """
    
    Finds circular dots in the given image within the radius range, displaying
    them on console and graphically if show is set to True

    Works by detecting white circular blobs in the raw image, and in 
    thresholded copy.Circles that have similar center locations and radii in
    both images are kept.
    
    The show and debugging options are for local testing, show = True will print
    more diagnostics and debugging = True will save a file with found blobs on
    the image 
    
    See https://docs.opencv.org/master/d6/d00/tutorial_py_root.html

    :return: a list of opencv blobs for each detected dot.
    
    """
    # Open the image file and attempt to convert it to greyscale.
    image = cv2.imread(path)
    try:
        greyscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    except cv2.error as err:
        raise OtsuFibreFindingError(
            "OpenCV returned error %s for image %s" % (str(err), path)
        )
        
    # Blur the image with a 5x5 Guassian kernel.
    # See https://docs.opencv.org/master/d4/d13/tutorial_py_filtering.html
    blur = cv2.GaussianBlur(
                greyscale,   # Input image
                (5, 5),      # Size of kernel
                0            # Sigma for Gaussian (derived from kernel size if zero)
           )
    
    # Apply a binary threshold to the blurred image at the given threshold level.
    # Values below and above the threshold are set to 0 and 255.
    # NOTE: The threshold is fixed. OTSU thresholding is not actually needed.
    # See https://docs.opencv.org/master/d7/d4d/tutorial_py_thresholding.html
    _, thresholded = cv2.threshold(
                        blur,               # Input image
                        threshold,          # Threshold level
                        255,                # Maximum value
                        cv2.THRESH_BINARY   # Thresholding mode (was cv.THRESH_BINARY+cv.THRESH_OTSU)
                     )
    output = image.copy() # FIXME: Only used in debugging mode?

    # Create opencv blob detector to locate blobs matching the expected
    # size range and shape of the illuminated fibre.
    # See https://docs.opencv.org/master/d0/d7a/classcv_1_1SimpleBlobDetector.html

    large_params = cv2.SimpleBlobDetector_Params()
    large_params.minArea = math.pi * min_radius * min_radius
    large_params.maxArea = math.pi * max_radius * max_radius
    large_params.blobColor = 255  # white
    large_params.filterByColor = True
    large_params.minCircularity = (quality)  # smooth sided (0 is very pointy) 0.4 was used by Alex
    large_params.filterByCircularity = True
    large_params.minInertiaRatio = 0.7  # non stretched
    large_params.filterByInertia = True
    large_params.minConvexity = 0.7  # convex
    large_params.filterByConvexity = True

    large_detector = cv2.SimpleBlobDetector_create(large_params)

    # Detect the blobs in the thresholded image
    large_blobs = large_detector.detect(thresholded)

    # If required, display the sizes of all the blobs
    if show:
        print(path)
        print("All large round blobs (x, y, radius):")
        print([(blob.pt[0], blob.pt[1], blob.size / 2.0) for blob in large_blobs])

    # If more than one blob has been found, keep the largest.
    largest_blob = None
    largest_size = 0.0
    for large in large_blobs:
        if large.size > largest_size:
            largest_blob = large
            largest_size = large.size
    if largest_blob is not None:
        fibre_blob_list = [largest_blob]
    else:
        fibre_blob_list = []

    if show:
        print("Largest blob (x, y, radius):")
        print([(blob.pt[0], blob.pt[1], blob.size / 2.0) for blob in fibre_blob_list])

    # In debugging mode, save a diagnostic image.
    if debugging:
        # Resize the image.
        # See https://docs.opencv.org/master/da/d6e/tutorial_py_geometric_transformations.html
        width, height = image.shape[1] // 4, image.shape[0] // 4
        shrunk_original = cv2.resize(image, (width, height))
        # Ensure at least some circles were found
        if fibre_blob_list is not None:
            # convert the (x, y) coordinates and radius of the circles to integers
            print("matching points:")
            print(
                [(blob.pt[0], blob.pt[1], blob.size / 2.0) for blob in fibre_blob_list]
            )
            # loop over the (x, y) coordinates and radius of the circles
            for circle in large_blobs:
                x, y = circle.pt
                x = int(x)
                y = int(y)
                r = int(circle.size / 2)
                # draw the circle in the output image, then draw a rectangle
                # corresponding to the center of the circle
                cv2.circle(output, (x, y), r, (0, 255, 0), 4)
                cv2.rectangle(output, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)

        # show the output image
        shrunk_output = cv2.resize(output, (width, height))
        shrunk_thresh = cv2.resize(
                            cv2.cvtColor(thresholded, cv2.COLOR_GRAY2BGR),
                            (width, height)
                        )
        outpath = path.replace('.bmp', 'thresnew.bmp')
        cv2.imwrite(outpath, np.hstack([shrunk_original, shrunk_output, shrunk_thresh]))
        # FIXME: These two lines lead to a core dump!
        #cv2.imshow(path, np.hstack([shrunk_original, shrunk_output, shrunk_thresh]))
        #cv2.moveWindow(path, 0, 0)
        print("Labelled image written to \'%s\'\n" % outpath)

    return fibre_blob_list


def fibreCoordinates(image_path, pars=None, correct=None, debugging=None):
    """
    
    Wrapper for find_largest_bright_circle

    :param image_path:
    :param pars:
    
    :return: A tuple length 6 containing the x,y coordinate in mm and a minimun
    guaranteed quality factor for the small and large targets
    (small_x, small_y, small_qual, big_x, big_y, big_qual)
    
    """

   # Find correct conversion from px to mm
    if correct is None:
        correct = get_correction_func(
                    calibration_pars=pars.CALIBRATION_PARS,
                    platescale=pars.PLATESCALE,
                    loglevel=pars.loglevel,
                  )

    # Depending on the camera calibration this step is approximate, as the
    # position is unknown.
    min_radius_px = pars.MIN_RADIUS / pars.PLATESCALE
    max_radius_px = pars.MAX_RADIUS / pars.PLATESCALE
    
    blobs = find_largest_bright_circle(
                image_path,
                min_radius_px,
                max_radius_px,
                threshold=pars.THRESHOLD_LIMIT,
                quality=pars.QUALITY_METRIC,
                show=debugging,
                debugging=debugging
            )
    if len(blobs) != 1:
        raise OtsuFibreFindingError(
            "{} blobs found in image {}, there should be exactly one blob".format(
                len(blobs), image_path
            )
        )
    large_blob = blobs[0]

    # convert results from pixels to mm
    large_blob_x, large_blob_y = correct(large_blob.pt[0], large_blob.pt[1])


    # The returned quality is a fixed value, the new blob detector doesn't
    # return the quality of each blob, but a minimum can be set so results
    # are guaranteed to have a equal or higher quality to the returned value
    return (
        large_blob_x,
        large_blob_y,
        pars.QUALITY_METRIC,
    )
