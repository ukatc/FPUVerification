# -*- coding: utf-8 -*-
"""

Module to evaluate pupil alignment.

"""

from __future__ import division, print_function

import numpy as np
import math

RAD_TO_ARCMIN = 180.0 * 60.0 / math.pi  # Radians to arcminutes


def evaluate_pupil_alignment(dict_of_coordinates, pars=None):
    """
    
    Takes a dictionary of coordinates. The dictionary keys are a 2-tuple
    containing (alpha, beta) angles at which each pupil image has been
    measured and the dictionary values are a 3-tuple containing
    (xcentroid, ycentroid, quality) for each measurement.

    alpha and beta are measured in degrees and xcentroid, ycentroid
    are measured in millimetres.
    
    pars is a data structure containing configurable parameters, such as
    pars.CURVATURE: the radius of curvature of the pupil wavefront.
    See the PUP_ALGN_EVALUATION_PARS data structure in vfr/conf.py.

    The returned values are pupil alignment errors in millimeter:
    TODO: Convert the units from mm on the screen to arcmin of pupil error?

    Any error should be signalled by throwing an Exception of class
    PupilAlignmentAnalysisError, with a string member which describes the problem.

    """

    # Group together sets of measurements with the same alpha coordinates
    # to make alpha_dict.
    alpha_dict = {}
    for pos, (x, y, q) in dict_of_coordinates.items():
        alpha, beta = pos
        if not alpha_dict.has_key(alpha):
            alpha_dict[alpha] = []
        alpha_dict[alpha].append((x, y))

    # Estimate the beta error by calculating the error for all the measurements
    # made at the same alpha angle.
    beta_errors = []
    beta_centers = []
    for alpha, bgroup in alpha_dict.items():
        # alpha is the alpha angle of measurement
        # bgroup is the list of (x,y) coordinates at this same alpha angle.
        bcoords = np.array(bgroup)
        # There must be at least 2 measurements, or the np.mean will
        # average the X and Y coordinates together.
        if len(bgroup) > 1:
            # bcentre is the average of all the centroid measurements
            bcenter = np.mean(bcoords, axis=0)
        else:
            # The average of a group with only one member is that member.
            bcentre = bcoords
        beta_centers.append(bcenter)
        # beta_error is the mean distance of all the measurements
        # from the average.
        beta_errors.append(np.mean(map(np.linalg.norm, bcoords - bcenter)))

    # The overall beta error is the mean beta error over all the alpha angles.
    pupalnBetaErr = np.mean(beta_errors)

    # alpha_centre average centroid for the entire set of measurements.
    alpha_center = np.mean(beta_centers, axis=0)
    # The overall alpha error is the mean distance of all the beta centres
    # from the alpha centre (assuming that averaging all the beta measurements
    # at each alpha angle has removed the beta error).
    pupalnAlphaErr = np.mean(map(np.linalg.norm, beta_centers - alpha_center))

    # TODO: Convert the units from mm on the screen to arcmin of pupil error
#     pupalnAlphaErr = RAD_TO_ARCMIN * math.asin(pupalnAlphaErr/pars.CURVATURE)
#     pupalnBetaErr = RAD_TO_ARCMIN * math.asin(pupalnBetaErr/pars.CURVATURE)

    # The total error is the sum of the alpha and beta errors.
    # TODO: Why the sum, rather than RMS?
    pupalnTotalErr = sum([pupalnAlphaErr, pupalnBetaErr])

    pupalnErrorBars = "TBD"

    return (pupalnAlphaErr, pupalnBetaErr, pupalnTotalErr, pupalnErrorBars)


def get_min_quality_pupil(list_of_coords):
    """
    
    Compute minimum quality from a set of coordinate / quality triple
    pairs, as computed by pupilCoordinates().

    """
    # Each coord_array element consists of (x, y, quality).
    coord_array = np.array(list_of_coords)
    return np.min(coord_array[:, 2])
