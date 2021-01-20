# -*- coding: utf-8 -*-
"""

Module to evaluate path tracking: measuring the track taken by
the fibre centre while the FPU is following a path.

"""
from __future__ import division, print_function

import math
from math import pi
import numpy as np
import logging
# logger = logging.getLogger(__name__)
# #logger.setLevel(level=logging.INFO)   # Informational output
# logger.setLevel(level=logging.DEBUG)  # Debugging output

#from scipy import optimize
#from scipy import stats

try:
    from mocpath.path.path_generator import read_path_file
    MOCPATH_OK = True
except ImportError:
    MOCPATH_OK = False

#from vfr.evaluation.measures import get_errors, get_grouped_errors, group_by_subkeys
from vfr.conf import PATH_TRACK_ANALYSIS_PARS

# Plotting library used for diagnostics.
try:
    import moc_plotting as plotting
except ImportError:
    logging.error("Can't import mocpath. Graphics disabled.")
    plotting = None


ALPHA_LENGTH = 8.0
BETA_LENGTH = 17.0
DEG2RAD = pi / 180.0
RAD2DEG = 180.0 / pi
TWOPI = 2.0 * pi
PIBY2 = pi / 2.0

def path_targets_to_fibre( path_targets, pars=PATH_TRACK_ANALYSIS_PARS):
    """
    
    Take a list of path targets of the form
    (xsmall, ysmall, qsmall, xlarge, ylarge, qlarge)
    and estimate the location of the fibre centre,
    returning a list of fibre centres of the form
    (xfibre, yfibre)
    
    """
    fibre_locations = []
    for path_target in path_targets:
        id = path_target[0]
        xs = path_target[1]
        ys = path_target[2]
        xl = path_target[4]
        yl = path_target[5]
        xf = xl + pars.FIBRE_MULTIPLER * (xl-xs)
        yf = yl + pars.FIBRE_MULTIPLER * (yl-ys)
        fibre_locations.append( [id,xf,yf])
    return fibre_locations

def read_track( filename ):
    """
    
    Read a track from the comma-separated list within a file
    
    """
    track = []

    # Open the paths file within a Python context.
    with open(filename, 'r') as file_in:
        # Read the ID and alpha and beta paths for each positioner from the file
        while True:
            line = file_in.readline()
            if line != '\n' and not line:
                # Empty line means end of file
                break
            if not line.strip():
                # Skip a blank line
                continue
            line = line.replace(',', ' ') # remove commas
            words = line.split()
            if len(words) > 2:
                id = int(words[0])
                xtrack = float(words[1])
                ytrack = float(words[2])
                track.append( [xtrack, ytrack] )
    file_in.close()
    return track

def read_path_to_track( filename, id):
    """
    
    Read the path associated with the given fibre positioner and
    return it as a track.
    
    """
    track = []
    if MOCPATH_OK:
        paths = read_path_file( filename )
        
        # Select the relevant path from the file
        alpha_list = []
        beta_list = []
        for (fid, apath, bpath) in paths:
            if fid == id:
                alphas = apath
                betas = bpath
                break
        if alpha_list and beta_list:
            for alpha, beta in zip(alpha_list, beta_list):
                # Convert alpha, beta to X,Y
                elbowx = ALPHA_LENGTH * math.cos(DEG2RAD * alpha)
                elbowy = ALPHA_LENGTH * math.sin(DEG2RAD * alpha)
                fibrex = elbowx + (BETA_LENGTH * math.cos(DEG2RAD * beta))
                fibrey = elbowy + (BETA_LENGTH * math.sin(DEG2RAD * beta))
                track.append( [fibrex, fibrey])
        else:
            raise ValueError("Positioner %d not found in paths file." % id)
    else:
        raise ImportError("mocpath module could not be imported")
    return track


