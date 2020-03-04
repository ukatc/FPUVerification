# -*- coding: utf-8 -*-
"""

This module contains the gearbox calibration software
used by the MOONS fibre positioner verification system.

See "MOONS Fibre Positioner Gearbox Calibration"
by Johannes Nix, revision 0.4, 2 October 2019.

Source code documentation added by Steven Beard,
February 2020. Comments which look like this

# << Here is a code snippet. >>

refer to the snippets of code which are named and
described in Johannes' document.

"""

from __future__ import division, print_function

from math import pi
import numpy as np
import logging

from scipy import optimize

from fpu_constants import (
    ALPHA_DATUM_OFFSET_RAD,
    BETA_DATUM_OFFSET_RAD,
    StepsPerRadianAlpha,
    StepsPerRadianBeta,
)
from vfr.conf import BLOB_WEIGHT_FACTOR, POS_REP_EVALUATION_PARS, PERCENTILE_ARGS


# Exceptions which are raised if image analysis functions fail
class GearboxFitError(Exception):
    pass


# Version number for gearbox correction algorithm
# (each different result for the same data
# should yield a version number increase)
GEARBOX_CORRECTION_VERSION = (5, 0, 2)

# Minimum version for which this code works
# and yields a tolerable result
GEARBOX_CORRECTION_MINIMUM_VERSION = (5, 0, 0)


def cartesian2polar(x, y):
    # Convert Cartesian to polar coordinates.
    # phi_rad is returnedin radians.
    rho = np.sqrt(x ** 2 + y ** 2)
    phi_rad = np.arctan2(y, x)
    return (phi_rad, rho)


def polar2cartesian(phi_rad, rho):
    # Convert polar to Cartesian coordinates.
    # phi_rad must be given in radians.
    x = rho * np.cos(phi_rad)
    y = rho * np.sin(phi_rad)
    return (x, y)


def calc_R(x, y, xc, yc):
    """ calculate the distance of each 2D points from the center (xc, yc)
    x and y can be numpy arrays of coordinates.
    """
    return np.sqrt((x - xc) ** 2 + (y - yc) ** 2)


def rot_axis(x, y, psi):
    """

    Transfer the point (x,y) by rotating the Cartesian X and Y axes
    by psi radians to make a new point (x2,xy).

    """
    c1 = np.cos(psi)
    c2 = np.sin(psi)
    x2 = c1 * x + c2 * y
    y2 = -c2 * x + c1 * y
    return x2, y2


def elliptical_distortion(x, y, xc, yc, psi, stretch):
    """

    This rotates the coordinates x and y by the angle
    psi radians, applies a stretch factor of stretch
    to the x axis, and rotates the coordinates back.
    A stretch factor of 1 means a perfect circle.
    The distorted coordinates are returned.

    NOTE: It is pointless calling this function when
    stretch = 1.0 since it will do nothing.

    """
    x1, y1 = rot_axis(x - xc, y - yc, psi)
    x2, y2 = rot_axis(x1 * stretch, y1, -psi)

    return x2 + xc, y2 + yc


def f(c, x, y):
    """

    Calculate the algebraic distance between the data points and the mean circle centered at c=(xc, yc)
    or the mean ellipse of parameters c=(xc, yc, psi, stretch).
    This function is used by the optimise.leastsq function.

    NOTE: Arguments x and y are numpy arrays of coordinates.

    """

    # Rotate coordinates, apply stretch, rotate back
    if len(c) == 4:
        # Ellipse. Apply an elliptical distortion to the x,y coordinates.
        xc, yc, psi, stretch = c
        xnew, ynew = elliptical_distortion(x, y, xc, yc, psi, stretch)
        Ri = calc_R(xnew, ynew, xc, yc)
    else:
        # Circle. No distortion needed.
        xc, yc = c
        Ri = calc_R(x, y, xc, yc)

    return Ri - Ri.mean()


def leastsq_circle(x, y):
    """

    Find optimised circle (or ellipse) parameters.
    An ellipse is fitted if the parameter POS_REP_EVALUATION_PARS.APPLY_ELLIPTICAL_CORRECTION is True.
    Called by fit_circle.

    Returns xc,yc of centre, radius, psi (ellipse), stretch (ellipse) and RMS radius error.

    """

    # The initial estimate of the location of the centre of the circle is
    # the coordinates of the barycenter.
    x_m = np.mean(x)
    y_m = np.mean(y)

    apply_elliptical_correction = POS_REP_EVALUATION_PARS.APPLY_ELLIPTICAL_CORRECTION

    if apply_elliptical_correction:
        # Set the starting values for x and y centre, psi, and stretch.
        # NOTE: stretch has to begin with a value that isn't 1.0 or the fitting of psi becomes unstable.
        param_estimate = x_m, y_m, 0.0, 1.01
    else:
        # Set the starting values for x and y centre
        param_estimate = x_m, y_m

    # scipy.optimize.leastsq: See https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.leastsq.html
    # f: callable function
    # param_estimate: The starting estimate for the minimization
    # args: Any extra arguments to func are placed in this tuple
    # ftol: Relative error desired in the sum of squares
    # xtol: Relative error desired in the approximate solution.
    fitted_params, ier = optimize.leastsq(
        f, param_estimate, args=(x, y), ftol=1.5e-10, xtol=1.5e-10
    )

    if apply_elliptical_correction:
        xc, yc, psi, stretch = fitted_params
        # The fitted radius is the mean distance of the distorted
        # points from the centre.
        x2, y2 = elliptical_distortion(x, y, xc, yc, psi, stretch)
        Ri = calc_R(x2, y2, xc, yc)
    else:
        xc, yc = fitted_params
        psi, stretch = 0.0, 1.0 # Default values for a circle fit.
        # The fitted radius is the mean distance of the points from the centre.
        Ri = calc_R(x, y, xc, yc)

    R = Ri.mean()
    residu = np.sum((Ri - R) ** 2)
    radius_RMS = np.sqrt(residu / len(x))

    return xc, yc, R, psi, stretch, radius_RMS


