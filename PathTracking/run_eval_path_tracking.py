"""

Compare the track derived from a path tracking measurement (run_path_tracking and evalu

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

                        
from vfr.evaluation.eval_path_tracking import read_track, evaluate_path_tracking, \
                                              find_end_index, match_tracks, find_max_deviation
from vfr.conf import PATH_TRACK_ANALYSIS_PARS

parser = argparse.ArgumentParser()
parser.add_argument("vfrig_file", type=str,
                    help="Name of file containing track derived from verification rig images")
parser.add_argument("mocpath_file", type=str,
                    help="Name of file containing track predicted by path planning simulator")

parser.add_argument("--vfrig_end", type=int, default=-1,
                    help="Index of end of track in verification rig path (default last element).")
parser.add_argument("--mocpath_end", type=int, default=-1,
                    help="Index of end of track in path planning simulator (default last element).")

parser.add_argument("-t", "--test", action="store_true",
                    help="Test run to evaluate end index")
parser.add_argument("-d", "--debug", action="store_true",
                    help="Run with debugging log level")
parser.add_argument("-v", "--verbose", action="store_true",
                    help="Run with extreme verbose output and additional graphics")
parser.add_argument("-p", "--plot", action="store_true",
                    help="Plot the results")


# Plotting library used for diagnostics.


if __name__ == "__main__":
    args = parser.parse_args()
    logger = logging.getLogger("")
    if args.debug:
        logger.setLevel( logging.DEBUG )
        
    graphics = args.plot
    if graphics:
        try:
            import moc_plotting as plotting
        except ImportError:
            graphics = False

    name = os.path.basename( args.vfrig_file )
    if args.test:
        print("Analysing track file %s to determine end index" % args.vfrig_file)
        track2 = read_track( args.vfrig_file )
        find_end_index( track2, end2=args.vfrig_end, graphics=graphics,
                        name=name)
        
    else:
        print("Comparing track files %s and %s." % (args.vfrig_file, args.mocpath_file))
        track1 = read_track( args.mocpath_file )
        track2 = read_track( args.vfrig_file )
    
        new1, new2 = match_tracks( track1, track2, end1=args.mocpath_end,
                                   end2=args.vfrig_end, graphics=graphics,
                                   verbose=args.verbose, name=name )
    
        (maxdist, element) = find_max_deviation( new1, new2, verbose=args.verbose )
        print("Maximum deviation between tracks is %f mm at element %d." % (maxdist,element))

    print("Analysis finished")
