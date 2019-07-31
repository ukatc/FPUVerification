# -*- coding: utf-8 -*-
from __future__ import division, print_function

from math import pi
import numpy as np
import warnings
import functools
# import matplotlib.pyplot as plt

# import numpy as np
from scipy import optimize
from matplotlib import pyplot as plt

from fpu_constants import (
    ALPHA_DATUM_OFFSET_RAD,
    BETA_DATUM_OFFSET_RAD,
    StepsPerRadianAlpha,
    StepsPerRadianBeta,
)
from vfr.conf import BLOB_WEIGHT_FACTOR, POS_REP_EVALUATION_PARS, PERCENTILE_ARGS

# exceptions which are raised if image analysis functions fail


class GearboxFitError(Exception):
    pass


# version number for gearbox correction algorithm
# (each different result for the same data
# should yield a version number increase)

GEARBOX_CORRECTION_VERSION = (5, 0, 0)

# minimum version for which this code works
# and yields a tolerable result
GEARBOX_CORRECTION_MINIMUM_VERSION = (5, 0, 0)

def cartesian2polar(x, y):
    rho = np.sqrt(x ** 2 + y ** 2)
    phi_rad = np.arctan2(y, x)
    return (phi_rad, rho)


def polar2cartesian(phi_rad, rho):
    x = rho * np.cos(phi_rad)
    y = rho * np.sin(phi_rad)
    return (x, y)


def calc_R(x, y, xc, yc):
    """ calculate the distance of each 2D points from the center (xc, yc) """
    return np.sqrt((x - xc) ** 2 + (y - yc) ** 2)

def rot_axis(x, y, psi):
    c1 = np.cos(psi)
    c2 = np.sin(psi)
    x2 = c1 * x + c2 * y
    y2 = - c2 * x + c1 * y
    return x2, y2

def elliptical_distortion(x, y, xc, yc, psi, stretch):
    """this rotates the coordinates x and y by the angle
    psi, applies a stretch factor of stretch to the x axis,
    and rotates the coordinates back. A stretch
    factor of 1 means a perfect circle.
    """
    x1, y1 = rot_axis(x-xc, y-yc, psi)
    x2, y2 = rot_axis(x1 * stretch, y1, - psi)

    return x2+xc, y2+yc

def f(c, x, y):
    """ calculate the algebraic distance between the data points and the mean circle centered at c=(xc, yc) """

    #rotate coordinates, apply stretch, rotate back

    if len(c) == 4:
        xc, yc, psi, stretch = c
        x, y = elliptical_distortion(x, y, xc, yc, psi, stretch)
    else:
        xc, yc = c


    Ri = calc_R(x, y, xc, yc)
    return Ri - Ri.mean()


def leastsq_circle(x, y):
    # coordinates of the barycenter
    x_m = np.mean(x)
    y_m = np.mean(y)

    apply_elliptical_correction = POS_REP_EVALUATION_PARS.APPLY_ELLIPTICAL_CORRECTION

    if apply_elliptical_correction:
        param_estimate = x_m, y_m, 0.0, 1.02
    else:
        param_estimate = x_m, y_m

    fitted_params, ier = optimize.leastsq(
        f, param_estimate, args=(x, y), ftol=1.5e-10, xtol=1.5e-10
    )

    if apply_elliptical_correction:
        xc, yc, psi, stretch = fitted_params

    else:
        xc, yc = fitted_params
        psi, stretch = 0.0, 1.0

    x2, y2 = elliptical_distortion(x, y, xc, yc, psi, stretch)

    Ri = calc_R(x2, y2, xc, yc)

    R = Ri.mean()
    residu = np.sum((Ri - R) ** 2)

    return xc, yc, R, psi, stretch, residu


def plot_data_circle(fpu_id, x_s2, y_s2, xc, yc, R, psi=None, stretch=None, axis=None):
    plt.figure(facecolor="white")  # figsize=(7, 5.4), dpi=72,
    plt.axis("equal")

    theta_fit = np.linspace(-pi, pi, 10 * 360)

    x_fit = xc + R * np.cos(theta_fit)
    y_fit = yc + R * np.sin(theta_fit)
    plt.plot(x_fit, y_fit, "b-", label="fitted circle", lw=2)
    plt.plot([xc], [yc], "bD", mec="y", mew=1)
    # plot data
    plt.plot(x_s2, y_s2, "r.", label="data fitted with psi = {} degree, stretch = {}"
             .format(np.rad2deg(psi), stretch), mew=1)

    plt.legend(loc="best", labelspacing=0.1)
    plt.grid()
    plt.title(fpu_id + " plot C: Least Squares Circle " + axis)
    plt.xlabel("x [millimeter], Cartesian camera coordinates")
    plt.ylabel("y [millimeter], Cartesian camera coordinates")
    plt.show()


def cartesian_blob_position(val):
    x1, y1, q1, x2, y2, q2 = val

    # compute weigthed midpoint between small (x, y1) and
    # large metrology target (x2, y2)
    image_x = (1.0 - BLOB_WEIGHT_FACTOR) * x1 + BLOB_WEIGHT_FACTOR * x2
    image_y = (1.0 - BLOB_WEIGHT_FACTOR) * y1 + BLOB_WEIGHT_FACTOR * y2
    # the resulting coordinates are image coordinates, which
    # are always positive, with (x0,y0) the upper left edge.

    # convert image coordinates to Cartesian coordinates,
    # so that correct orientation conventions are used.

    x = image_x
    y = - image_y

    return x, y