def get_weighted_coordinates(blob_coordinates, weight_factor=BLOB_WEIGHT_FACTOR):
    # Compute the weighted coordinates of the point
    # between the big and small metrology blob
    #
    # This is also used to compute error measures
    # from the datum repeatability / positional
    # repeatability, it is called in the
    # vfr.evaluation.measures module.
    blob_coordinates = np.asarray(blob_coordinates)
    assert( blob_coordinates.ndim == 2)

    coords_big_blob = blob_coordinates[:, 3:5]
    coords_small_blob = blob_coordinates[:, :2]
    weighted_coordinates = ( ( 1.0 - weight_factor ) *
                             coords_small_blob + (weight_factor *
                                                  coords_big_blob))

    # return Cartesian coordinates, by
    # inverting y axis of OpenCV image coordinates
    return weighted_coordinates * np.array([1, -1])


def cartesian_blob_position(val, weight_factor=BLOB_WEIGHT_FACTOR):
    x, y = get_weighted_coordinates([val], weight_factor=weight_factor)[0]
    return x, y


def wrap_angle_radian(angle):
    # Wraps a scalar angle to prevent it going outside the range
    # -pi to +pi.
    while angle < -pi:
       angle += 2*pi
    while angle > pi:
       angle -= 2*pi
    return angle


def normalize_difference_radian(x):
    # Keep the values contained in the array x within the range -pi to +pi.
    # Add 2*pi to elements smaller than -pi.
    # Subtract 2*pi from elements larger than +pi.
    # TODO: Should there be a while loop to account for larger deviations? 
    x = np.where(x < -pi, x + 2*pi, x)
    x = np.where(x > +pi, x - 2*pi, x)
    return x


def nominal_angle_radian(key):
    # NOTE: Nominal angle means demanded angle.
    # Convert a pair of angular coordinates from degrees to radians.
    return np.deg2rad(key[0]), np.deg2rad(key[1])


def extract_points(analysis_results):
    """ Returns (x,y) positions from image analysis and
    nominal (demanded) angles of alpha and beta arm, in radians.
    """
    nominal_coordinates_rad = []
    circle_points = []
    pos_keys = []

    for key, val in analysis_results.items():
        alpha_nom_rad, beta_nom_rad = nominal_angle_radian(key)
        x, y = cartesian_blob_position(val)

        circle_points.append((x, y))
        nominal_coordinates_rad.append((alpha_nom_rad, beta_nom_rad))
        pos_keys.append(key)

    return circle_points, nominal_coordinates_rad, pos_keys


def fit_circle(analysis_results, motor_axis):
    """

    Fit a circle or an ellipse to a set of analysis results.
    An ellipse is fitted if the parameter POS_REP_EVALUATION_PARS.APPLY_ELLIPTICAL_CORRECTION is True.

    NOTE: In Johannes' terminology, nominal coordinates are demanded coordinates.
          Real coordinates are the actual, measured coordinates.

    """
    # Get list of points to which circle is fitted. Note that extract_points
    # combines the coordinates of the large and the small metrology blobs into a
    # midpoint coordinate, so that the measurement is represented by a single point.
    circle_points, nominal_coordinates_rad, pos_keys = extract_points(analysis_results)

    # NOTE: The .T attribute selects the transposed array from an ndarray object.
    # See https://docs.scipy.org/doc/numpy/reference/generated/numpy.ndarray.html
    x_s, y_s = np.array(circle_points).T
    alpha_nominal_rad, beta_nominal_rad = np.array(nominal_coordinates_rad).T

    # << Perform least-squares fit of circle to input data. >>
    xc, yc, R, psi, stretch, radius_RMS = leastsq_circle(x_s, y_s)

    # Wrap the ellipse orientation to the range +/- pi.
    psi = wrap_angle_radian( psi )

    # TODO: logger.debug?
    print(
        "axis {}: fitted elliptical params: psi = {} degrees, stretch = {}".format(
            motor_axis, np.rad2deg(psi), stretch
        )
    )

    # << Retrieve angles relative to camera coordinates. >>
    if POS_REP_EVALUATION_PARS.APPLY_ELLIPTICAL_CORRECTION:
        # Ellipse fitted. Apply the distortion correction to the points
        x_s2, y_s2 = elliptical_distortion(x_s, y_s, xc, yc, psi, stretch)
    else:
        # Circle fitted. Use the original points.
        x_s2 = x_s
        y_s2 = y_s

    phi_real_rad, r_real = cartesian2polar(x_s2 - xc, y_s2 - yc)
    if motor_axis == "alpha":
        phi_nominal_rad = alpha_nominal_rad
    else:
        phi_nominal_rad = beta_nominal_rad

    # << Estimate the camera offset. >>
    # 04-Feb-2020: Changed from mean to median. Angle wrapping can lead to a bi-modal distribution.
    # np.mean results in an estimate in between the two modes, whereas np.median chooses one of them.
    offset_estimate = np.median(phi_real_rad - phi_nominal_rad)
    #offset_estimate = np.mean(phi_real_rad - phi_nominal_rad)
    # TODO: logger.debug?
    print(
        "axis {}: initial camera offset estimate = {} degrees".format(
            motor_axis, np.rad2deg(offset_estimate)
        )
    )

    # << Return the result. >>
    result = {
        "xc": xc,                               # Coordinates of the
        "yc": yc,                               # centre point.
        "R": R,                                 # Radius found.
        "psi": psi,                             # Elliptical orientation (radians)
        "stretch": stretch,                     # Eliiptical "stretch" factor.
        "radius_RMS": radius_RMS,               # Error estimate of fitted radius.
        "x_s": x_s,                             # Input data
        "y_s": y_s,                             #
        "x_s2": x_s2,                           # Input data after distortion correction.
        "y_s2": y_s2,                           # (if elliptical fitting turned on)
        "pos_keys": pos_keys,                   # Iteration parameters for measurement.
        "alpha_nominal_rad": alpha_nominal_rad, # Nominal (demanded) alpha position.
        "beta_nominal_rad": beta_nominal_rad,   # Nominal (demanded) beta position.
        "offset_estimate": offset_estimate,     # Estimated camera rotation offset.
    }
    return result


