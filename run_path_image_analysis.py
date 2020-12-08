"""

Test blending all the images contained in a path tracking folder to make a combined image.

"""
from __future__ import absolute_import, division, print_function

import logging
#logging.basicConfig(level=logging.INFO)   # Informational output
logging.basicConfig(level=logging.DEBUG)  # Debugging output


import os
from os.path import abspath
import argparse
from argparse import Namespace

from ImageAnalysisFuncs.analyze_path_tracking import blend_images_in_folder, \
                                                     analyze_images_in_folder

TEST_FOLDER = "./images_1_15_large"
OUTPUT = "saved_1_15_large.bmp"

from vfr.conf import POS_REP_CALIBRATION_PARS, POS_REP_PLATESCALE, \
    SMALL_TARGET_RADIUS, LARGE_TARGET_RADIUS, \
    TARGET_SEPERATION, THRESHOLD_LIMIT
PATH_TRACK_TARGET_DETECTION_OTSU_PARS = Namespace(
    CALIBRATION_PARS=POS_REP_CALIBRATION_PARS,
    PLATESCALE=POS_REP_PLATESCALE,  # millimeter per pixel
    SMALL_RADIUS=SMALL_TARGET_RADIUS,  # in mm
    LARGE_RADIUS=LARGE_TARGET_RADIUS,  # in mm
    GROUP_RANGE=TARGET_SEPERATION,  # in mm
    THRESHOLD_LIMIT=THRESHOLD_LIMIT,
    QUALITY_METRIC=0.4,  # dimensionless
    BLOB_SIZE_TOLERANCE=0.2, # dimensionless
    GROUP_RANGE_TOLERANCE=0.1, # dimensionless
    MAX_FAILURE_QUOTIENT=0.2,
    display=False,
    verbosity=0,
    loglevel=0,
)

if __name__ == "__main__":
        
    print("Starting tests")

    #blend_images_in_folder( TEST_FOLDER, OUTPUT )

    results = analyze_images_in_folder( TEST_FOLDER, show=False, debugging=False )
    for result in results:
        print(results)

    print("Tests finished")
