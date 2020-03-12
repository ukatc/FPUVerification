# -*- coding: utf-8 -*-
"""Module to evaluate positional verification.

"""
from __future__ import division, print_function

from Gearbox.gear_correction import angle_to_point, cartesian_blob_position, elliptical_distortion, leastsq_circle
from vfr.evaluation.measures import get_errors, get_measures, get_weighted_coordinates

import numpy as np
import warnings

POS_VER_ALGORITHM_VERSION = (1, 0, 0)

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
    plot=True,
    **kwargs
):
    """Takes a dictionary. The keys of the dictionary are the idx, alpha_nom,
    beta_nom parameters of the positional repeteability measurement.

    The values of the dictionary are a 6-tuple
    (x_measured_1, y_measured_1, qual1, x_measured_2, y_measured_2, qual2).

    Here, (alpha_nom, beta_nom) are the angle coordinates given by the
    motor step counts (measured in degrees), and (x_measured,
    y_measured) are the cartesian values of the large (index 1) and
    the small (index 2) blob target coordinates measured from the
    images taken.


    The units are in degrees (for alpha_nom and beta_nom) and pixel
    units (for x_measured and y_measured). The y axis of the pixel
    units is always positive with the origiin in the upper left corner
    (that is, it is pointing in the inverse direction compared to the
    y axis of a Cartesian system).

    The returned value are the repeatability measures in millimeter.

    Any error should be signalled by throwing an Exception of class
    ImageAnalysisError, with a string member which describes the problem.

    """

    expected_points = {} # arm coordinates + index vs. expected Cartesian position
    measured_points = {} # arm coordinates + index vs. actual Cartesian position
    error_vectors = {} # arm coordinates + index vs. delta (expected - measured)
    error_by_angle = {} # arm coordinates + index vs. magnitude of error vector

    # get measured circle center point from alpha arm
    # calibration
    #
    # FPU center has changesd so it needs to be rederived from the images taken
    # The first 8 images taken are explicitly for this purpose
    # This method is similar to Gearbox.gear_correction.fit_circle but has different inputs.
    
    
    homeing_dict = {k[0]: blob_pair for k,blob_pair in dict_of_coords.items() if k[0] < 8}
    circle_points = []
    for idx in range(8):
        blob_pair = homeing_dict[idx]
        circle_points.append(cartesian_blob_position(blob_pair, weight_factor=BLOB_WEIGHT_FACTOR))
    
    x_s, y_s = np.array(circle_points).T
    
    xc, yc, _, psi, stretch, _ = leastsq_circle(x_s, y_s)
    
    P0 = np.array([xc, yc])


    print("P0 = ", P0)

    for coords, blob_pair in dict_of_coords.items():
        print("-------------")
        # get nominal coordinates
        (idx, alpha_nom_deg, beta_nom_deg) = coords
        print("nominal: (alpha, beta) = ", (alpha_nom_deg, beta_nom_deg))
        alpha_nom_rad, beta_nom_rad = np.deg2rad(alpha_nom_deg), np.deg2rad(beta_nom_deg)
        expected_pos = angle_to_point(
            alpha_nom_rad,
            beta_nom_rad,
            P0=P0,
            #coeffs=coeffs,
            coeffs=None, # inactive because already corrected
            R_alpha=R_alpha,
            R_beta_midpoint=R_beta_midpoint,
            camera_offset_rad=camera_offset_rad,
            beta0_rad=beta0_rad,
            broadcast=False,
        )

        expected_points[coords] = expected_pos

        print("expected_pos = ", expected_pos)
        # convert blob pair image coordinates to
        # Cartesian coordinates of mid point
        #
        # Attention: This function flips the y axis, as in the gearbox calibration
        xmd, ymd = cartesian_blob_position(blob_pair, weight_factor=BLOB_WEIGHT_FACTOR)

        # apply (small) elliptical distortion correction as in the
        # gearbox calibration computation for the alpha arm.
        #
        # FIXME: This is sloppy and only a stop-gap: we probably need
        # to model that the FPU metrology targets are really moving on
        # a sphere, not on a tilted plane. The circles for alpha and
        # beta calibration measurements are just two subsets of that
        # sphere, but the verification measurement can select any
        # point on it.
        xm, ym = elliptical_distortion(xmd, ymd, xc, yc, psi, stretch)

        measured_pos = np.array([xm, ym], dtype=float)
        measured_points[coords] = measured_pos
        #measured_pos -= np.array([ 5.09616146, -3.28669922])

        print("measured_pos = ", measured_pos)
        error_vec = measured_pos - expected_pos
        error_vectors[coords] = error_vec
        error_vec_norm = np.linalg.norm(measured_pos - expected_pos)

        print("error = ", error_vec, "magnitude = ", error_vec_norm)

        error_by_angle[coords] = error_vec_norm


    print("############ computing summary statistics")
    mean_error_vector = np.mean(error_vectors.values(), axis=0)
    print("mean error vector =", mean_error_vector)
    error_measures = get_measures(error_by_angle.values())
    print("pos ver error_measures=%r" % error_measures)

    return error_by_angle, expected_points, measured_points, error_measures, mean_error_vector
