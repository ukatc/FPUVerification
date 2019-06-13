# -*- coding: utf-8 -*-
"""Module to evaluate positional verification.

"""
from __future__ import division, print_function

from Gearbox.gear_correction import polar2cartesian
from vfr.evaluation.measures import get_errors, get_grouped_errors, group_by_subkeys

from math import sin, cos
import numpy as np


def angle_to_point(
        alpha_nom,
        beta_nom,
        coeffs=None,
        x_center=None,
        y_center=None,
        R_alpha=None,
        R_beta_midpoint=None,
        alpha0=None,
):

    # these offsets make up for the rotation of
    # the camera *and* for the +180 degree offset
    # for beta in respect for the Cartesian system
    a_alpha = coeffs['coeffs_alpha']['a']
    a_beta = coeffs['coeffs_beta']['a']
    print("offset alpha = ", np.rad2deg(a_alpha))
    print("offset beta = ", np.rad2deg(a_beta))
    print("R_alpha=", R_alpha)
    print("R_beta_midpoint=", R_beta_midpoint)
    if alpha0 is None:
        # alpha reference point for deriving gamma
        alpha0 = -180.3 + 5.0 # alpha_min + pos_rep_safety_margin

    P0 = np.array([x_center, y_center])

    # add offset from fitting
    alpha = alpha_nom + np.rad2deg(a_alpha)
    beta = beta_nom + np.rad2deg(a_beta)
    # add difference to alpha when the beta
    # correction was measured (these angles add up
    # because when the alpha arm is turned (clockwise),
    # this turns the beta arm (clockwise) as well).
    gamma = beta + (alpha - alpha0)
    # compute expected Cartesian coordinate of observation
    pos_alpha = np.array(polar2cartesian(np.deg2rad(alpha), R_alpha))
    pos_beta = np.array(polar2cartesian(np.deg2rad(gamma), R_beta_midpoint))

    expected_point = P0 + pos_alpha + pos_beta
    print("alpha_nom=%f, beta_nom=%f" % (alpha_nom, beta_nom))
    print("alpha=%f, beta=%f, gamma=%f" % (alpha, beta, gamma))
    print("p0=", P0)
    print("p_expected=",expected_point)
    print("p_a=", pos_alpha)
    print("p_b=", pos_beta)

    return expected_point


def evaluate_positional_verification(
    dict_of_coords,
    pars=None,
    x_center=None,
    y_center=None,
    R_alpha=None,
    R_beta_midpoint=None,
    alpha0=None,
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
    the motor step counts (measured in degrees), and (alpha_measured,
    beta_measured) are the cartesian values of the large (index 1) and
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
    # as the alpha arm is in exactly the same position relative to the
    # camera, so no changes to the camera or verification rig are
    # allowed!
    expected_coords = []
    point_list = []

    print(">>>>>>>>>>>> computing point error values")
    for coords, point_pair in dict_of_coords.items():
        print("-------------")
        # get nominal coordinates
        (idx, alpha_nom, beta_nom) = coords
        expected_point = angle_to_point(
            alpha_nom,
            beta_nom,
            coeffs=coeffs,
            x_center=x_center,
            y_center=y_center,
            R_alpha=R_alpha,
            R_beta_midpoint=R_beta_midpoint,
            alpha0=alpha0,
            )

        expected_coords.append(expected_point)
        point_list.append([point_pair])
        error_by_angle[coords] = get_errors(
            [point_pair], centroid=expected_point, weight_factor=BLOB_WEIGHT_FACTOR
        ).max
        print("error_by_angle[%r]=%r" % (coords, error_by_angle[coords]))

    print("############ computing summary statistics")
    keyfun = lambda x: (x[1], x[2])
    error_measures = get_grouped_errors(
        point_list,
        list_of_centroids=expected_coords,
        weight_factor=BLOB_WEIGHT_FACTOR,
    )
    print("pos ver error_measures=%r" % error_measures)
    return error_by_angle, error_measures