def wrap_complex_vals(angles):

    # Wrap the values in the array to prevent them going below -pi/4.0
    # Add 2*pi to elements smaller than -pi/4.0.
    # Leave other elements the same.
    return np.where(angles < -pi/4.0, angles + 2*pi, angles)


def angle_to_point(
    alpha_nom_rad,
    beta_nom_rad,
    P0=None,
    R_alpha=None,
    R_beta_midpoint=None,
    camera_offset_rad=None,
    beta0_rad=None,
    inverse=False,
    coeffs=None,
    broadcast=True,
    correct_axis=["alpha", "beta"],
    correct_fixpoint=True,
):
    """

    Convert nominal angles with a given pair of offsets to expected
    coordinate in the image plane. The function carries out the inverse
    of a circle fit, transforming points back to Cartesian coordinates.

    alpha_nom_rad and beta_nom_rad can be arrays or scalars.

    So, basically, angle_to_point() applies the camera offset to the angles,
    and computes the (x,y) point in the Cartesian plane which corresponds
    to the nominal angles. Because the fitting procedure minimizes the error
    it minimizes the distance between these points and the actually measured
    points, and with this it finds the right camera offset.

    NOTE: In Johannes' terminology, nominal coordinates are demanded coordinates.
          Real coordinates are the actual, measured coordinates.

    """

    if coeffs is None:
        # Extremely verbose diagnostic.
        #print("angle_to_point: NO gearbox coefficients. Gearbox correction skipped.")
        delta_alpha = 0.0
        delta_beta = 0.0
        delta_alpha_fixpoint = 0.0
        delta_beta_fixpoint = 0.0
    else:
        # Extremely verbose diagnostic.
        #if inverse:
        #    print("angle_to_point: INVERSE gearbox correction applied.")
        #else:
        #    print("angle_to_point: NORMAL gearbox correction applied.")

        if "alpha" in correct_axis:

            # Here the gearbox distortion function (the inverse of the correction
            # function) is applied to alpha.
            delta_alpha = -alpha_nom_rad + apply_gearbox_parameters(
                alpha_nom_rad,
                wrap=True,
                inverse_transform=inverse,
                **coeffs["coeffs_alpha"]
            )

            alpha_fixpoint_rad = coeffs["coeffs_beta"]["alpha_fixpoint_rad"]
            delta_alpha_fixpoint = -alpha_fixpoint_rad + apply_gearbox_parameters(
                alpha_fixpoint_rad,
                wrap=True,
                inverse_transform=inverse,
                **coeffs["coeffs_alpha"]
            )
        else:
            delta_alpha = 0
            delta_alpha_fixpoint = 0

        if "beta" in correct_axis:
            # Here the gearbox distortion function (the inverse of the correction
            # function) is applied to beta.
            delta_beta = -beta_nom_rad + apply_gearbox_parameters(
                beta_nom_rad,
                wrap=True,
                inverse_transform=inverse,
                **coeffs["coeffs_beta"]
            )

            beta_fixpoint_rad = coeffs["coeffs_alpha"]["beta_fixpoint_rad"]
            delta_beta_fixpoint = -beta_fixpoint_rad + apply_gearbox_parameters(
                beta_fixpoint_rad,
                wrap=True,
                inverse_transform=inverse,
                **coeffs["coeffs_alpha"]
            )
        else:
            delta_beta = 0
            delta_beta_fixpoint = 0

        if not correct_fixpoint:
            delta_alpha_fixpoint = 0
            delta_beta_fixpoint = 0

    # Rotate (possibly corrected) angles to camera orientation,
    # and apply beta arm offset
    alpha_rad = alpha_nom_rad + camera_offset_rad
    beta_rad = beta_nom_rad + beta0_rad

    # Add difference to alpha when the beta
    # correction was measured (these angles add up
    # because when the alpha arm is turned (clockwise),
    # this turns the beta arm (clockwise) as well).
    gamma_rad = beta_rad + alpha_rad + (delta_alpha - delta_alpha_fixpoint)

    vec_alpha = np.array(
        polar2cartesian(alpha_rad + (delta_alpha - delta_alpha_fixpoint), R_alpha)
    )
    vec_beta = np.array(
        polar2cartesian(gamma_rad + (delta_beta - delta_beta_fixpoint), R_beta_midpoint)
    )

    # << Bring P0 into broadcastable form. >>
    # The angle_to_point function can be called with both vector and scalar
    # arguments. The shape of the constant P0 is adapted automatically so
    # it can be added without a broadcasting error.
    if broadcast and (len(P0.shape) < len(vec_alpha.shape)):
        # adapt shape
        P0 = np.reshape(P0, P0.shape + (1,))

    expected_point = P0 + vec_alpha + vec_beta

    return expected_point


def get_angle_error(
    x_s2,
    y_s2,
    xc,
    yc,
    alpha_nominal_rad,
    beta_nominal_rad,
    P0=None,
    R_alpha=None,
    R_beta_midpoint=None,
    camera_offset_rad=None,
    beta0_rad=None,
):
    """

    The function get_angle_error() computes the differences between the angles
    which would be expected between the nominal (demanded) angles and the real
    (measured) angles. For this, the angles are converted to polar coordinates
    and the difference between nominal and real polar coordinates is computed.

    """
    # TODO: logger.debug?
    print("get_angle_error: center (x,y) = ({},{}) millimeter".format(xc, yc))

    # << Get place vectors of measured points. >>
    # This computes the place vectors of the measured points relative
    # to the circle origin, i.e. a vector from the centre of the
    # circle to that point.
    x_real = x_s2 - xc
    y_real = y_s2 - yc

    # << Compute expected points. >>
    # Compute expected Cartesian points from common fit parameters.
    # The points expected from the nominal angles are computed
    # using the angle_to_point function. This might look more
    # complicated than needed, but one of the advantages of
    # using this function is that it includes both camera offset
    # and the beta zero point.
    #
    # NOTE: angle_to_point takes a coeffs parameter which defaults to None.
    # Not specifying a coeffs parameter means no gearbox calibration
    # coefficients are applied when converting an angle to a point.
    x_n, y_n = angle_to_point(
        alpha_nominal_rad,
        beta_nominal_rad,
        P0=P0,
        R_alpha=R_alpha,
        R_beta_midpoint=R_beta_midpoint,
        camera_offset_rad=camera_offset_rad,
        beta0_rad=beta0_rad,
        broadcast=True,
    )

    # << Compute expected nominal points. >>
    # The nominal points in the Cartesian plane are transformed
    # into place vectors.
    x_fitted = x_n - xc
    y_fitted = y_n - yc

    # << Compute angular difference. >>
    # Compute the remaining difference in the complex plane.
    # Now both sets of points are converted to polar coordinates.
    # Complex notation is used because it makes the next step easier.
    points_real = x_real + 1j * y_real
    points_fitted = x_fitted + 1j * y_fitted

    # compute _residual_ offset of fitted - real
    # (no unwrapping needed because we use the complex domain)
    #
    # note, the alpha0 / beta0 values are not included
    # (camera_offset is considered to be specific to the camera)
    angular_difference = np.log(points_real / points_fitted).imag

    # << Compute phase-wrapped real and nominal values. >>
    # Finally, the nominal and real input angles are converted
    # to a phase-wrapped representation.
    phi_fitted_rad = wrap_complex_vals(np.log(points_fitted).imag)
    phi_real_rad = wrap_complex_vals(np.log(points_real).imag)

    return phi_real_rad, phi_fitted_rad, angular_difference