def transform_coords( xlist, ylist, x0, y0, xscale=1.0, yscale=1.0, rotation=0.0):
    """
    
    Transform Cartesian coordinate (x,y) into (xnew, ynew) by
    translating, rotating and magnifying.
    
    """
    # Convert the lists of points into arrays of X and Y coordinates
    xpt = np.array(xlist) # - x0 ?
    ypt = np.array(ylist) # - y0 ?
    
    xnew = x0 + (xpt * xscale * math.cos( rotation )) + (ypt * yscale * math.sin( rotation ))
    ynew = y0 - (xpt * xscale * math.sin( rotation )) + (ypt * yscale * math.cos( rotation ))
    
    return (xnew, ynew)

def find_end_index( track, end2=-1, graphics=True, name="eval_path_tracking" ):
    """
    
    A diagnostic function to determine which index contains the end point of a track.
    
    """
    base_points = np.array(track).T

    # Diagnostic plot
    if graphics and (plotting is not None):
        title = "%s: vfrig points (blue)." % name
        title += "\n vfrig end index=%d yellow O" % end2
        plotaxis = plotting.plot_xy( base_points[0], base_points[1],
                          title=title, xlabel='x (mm)', ylabel='y (mm)',
                          linefmt='b.', linestyle=' ', equal_aspect=True,
                          showplot=False )
        plotting.plot_xy( base_points[0][end2], base_points[1][end2], 
                          linefmt='yo', linestyle=' ', equal_aspect=True,
                          plotaxis=plotaxis, showplot=True )

def match_tracks(track1, track2, end1=-1, end2=-1, graphics=False, verbose=False,
                 name="eval_path_tracking"):
    """

    Find optimised coordinate transformation parameters which give the best match
    between the two tracks.
    
    track1 = [(fx1,fy1), (fx2, fy2) ...]
    track2 = [(sx1,sy1), (sx2, sy2) ...]
    
    end1 and end2 give the indices of track1 and track2 corresponding to the
    end of the track (with -1 for last index). If the track is reversed, the
    last index may not be at the end of the track.

    Returns matched tracks (newpoints1, newpoints2).

    """
    logger = logging.getLogger(__name__)

    lmin = min( len(track1), len(track2) )
    lmax = max( len(track1), len(track2) )
    if verbose:
        print("Track 1              \t Track 2")
        print("---------------------\t ------------------------")
        for ii in range(0, lmax):
            strg = ""
            if ii < len(track2):
                strg += "%s,\t" % str(track2[ii])
            else:
                strg += "     - - - - -     \t"
            if ii < len(track1):
                strg += "%s" % str(track1[ii])
            else:
                strg += "     - - - - -     "
            print(strg)

    fit_points = np.array(track1).T
    base_points = np.array(track2).T

    # Flip the X axis
    fit_points[0] = fit_points[0] * -1.0

    # The initial estimate of the relative rotation.
    logger.debug("Fit 1: Estimating the relative rotation.")

    # NOTE: The end point of the base data as at [end2] because the FPU is
    # reversed during the movement, and [-1] is back at the beginning.
#    print("base Y diff = ", base_points[1][end2], "-", base_points[1][0])
#    print("base X diff = ", base_points[0][end2], "-", base_points[0][0])
    basey = (base_points[1][end2] - base_points[1][0])
    basex = (base_points[0][end2] - base_points[0][0])
    theta_base = math.atan2( basey, basex )
#    print("fit Y diff = ", fit_points[1][end1], "-", fit_points[1][0])
#    print("fit X diff = ", fit_points[0][end1], "-", fit_points[0][0])
    fity = (fit_points[1][end1] - fit_points[1][0])
    fitx = (fit_points[0][end1] - fit_points[0][0])
    theta_fit = math.atan2( fity, fitx )
    rotation = theta_fit - theta_base
