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
from Gearbox.gear_correction import (
    fit_gearbox_correction,
    angle_to_point,
    get_expected_points,
    apply_gearbox_parameters,
    apply_gearbox_parameters_fitted,
)

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
    radius_RMS=None,
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
            serial_number,
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
