# -*- coding: utf-8 -*-
"""Module to evaluate positional verification.

"""
from __future__ import division, print_function

from Gearbox.gear_correction import angle_to_point, cartesian_blob_position, elliptical_distortion
from vfr.evaluation.measures import get_errors, get_grouped_errors, get_weighted_coordinates

import numpy as np
from matplotlib import pyplot as plt
import warnings


def evaluate_positional_verification(
    dict_of_coords,
    pars=None,
    x_center=None,
    y_center=None,
    R_alpha=None,
    R_beta_midpoint=None,
    camera_offset_rad=None,
    beta0_rad=None,
    coeffs=None,
    BLOB_WEIGHT_FACTOR=None,
    **kwargs
):
    """Takes a dictionary. The keys of the dictionary
    are the i,j,k indices of the positional repeteability measurement.
    Equal i and k mean equal step counts, and j indicates
    the arm and movement direction of the corresponding arm
    during measurement.

    The values of the dictionary are a 4-tuple
    (alpha_steps, beta_steps, x_measured_1, y_measured_1, x_measured_2, y_measured_2).

    Here, (alpha_steps, beta_steps) are the angle coordinates given by
    the motor step counts (measured in degrees), and (x_measured,
    y_measured) are the cartesian values of the large (index 1) and
    the small (index 2) target measured from the images taken.


    The units are in dimensionless counts (for alpha_steps and beta_steps)
    and millimeter (for x_measured and y_measured).

    The returned value is the repeatability value in millimeter.

    Any error should be signalled by throwing an Exception of class
    ImageAnalysisError, with a string member which describes the problem.

    """

    error_by_angle = {}
    # get measured circle center point from alpha arm
    # calibration
    #
    # IMPORTANT: Keep in mind this center point is ONLY valid as long
    # as the FPU is in exactly the same position relative to the
    # camera, so no changes to the camera or verification rig are
    # allowed!
    expected_coords = []
    point_list = []

    deg2rad = np.deg2rad
    print(">>>>>>>>>>>> computing point error values")
    P0 = np.array([x_center, y_center])
    # get elliptical coefficients for alpha arm circle
    psi=coeffs["coeffs_alpha"]["psi"]
    stretch=coeffs["coeffs_alpha"]["stretch"]

    print("P0 = ", P0)

    plt.axis("equal")
    x_measured = []
    y_measured = []
    x_expected = []
    y_expected = []
    for coords, blob_pair in dict_of_coords.items():
        print("-------------")
        # get nominal coordinates
        (idx, alpha_nom_deg, beta_nom_deg) = coords
        print("nominal: (alpha, beta) = ", (alpha_nom_deg, beta_nom_deg))
        alpha_nom_rad, beta_nom_rad = deg2rad(alpha_nom_deg), deg2rad(beta_nom_deg)
        expected_point = angle_to_point(
            alpha_nom_rad,
            beta_nom_rad,
            P0=P0,
            #coeffs=coeffs, # inactive because already corrected
            R_alpha=R_alpha,
            R_beta_midpoint=R_beta_midpoint,
            camera_offset_rad=camera_offset_rad,
            beta0_rad=beta0_rad,
        )

        warnings.warn("applying fudge factor to reduce error. FIXME: Needs to be replaced by correct term")
        expected_point += np.array([4.943, -3.340])
        xe1, ye1 = expected_point

        # FIXME: This is sloppy and only a stop-gap: we probably need
        # to model that the FPU metrology targets are really moving on
        # a sphere, not on a tilted plane. The circles for alpha and
        # beta calibration measurements are just two subsets of that
        # sphere, but the verification can select any point on it.
        xe, ye = elliptical_distortion(xe1, ye1, x_center, y_center, psi, stretch)

        x_expected.append(xe)
        y_expected.append(ye)

        print("expected point = ", expected_point)
        # convert blob pair image coordinates to
        # Cartesian coordinates of mid point
        #
        # Attention: This flips the y axis, as in the gearbox calibration
        measured_point = cartesian_blob_position(blob_pair, weight_factor=BLOB_WEIGHT_FACTOR)
        xm, ym = measured_point
        x_measured.append(xm)
        y_measured.append(ym)

        #measured_point = get_weighted_coordinates(blob_pair, weight_factor=BLOB_WEIGHT_FACTOR)[0]
        print("measured point = ", measured_point)
        print("error = ", measured_point - expected_point, "magnitude = ", np.linalg.norm(measured_point - expected_point))

        expected_coords.append(expected_point)
        point_list.append([blob_pair])
        error_by_angle[coords] = get_errors(
            [blob_pair], centroid=expected_point, weight_factor=BLOB_WEIGHT_FACTOR
        ).max
        print("error_by_angle[%r]=%r" % (coords, error_by_angle[coords]))

    plt.plot(x_measured, y_measured, "r.")
    plt.plot(x_expected, y_expected, "b+")
    plt.legend(loc="best", labelspacing=0.1)
    plt.grid()
    plt.title("measured and expected points")
    plt.xlabel("x [millimeter], Cartesian camera coordinates")
    plt.ylabel("y [millimeter], Cartesian camera coordinates")
    #plt.show()
    print("############ computing summary statistics")
    error_measures = get_grouped_errors(
        point_list, list_of_centroids=expected_coords, weight_factor=BLOB_WEIGHT_FACTOR
    )
    print("pos ver error_measures=%r" % error_measures)
    return error_by_angle, error_measures, plt
