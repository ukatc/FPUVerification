from __future__ import print_function

import math

import numpy as np
import cv2
import warnings

from DistortionCorrection import get_correction_func
from ImageAnalysisFuncs.base import ImageAnalysisError


class OtsuTargetFindingError(ImageAnalysisError):
    pass


def distance(p1, p2):
    """Helper function to find the distance between two points"""
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def find_bright_sharp_circles_triplet(path,
                                      small_radius,
                                      large_radius,
                                      fieldstop_radius,
                                      group_range=None,
                                      fieldstop_range=None,
                                      threshold=60,
                                      quality=0.4,
                                      blob_size_tolerance=0.2,
                                      group_range_tolerance=0.2,
                                      fieldstop_range_tolerance=0.5,
                                      show=False,
                                      debugging=False):
    """
    
    Finds circular dots in the given image within the radius range, displaying
    them on console and graphically if show is set to True

    Works by detecting white circular blobs in the raw image, and in 
    thresholded copy.Circles that have similar center locations and radii in
    both images are kept.

    Setting group_range to a number will mean only circles within that distance
    of other circles are returned, however if only 1 is found, it will be
    returned and group_range will have no effect.
    
    The show and debugging options are for local testing, show = True will print
    more diagnostics and debugging = True will save a file with found blobs on
    the image 
    
    See https://docs.opencv.org/master/d6/d00/tutorial_py_root.html

    :return: a list of opencv blobs for each detected dot.

    NOTE: THIS ALGORITHM DOES NOT CURRENTLY WORK. THE DOUGHNUT-SHAPED FIELDSTOP
    IS NOT DETECTABLE.
    
    """
    # Open the image file and attempt to convert it to greyscale.
    image = cv2.imread(path)
    try:
        greyscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    except cv2.error as err:
        raise OtsuTargetFindingError(
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

    # Create two opencv blob detectors to locate blobs matching the expected
    # size and shape of the small and large metrology targets.
    # See https://docs.opencv.org/master/d0/d7a/classcv_1_1SimpleBlobDetector.html
    small_params = cv2.SimpleBlobDetector_Params()
    small_params.minArea = math.pi * (small_radius*(1-blob_size_tolerance)) ** 2
    small_params.maxArea = math.pi * (small_radius*(1+blob_size_tolerance)) ** 2
    small_params.blobColor = 255  # white
    small_params.filterByColor = True
    small_params.minCircularity = (quality)  # smooth sided (0 is very pointy) 0.4 was used by Alex
    small_params.filterByCircularity = True
    small_params.minInertiaRatio = 0.7  # non stretched
    small_params.filterByInertia = True
    small_params.minConvexity = 0.7  # convex
    small_params.filterByConvexity = True

    large_params = cv2.SimpleBlobDetector_Params()
    large_params.minArea = math.pi * (large_radius*(1-blob_size_tolerance)) ** 2
    large_params.maxArea = math.pi * (large_radius*(1+blob_size_tolerance)) ** 2
    large_params.blobColor = 255  # white
    large_params.filterByColor = True
    large_params.minCircularity = (quality)  # smooth sided (0 is very pointy) 0.4 was used by Alex
    large_params.filterByCircularity = True
    large_params.minInertiaRatio = 0.7  # non stretched
    large_params.filterByInertia = True
    large_params.minConvexity = 0.7  # convex
    large_params.filterByConvexity = True

    # Fieldstop is doughnut-shaped, so the area is going to be less than expected
    # from the radius
    fieldstop_donut_ratio = 0.8
    fieldstop_size_tolerance = 1.2 * blob_size_tolerance
    fieldstop_quality = 2.0 * quality
    fieldstop_params = cv2.SimpleBlobDetector_Params()
    fieldstop_params.minArea = fieldstop_donut_ratio * math.pi * (fieldstop_radius*(1-fieldstop_size_tolerance)) ** 2
    fieldstop_params.maxArea = math.pi * (fieldstop_radius*(1+fieldstop_size_tolerance)) ** 2
    fieldstop_params.blobColor = 255  # white
    fieldstop_params.filterByColor = True
    fieldstop_params.minCircularity = (fieldstop_quality)  # smooth sided (0 is very pointy) 0.4 was used by Alex
    fieldstop_params.filterByCircularity = True
    fieldstop_params.minInertiaRatio = 0.7  # non stretched
    fieldstop_params.filterByInertia = True
    fieldstop_params.minConvexity = 0.7  # convex
    fieldstop_params.filterByConvexity = False # There is a hole in the middle

    small_detector = cv2.SimpleBlobDetector_create(small_params)
    large_detector = cv2.SimpleBlobDetector_create(large_params)
    fieldstop_detector = cv2.SimpleBlobDetector_create(fieldstop_params)

    # Detect the small and large blobs in the thresholded image
    small_blobs = small_detector.detect(thresholded)
    large_blobs = large_detector.detect(thresholded)
    fieldstop_blobs = fieldstop_detector.detect(thresholded)

    # If required, display all the blobs found.
    if show:
        print(path)
        print("%d small round blobs (x, y, radius):" % len(small_blobs))
        print([(blob.pt[0], blob.pt[1], blob.size / 2.0) for blob in small_blobs])
        print("%d large round blobs (x, y, radius):" % len(large_blobs))
        print([(blob.pt[0], blob.pt[1], blob.size / 2.0) for blob in large_blobs])
        print("%d fieldstop-sized round blobs (x, y, radius):" % len(fieldstop_blobs))
        print([(blob.pt[0], blob.pt[1], blob.size / 2.0) for blob in fieldstop_blobs])
    # Filter the list to keep only large and small blobs separated
    # by the expected distance.
    target_blob_list = []
    if group_range is not None:
        accepted = []
        for small in small_blobs:
            for large in large_blobs:
                dist = distance(small.pt, large.pt)
                low = group_range*(1-group_range_tolerance)
                high = group_range*(1+group_range_tolerance)
                if show:
                    print("small/large distance=%f c.f. range %f to %f" % (dist, low, high))
                if (dist > low and dist < high):
                    accepted.append(small)
                    accepted.append(large)
                    break # Break after first successful find
        target_blob_list = accepted
    if fieldstop_range is not None:
        accepted = []
        for large in large_blobs:
            for fieldstop in fieldstop_blobs:
                dist = distance(large.pt, fieldstop.pt)
                low = fieldstop_range*(1-fieldstop_range_tolerance)
                high = fieldstop_range*(1+fieldstop_range_tolerance)
                if show:
                    print("large/fieldstop distance=%f c.f. range %f to %f" % (dist, low, high))
                if (dist > low and dist < high):
                    if large not in target_blob_list:
                        accepted.append(large)
                    accepted.append(fieldstop)
                    break # Break after first successful find
        target_blob_list = target_blob_list + accepted

    if show:
        print("Blobs at expected distance (x, y, radius)")
        print([(blob.pt[0], blob.pt[1], blob.size / 2.0) for blob in target_blob_list])

    # In debugging mode, save a diagnostic image.
    if debugging:
        # Resize the image.
        # See https://docs.opencv.org/master/da/d6e/tutorial_py_geometric_transformations.html
        width, height = image.shape[1] // 4, image.shape[0] // 4
        shrunk_original = cv2.resize(image, (width, height))
        # Ensure at least some circles were found
        if target_blob_list is not None:
            # convert the (x, y) coordinates and radius of the circles to integers
            print("matching points:")
            print(
                [(blob.pt[0], blob.pt[1], blob.size / 2.0) for blob in target_blob_list]
            )
            # loop over the (x, y) coordinates and radius of the circles
            for circle in fieldstop_blobs:
                x, y = circle.pt
                x = int(x)
                y = int(y)
                r = int(circle.size / 2)
                # draw the circle in the output image, then draw a rectangle
                # corresponding to the center of the circle
                cv2.circle(output, (x, y), r, (0, 0, 255), 4)
                cv2.rectangle(output, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)
            for circle in large_blobs:
                x, y = circle.pt
                x = int(x)
                y = int(y)
                r = int(circle.size / 2)
                # draw the circle in the output image, then draw a rectangle
                # corresponding to the center of the circle
                cv2.circle(output, (x, y), r, (0, 255, 0), 4)
                cv2.rectangle(output, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)
            for circle in small_blobs:
                x, y = circle.pt
                x = int(x)
                y = int(y)
                r = int(circle.size / 2)
                # draw the circle in the output image, then draw a rectangle
                # corresponding to the center of the circle
                cv2.circle(output, (x, y), r, (255, 0, 0), 4)
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

    return target_blob_list


def fieldstopCoordinates(image_path, pars=None, correct=None, debugging=False):
    """
    
    Wrapper for find_bright_sharp_circles

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
    small_radius_px = pars.SMALL_RADIUS / pars.PLATESCALE
    large_radius_px = pars.LARGE_RADIUS / pars.PLATESCALE
    fieldstop_radius_px = pars.FIELDSTOP_RADIUS / pars.PLATESCALE
    group_range_px = pars.GROUP_RANGE / pars.PLATESCALE
    fieldstop_range_px = pars.FIELDSTOP_RANGE / pars.PLATESCALE

    blobs = find_bright_sharp_circles_triplet(
                image_path,
                small_radius_px,
                large_radius_px,
                fieldstop_radius_px,
                group_range=group_range_px,
                fieldstop_range=fieldstop_range_px,
                threshold=pars.THRESHOLD_LIMIT,
                quality=pars.QUALITY_METRIC,
                blob_size_tolerance=pars.BLOB_SIZE_TOLERANCE,
                group_range_tolerance=pars.GROUP_RANGE_TOLERANCE,
                fieldstop_range_tolerance=pars.FIELDSTOP_RANGE_TOLERANCE,
                show=debugging,
                debugging=debugging
            )
    if len(blobs) < 2 or len(blobs) > 3:
        raise OtsuTargetFindingError(
            "{} blobs found in image {}, there should be two or three blobs".format(
                len(blobs), image_path
            )
        )

    if len(blobs) == 3:
        # Assume small, large and fieldstop blobs found.
        # Sort the blobs into the correct order
        minii = None
        maxii = None
        minsize = 99999.0
        maxsize = 0.0
        taken = [False, False, False]
        for ii in range(0,3):
            if blobs[ii].size < minsize:
                minii = ii
                minsize = blobs[ii].size
            if blobs[ii].size > maxsize:
                maxii = ii
                maxsize = blobs[ii].size
        small_blob = blobs[minii]
        fieldstop_blob = blobs[maxii]
        taken[minii] = True
        taken[maxii] = True
        for ii in range(0,3):
            if not taken[ii]:
                large_blob = blobs[ii]
                break
    else:
        warnings.warn("%s: Only 2 blobs detected. Assuming field stop is missing." % image_path)
        # Assume only small and large targets found.
        # check blobs are in the correct order
        if blobs[0].size < blobs[1].size:
            small_blob, large_blob = blobs
        else:
            large_blob, small_blob = blobs
        fieldstop_blob = None

    # convert results from pixels to mm
    small_blob_x, small_blob_y = correct(small_blob.pt[0], small_blob.pt[1])
    large_blob_x, large_blob_y = correct(large_blob.pt[0], large_blob.pt[1])
    if len(blobs) == 3:
        fieldstop_blob_x, fieldstop_blob_y = correct(fieldstop_blob.pt[0], fieldstop_blob.pt[1])
    else:
        fieldstop_blob_x = None
        fieldstop_blob_y = None


    # The returned quality is a fixed value, the new blob detector doesn't
    # return the quality of each blob, but a minimum can be set so results
    # are guaranteed to have a equal or higher quality to the returned value
    return (
        small_blob_x,
        small_blob_y,
        pars.QUALITY_METRIC,
        large_blob_x,
        large_blob_y,
        pars.QUALITY_METRIC,
        fieldstop_blob_x,
        fieldstop_blob_y,
        pars.QUALITY_METRIC,    )