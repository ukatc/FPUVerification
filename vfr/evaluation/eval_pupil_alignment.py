# -*- coding: utf-8 -*-
"""Module to evaluate pupil alignment.

"""

from __future__ import division, print_function

import numpy as np
import math

RAD_TO_ARCMIN = 180.0 * 60.0 / math.pi  # Radians to arcminutes


def evaluate_pupil_alignment(dict_of_coordinates, pars=None):
    """
    ...

    Any error should be signalled by throwing an Exception of class
    PupilAlignmentAnalysisError, with a string member which describes the problem.

    """

    # group by having the same alpha coordinates
    alpha_dict = {}
    for pos, (x, y, q) in dict_of_coordinates.items():
        alpha, beta = pos
        if not alpha_dict.has_key(alpha):
            alpha_dict[alpha] = []
        alpha_dict[alpha].append((x, y))

    beta_errors = []
    beta_centers = []
    for alpha, bgroup in alpha_dict.items():
        bcoords = np.array(bgroup)
        bcenter = np.mean(bcoords, axis=0)
        beta_centers.append(bcenter)
        beta_errors.append(np.mean(map(np.linalg.norm, bcoords - bcenter)))

    pupalnBetaErr = np.mean(beta_errors)

    alpha_center = np.mean(beta_centers, axis=0)
    pupalnAlphaErr = np.mean(map(np.linalg.norm, beta_centers - alpha_center))

    # TODO: Convert the units from mm on the screen to arcmin of pupil error
#     pupalnAlphaErr = RAD_TO_ARCMIN * math.asin(pupalnAlphaErr/pars.CURVATURE)
#     pupalnBetaErr = RAD_TO_ARCMIN * math.asin(pupalnBetaErr/pars.CURVATURE)

    pupalnTotalErr = sum([pupalnAlphaErr, pupalnBetaErr])

    pupalnErrorBars = "TBD"

    return (pupalnAlphaErr, pupalnBetaErr, pupalnTotalErr, pupalnErrorBars)


def get_min_quality_pupil(list_of_coords):
    """compute minimum quality from a set of coordinate / quality triple
    pairs, as computed by pupAlgnCoordinates()

    """

    cord_array = np.array(list_of_coords)
    return np.min(cord_array[:, 2])
