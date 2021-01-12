# -*- coding: utf-8 -*-
#
# Analyses the images written by the path tracking in one folder.
#
from __future__ import division, print_function

import os
import math
import numpy as np
import logging

import cv2
from ImageAnalysisFuncs.base import ImageAnalysisError
from ImageAnalysisFuncs import target_detection_otsu
from ImageAnalysisFuncs.analyze_positional_repeatability import posrepCoordinates

from vfr.conf import PATH_TRACK_ANALYSIS_PARS
from target_detection_otsu import OtsuTargetFindingError


class PathTrackingAnalysisError(ImageAnalysisError):
    pass


def path_tracking_target_coordinates(image_path, pars=PATH_TRACK_ANALYSIS_PARS, debugging=False):
    """
    
    Reads the image and analyse the location and quality of the metrology targets

    :return: A tuple length 6 containing the x,y coordinate and quality factor for the small and large targets
    Where quality is measured by 4 * pi * (area / (perimeter * perimeter)).
    (small_x, small_y, small_qual, big_x, big_y, big_qual)
    
    """

    try:
        positions = target_detection_otsu.targetCoordinates(image_path, pars, debugging=debugging)
    except OtsuTargetFindingError as err:
        raise PathTrackingAnalysisError(
            err.message + " from Image {}".format(image_path)
        )

    return positions

def blend_images_in_folder( folder, newfile ):
    """
    
    Blends all the images found in the given folder and saves them
    to a single, combined image.
    
    """
    logger = logging.getLogger(__name__)
    
    nimages = len(list(os.listdir(folder)))
    logging.info("Blending %d path tracking images." % nimages)
    wcount = 1
    newimg = None

    sorted_list = sorted(list(os.listdir(folder)))
    for filename in sorted_list:

        logger.debug("Reading image %d from %s" % (wcount,filename))
        img = cv2.imread(os.path.join(folder, filename), 1)
        try:
            greyscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        except cv2.error as err:
            raise PathTrackingAnalysisError(
                "OpenCV returned error %s for image %s" % (str(err), filename)
            )

        if newimg is None:
            #Start with the first image
            newimg = img
        else:
            # Blend subsequent images.
            thisweight = 1.0 / float(wcount)
            #thisweight = 1.0 / float(nimages)
            otherweight = 1.0 - thisweight
            newimg = cv2.addWeighted(img, thisweight, newimg, otherweight, 0)
            wcount += 1
            
    cv2.imwrite(newfile, newimg)
    logger.info("%d images blended together and saved to %s" % (wcount, newfile))

def analyze_images_in_folder( folder, pars=PATH_TRACK_ANALYSIS_PARS,
                              debugging=False ):
    """
    
    Analyses all the images found in the given folder and returns a
    list of target positions.
    
    """
    logger = logging.getLogger(__name__)
    path_targets = []
    
    nimages = len(list(os.listdir(folder)))
    logging.info("Analysing %d path tracking images." % nimages)
    wcount = 1
    ngood = 0
    nbad = 0

    sorted_list = sorted(list(os.listdir(folder)))
    for filename in sorted_list:
        logger.debug("Analysing image %d from %s" % (wcount,filename))
        imgpath = os.path.join(folder, filename)
        try:
            #positions = path_tracking_target_coordinates( filename, pars, debugging=debugging )
            positions = posrepCoordinates( imgpath, pars, debugging=debugging )
            path_targets.append( [wcount] + list(positions) )
            ngood += 1
        except ImageAnalysisError as err:
            logger.error( "Image analysis error %s.\n\t Image %s ignored." % (str(err), filename) )
            nbad += 1

        wcount += 1
    logging.info("There were %d good and %d bad image files." % (ngood, nbad) )
    return path_targets