def normalize_difference_radian(x):
    x = np.where(x < - pi, x + 2 * pi, x)

    x = np.where(x > + pi, x - 2 * pi, x)

    return x

def nominal_angle_radian(key):
    return np.deg2rad(key[0]), np.deg2rad(key[1])

def extract_points(analysis_results):
    """returns (x,y) positions from image analysis and
    nominal angles of alpha and beta arm, in radians.
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
    # get list of points to which circle is fitted

    circle_points, nominal_coordinates_rad, pos_keys = extract_points(analysis_results)

    x_s, y_s = np.array(circle_points).T
    alpha_nominal_rad, beta_nominal_rad = np.array(nominal_coordinates_rad).T

    xc, yc, R, psi, stretch, residual = leastsq_circle(x_s, y_s)

    print("axis {}: fitted elliptical params: psi = {} degrees, stretch = {}".format(motor_axis, np.rad2deg(psi), stretch))

    x_s2, y_s2 = elliptical_distortion(x_s, y_s, xc, yc, psi, stretch)

    phi_real_rad, r_real = cartesian2polar(x_s2 - xc, y_s2 - yc)
    if motor_axis=="alpha":
        phi_nominal_rad = alpha_nominal_rad
    else:
        phi_nominal_rad = beta_nominal_rad

    offset_estimate = np.mean(phi_real_rad - phi_nominal_rad)

    result = {
        "xc": xc,
        "yc": yc,
        "R": R,
        "psi" : psi,
        "stretch" : stretch,
        "x_s" : x_s,
        "y_s" : y_s,
        "x_s2" : x_s2,
        "y_s2" : y_s2,
        "pos_keys" : pos_keys,
        "alpha_nominal_rad" : alpha_nominal_rad,
        "beta_nominal_rad" : beta_nominal_rad,
        "offset_estimate" : offset_estimate,
    }
    return result

def wrap_complex_vals(angle) :
    return np.where(angle < - pi / 4, angle + 2 * pi, angle)


def get_angle_error(x_s2, y_s2,
                    xc, yc,
                    alpha_nominal_rad,
                    beta_nominal_rad,
                    P0=None,
                    R_alpha=None,
                    R_beta_midpoint=None,
                    camera_offset_rad=None,
                    beta0_rad=None
):

    print("get_angle_error: center (x,y) = ({},{}) millimeter".format(xc, yc))
    x_real = x_s2 - xc
    y_real = y_s2 - yc


    # compute expected points from common fit parameters

    x_n, y_n = angle_to_point(alpha_nominal_rad,
                              beta_nominal_rad,
                              P0=P0,
                              R_alpha=R_alpha,
                              R_beta_midpoint=R_beta_midpoint,
                              camera_offset_rad=camera_offset_rad,
                              beta0_rad=beta0_rad,
                              broadcast=True)


    x_fitted = x_n - xc
    y_fitted = y_n - yc


    # compute remaining difference in the complex plane

    points_real = x_real + 1j * y_real
    points_fitted = x_fitted + 1j * y_fitted

    # compute _residual_ offset of fitted - real
    # (no unwrapping needed because we use the complex domain)
    #
    # note, the alpha0 / beta0 values are not included
    # (camera_offset is considered to be specific to the camera)
    angular_difference = np.log(points_real / points_fitted).imag

    phi_fitted_rad = wrap_complex_vals(np.log(points_fitted).imag)
    phi_real_rad = wrap_complex_vals(np.log(points_real).imag)


    return phi_real_rad, phi_fitted_rad, angular_difference


def fit_gearbox_parameters(motor_axis, circle_data,
                           P0=None,
                           R_alpha=None,
                           R_beta_midpoint=None,
                           camera_offset_rad=None,
                           beta0_rad=None,
                           return_intermediate_results=False):


    x_s = circle_data["x_s"]
    y_s = circle_data["y_s"]
    x_s2 = circle_data["x_s2"]
    y_s2 = circle_data["y_s2"]

    psi = circle_data["psi"]
    stretch=circle_data["stretch"]

    xc = circle_data["xc"]
    yc = circle_data["yc"]

    alpha_nominal_rad = circle_data["alpha_nominal_rad"]
    beta_nominal_rad = circle_data["beta_nominal_rad"]

    if motor_axis == "beta":
        # common angle for beta measurements
        alpha_fixpoint_rad = np.mean(alpha_nominal_rad)
        print("alpha fixpoint = {} degree".format(np.rad2deg(alpha_fixpoint_rad)))
        beta_fixpoint_rad = np.NaN
    else:
        alpha_fixpoint_rad = np.NaN
        beta_fixpoint_rad = np.mean(beta_nominal_rad)
        print("beta fixpoint = {} degree".format(np.rad2deg(beta_fixpoint_rad)))

    _, R_real = cartesian2polar(x_s2 - xc, y_s2 - yc)
    print("fit_gearbox_parameters(): finding angular error for {} arm ".format(motor_axis))

    phi_real_rad, phi_fitted_rad, err_phi_1_rad = get_angle_error(x_s2, y_s2,
                                                                   xc, yc,
                                                                   alpha_nominal_rad,
                                                                   beta_nominal_rad,
                                                                   P0=P0,
                                                                   R_alpha=R_alpha,
                                                                   R_beta_midpoint=R_beta_midpoint,
                                                                   camera_offset_rad=camera_offset_rad,
                                                                   beta0_rad=beta0_rad)



    support_points = {}
    for (fitted_angle, yp) in zip(phi_fitted_rad, err_phi_1_rad):
        if fitted_angle not in support_points:
            support_points[fitted_angle] = []
        support_points[fitted_angle].append(yp)

    phi_fit_support_rad = np.array(sorted(support_points.keys()))

    phi_corr_support_rad = [np.mean(np.array(support_points[k])) for k in phi_fit_support_rad]

    err_phi_support_rad = normalize_difference_radian(err_phi_1_rad - np.interp(phi_fitted_rad, phi_fit_support_rad, phi_corr_support_rad, period=2 * pi))


    phi_fitted_correction_rad = phi_fitted_rad + np.interp(
        phi_fitted_rad, phi_fit_support_rad, phi_corr_support_rad, period=2 * pi
    )

    ## combine first and second order fit, to get an invertible function

    corrected_shifted_angle_rad = np.array(phi_corr_support_rad) + phi_fit_support_rad

    print("fit_gearbox_parameters(): beta0_rad = {} rad = {} degree".format(beta0_rad, np.rad2deg(beta0_rad)))
    print("fit_gearbox_parameters(): beta0_rad - pi = {} rad = {} degree".format(beta0_rad - pi, 360 + np.rad2deg(beta0_rad - pi)))

    if motor_axis == "alpha":
        nominal_angle_rad = phi_fit_support_rad - camera_offset_rad
        corrected_angle_rad = corrected_shifted_angle_rad - camera_offset_rad
    else:
        nominal_angle_rad = phi_fit_support_rad - beta0_rad - camera_offset_rad - pi
        corrected_angle_rad = corrected_shifted_angle_rad - beta0_rad - camera_offset_rad - pi

    print("for axis {}: mean(corrected - nominal) = {} degrees".format(
        motor_axis, np.rad2deg(np.mean(corrected_angle_rad - nominal_angle_rad
        ))))

    # Pad table support points with values for the ends of the range.
    # This is espcially needed since the support points which are
    # used in the control plot, are outside the fitted range,
    # and without these padding values, the result of the
    # gearbox interpolation would be off to the first defined point.
    phi_min = np.deg2rad(-185)
    phi_max = np.deg2rad(+185)
    nominal_angle_rad = np.hstack([[phi_min], nominal_angle_rad, [phi_max]])
    corrected_angle_rad = np.hstack([[phi_min], corrected_angle_rad, [phi_max]])


    results = {
        "algorithm": "linfit+piecewise_interpolation",
        "xc": xc,
        "yc": yc,
        "R": circle_data["R"],
        "P0" : P0,
        "R_alpha" : R_alpha,
        "psi" : psi,
        "stretch" : stretch,
        "R_beta_midpoint" : R_beta_midpoint,
        "camera_offset_rad" : camera_offset_rad,
        "beta0_rad" : beta0_rad,
        "alpha_fixpoint_rad" : alpha_fixpoint_rad,
        "beta_fixpoint_rad" : beta_fixpoint_rad,
        "num_support_points": len(phi_fit_support_rad),
        "num_data_points": len(x_s2),
        "nominal_angle_rad" : nominal_angle_rad,
        "corrected_angle_rad": corrected_angle_rad,
    }

    if return_intermediate_results:

        extra_results =  {
            "x_s": x_s,
            "y_s": y_s,
            "x_s2": x_s2,
            "y_s2": y_s2,
            "phi_fitted_rad": phi_fitted_rad,
            "phi_fit_support_rad": phi_fit_support_rad,
            "corrected_shifted_angle_rad": corrected_shifted_angle_rad,
            "alpha_nominal_rad" : circle_data["alpha_nominal_rad"],
            "beta_nominal_rad" : circle_data["beta_nominal_rad"],
            "R_real": R_real,
            "yp": phi_corr_support_rad,
            "pos_keys" : circle_data["pos_keys"],
            "err_phi_support_rad" : err_phi_support_rad,

            "fits": {
                0: (phi_fitted_rad, phi_real_rad, "real angle as function of c-rotated nominal angle"),
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
    """convert nominal angles with a given pair of offsets to expected
    coordinate in the image plane.

    alpha_nom_rad and beta_nom_rad can be arrays.

    """

    if coeffs is None:
        delta_alpha = 0.0
        delta_beta = 0.0
        delta_alpha_fixpoint = 0.0
        delta_beta_fixpoint = 0.0
    else:
            if "alpha" in correct_axis:

                delta_alpha = - alpha_nom_rad + apply_gearbox_parameters(
                    alpha_nom_rad, wrap=True, inverse_transform=inverse, **coeffs["coeffs_alpha"]
                )

                alpha_fixpoint_rad = coeffs["coeffs_beta"]["alpha_fixpoint_rad"]
                delta_alpha_fixpoint = - alpha_fixpoint_rad + apply_gearbox_parameters(
                    alpha_fixpoint_rad, wrap=True, inverse_transform=inverse, **coeffs["coeffs_alpha"]
                )
            else:
                delta_alpha = 0
                delta_alpha_fixpoint = 0

            if "beta" in correct_axis:
                delta_beta = - beta_nom_rad + apply_gearbox_parameters(
                    beta_nom_rad, wrap=True, inverse_transform=inverse, **coeffs["coeffs_beta"]
                )

                beta_fixpoint_rad = coeffs["coeffs_alpha"]["beta_fixpoint_rad"]
                delta_beta_fixpoint = - beta_fixpoint_rad + apply_gearbox_parameters(
                    beta_fixpoint_rad, wrap=True, inverse_transform=inverse, **coeffs["coeffs_alpha"]
                )
            else:
                delta_beta = 0
                delta_beta_fixpoint = 0


            if not correct_fixpoint:
                delta_alpha_fixpoint = 0
                delta_beta_fixpoint = 0


    # rotate (possibly corrected) angles to camera orientation,
    # and apply beta arm offset
    alpha_rad = alpha_nom_rad + camera_offset_rad
    beta_rad = beta_nom_rad + beta0_rad

    # add difference to alpha when the beta
    # correction was measured (these angles add up
    # because when the alpha arm is turned (clockwise),
    # this turns the beta arm (clockwise) as well).
    gamma_rad = beta_rad + alpha_rad + (delta_alpha - delta_alpha_fixpoint)


    vec_alpha = np.array(polar2cartesian(alpha_rad + (delta_alpha - delta_alpha_fixpoint), R_alpha))
    vec_beta = np.array(polar2cartesian(gamma_rad + (delta_beta - delta_beta_fixpoint), R_beta_midpoint))

    if broadcast and (len(P0.shape) < len(vec_alpha.shape)):
        # adapt shape
        P0 = np.reshape(P0, P0.shape + (1,))

    expected_point = P0 + vec_alpha + vec_beta

    return expected_point


def fit_offsets(
        circle_alpha,
        circle_beta,
        P0=None,
        R_alpha=None,
        R_beta_midpoint=None,
        camera_offset_start=None,
        beta0_start=None
):
    """ The goal of this function is to find the best matching global
    offset between nominal coordinates and camera coordinates
    for both alpha and beta arm. This offset is assumed
    to be caused by the camera orientation.

    This is done by computing the image points from the nominal
    coordinates with a variable offset, and minimizing for the
    distance to the actual measured points.
    """

    circle_points = []
    nominal_coordinates_rad = []

    for c in circle_alpha, circle_beta:
        for x_s2, y_s2 in zip(c["x_s2"], c["y_s2"]):
            circle_points.append((x_s2,  y_s2))
        for alpha_nom, beta_nom in zip(c["alpha_nominal_rad"], c["beta_nominal_rad"]):
            nominal_coordinates_rad.append((alpha_nom, beta_nom))


    circle_points = np.array(circle_points).T
    alpha_nom_rad, beta_nom_rad = np.array(nominal_coordinates_rad).T

    def g(offsets):
        camera_offset, beta0 = offsets
        points = angle_to_point(
            alpha_nom_rad,
            beta_nom_rad,
            P0=P0,
            R_alpha=R_alpha,
            R_beta_midpoint=R_beta_midpoint,
            camera_offset_rad=camera_offset,
            beta0_rad=beta0
        )

        return np.linalg.norm(points - circle_points, axis=0)


    # coordinates of the barycenter
    offsets_estimate = np.array([camera_offset_start,  beta0_start])
    offsets, ier = optimize.leastsq(
        g, offsets_estimate,
        ftol=1.5e-10, xtol=1.5e-10
    )
    camera_offset,beta0 = offsets

    print("mean norm from offset fitting = ", np.mean(g(offsets)))

    return camera_offset, beta0

def get_expected_points(
        coeffs,
        R_alpha=None,
        R_beta_midpoint=None,
        camera_offset_rad=None,
        beta0_rad=None,
        P0=None,
        return_points=False,
):
    expected_vals = {}

    for lcoeffs, motor_axis in [
            (coeffs["coeffs_alpha"], "alpha"),
            (coeffs["coeffs_beta"], "beta"),
    ]:
        print("evaluating correction for {} motor axis".format(motor_axis))
        xc = lcoeffs["xc"]
        yc = lcoeffs["yc"]
        x_s = lcoeffs["x_s2"]
        y_s = lcoeffs["y_s2"]
        R = lcoeffs["R"]
        alpha_nominal_rad = lcoeffs["alpha_nominal_rad"]
        beta_nominal_rad = lcoeffs["beta_nominal_rad"]



        print_mean_correction = True
        if print_mean_correction:

            alpha_nom_corrected_rad = apply_gearbox_parameters(
                alpha_nominal_rad, wrap=True, inverse_transform=True, **coeffs["coeffs_alpha"]
            )
            beta_nom_corrected_rad = apply_gearbox_parameters(
                beta_nominal_rad, wrap=True, inverse_transform=True, **coeffs["coeffs_beta"]
            )


            print("for axis {}: mean(corrected - nominal) = {} degrees".format(
                "alpha", np.rad2deg(np.mean(alpha_nom_corrected_rad - alpha_nominal_rad
                ))))
            print("for axis {}: mean(corrected - nominal) = {} degrees".format(
                "beta", np.rad2deg(np.mean(beta_nom_corrected_rad - beta_nominal_rad
                ))))


            alpha_fixpoint_rad = lcoeffs["alpha_fixpoint_rad"]
            beta_fixpoint_rad = lcoeffs["beta_fixpoint_rad"]
            alpha_fixpoint_corrected_rad = apply_gearbox_parameters(
                alpha_fixpoint_rad, wrap=True, inverse_transform=True, **coeffs["coeffs_alpha"]
            )
            beta_fixpoint_corrected_rad = apply_gearbox_parameters(
                beta_fixpoint_rad, wrap=True, inverse_transform=True, **coeffs["coeffs_beta"]
            )

            print("for axis {}: mean(corrected - fixpoint) = {}".format(
                "alpha", np.rad2deg(np.mean(alpha_fixpoint_corrected_rad - alpha_fixpoint_rad
                ))))
            print("for axis {}: mean(corrected - fixpoint) = {}".format(
                "beta", np.rad2deg(np.mean(beta_fixpoint_corrected_rad - beta_fixpoint_rad
                ))))


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
                #correct_axis=[motor_axis],
                #correct_fixpoint=False,
                broadcast=False
            )

            expected_points.append(ep)


        expected_points = np.array(expected_points).T
        measured_points = np.array((x_s, y_s))
        xe, ye = expected_points
        error_magnitudes = np.linalg.norm(expected_points - measured_points, axis=0)
        RMS = np.sqrt(np.mean(error_magnitudes ** 2)) * 1000
        percentile_vals = np.percentile(error_magnitudes * 1000, PERCENTILE_ARGS)

        print("RMS [{}] = {} micron".format(motor_axis, RMS))
        pcdict = {PERCENTILE_ARGS[k] : pv for k, pv in enumerate(percentile_vals)}
        print("percentiles = {} microns".format(", ".join(["P[%s]: %.1f" % (k, pcdict[k]) for k in sorted(pcdict.keys()) ])))
        axis_result = {
            "RMS" : RMS,
            "pcdict" : pcdict,
            "expected_points" : expected_points,
            "measured_points" : measured_points,
            "xc" : xc,
            "yc" : yc,
            "R" : R,
            }

        if return_points:
            # include extra results for plotting
            axis_result.update({
                "x_s" : x_s,
                "y_s" : y_s,
                "xe" : xe,
                "ye" : ye,
                })

        expected_vals[motor_axis] = axis_result

    return expected_vals

def fit_gearbox_correction(dict_of_coordinates_alpha, dict_of_coordinates_beta, return_intermediate_results=False):
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

    circle_alpha = fit_circle(
        dict_of_coordinates_alpha,
        "alpha"
    )

    circle_beta = fit_circle(
        dict_of_coordinates_beta,
        "beta"
    )

    # find centers of alpha circle
    x_center = circle_alpha["xc"]
    y_center = circle_alpha["yc"]
    P0 = np.array([x_center, y_center])
    # find center of beta circles
    x_center_beta = circle_beta["xc"]
    y_center_beta = circle_beta["yc"]
    Pcb = np.array([x_center_beta, y_center_beta])
    # radius of alpha arm is distance from P0 to Pcb
    R_alpha = np.linalg.norm(Pcb - P0)
    # radius from beta center to weighted midpoint between metrology targets
    R_beta_midpoint = circle_beta["R"]

    camera_offset_start = circle_alpha["offset_estimate"]
    beta0_start = circle_beta["offset_estimate"] + camera_offset_start

    r2d = np.rad2deg
    print("camera_offset_start =", camera_offset_start, "radian = {} degree".format(r2d(camera_offset_start)))
    print("beta0_start =", beta0_start, "radian = {} degree".format(r2d(beta0_start)))

    camera_offset_rad, beta0_rad = fit_offsets(circle_alpha, circle_beta,
                                               P0=P0,
                                               R_alpha=R_alpha,
                                               R_beta_midpoint=R_beta_midpoint,
                                               camera_offset_start=camera_offset_start,
                                               beta0_start=beta0_start,
    )

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

    if (coeffs_alpha is None) or (coeffs_beta is None):
        return {
            "version": GEARBOX_CORRECTION_VERSION,
            "coeffs": {"coeffs_alpha": coeffs_alpha, "coeffs_beta": coeffs_beta},
        }



    print("camera_offset_rad =", camera_offset_rad, "= {} degree".format(r2d(camera_offset_rad)))
    print("beta0_rad =", beta0_rad, "= {} degree".format(r2d(beta0_rad)))

    coeffs = {"coeffs_alpha": coeffs_alpha, "coeffs_beta": coeffs_beta}

    P0 = np.array([x_center, y_center])

    expected_vals= get_expected_points(
        coeffs,
        R_alpha=R_alpha,
        R_beta_midpoint=R_beta_midpoint,
        camera_offset_rad=camera_offset_rad,
        beta0_rad=beta0_rad,
        P0=P0,
    )


    return {
        "version": GEARBOX_CORRECTION_VERSION,
        "coeffs": coeffs,
        "x_center": x_center,
        "y_center": y_center,
        "camera_offset_rad" : camera_offset_rad,
        "beta0_rad" : beta0_rad,
        "R_alpha": R_alpha,
        "R_beta_midpoint": R_beta_midpoint,
        "BLOB_WEIGHT_FACTOR": BLOB_WEIGHT_FACTOR,
        "expected_vals" : expected_vals,
    }



def split_iterations(
        motor_axis,
        pos_keys,
        err_phi_support_rad
):

    d2r = np.deg2rad
    # get set of iteration indices
    # loop and select measurements for each iteration

    if motor_axis == "alpha":
        directionlist = [0, 1]
    else:
        directionlist = [2, 3]

    err_phi_support_map = {}
    for key, err_phi_2 in zip(pos_keys, err_phi_support_rad):
        err_phi_support_map[key] = err_phi_2

    for selected_iteration in set([k_[2] for k_ in pos_keys]):
        for direction in directionlist:
            residual_ang_rad = []
            nom_ang_rad = []
            match_sweep = lambda key: (key[2] == selected_iteration) and (
                key[3] == direction
            )

            for key in filter(match_sweep, pos_keys):

                alpha_nominal_rad, beta_nominal_rad = d2r(key[0]), d2r(key[1])
                if motor_axis =="alpha":
                    phi_nominal_rad = alpha_nominal_rad
                else:
                    phi_nominal_rad = beta_nominal_rad


                nom_ang_rad.append(phi_nominal_rad)
                residual_ang_rad.append(err_phi_support_map[key])

            yield selected_iteration, direction, nom_ang_rad, residual_ang_rad


CALIBRATION_PLOTSET = set("CDEFGHIJKLMOP")
PLOT_CORR = "P"
PLOT_FIT = "Q"
PLOT_CAL_DEFAULT = set("IKLOQ")
PLOT_CAL_ALL = set("CDEFHIJKLMOPQ")

def plot_gearbox_calibration(
    fpu_id,
    motor_axis,
    algorithm=None,
    pos_keys=None,
    num_support_points=None,
    num_data_points=None,
    x_s=None,
    y_s=None,
    x_s2=None,
    y_s2=None,
    xc=None,
    yc=None,
    R=None,
    psi=None,
    stretch=None,
    camera_offset_rad=None,
    beta0_rad=None,
    P0=None,
    R_alpha=None,
    R_beta_midpoint=None,
    R_real=None,
    phi_fitted_rad=None,
    alpha_nominal_rad=None,
    beta_nominal_rad=None,
    phi_fit_support_rad=None,
    alpha_fixpoint_rad=None,
    beta_fixpoint_rad=None,
    yp=None,
    corrected_shifted_angle_rad=None,
    corrected_angle_rad=None,
    nominal_angle_rad=None,
    err_phi_support_rad=None,
    fits=None,
    residuals=None,
    plot_selection="CD",
):

    r2d = np.rad2deg
    # get list of points to which circle is fitted
    if "C" in plot_selection:
        plot_data_circle(fpu_id, x_s2 - xc, y_s2 - yc, 0, 0, R, psi=psi, stretch=stretch, axis=motor_axis)

    if "D" in plot_selection:
        plt.plot(r2d(fits[0][0]), r2d(fits[0][1]), "g.", label=fits[0][2])
        plt.title("FPU {} plot D: real vs c-rotated angle for {}".format(fpu_id, motor_axis))
        plt.legend(loc="best", labelspacing=0.1)
        plt.xlabel("c-rotated angle [degrees], polar camera coordinates")
        plt.ylabel("real angle [degrees], polar camera coordinates")
        plt.show()

    if "E" in plot_selection:
        plt.plot(r2d(fits[0][0]), r2d(fits[0][1]), "g.", label=fits[0][2])

    if "F" in plot_selection:
        plt.plot(r2d(fits[1][0]), r2d(fits[1][1]), "b+", label="{}".format(fits[1][2]))

    if "G" in plot_selection:
        plt.plot(r2d(fits[2][0]), r2d(fits[2][1]), "r.", label=fits[2][2])


    if set("EFG") & plot_selection:
        plt.title("FPU {} plot E,F,G: fitted, c-rotated nominal angle vs real angle for {}".format(fpu_id, motor_axis))
        plt.legend(loc="best", labelspacing=0.1)
        plt.xlabel("c-rotated angle [degrees], polar camera coordinates")
        plt.ylabel("real angle [degrees], polar camera coordinates")
        plt.show()

    if "H" in plot_selection:
        plt.plot(r2d(phi_fit_support_rad), r2d(corrected_shifted_angle_rad), "r.", label="correction table {} (fitted, c-rotated)".format(motor_axis))

        plt.title("FPU {} plot H: fitted, c-rotated angle to corrected (real) angle for {}".format(fpu_id, motor_axis))
        plt.legend(loc="best", labelspacing=0.1)
        plt.xlabel("c-rotated angle [degrees], polar camera coordinates")
        plt.ylabel("real angle [degrees], polar camera coordinates")
        plt.show()

    if "I" in plot_selection:
        plt.plot(r2d(nominal_angle_rad), r2d(nominal_angle_rad), "k-", label="nominal / nominal".format(motor_axis))
        plt.plot(r2d(nominal_angle_rad), r2d(corrected_angle_rad), "r.", label="correction table {} (nominal)".format(motor_axis))

        plt.title("FPU {} plot I: fitted nominal angle to tabled corrected (real) angle for {}".format(fpu_id, motor_axis))
        plt.legend(loc="best", labelspacing=0.1)
        plt.xlabel("nominal angle [degrees], FPU arm coordinates")
        plt.ylabel("real angle [degrees], FPU arm coordinates")
        plt.show()

    if "J" in plot_selection:
        input_nominal_angle_rad = np.deg2rad(np.linspace(-185, 185, 450, endpoint=True))
        apply_fit = functools.partial(apply_gearbox_parameters,
                                      nominal_angle_rad=nominal_angle_rad,
                                      corrected_angle_rad=corrected_angle_rad,
                                      inverse_transform=True,
                                      algorithm=algorithm,
                                      wrap=True,
                                      )


        interpolated_corrected_angle_rad = apply_fit(input_nominal_angle_rad)

        if motor_axis == "alpha":
            fixpoint_rad = beta_fixpoint_rad
            fname = "beta"
        else:
            fixpoint_rad = alpha_fixpoint_rad
            fname = "alpha"

        fixpoint_value = apply_fit(fixpoint_rad)

        plt.plot(r2d(input_nominal_angle_rad), r2d(input_nominal_angle_rad), "k-", label="nominal / nominal".format(motor_axis))
        plt.plot(r2d(input_nominal_angle_rad), r2d(interpolated_corrected_angle_rad), "r.",
                 label="inverse correction table {} (nominal)".format(motor_axis))
        plt.plot([r2d(fixpoint_rad)], [r2d(fixpoint_value)], "mD", label="fixpoint {}".format(fname))

        plt.title("FPU {} plot J: fitted nominal angle to inverse interpolated (real) angle for {}".format(fpu_id, motor_axis))
        plt.legend(loc="best", labelspacing=0.1)
        plt.xlabel("nominal angle [degrees], FPU arm coordinates")
        plt.ylabel("real angle [degrees], FPU arm coordinates")
        plt.show()

    if "K" in plot_selection:
        plt.plot(r2d(phi_fitted_rad), R_real - R, "r.", label="radial delta")

        plt.title("FPU {} plot K: first-order residual radius  for {} vs. c-rotated angle".format(fpu_id, motor_axis))
        plt.legend(loc="best", labelspacing=0.1)
        plt.xlabel("fitted c-rotated angle [degrees], polar camera coordinates")
        plt.ylabel("residual radius [millimeter]")
        plt.show()

    if "L" in plot_selection:
        plt.plot(
            r2d(residuals[1][0]), r2d(residuals[1][1]), "r.", label=residuals[1][2]
        )

        plt.title(
            "FPU {} plot L: first-order residual real vs c-rotated angle for {}".format(
                fpu_id, motor_axis
            )
        )
        plt.legend(loc="best", labelspacing=0.1)
        plt.xlabel("c-rotated angle [degrees], polar camera coordinates")
        plt.ylabel("real angle deltas [degrees]")
        plt.show()

    if "M" in plot_selection:
        plt.plot(
            r2d(residuals[2][0]), r2d(residuals[2][1]), "b+", label=residuals[2][2]
        )

        plt.title(
            "FPU {} plot M: second-order residual real vs c-rotated angle for {}".format(
                fpu_id, motor_axis
            )
        )
        plt.legend(loc="best", labelspacing=0.1)
        plt.xlabel("c-rotated angle [degrees], polar camera coordinates")
        plt.ylabel("real angle deltas [degrees]")
        plt.show()

    if "O" in plot_selection:

        plt.title(
            "FPU {} plot O: second-order residual vs nominal angle by iteration for {}".format(
                fpu_id, motor_axis
            )
        )
        plt.xlabel("nominal angle [degrees], FPU arm coordinates")
        plt.ylabel("real angle deltas [degrees], FPU arm coordinates")

        for iteration, direction, nom_angles, residual_angles in split_iterations(
                motor_axis,
                pos_keys,
                err_phi_support_rad,
        ):

            markers = [
                ".",
                "|",
                "^",
                "D",
                (5, 1, 0),
                "h",
                (7, 1, 0),
                "8",
                "$9$",
                "$10$",
                "$11$",
                "$12$",
            ]
            marker = markers[iteration]
            dirlabel, color = {
                0: ("up", "r"),
                1: ("down", "b"),
                2: ("up", "r"),
                3: ("down", "b"),
            }[direction]
            plt.plot(
                r2d(nom_angles),
                r2d(residual_angles),
                color,
                marker=marker,
                linestyle="",
                label="%s arm, direction=%s, iteration=%i" % (motor_axis, dirlabel, iteration),
            )

        plt.legend(loc="best", labelspacing=0.1)
        plt.show()


def plot_correction(fpu_id, motor_axis, fits=None, **coefs):

    """
    This applies the correction to the real (measured) angles, and
    plots the corrected angles vs the nominal angles. The result
    should be a (noisy) identity function without systematic error.
    """

    r2d = np.rad2deg

    real_angle_rad = fits[0][1]
    phi_fit_support_rad = fits[0][0]
    corrected_shifted_angle_rad = [apply_gearbox_parameters_fitted(phi, **coefs) for phi in real_angle_rad]

    plt.plot(r2d(phi_fit_support_rad), r2d(phi_fit_support_rad), "b-", label="fitted nominal/ fitted nominal")
    plt.plot(r2d(phi_fit_support_rad), r2d(corrected_shifted_angle_rad), "g.", label="fitted nominal/corrected")
    plt.title("FPU {} plot {}: c-rotated vs. corrected real angle for {}".format(fpu_id, PLOT_CORR, motor_axis))
    plt.legend(loc="best", labelspacing=0.1)
    plt.xlabel("c-rotated angle [degrees], polar camera coordinates")
    plt.ylabel("corrected angle [degrees], polar camera coordinates")
    plt.show()



def apply_gearbox_parameters_fitted(
        angle_rad,
        phi_fit_support_rad=None,
        corrected_shifted_angle_rad=None,
        algorithm=None,
        inverse_transform=False,
        wrap=False,
        **rest_coeffs
):
    """applies gearbox parameters to the fitted, c-rotated (rotated) angle
    (instead of the FPU coordinates).
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

    #phi_corrected = np.interp(angle_rad, x_points, y_points, period=2 * pi)
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


