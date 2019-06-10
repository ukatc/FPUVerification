from __future__ import print_function

import numpy as np
import cv2
import math
import os
from itertools import chain

from DistortionCorrection import get_correction_func
from ImageAnalysisFuncs.base import ImageAnalysisError


class OtsuTargetFindingError(ImageAnalysisError):
    pass


def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def find_bright_sharp_circles(
    path, minradius, maxradius, grouprange=None, quality=0.4, show=False, tolerence=7.0
):
    """
    Finds circular dots in the given image within the radius range, displaying them on console and graphically if show is set to True

    Works by detecting white circular blobs in the raw image, and in an otsu thresholded copy.
    Circles that have similar center locations and radii in both images are kept.

    Setting grouprange to a number will mean only circles within that distance of other circles are returned,
    however if only 1 is found, it will be returned and grouprange will have no effect.
    :return: a list of opencv blobs for each detected dot.
    """
    image = cv2.imread(path)
    try:
        greyscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    except cv2.error as err:
        raise OtsuTargetFindingError(
            "OpenCV returned error %s for image %s" % (str(err), path)
        )
    blur = cv2.GaussianBlur(greyscale, (5, 5), 0)
    retval, thresholded = cv2.threshold(
        blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    output = image.copy()

    params = cv2.SimpleBlobDetector_Params()
    params.minArea = math.pi * minradius ** 2
    params.maxArea = math.pi * maxradius ** 2
    params.blobColor = 255  # white
    params.filterByColor = True
    params.minCircularity = (
        quality
    )  # smooth sided (0 is very pointy) 0.4 was used by Alex
    params.filterByCircularity = True
    params.minInertiaRatio = 0.9  # non stretched
    params.filterByInertia = True
    params.minConvexity = 0.9  # convex
    params.filterByConvexity = True

    detector = cv2.SimpleBlobDetector_create(params)

    # blob detect on the original
    blobs = detector.detect(image)

    # blob detect on the thresholded copy
    binary_blobs = detector.detect(thresholded)

    # keep blobs found in both with similar sizes
    if show:
        print(path)
        print("round blobs in original:")
        print([(blob.pt[0], blob.pt[1], blob.size / 2.0) for blob in blobs])
        print("round blobs after otsu thresholding:")
        print([(blob.pt[0], blob.pt[1], blob.size / 2.0) for blob in binary_blobs])

    circles = []
    target_blob_list = []
    for blob in blobs:
        for binary_blob in binary_blobs:
            # They match if center's and radii are similar
            if (
                distance(blob.pt, binary_blob.pt)
                + abs(blob.size / 2.0 - binary_blob.size / 2.0)
                < tolerence
            ):
                circles.append((blob.pt[0], blob.pt[1], blob.size / 2.0))
                target_blob_list.append(blob)
                if show:
                    print(
                        distance(blob.pt, binary_blob.pt)
                        + abs(blob.size / 2.0 - binary_blob.size / 2.0)
                    )
                break

    if (grouprange is not None) or len(target_blob_list) >= 2:
        accepted = []
        for i in range(len(target_blob_list)):
            for j in range(i + 1, len(target_blob_list)):
                if show:
                    print(distance(target_blob_list[i].pt, target_blob_list[j].pt))
                if (
                    distance(target_blob_list[i].pt, target_blob_list[j].pt)
                    < grouprange
                ):
                    accepted.append(target_blob_list[i])
                    accepted.append(target_blob_list[j])
                    break
        target_blob_list = accepted

    if show:
        width, height = image.shape[1] // 4, image.shape[0] // 4
        shrunk_original = cv2.resize(image, (width, height))
        # ensure at least some circles were found
        if target_blob_list is not None:
            # convert the (x, y) coordinates and radius of the circles to integers
            print("matching points:")
            print(
                [(blob.pt[0], blob.pt[1], blob.size / 2.0) for blob in target_blob_list]
            )
            # loop over the (x, y) coordinates and radius of the circles
            for circle in target_blob_list:
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
            cv2.cvtColor(thresholded, cv2.COLOR_GRAY2BGR), (width, height)
        )
        cv2.imshow(path, np.hstack([shrunk_original, shrunk_output, shrunk_thresh]))
        cv2.moveWindow(path, 0, 0)
        print()

    return target_blob_list