#    print("Base x, y, angle", basex, basey, theta_base, RAD2DEG * theta_base )
#    print("Fit x, y, angle", fitx, fity, theta_fit, RAD2DEG * theta_fit )
    logger.debug("Estimated rotation: %f (rad) %f (deg)" % (rotation, RAD2DEG * rotation))

    # Diagnostic plot
    if verbose and graphics and (plotting is not None):
        title = "%s: vfrig points (blue) and unadjusted comparision points (green)." % name
        plotaxis = plotting.plot_xy( fit_points[0], fit_points[1],
                            title=title, xlabel='x (mm)', ylabel='y (mm)',
                            linefmt='r.', linestyle=' ', equal_aspect=True, showplot=False )
        plotting.plot_xy( base_points[0], base_points[1],
                          linefmt='b.', linestyle=' ', equal_aspect=True,
                          plotaxis=plotaxis, showplot=True )

    rot_points = transform_coords( fit_points[0], fit_points[1], 0.0, 0.0, 1.0, 1.0, rotation)

    logger.debug("Fit 2: Initial translation between starting points.")
    x0 = (base_points[0][0] - rot_points[0][0])
    y0 = (base_points[1][0] - rot_points[1][0])
    logger.debug("Initial translation: (%f,%f) mm" % (x0, y0))

    # Diagnostic plot
    if verbose and graphics and (plotting is not None):
        title = "%s: vfrig points (blue) and rotated comparision points (green)." % name
        plotaxis = plotting.plot_xy( rot_points[0], rot_points[1], title=title, xlabel='x (mm)', ylabel='y (mm)',
                          linefmt='g.', linestyle=' ', equal_aspect=True, showplot=False )
        plotting.plot_xy( base_points[0], base_points[1],
                          linefmt='b.', linestyle=' ', equal_aspect=True,
                          plotaxis=plotaxis, showplot=True )

    # Translate the points
    trans_points = transform_coords( rot_points[0], rot_points[1], x0, y0,
                                      1.0, 1.0, 0.0)

    logger.debug("Fit 3: Matching R,theta from the starting point.")
    xzero = base_points[0][0]
    yzero = base_points[1][0]
    #print("new base Y diff = ", base_points[1][end2], "-", base_points[1][0])
    #print("new base X diff = ", base_points[0][end2], "-", base_points[0][0])
    basey = (base_points[1][end2] - base_points[1][0])
    basex = (base_points[0][end2] - base_points[0][0])
    theta_base = math.atan2( basey, basex )

    #print("new fit Y diff = ", trans_points[1][end1], "-", trans_points[1][0])
    #print("new fit X diff = ", trans_points[0][end1], "-", trans_points[0][0])
    fity = (trans_points[1][end1] - trans_points[1][0])
    fitx = (trans_points[0][end1] - trans_points[0][0])
    theta_fit = math.atan2( fity, fitx )
    theta_shift = theta_fit - theta_base

    rbase = math.sqrt( basex*basex + basey*basey )
    rfit = math.sqrt( fitx*fitx + fity*fity )
    rscale = rbase / rfit
    #print("Base x, y, angle", basex, basey, theta_base, RAD2DEG * theta_base )
    #print("Fit x, y, angle", fitx, fity, theta_fit, RAD2DEG * theta_fit )
    logger.debug("Estimated theta shift: %f (rad) %f (deg)" % (theta_shift, RAD2DEG * theta_shift))
    logger.debug("Estimated rscale: %f" % rscale)

    # Diagnostic plot
    if verbose and graphics and (plotting is not None):
        title = "%s: vfrig points (blue) and rotated+shifted comparision points (green)." % name
        title += "\n vfrig end index yellow O, comparison end index magenta *"
        plotaxis = plotting.plot_xy( trans_points[0], trans_points[1],
                          title=title, xlabel='x (mm)', ylabel='y (mm)',
                          linefmt='g.', linestyle=' ', equal_aspect=True, showplot=False )
        plotaxis = plotting.plot_xy( base_points[0], base_points[1],
                          linefmt='b.', linestyle=' ', equal_aspect=True,
                          plotaxis=plotaxis, showplot=False )
        plotaxis = plotting.plot_xy( xzero, yzero, 
                          linefmt='k+', linestyle=' ', equal_aspect=True,
                          plotaxis=plotaxis, showplot=False )
        plotaxis = plotting.plot_xy( trans_points[0][end1], trans_points[1][end1], 
                          linefmt='m*', linestyle=' ', equal_aspect=True,
                          plotaxis=plotaxis, showplot=False )
        plotting.plot_xy( base_points[0][end2], base_points[1][end2], 
                          linefmt='yo', linestyle=' ', equal_aspect=True,
                          plotaxis=plotaxis, showplot=True )

    # Adjust the polar coordinates
    xshifted = trans_points[0] - xzero
    yshifted = trans_points[1] - yzero

    rarray = np.sqrt( xshifted*xshifted + yshifted*yshifted )
    tharray = np.arctan2( yshifted, xshifted )

    rscaled = rarray * rscale
    xnew = xzero + rscaled * np.cos( tharray )
    ynew = yzero + rscaled * np.sin( tharray )
    polar_adjust = [xnew, ynew]

    # Diagnostic plot
    if graphics and (plotting is not None):
        XSHIFT = 0.0 # Set to 2.0 to show an offset plot
        YSHIFT = 0.0 # Set to 1.0 to show an offset plot
        title = "%s: vfrig points (blue) and rotated+scaled comparision points (green)." % name
        plotaxis = plotting.plot_xy( polar_adjust[0]+XSHIFT, polar_adjust[1]+YSHIFT,
                          title=title, xlabel='x (mm)', ylabel='y (mm)',
                          linefmt='g.', linestyle=' ', equal_aspect=True, showplot=False )
        plotting.plot_xy( base_points[0], base_points[1],
                          linefmt='b.', linestyle=' ', equal_aspect=True,
                          plotaxis=plotaxis, showplot=True )

    # Reorient all the coordinates to align the start and end points vertically
    logger.debug("Fit 4: Rescaling perpendicular to the track direction.")
    polar_new = transform_coords( xnew, ynew, 0.0, 0.0, 1.0, 1.0, theta_base-PIBY2 )
    base_new = transform_coords( base_points[0], base_points[1], 0.0, 0.0, 1.0, 1.0, theta_base-PIBY2 )

    # Diagnostic plot
    if verbose and graphics and (plotting is not None):
        title = "%s: vfrig points (blue) and rotated+shifted+scaled+reoriented comparision points (green)." % name
        plotaxis = plotting.plot_xy( polar_new[0], polar_new[1],
                          title=title, xlabel='x (mm)', ylabel='y (mm)',
                          linefmt='g.', linestyle=' ', equal_aspect=True, showplot=False )
        plotting.plot_xy( base_new[0], base_new[1],
                          linefmt='b.', linestyle=' ', equal_aspect=True,
                          plotaxis=plotaxis, showplot=True )

    # Rescale the X axis
    polar_xmax = np.max( polar_new[0] - polar_new[0][0] )
    base_xmax = np.max( base_new[0] - base_new[0][0] )
    xscale = base_xmax / polar_xmax
    logger.debug("Estimated xscale: %f" % xscale)
    polar_xscaled = polar_new[0][0] + (polar_new[0]-polar_new[0][0]) * xscale
    polar_scaled = [polar_xscaled, polar_new[1]]
    # Reverse the rotation
    polar_scaled = transform_coords( polar_scaled[0], polar_scaled[1], 0.0, 0.0, 1.0, 1.0, PIBY2-theta_base )

    # Diagnostic plot
    if graphics and (plotting is not None):
        title = "%s: vfrig points (blue) and rotated+scaled+tilted comparision points (green)." % name
        plotaxis = plotting.plot_xy( polar_scaled[0], polar_scaled[1],
                          title=title, xlabel='x (mm)', ylabel='y (mm)',
                          linefmt='g.', linestyle=' ', equal_aspect=True, showplot=False )
        plotting.plot_xy( base_points[0], base_points[1],
                          linefmt='b.', linestyle=' ', equal_aspect=True,
                          plotaxis=plotaxis, showplot=True )

    return polar_scaled, base_new