def apply_gearbox_correction(incoords_rad, coeffs=None):

    alpha_angle_rad, beta_angle_rad = incoords_rad
    coeffs_alpha = coeffs["coeffs_alpha"]
    coeffs_beta = coeffs["coeffs_beta"]

    # transform from desired / real angle to required nominal (uncalibrated) angle
    alpha_corrected_rad = apply_gearbox_parameters(alpha_angle_rad, **coeffs_alpha)
    beta_corrected_rad = apply_gearbox_parameters(beta_angle_rad, **coeffs_beta)

    # transform from angle to steps
    alpha_steps = int(
        round((alpha_corrected_rad - ALPHA_DATUM_OFFSET_RAD) * StepsPerRadianAlpha)
    )
    beta_steps = int(round((beta_corrected_rad - BETA_DATUM_OFFSET_RAD) * StepsPerRadianBeta))

    return (alpha_steps, beta_steps)





def plot_measured_vs_expected_points(serial_number,
                                     version=None,
                                     coeffs=None,
                                     x_center=None,
                                     y_center=None,
                                     camera_offset_rad=None,
                                     beta0_rad=None,
                                     R_alpha=None,
                                     R_beta_midpoint=None,
                                     BLOB_WEIGHT_FACTOR=None,
                                     expected_vals=None,
):

    if (coeffs["coeffs_alpha"] is None) or (
            coeffs["coeffs_beta"] is None):
        return

    plt.figure(facecolor="white")  # figsize=(7, 5.4), dpi=72,
    plt.axis("equal")

    theta_fit = np.linspace(-pi, pi, 2 * 360)
    P0=np.array([x_center, y_center])

    # re-compute expected values, to get point coordinates

    for motor_axis, expected_vals in get_expected_points(
            coeffs,
            R_alpha=R_alpha,
            R_beta_midpoint=R_beta_midpoint,
            camera_offset_rad=camera_offset_rad,
            beta0_rad=beta0_rad,
            P0=P0,
            return_points=True,
    ).items():

        if motor_axis == "alpha":
            color = "r"
            color2 = "m"
            fc = "y-"
        else:
            color = "b"
            color2 = "g"
            fc= "c-"

        RMS = expected_vals["RMS" ]
        pcdict = expected_vals["pcdict" ]
        expected_points = expected_vals["expected_points"]
        measured_points = expected_vals["measured_points"]

        xc = expected_vals["xc"]
        yc = expected_vals["yc"]
        xe = expected_vals["xe"]
        ye = expected_vals["ye"]

        x_s = expected_vals["x_s"]
        y_s = expected_vals["y_s"]
        R = expected_vals["R"]

        x_fit = xc + R * np.cos(theta_fit)
        y_fit = yc + R * np.sin(theta_fit)

        plt.plot(x_fit, y_fit, fc, label="{} fitted circle ".format(motor_axis), lw=2)
        plt.plot([xc], [yc], color + "D", mec="y", mew=1, label="{} fitted center".format(motor_axis))
        plt.plot(x_s, y_s, color + ".", label="{} measured point ".format(motor_axis), mew=1)
        plt.plot(xe, ye, color2 + "+", label="{} expected pts,"
                 " RMS = {:5.1f} $\mu$m, 95% perc = {:5.1f} $\mu$m".format(motor_axis, RMS, pcdict[95]), mew=1)

        plt.legend(loc="best", labelspacing=0.1)

    plt.grid()
    plt.title("FPU {} plot {}: measured vs expected points".format(serial_number, PLOT_FIT))
    plt.xlabel("x [millimeter], Cartesian camera coordinates")
    plt.ylabel("y [millimeter], Cartesian camera coordinates")
    plt.show()