def fit_gearbox_parameters(
    motor_axis,
    circle_data,
    P0=None,
    R_alpha=None,
    R_beta_midpoint=None,
    camera_offset_rad=None,
    beta0_rad=None,
    return_intermediate_results=False,
):
    """

    Fit the gearbox parameters.

    """

    # << Retrieve constants from the circle fit data. >>
    x_s = circle_data["x_s"]
    y_s = circle_data["y_s"]
    x_s2 = circle_data["x_s2"]
    y_s2 = circle_data["y_s2"]

    psi = circle_data["psi"]
    stretch = circle_data["stretch"]

    xc = circle_data["xc"]
    yc = circle_data["yc"]

    alpha_nominal_rad = circle_data["alpha_nominal_rad"]
    beta_nominal_rad = circle_data["beta_nominal_rad"]

    # << Define fixpoints of fit. >>
    # The fixpoints (fixed points) are the angles where one arm was moved and
    # the other was held fixed. This independence of movement is necessary to
    # analyse the measured data. We get the fixpoint values from computing the
    # mean of the non-changed coordinate and storing it.
    if motor_axis == "beta":
        # Common angle for beta measurements
        alpha_fixpoint_rad = np.mean(alpha_nominal_rad)
        beta_fixpoint_rad = np.NaN
        # TODO: logger.debug?
        print("fit_gearbox_parameters: alpha fixpoint = {} degree".format(np.rad2deg(alpha_fixpoint_rad)))
    else:
        alpha_fixpoint_rad = np.NaN
        beta_fixpoint_rad = np.mean(beta_nominal_rad)
        # TODO: logger.debug?
        print("fit_gearbox_parameters: beta fixpoint = {} degree".format(np.rad2deg(beta_fixpoint_rad)))
    _, R_real = cartesian2polar(x_s2 - xc, y_s2 - yc)

    # TODO: logger.debug?
    print(
        "fit_gearbox_parameters(): finding angular error for {} arm ".format(motor_axis)
    )

    # << Get angular error between nominal and measured angles. >>
    # get_angle_error returns the deviation between measured (real) and nominal
    # angle. Because we have offsets for the camera, we can match the measured
    # coordinate to the nominal value.
    #
    # phi_real_rad is the angle of the measured point, relative to the fitted
    # circle centre.
    #
    # phi_fitted_rad is the nominal angle of the measurement, also relative to the
    # fitted circle centre *and* the camera offset.
    #
    # err_phi_1_rad is the error between the real and nominal angle.
    #
    # All angles are relative to a specific polar coordinate system/
    phi_real_rad, phi_fitted_rad, err_phi_1_rad = get_angle_error(
        x_s2,
        y_s2,
        xc,
        yc,
        alpha_nominal_rad,
        beta_nominal_rad,
        P0=P0,
        R_alpha=R_alpha,
        R_beta_midpoint=R_beta_midpoint,
        camera_offset_rad=camera_offset_rad,
        beta0_rad=beta0_rad,
    )

    # << Compute support points for linear least squares fit. >>
    # Here the values phi_fitted_rad etc... represent the angles
    # *after the camera offset was fitted to the measured data*.
    # The average remaining error between nominal and real values
    # is the gearbox distortion function.
    #
    # The next step uses a further least-squares fitting procedure
    # which takes the average from several measured points taken
    # for the same nominal angle. For each nominal angle there are
    # two or more observed data points. The following statements
    # create a mapping from nominal to observed data points.
    # The key of the map is phi_fit_support_rad, which is the
    # nominal (demanded) angle.
    # The value of the map is a list of different error angles,
    # err_phi_1_rad, which represent the difference or "gearbox
    # error".
    support_points = {}
    for (fitted_angle, yp) in zip(phi_fitted_rad, err_phi_1_rad):
        if fitted_angle not in support_points:
            support_points[fitted_angle] = []
        support_points[fitted_angle].append(yp)

    # Nominal angles are sorted.
    phi_fit_support_rad = np.array(sorted(support_points.keys()))

    # Then we compute the mean value of the observed data.
    # The array phi_cor_support_rad is the input for the linear
    # interpolation. For each "x" value of phi_fitted_rad, it
    # contains the corresponding "y" or "corrected" value
    # corresponding to y = g(x), where g() is the gearbox distortion
    # function.
    phi_corr_support_rad = [
        np.mean(np.array(support_points[k])) for k in phi_fit_support_rad
    ]

    # For the error, an additional computational step is needed to
    # compute a normalized error angle. The function ensures the
    # values remain within the range -pi to +pi.
    err_phi_support_rad = normalize_difference_radian(
        err_phi_1_rad
        - np.interp(
            phi_fitted_rad, phi_fit_support_rad, phi_corr_support_rad, period=2 * pi
        )
    )

    # << Compute calibration tables. >>
    phi_fitted_correction_rad = phi_fitted_rad + np.interp(
        phi_fitted_rad, phi_fit_support_rad, phi_corr_support_rad, period=2 * pi
    )

    ## Combine first and second order fit, to get an invertible function
    corrected_shifted_angle_rad = np.array(phi_corr_support_rad) + phi_fit_support_rad

    # TODO: logger.debug?
    print(
        "fit_gearbox_parameters(): beta0_rad = {} rad = {} degree".format(
            beta0_rad, np.rad2deg(beta0_rad)
        )
    )
    print(
        "fit_gearbox_parameters(): beta0_rad - pi = {} rad = {} degree".format(
            beta0_rad - pi, 360 + np.rad2deg(beta0_rad - pi)
        )
    )


    # Using the mean error angles, we then define the interpolation tables.
    # To get an invertible function, the interpolation input must defin a
    # strictly monotonic function, so we add the function.
    #
    #   y = f(x) = x
    #
    # to it, which makes it monotonic. Also we subtract the camera offset,
    # since this is purely a property of the measurement system, not the FPUs.
    # The resulting arrays, nominal_angle_rad (which keeps the nominal values)
    # and corrected_angle_rad (which holds the real value of the gearbox position)
    # are the calibration tables. We need to subtract the camerqa offset to
    # make the tables independent of the camera orientation.
    if motor_axis == "alpha":
        nominal_angle_rad = phi_fit_support_rad - camera_offset_rad
        corrected_angle_rad = corrected_shifted_angle_rad - camera_offset_rad
    else:
        nominal_angle_rad = phi_fit_support_rad - beta0_rad - camera_offset_rad - pi
        corrected_angle_rad = (
            corrected_shifted_angle_rad - beta0_rad - camera_offset_rad - pi
        )

    # TODO: logger.debug?
    print(
        "for axis {}: mean(corrected - nominal) = {} degrees".format(
            motor_axis, np.rad2deg(np.mean(corrected_angle_rad - nominal_angle_rad))
        )
    )

    # Pad table support points with values for the ends of the range.
    # This is especially needed since the support points which are
    # used in the control plot, are outside the fitted range,
    # and without these padding values, the result of the
    # gearbox interpolation would be off to the first defined point.
    #
    # As final step, we need to make sure that the calibration table has
    # meaningful results for input values outside the measurement range
    # (towards the upper and lower end of the range of movement).
    # We extend the data by assuming the real value is equal to the
    # corresponding nominal value.
    phi_min = np.deg2rad(-185)
    phi_max = np.deg2rad(+185)
    nominal_angle_rad = np.hstack([[phi_min], nominal_angle_rad, [phi_max]])
    corrected_angle_rad = np.hstack([[phi_min], corrected_angle_rad, [phi_max]])

    # << Assemble the results dictionary. >>
    results = {
        "algorithm": "linfit+piecewise_interpolation",
        "xc": xc,
        "yc": yc,
        "R": circle_data["R"],
        "P0": P0,
        "R_alpha": R_alpha,
        "psi": psi,
        "stretch": stretch,
        "radius_RMS": circle_data["radius_RMS"],
        "R_beta_midpoint": R_beta_midpoint,
        "camera_offset_rad": camera_offset_rad,
        "beta0_rad": beta0_rad,
        "alpha_fixpoint_rad": alpha_fixpoint_rad,
        "beta_fixpoint_rad": beta_fixpoint_rad,
        "num_support_points": len(phi_fit_support_rad),
        "num_data_points": len(x_s2),
        "nominal_angle_rad": nominal_angle_rad,
        "corrected_angle_rad": corrected_angle_rad,
        "alpha_nominal_rad": circle_data["alpha_nominal_rad"],
        "beta_nominal_rad": circle_data["beta_nominal_rad"],
        "x_s2": x_s2,
        "y_s2": y_s2,
    }

    if return_intermediate_results:

        extra_results = {
            "x_s": x_s,
            "y_s": y_s,
            "phi_fitted_rad": phi_fitted_rad,
            "phi_fit_support_rad": phi_fit_support_rad,
            "corrected_shifted_angle_rad": corrected_shifted_angle_rad,
            "R_real": R_real,
            "yp": phi_corr_support_rad,
            "pos_keys": circle_data["pos_keys"],
            "err_phi_support_rad": err_phi_support_rad,
            "fits": {
                0: (
                    phi_fitted_rad,
                    phi_real_rad,
                    "real angle as function of c-rotated nominal angle",
                ),
                1: (
                    phi_fitted_rad,
                    phi_fitted_rad,
                    "first-order fitted, c-rotated angle as function of fitted, c-rotated nominal angle",
                ),
                2: (
                    phi_fitted_rad,
                    phi_fitted_correction_rad,
                    "second-order fitted, c-rotated angle as function of fitted, c-rotated nominal angle",
                ),
            },
            "residuals": {
                1: (
                    phi_fitted_rad,
                    err_phi_1_rad,
                    "first-order residual angle as function of fitted, c-rotated nominal angle",
                ),
                2: (
                    phi_fitted_rad,
                    err_phi_support_rad,
                    "second-order residual angle as function of fitted, c-rotated nominal angle",
                ),
            },
        }

        results.update(extra_results)

    return results