def find_max_deviation( points1, points2, verbose=False ):
    """
    
    Find the approximate maximum deviation of the minimum distance
    between the two Cartesian tracks.
    The function finds the minimum X difference and minimum Y difference
    separately and then combines them.
    
    NOTE: A better algorithm would be to calculate the minimum approach
    distance along the length of each track, but this would take a lot
    longer to execute.
    
    """
    maxdist = 0.0
    maxelement = 0
    element = 0
    for xpoint1,ypoint1 in zip(points1[0], points1[1]):
        mindist = 99999.0
        for xpoint2,ypoint2 in zip(points2[0], points2[1]):
            xdiff = abs(xpoint1 - xpoint2)
            ydiff = abs(ypoint1 - ypoint2)
            dist = math.sqrt( xdiff*xdiff + ydiff*ydiff )
            # The rescaling with have deliberately matched the points at
            # the beginning and end of the track. Ignore these points
            # by ignoring distances of exactly zero.
            if dist > 0.00001 and dist < mindist:
                mindist = dist
            if verbose:
                print("Comparing (%.4f,%.4f) with (%.4f,%.4f). diff=(%.4f,%.4f), dist=%.4f" % \
                    (xpoint1,ypoint1 , xpoint2,ypoint2, xdiff,ydiff, dist))
        if mindist > maxdist:
            maxdist = mindist
            maxelement = element
        if verbose:
            print("%d: Analysed point (%.4f,%.4f) and found min distance=%.4f (max so far %.4f)" % \
                  (element, xpoint1, ypoint1, mindist, maxdist))
        element += 1

    return (maxdist, maxelement)

