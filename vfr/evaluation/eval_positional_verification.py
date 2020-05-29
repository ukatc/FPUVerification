# -*- coding: utf-8 -*-
"""Module to evaluate positional verification.

"""
from __future__ import division, print_function

from Gearbox.gear_correction import angle_to_point, cartesian_blob_position, \
                                    elliptical_distortion, leastsq_circle, fit_offsets
from vfr.evaluation.measures import get_errors, get_measures, get_weighted_coordinates

from vfr.conf import POS_REP_EVALUATION_PARS, GRAPHICAL_DIAGNOSTICS

# Plotting library used for diagnostics.
if GRAPHICAL_DIAGNOSTICS:
    try:
        import moc_plotting as plotting
    except ImportError:
        GRAPHICAL_DIAGNOSTICS = False

import numpy as np
import warnings

POS_VER_ALGORITHM_VERSION = (1, 0, 0)

#
# Modify these flags to control how the algorithm works.
#
# Fit a new camera offset as well as fitting a new alpha axis centre.
# Set True to implement SMB change or False for old behaviour.
FIT_CAMERA_OFFSET = False
# Apply an elliptical distortion to the measured points.
# Set False to implement the SMB change or True for old behaviour.
APPLY_ELLIPTICAL_DISTORTION = False


def evaluate_positional_verification(
    dict_of_coords,            # Dictionary of coordinates, as defined below.
    pars=None,                 # Configuration parameters?
    x_center=None,             # X centre of alpha axis
    y_center=None,             # Y centre of alpha axis
    R_alpha=None,              # Calibrated radius of alpha circle
    R_beta_midpoint=None,      # Calibrated radius of beta circle
    camera_offset_rad=None,    # Calibrated camera angle offset
    beta0_rad=None,            # Calibrated beta angle offset
    coeffs=None,               # Gearbox calibration coefficients
    BLOB_WEIGHT_FACTOR=None,   # Weighting factor between large and small metrology blobs.
    plot=True,                 # Not used
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
    #
    # FIXME: SMB 26-05-2020: This step rederives the location of the alpha axis but is does
    # not redefine the camera offset, circle radii or beta0. If there is a dependency between
    # turntable shift and rotation, all the calibration parameters need to be rederived.

    homeing_dict = {k[0]: blob_pair for k,blob_pair in dict_of_coords.items() if k[0] < 8}
    circle_points = []
    for idx in range(8):
        blob_pair = homeing_dict[idx]
        circle_points.append(cartesian_blob_position(blob_pair, weight_factor=BLOB_WEIGHT_FACTOR))

    x_s, y_s = np.array(circle_points).T
    xc, yc, radius, psi, stretch, _ = leastsq_circle(x_s, y_s)
    P0 = np.array([xc, yc])
    #P0 = np.array([x_center, y_center])
    print("P0 = ", P0, " compared with (x_center,y_center) = ", x_center, y_center)
    print("R = ", radius, " compared with R_alpha=", R_alpha, "R_beta_midpoint=", R_beta_midpoint)

    # Option to recalibrate the camera offset angle.
    if FIT_CAMERA_OFFSET:
        # Extract the alpha circle information from the first 8 points.
        alpha_nom_rad_array = []
        beta_nom_rad_array = []
        for coords, blob_pair in dict_of_coords.items():
            #print("-------------")
            # get nominal coordinates for first 8 points
            (idx, alpha_nom_deg, beta_nom_deg) = coords
            if idx < 8:
                #print("nominal: (alpha, beta) = ", (alpha_nom_deg, beta_nom_deg))
                alpha_nom_rad, beta_nom_rad = np.deg2rad(alpha_nom_deg), np.deg2rad(beta_nom_deg)
                alpha_nom_rad_array.append(alpha_nom_rad)
                beta_nom_rad_array.append(beta_nom_rad)
        alpha_nom_rad_array = np.asarray(alpha_nom_rad_array)
        beta_nom_rad_array = np.asarray(beta_nom_rad_array)

        circle_alpha = { 'x_s2': x_s,
                         'y_s2': y_s,
                         'xc': xc,
                         'yc': yc,
                         'stretch': stretch,
                         'psi': psi,
                         'R': radius,
                         'alpha_nominal_rad': alpha_nom_rad_array,
                         'beta_nominal_rad' : beta_nom_rad_array
                       }

        # Treat the remaining points as beta circle information (TBD)??

        # Find the best fit for the camera offset
        print("circle_alpha=", circle_alpha)
        camera_offset_new, beta0_new = fit_offsets(
                               circle_alpha,                         # Fit alpha circle only
                               circle_beta=None,                     #
                               P0=P0,                                # Use new alpha axis centre
                               R_alpha=R_alpha,                      # Previous calibrated radius of alpha circle
                               R_beta_midpoint=R_beta_midpoint,      # Previous calibrated radius of beta circle
                               camera_offset_start=camera_offset_rad,# Start with previous camera angle offset
                               beta0_start=beta0_rad                 # Fixed beta0
                          )
        print("New camera offset=", camera_offset_new, "compared with", camera_offset_rad)
        print("New beta0=", beta0_new, "(ignored) compared with", beta0_rad)
    else:
        # No fit. The camera offset does not change.
        camera_offset_new = camera_offset_rad


    # Now extract all the points from the disctionary.
    for coords, blob_pair in dict_of_coords.items():
        print("-------------")
        # get nominal coordinates
        (idx, alpha_nom_deg, beta_nom_deg) = coords
        print("nominal: (alpha, beta) = ", (alpha_nom_deg, beta_nom_deg))
        alpha_nom_rad, beta_nom_rad = np.deg2rad(alpha_nom_deg), np.deg2rad(beta_nom_deg)
        expected_pos = angle_to_point(
            alpha_nom_rad,
            beta_nom_rad,
            P0=P0,                               # Use the new alpha axis centre
            #coeffs=coeffs,
            coeffs=None, # inactive because already corrected
            R_alpha=R_alpha,                     # Use the previous calibrated alpha radius
            R_beta_midpoint=R_beta_midpoint,     # Use the previous calibrated beta radius
            camera_offset_rad=camera_offset_new, # Use the new camera offset
            beta0_rad=beta0_rad,                 # Stick with the original beta0
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
        if APPLY_ELLIPTICAL_DISTORTION:
           xm, ym = elliptical_distortion(xmd, ymd, xc, yc, psi, stretch)
        else:
           xm, ym = xmd, ymd

        measured_pos = np.array([xm, ym], dtype=float)
        measured_points[coords] = measured_pos
        #measured_pos -= np.array([ 5.09616146, -3.28669922])

        print("measured_pos = ", measured_pos)
        error_vec = measured_pos - expected_pos
        error_vectors[coords] = error_vec
        error_vec_norm = np.linalg.norm(measured_pos - expected_pos)

        print("error = ", error_vec, "magnitude = ", error_vec_norm)

        error_by_angle[coords] = error_vec_norm

    if GRAPHICAL_DIAGNOSTICS:
        expected_x =[]
        expected_y = []
        measured_x = []
        measured_y = []
        for key in measured_points.keys():
           (mx, my) = measured_points[key]
           (ex, ey) = expected_points[key]
           expected_x.append(ex)
           expected_y.append(ey)
           measured_x.append(mx)
           measured_y.append(my)
        title = "evaluate_positional_verification: Measured (blue) and expected (red) points overlaid."
        plotaxis = plotting.plot_xy( expected_x, expected_y, title=title,
                          xlabel='X (mm)', ylabel='Y (mm)',
                          linefmt='b.', linestyle=' ', equal_aspect=True, showplot=False )
        plotting.plot_xy( measured_x, measured_y, title=None,
                          xlabel=None, ylabel=None,
                          linefmt='r.', linestyle=' ', equal_aspect=True,
                          plotaxis=plotaxis, showplot=True )

    print("############ computing summary statistics")
    mean_error_vector = np.mean(error_vectors.values(), axis=0)
    print("mean error vector =", mean_error_vector)
    error_measures = get_measures(error_by_angle.values())
    print("pos ver error_measures=%r" % error_measures)

    return error_by_angle, expected_points, measured_points, error_measures, mean_error_vector