def fit_offsets(
    circle_alpha,
    circle_beta,
    P0=None,
    R_alpha=None,
    R_beta_midpoint=None,
    camera_offset_start=None,
    beta0_start=None,
):
    """

    The goal of this function is to find the best matching global
    offset between nominal coordinates and camera coordinates
    for both alpha and beta arm. This offset is assumed
    to be caused by the camera orientation.

    This is done by computing the image points from the nominal
    coordinates with a variable offset, and minimizing for the
    distance to the actual measured points.

    """

    # << Gather data for fitting step. >>
    # NOTE: Both the nominal coordinates, and the measured values, need to be captured
    # in ordered collections because, unlike the circle fitting, the g function
    # needs to compare coordinates from both representations directly.
    circle_points = []
    nominal_coordinates_rad = []

    for c in circle_alpha, circle_beta:
        for x_s2, y_s2 in zip(c["x_s2"], c["y_s2"]):
            circle_points.append((x_s2, y_s2))
        for alpha_nom, beta_nom in zip(c["alpha_nominal_rad"], c["beta_nominal_rad"]):
            nominal_coordinates_rad.append((alpha_nom, beta_nom))

    circle_points = np.array(circle_points).T
    alpha_nom_rad, beta_nom_rad = np.array(nominal_coordinates_rad).T

    # << Fit offsets so that the difference between nominal (demanded) and
    # real (measured) points is minimal. >>
    #
    # NOTE: angle_to_point takes a coeffs parameter which defaults to None.
    # Not specifying a coeffs parameter means no gearbox calibration
    # coefficients are applied when converting an angle to a point.
    def g(offsets):
        # This function is used by the optimise.leastsq function.
        camera_offset, beta0 = offsets
        points = angle_to_point(
            alpha_nom_rad,
            beta_nom_rad,
            P0=P0,
            R_alpha=R_alpha,
            R_beta_midpoint=R_beta_midpoint,
            camera_offset_rad=camera_offset,
            beta0_rad=beta0,
        )
        # See https://docs.scipy.org/doc/numpy/reference/generated/numpy.linalg.norm.html
        return np.linalg.norm(points - circle_points, axis=0)

    # Coordinates of the barycenter
    # scipy.optimize.leastsq: See https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.leastsq.html
    # g: callable function
    # offsets_estimate: The starting estimate for the minimization
    # ftol: Relative error desired in the sum of squares
    # xtol: Relative error desired in the approximate solution.
    offsets_estimate = np.array([camera_offset_start, beta0_start])
    offsets, ier = optimize.leastsq(g, offsets_estimate, ftol=1.5e-10, xtol=1.5e-10)
    camera_offset, beta0 = offsets

    # TODO: logger.debug?
    print(
        "fit_offset: fitted camera offset = {} degree. beta0 = {} degree".format(np.rad2deg(camera_offset), np.rad2deg(beta0))
    )
    print("fit_offset: mean norm from offset fitting = ", np.mean(g(offsets)))

    return camera_offset, beta0


