"""

Test blending all the images contained in a path tracking folder to make a combined image.

"""
from __future__ import absolute_import, division, print_function

import logging
logging.basicConfig(level=logging.INFO)   # Informational output
#logging.basicConfig(level=logging.DEBUG)  # Debugging output


import os
from os.path import abspath
import argparse
from argparse import Namespace
import numpy as np

from ImageAnalysisFuncs.analyze_path_tracking import blend_images_in_folder, \
                                                     analyze_images_in_folder

        
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

parser = argparse.ArgumentParser()
parser.add_argument("imagefolder", type=str,
                    help="Name of folder containing path tracking images")

parser.add_argument("--blend", action="store_true", default=False,
                    help="Bland images in folder together")
parser.add_argument("--locate", action="store_true", default=False,
                    help="Track path by locating targets")
parser.add_argument("-d", "--debug", action="store_true",
                    help="Run with debugging log level")
parser.add_argument("-p", "--plot", action="store_true",
                    help="Plot the results")

#TEST_FOLDER = "./images1_15_long"
#OUTPUT = "blended1_15_long.bmp"
#BLEND_IMAGES = False
#LOCATE_TARGETS = True
#PLOT_PATH = True

# Plotting library used for diagnostics.


if __name__ == "__main__":
    args = parser.parse_args()
    logger = logging.getLogger("")
    if args.debug:
        mlogger.setLevel( logging.DEBUG )
    PLOT_PATH = args.plot
    if PLOT_PATH:
        try:
            import moc_plotting as plotting
        except ImportError:
            PLOT_PATH = False

    print("Starting tests")

    # Blend the images together to make one combined image showing the path
    if args.blend:
        output = "%s_blended.bmp" % args.imagefolder
        blend_images_in_folder( args.imagefolder, output )

    # Locate the targets more accurately to analyse the path in more detail.
    if args.locate:
        results = analyze_images_in_folder( args.imagefolder, debugging=False )
        array = np.asarray(results)
        print("results is of size", array.shape)
        for result in results:
            print(result)

        if PLOT_PATH:
            xpath = []
            ypath = []
            for result in results:
                xpath.append( result[3])
                ypath.append( result[4])
            title = "%s: Path followed by large target" % args.imagefolder
            plotting.plot_xy( xpath, ypath, title=title, xlabel='xpath (mm)', ylabel='ypath (mm)',
                              linefmt='b.', linestyle=' ', equal_aspect=True )

    print("Tests finished")