def targetCoordinates(image_path, pars=None, correct=None):
    """Wrapper for find_bright_sharp_circles

    :param image_path:
    :param pars:
    :return: A tuple length 6 containing the x,y coordinate and quality factor for the small and large targets
    (small_x, small_y, small_qual, big_x, big_y, big_qual)
    """

    if correct is None:
        correct = get_correction_func(
            calibration_pars=pars.CALIBRATION_PARS,
            platescale=pars.PLATESCALE,
            loglevel=pars.loglevel,
        )

    blobs = find_bright_sharp_circles(
        image_path,
        pars.MIN_RADIUS,
        pars.MAX_RADIUS,
        grouprange=pars.GROUP_RANGE,
        quality=pars.QUALITY_METRIC,
        tolerence=pars.TOLERENCE,
    )
    if len(blobs) != 2:
        raise OtsuTargetFindingError(
            "{} blobs found in image {}, there should be exactly two blobs".format(
                len(blobs), image_path
            )
        )

    # check blobs are in the correct order
    if blobs[0].size < blobs[1].size:
        small_blob, large_blob = blobs
    else:
        large_blob, small_blob = blobs

    small_blob_x, small_blob_y = correct(small_blob.pt[0], small_blob.pt[1])
    large_blob_x, large_blob_y = correct(large_blob.pt[0], large_blob.pt[1])

    # out of date
    # small_quality = 4 * math.pi * small_blob.area / (small_blob.length * small_blob.length)

    # large_quality = 4 * math.pi * large_blob.area / (large_blob.length * large_blob.length)

    # return (small_blob.centroid.x, small_blob.centroid.y, small_quality,
    #        large_blob.centroid.x, large_blob.centroid.y, large_quality)
    return (
        small_blob_x,
        small_blob_y,
        pars.QUALITY_METRIC,
        large_blob_x,
        large_blob_y,
        pars.QUALITY_METRIC,
    )


if __name__ == "__main__":
    path, maxr, minr = "metrology_dots/PT25_metcal_1_00{}.bmp", 200, 45
    paths = [path.format(i) for i in range(1, 6)]
    for path in paths:
        if os.path.isfile(path):
            find_bright_sharp_circles(path, minr, maxr, 525, show=True)
            cv2.waitKey()
            cv2.destroyWindow(path)

    path, maxr, minr = "metrology_dots/PT25_posrep_1_00{}.bmp", 55, 15
    paths = [path.format(i) for i in range(1, 6)]
    for path in paths:
        if os.path.isfile(path):
            find_bright_sharp_circles(path, minr, maxr, 200, show=True)
            cv2.waitKey()
            cv2.destroyWindow(path)

    path, maxr, minr = "metrology_dots/PT24_posrep_selftest.bmp", 55, 15
    if os.path.isfile(path):
        find_bright_sharp_circles(path, minr, maxr, 200, show=True)
        cv2.waitKey()
        cv2.destroyWindow(path)

    locations = ("image_dump", "image_dump2")

    posreps = 0
    empty = 0
    metcal = 0
    height = 0
    pupil = 0
    other = []
    for root, directories, files in chain.from_iterable(
        os.walk(location) for location in locations
    ):
        for file in files:
            path = os.path.join(root, file)
            if os.stat(path).st_size == 0:
                empty += 1
            elif "posrep" in path or "positional" in path:
                posreps += 1
            elif "metcal" in path or "datumed" in path or "met-cal-target" in path:
                metcal += 1
            elif "metrology-height" in path:
                height += 1
            elif "pupil" in path:
                pupil += 1
            else:
                other.append(path)

    print(other, len(other), posreps, metcal, empty, height, pupil)

    opened = 0
    checked = 0
    for root, directories, files in chain.from_iterable(
        os.walk(location) for location in locations
    ):
        for file in files:
            path = os.path.join(root, file)
            if ("posrep" in path or "positional" in path) and os.stat(path).st_size > 0:
                blobs = find_bright_sharp_circles(
                    path, 15, 55, grouprange=200, show=True
                )
                cv2.waitKey()
                cv2.destroyWindow(path)
                if len(blobs) != 2:
                    print(path, blobs)
                    opened += 1
                checked += 1
    print(checked, opened)

    opened = 0
    checked = 0
    for root, directories, files in chain.from_iterable(
        os.walk(location) for location in locations
    ):
        for file in files:
            path = os.path.join(root, file)
            if (
                "metcal" in path or "datumed" in path or "met-cal-target" in path
            ) and os.stat(path).st_size > 0:
                blobs = find_bright_sharp_circles(
                    path, 45, 200, grouprange=525, show=True
                )
                cv2.waitKey()
                cv2.destroyWindow(path)
                if len(blobs) != 2:
                    print(path, blobs)
                    opened += 1
                checked += 1
    print(checked, opened)