def get_expected_points(
    fpu_id,
    coeffs,
    R_alpha=None,
    R_beta_midpoint=None,
    camera_offset_rad=None,
    beta0_rad=None,
    P0=None,
    return_points=False,
):
    """

    A generator which yields expected points.

    The expected points are result of a transformation which is dirent from
    the correction function. We obtain them by applying the gearbox distortion
    function to the nominal values, and then converting the points to the
    Cartesian plane, using the function angle_to_point(). If the gearbox is
    modeled correctly, we would expect to yield points which are close to the
    measured points in the Cartesian plane, except for any non-systematic
    residual error.

    Used by plot_expected_vs_measured_points.

    """
    logger = logging.getLogger(__name__)
    logger.info("get_expected_points: Computing gearbox calibration error")

    expected_vals = {}

    for lcoeffs, motor_axis in [
        (coeffs["coeffs_alpha"], "alpha"),
        (coeffs["coeffs_beta"], "beta"),
    ]:
        logger.info(
            "FPU {}: evaluating correction for {} motor axis".format(fpu_id, motor_axis)
        )
        xc = lcoeffs["xc"]
        yc = lcoeffs["yc"]
        x_s = lcoeffs["x_s2"]
        y_s = lcoeffs["y_s2"]
        R = lcoeffs["R"]
        alpha_nominal_rad = lcoeffs["alpha_nominal_rad"]
        beta_nominal_rad = lcoeffs["beta_nominal_rad"]

        alpha_nom_corrected_rad = apply_gearbox_parameters(
            alpha_nominal_rad,
            wrap=True,
            inverse_transform=True,
            **coeffs["coeffs_alpha"]
        )
        beta_nom_corrected_rad = apply_gearbox_parameters(
            beta_nominal_rad, wrap=True, inverse_transform=True, **coeffs["coeffs_beta"]
        )

        logger.info(
            "FPU {}: for axis {}: mean(corrected - nominal) = {} degrees".format(
                fpu_id,
                "alpha",
                np.rad2deg(np.mean(alpha_nom_corrected_rad - alpha_nominal_rad)),
            )
        )
        logger.info(
            "FPU {}: for axis {}: mean(corrected - nominal) = {} degrees".format(
                fpu_id,
                "beta",
                np.rad2deg(np.mean(beta_nom_corrected_rad - beta_nominal_rad)),
            )
        )

        alpha_fixpoint_rad = lcoeffs["alpha_fixpoint_rad"]
        beta_fixpoint_rad = lcoeffs["beta_fixpoint_rad"]
        alpha_fixpoint_corrected_rad = apply_gearbox_parameters(
            alpha_fixpoint_rad,
            wrap=True,
            inverse_transform=True,
            **coeffs["coeffs_alpha"]
        )
        beta_fixpoint_corrected_rad = apply_gearbox_parameters(
            beta_fixpoint_rad,
            wrap=True,
            inverse_transform=True,
            **coeffs["coeffs_beta"]
        )

        logger.info(
            "FPU {}: for axis {}: mean(corrected - fixpoint) = {}".format(
                fpu_id,
                "alpha",
                np.rad2deg(np.mean(alpha_fixpoint_corrected_rad - alpha_fixpoint_rad)),
            )
        )
        logger.info(
            "FPU {}: for axis {}: mean(corrected - fixpoint) = {}".format(
                fpu_id,
                "beta",
                np.rad2deg(np.mean(beta_fixpoint_corrected_rad - beta_fixpoint_rad)),
            )
        )

        # << Convert nominal angles to expected points. >>
        # Here the function angle_to_point() is called again, but this time the
        # fitted gearbox calibration coefficients are passed, along with the
        # flag inverse=True (which tells it to apply the inverse transformation).
        expected_points = []
        for alpha_nom_rad, beta_nom_rad in zip(alpha_nominal_rad, beta_nominal_rad):

            ep = angle_to_point(
                alpha_nom_rad,
                beta_nom_rad,
                P0=P0,
                R_alpha=R_alpha,
                R_beta_midpoint=R_beta_midpoint,
                camera_offset_rad=camera_offset_rad,
                beta0_rad=beta0_rad,
                inverse=True,
                coeffs=coeffs,
                # correct_axis=[motor_axis],
                # correct_fixpoint=False,
                broadcast=False,
            )

            expected_points.append(ep)

        expected_points = np.array(expected_points).T
        measured_points = np.array((x_s, y_s))
        xe, ye = expected_points
        # See https://docs.scipy.org/doc/numpy/reference/generated/numpy.linalg.norm.html
        error_magnitudes = np.linalg.norm(expected_points - measured_points, axis=0)
        RMS = np.sqrt(np.mean(error_magnitudes ** 2)) * 1000
        max_val = np.max(error_magnitudes * 1000)
        percentile_vals = np.percentile(error_magnitudes * 1000, PERCENTILE_ARGS)

        logger.info("FPU {}: RMS [{}] = {} micron".format(fpu_id, motor_axis, RMS))
        pcdict = {PERCENTILE_ARGS[k]: pv for k, pv in enumerate(percentile_vals)}
        logger.info(
            "FPU {}: percentiles = {} microns".format(
                fpu_id,
                ", ".join(
                    ["P[%s]: %.1f" % (k, pcdict[k]) for k in sorted(pcdict.keys())]
                ),
            )
        )
        axis_result = {"RMS": RMS, "pcdict": pcdict, "max_val": max_val}

        if return_points:
            # include extra results for plotting
            axis_result.update(
                {
                    "xc": xc,
                    "yc": yc,
                    "R": R,
                    "expected_points": expected_points,
                    "measured_points": measured_points,
                    "x_s": x_s,
                    "y_s": y_s,
                    "xe": xe,
                    "ye": ye,
                }
            )

        expected_vals[motor_axis] = axis_result

    return expected_vals


