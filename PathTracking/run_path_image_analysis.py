"""

Either blend all the images contained in a path tracking folder to make
one combined image.

Or analysis all the images contained in a path tracking folder, calculate
the fibre positions and write them to a track file.

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
from vfr.evaluation.eval_path_tracking import path_targets_to_fibre
from vfr.conf import PATH_TRACK_ANALYSIS_PARS

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

#TEST_FOLDER = "../images1_15_long"
#OUTPUT = "blended1_15_long.bmp"
#BLEND_IMAGES = False
#LOCATE_TARGETS = True
#PLOT_PATH = True

# Plotting library used for diagnostics.


if __name__ == "__main__":
    args = parser.parse_args()
    logger = logging.getLogger("")
    if args.debug:
        logger.setLevel( logging.DEBUG )
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
        results = analyze_images_in_folder( args.imagefolder, pars=PATH_TRACK_ANALYSIS_PARS, debugging=False )

        # Estimate the location of the fibre from the targets.
        fibre_paths = path_targets_to_fibre( results, pars=PATH_TRACK_ANALYSIS_PARS )

        # Write the results to an output file
        filename = "%s_path.txt" % args.imagefolder
        file = open( filename, "w" )
        try:
            for fibre in fibre_paths:
                file.write( "%d, %.4f, %.4f\n" % (fibre[0], fibre[1], fibre[2]) )
        finally:
            file.close()
        print("Path written to", filename )

        if PLOT_PATH:
            xpath = []
            ypath = []
#            for result in results:
#                xpath.append( result[4])
#                ypath.append( result[5])
#            title = "%s: Path followed by large target" % args.imagefolder
            for fibre in fibre_paths:
                xpath.append( fibre[1])
                ypath.append( fibre[2])
            title = "%s: Path followed by fibre" % args.imagefolder
            plotting.plot_xy( xpath, ypath, title=title, xlabel='xpath (mm)', ylabel='ypath (mm)',
                              linefmt='b.', linestyle=' ', equal_aspect=True )

    print("Tests finished")