def evaluate_path_tracking(
    fpu_track, comparison_track, end1=-1, end2=-1, graphics=False,
    pars=PATH_TRACK_ANALYSIS_PARS
):
    """
    
    Takes two lists of coordinates containing a tracked path, derives
    a coordinate transformation which overlays the paths and analyses
    the difference between the two paths.


    """
#    # Parameters must be provided
#    assert pars is not None

    # Match the two tracks through a series of translations, rotations and scales.
    (new_fpu_track, new_comparison_track) = match_tracks(fpu_track, comparison_track,
                                                end1=end1, end2=end2, graphics=graphics)

    min_diff = find_max_deviation( new_fpu_track, new_comparison_track )

#     # Transform the FPU track to match the comparison track.
#     transformed_track = transform_coords( fpu_track, x0, y0, xscale, yscale, rotation)
#     
#     # Evaluate the difference between the two tracks
#     rms_diff = np.linalg.norm(transformed_track - comparison_track, axis=0)
    
    return min_diff
    
#MOCPATH_FILE = "POS15_track.txt"
#VFRIG_FILE = "images1_15_long_path.txt"
#END_INDEX = 180

#MOCPATH_FILE = "POS3_track.txt"
#VFRIG_FILE = "images1_3_path.txt"
#END_INDEX = 280

#MOCPATH_FILE = "POS4_track.txt"
#VFRIG_FILE = "images1_4_path.txt"
#END_INDEX = 280

#MOCPATH_FILE = "POS5_track.txt"
#VFRIG_FILE = "images1_5_path.txt"
#END_INDEX = 220

MOCPATH_FILE = "POS9_test.txt"
VFRIG_FILE = "images1_9_test.txt"
END_INDEX = -1


if __name__ == "__main__":
    # Run a test
    # Define two tracks and minimise their differences.
#    track1 = [[10.0, 16.3],
#              [11.3, 17.0],
#              [14.5, 19.1],
#              [14.5, 19.1],
#              [14.4, 18.1],
#              [12.5, 18.5],
#              [16.0, 17.5],
#              [15.0, 17.0]]
#    track2 = [[22.0, 36.9],
#              [21.2, 37.0],
#              [24.5, 39.1],
#              [24.4, 38.1],
#              [22.5, 38.5],
#              [24.3, 38.9],
#              [25.7, 37.4],
#              [25.5, 38.0]]

    track1 = read_track( MOCPATH_FILE )
    track2 = read_track( VFRIG_FILE )

    new1, new2 = match_tracks( track1, track2, end1=-1, end2=END_INDEX, graphics=True )

    (maxdist, element) = find_max_deviation( new1, new2, verbose=True )
    print("Maximum deviation between tracks is %f mm at element %d." % (maxdist, element))