def fit_gearbox_correction(
    fpu_id,
    dict_of_coordinates_alpha,
    dict_of_coordinates_beta,
    return_intermediate_results=False,
):
    """Computes gearbox correction and returns correction coefficients
    as a dictionary.


    Input is a dictionary. The keys of the dictionary
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

    The units are in degrees (for alpha_steps and beta_steps)
    and millimeter (for x_measured and y_measured).

    """
    logger = logging.getLogger(__name__)
    logger.info("Fitting gearbox correction for FPU %s." % str(fpu_id))

    # << Fit circles to the alpha and beta arm points >>
    logger.debug("Fitting alpha and beta circles...")
    circle_alpha = fit_circle(dict_of_coordinates_alpha, "alpha")
    circle_beta = fit_circle(dict_of_coordinates_beta, "beta")

    # Find centers of alpha circle
    x_center = circle_alpha["xc"]
    y_center = circle_alpha["yc"]
    P0 = np.array([x_center, y_center])
    logger.debug("Alpha circle centre (%f, %f)." % (x_center, y_center))
    logger.debug("Alpha circle distortion: psi=%f (rad), stretch=%f." % (circle_alpha["psi"], circle_alpha["stretch"]))

    # Find center of beta circles
    x_center_beta = circle_beta["xc"]
    y_center_beta = circle_beta["yc"]
    Pcb = np.array([x_center_beta, y_center_beta])
    logger.debug("Beta circle centre (%f, %f)." % (x_center_beta, y_center_beta))
    logger.debug("Beta circle distortion: psi=%f (rad), stretch=%f." % (circle_beta["psi"], circle_beta["stretch"]))

    # Radius of alpha arm is distance from P0 to Pcb
    # See https://docs.scipy.org/doc/numpy/reference/generated/numpy.linalg.norm.html
    R_alpha = np.linalg.norm(Pcb - P0)
    # radius from beta center to weighted midpoint between metrology targets
    R_beta_midpoint = circle_beta["R"]
    logger.debug("Radius of alpha arm: %f (mm)" % R_alpha)
    logger.debug("Radius to beta metrology mid-point: %f (mm)" % R_beta_midpoint)

    # << Fit offsets of camera orientation >>
    camera_offset_start = circle_alpha["offset_estimate"]
    beta0_start = circle_beta["offset_estimate"] + camera_offset_start

    r2d = np.rad2deg
    # TODO: logger.debug?
    print(
        "camera_offset_start =", camera_offset_start,
        "radian = {} degree".format(r2d(camera_offset_start)),
    )
    print("beta0_start =", beta0_start, "radian = {} degree".format(r2d(beta0_start)))

    camera_offset_rad, beta0_rad = fit_offsets(
        circle_alpha,
        circle_beta,
        P0=P0,
        R_alpha=R_alpha,
        R_beta_midpoint=R_beta_midpoint,
        camera_offset_start=camera_offset_start,
        beta0_start=beta0_start,
    )

    # << Fit calibration tables for alpha and beta arm >>
    logger.debug("Fitting gearbox parameters to alpha points.")
    coeffs_alpha = fit_gearbox_parameters(
        "alpha",
        circle_alpha,
        P0=P0,
        R_alpha=R_alpha,
        R_beta_midpoint=R_beta_midpoint,
        camera_offset_rad=camera_offset_rad,
        beta0_rad=beta0_rad,
        return_intermediate_results=return_intermediate_results,
    )

    logger.debug("Fitting gearbox parameters to beta points.")
    coeffs_beta = fit_gearbox_parameters(
        "beta",
        circle_beta,
        P0=P0,
        R_alpha=R_alpha,
        R_beta_midpoint=R_beta_midpoint,
        camera_offset_rad=camera_offset_rad,
        beta0_rad=beta0_rad,
        return_intermediate_results=return_intermediate_results,
    )

    # << Check for missing result and return early in that case >>
    if (coeffs_alpha is None) or (coeffs_beta is None):
        return {
            "version": GEARBOX_CORRECTION_VERSION,
            "coeffs": {"coeffs_alpha": coeffs_alpha, "coeffs_beta": coeffs_beta},
        }

    # TODO: logger.debug?
    print(
        "camera_offset_rad =", camera_offset_rad,
        "= {} degree".format(r2d(camera_offset_rad)),
    )
    print("beta0_rad =", beta0_rad, "= {} degree".format(r2d(beta0_rad)))

    coeffs = {"coeffs_alpha": coeffs_alpha, "coeffs_beta": coeffs_beta}
    logger.debug("coeffs_alpha: %s" % str(coeffs_alpha))
    logger.debug("coeffs_beta: %s" % str(coeffs_beta))

    P0 = np.array([x_center, y_center])

    # << Produce or delete extra diagnostic values >>
    expected_vals = get_expected_points(
        fpu_id,
        coeffs,
        R_alpha=R_alpha,
        R_beta_midpoint=R_beta_midpoint,
        camera_offset_rad=camera_offset_rad,
        beta0_rad=beta0_rad,
        P0=P0,
    )

    # If intermediate results are not needed, remove them from the
    # database to save space. (These values are useful for plotting
    # but can create a record too large for the LMDB to handle.
    if not return_intermediate_results:
        # Delete some data to save space in
        # the database record.
        for axis in ["coeffs_alpha", "coeffs_beta"]:
            for del_key in ["alpha_nominal_rad", "beta_nominal_rad", "x_s2", "y_s2"]:
                del coeffs[axis][del_key]

    # << Return resulting coefficients >>
    return {
        "version": GEARBOX_CORRECTION_VERSION,    # Algorithm version.
        "coeffs": coeffs,                         # Looking tables for alpha and beta
        "x_center": x_center,                     # Centre point of
        "y_center": y_center,                     # the alpha arm axis.
        "camera_offset_rad": camera_offset_rad,
        "beta0_rad": beta0_rad,
        "R_alpha": R_alpha,                       # The length of the alpha arm.
        "R_beta_midpoint": R_beta_midpoint,       # Distance from beta axis to target midpoint.
        "BLOB_WEIGHT_FACTOR": BLOB_WEIGHT_FACTOR, # Weighting between target blobs.
        "expected_vals": expected_vals,           # Values generated when applying correction
                                                  # to actual measured data.
    }


def apply_gearbox_parameters_fitted(
    angle_rad,
    phi_fit_support_rad=None,
    corrected_shifted_angle_rad=None,
    algorithm=None,
    inverse_transform=False,
    wrap=False,
    **rest_coeffs
):
    """

    Applies gearbox parameters to the fitted, c-rotated (rotated) angle
    (instead of the FPU coordinates).
    This function is used for both the alpha and beta coordinate.

    * The function checks that the coecients match the algorithm it
      implements.

    * It has a flag that allows to invert the transform - that is, convert
      nominal coordinates to real coordinates. We will later see what this
      is good for, it is used in producing and plotting the correction
      coeffients.

    * It also has a flag which allows to wrap the angles, using Euler's
      formula. This flag is off by default.

    * The core correction is performed by calling np.interp(), which
      implements a piece-wise linear interpolation. This linear
      interpolation is a core operation which also needs to be
      implemented in the C++ interface.

    """

    assert (
        algorithm == "linfit+piecewise_interpolation"
    ), "no matching algorithm -- repeat fitting"

    phi_fit_support_rad = np.array(phi_fit_support_rad, dtype=float)
    corrected_shifted_angle_rad = np.array(corrected_shifted_angle_rad, dtype=float)

    if inverse_transform:
        x_points = phi_fit_support_rad
        y_points = corrected_shifted_angle_rad
    else:
        x_points = corrected_shifted_angle_rad
        y_points = phi_fit_support_rad

    # wrap in the same way as we did with the fit
    if wrap:
        angle_rad = wrap_complex_vals(np.log(np.exp(1j * angle_rad)).imag)

    # phi_corrected = np.interp(angle_rad, x_points, y_points, period=2 * pi)
    phi_corrected = np.interp(angle_rad, x_points, y_points)

    return phi_corrected


def apply_gearbox_parameters(
    angle_rad,
    nominal_angle_rad=None,
    corrected_angle_rad=None,
    algorithm=None,
    inverse_transform=False,
    wrap=False,
    **rest_coeffs
):

    assert (
        algorithm == "linfit+piecewise_interpolation"
    ), "no matching algorithm -- repeat fitting"

    nominal_angle_rad = np.array(nominal_angle_rad, dtype=float)
    corrected_angle_rad = np.array(corrected_angle_rad, dtype=float)

    if inverse_transform:
        x_points = nominal_angle_rad
        y_points = corrected_angle_rad
    else:
        x_points = corrected_angle_rad
        y_points = nominal_angle_rad

    # do not wrap, or shift by offset first!
    # (the nominal angle is not subject to camera rotation)

    phi_corrected = np.interp(angle_rad, x_points, y_points)

    return phi_corrected


# ----------------------------------------------------------------------------
def apply_gearbox_correction(incoords_rad, coeffs=None):
    """

    The main gearbox correction function.

    incoords_rad is a 2-tuple with the desired real (actual) input coordinates.

    The coeffs parameter holds the coefficients which define the correction
    function. These are produced by the fit_gearbox_correction function.

    """
    assert (coeffs is not None), "apply_gearbox_correction: No gearbox correction coefficients provided."

    logger = logging.getLogger(__name__)
    logger.info("Applying gearbox correction.")

    alpha_angle_rad, beta_angle_rad = incoords_rad
    coeffs_alpha = coeffs["coeffs_alpha"]
    coeffs_beta = coeffs["coeffs_beta"]

    # Transform from desired / real angle to required nominal (uncalibrated) angle
    if  POS_REP_EVALUATION_PARS.APPLY_GEARBOX_CORRECTION_ALPHA:
        alpha_corrected_rad = apply_gearbox_parameters(alpha_angle_rad, **coeffs_alpha)
    else:
        alpha_corrected_rad = alpha_angle_rad

    if  POS_REP_EVALUATION_PARS.APPLY_GEARBOX_CORRECTION_BETA:
        beta_corrected_rad = apply_gearbox_parameters(beta_angle_rad, **coeffs_beta)
    else:
        beta_corrected_rad = beta_angle_rad

    # Transform from nominal (uncalibrated) angle to steps
    alpha_steps = int(
        round((alpha_corrected_rad - ALPHA_DATUM_OFFSET_RAD) * StepsPerRadianAlpha)
    )
    beta_steps = int(
        round((beta_corrected_rad - BETA_DATUM_OFFSET_RAD) * StepsPerRadianBeta)
    )

    return (alpha_steps, beta_steps)
