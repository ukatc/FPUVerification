from __future__ import division, print_function

from math import pi
import numpy as np
import warnings
# import matplotlib.pyplot as plt

# import numpy as np
from scipy import optimize
from matplotlib import pyplot as plt

from fpu_constants import (
    ALPHA_DATUM_OFFSET,
    BETA_DATUM_OFFSET,
    StepsPerDegreeAlpha,
    StepsPerDegreeBeta,
)
from vfr.conf import BLOB_WEIGHT_FACTOR

# exceptions which are raised if image analysis functions fail


class GearboxFitError(Exception):
    pass


# version number for gearbox correction algorithm
# (each different result for the same data
# should yield a version number increase)

GEARBOX_CORRECTION_VERSION = 1.0


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


def f(c, x, y):
    """ calculate the algebraic distance between the data points and the mean circle centered at c=(xc, yc) """
    Ri = calc_R(x, y, *c)
    return Ri - Ri.mean()


def leastsq_circle(x, y):
    # coordinates of the barycenter
    x_m = np.mean(x)
    y_m = np.mean(y)
    center_estimate = x_m, y_m
    center, ier = optimize.leastsq(
        f, center_estimate, args=(x, y), ftol=1.5e-10, xtol=1.5e-10
    )
    xc, yc = center
    Ri = calc_R(x, y, *center)
    R = Ri.mean()
    residu = np.sum((Ri - R) ** 2)
    return xc, yc, R, residu


def plot_data_circle(x, y, xc, yc, R, title):
    plt.figure(facecolor="white")  # figsize=(7, 5.4), dpi=72,
    plt.axis("equal")

    theta_fit = np.linspace(-pi, pi, 10 * 360)

    x_fit = xc + R * np.cos(theta_fit)
    y_fit = yc + R * np.sin(theta_fit)
    plt.plot(x_fit, y_fit, "b-", label="fitted circle", lw=2)
    plt.plot([xc], [yc], "bD", mec="y", mew=1)
    # plot data
    plt.plot(x, y, "r.", label="data", mew=1)

    plt.legend(loc="best", labelspacing=0.1)
    plt.grid()
    plt.title("Least Squares Circle " + title)
    plt.xlabel("x")
    plt.ylabel("y")
    plt.show()


def fit_gearbox_parameters(axis, analysis_results, return_intermediate_results=False):
    if analysis_results is None:
        return None
    # get list of points to which circle is fitted
    nominal_angles_deg = []
    circle_points = []
    midpoints = {}

    for key, val in analysis_results.items():
        alpha_nom_deg, beta_nom_deg, i, j, k = key
        x1, y1, q1, x2, y2, q2 = val

        # compute weigthed midpoint between small and
        # large metrology target
        x = (1.0 - BLOB_WEIGHT_FACTOR) * x1 + BLOB_WEIGHT_FACTOR * x2
        y = (1.0 - BLOB_WEIGHT_FACTOR) * y1 + BLOB_WEIGHT_FACTOR * y2

        circle_points.append((x, y))
        nominal_angles_deg.append((alpha_nom_deg, beta_nom_deg))
        midpoints[key] = (x, y)
    x_s, y_s = np.array(circle_points).T
    alpha_nominal_deg, beta_nominal_deg = np.array(nominal_angles_deg).T

    xc, yc, R, residual = leastsq_circle(x_s, y_s)

    phi_real_rad, R_real = cartesian2polar(x_s - xc, y_s - yc)

    # change wrapping point to match it to nominal angle
    # (reaching a piecewise linear function)
    phi_real_rad = np.where(phi_real_rad > pi / 4, phi_real_rad - 2 * pi, phi_real_rad)
    # phi_real = np.unwrap(phi_real)

    if axis == "alpha":
        phi_nominal_rad = np.deg2rad(alpha_nominal_deg)
        alpha_ref_deg = np.NaN
        beta_ref_deg = np.mean(beta_nominal_deg)
    else:
        phi_nominal_rad = np.deg2rad(beta_nominal_deg)
        alpha_ref_deg = np.mean(alpha_nominal_deg)
        beta_ref_deg=np.NaN

    # fit data to a linear curve
    a0 = np.mean(phi_real_rad - phi_nominal_rad)
    b0 = 1.0

    def f(x, a, b):
        return a + b * x

    a, b = optimize.curve_fit(f, phi_nominal_rad, phi_real_rad, (a0, b0))[0]

    phi_fitted_rad = a + b * phi_nominal_rad

    err_phi_1_rad = phi_real_rad - phi_fitted_rad

    support_points = {}
    for (xp, yp) in zip(phi_nominal_rad, err_phi_1_rad):
        if xp not in support_points:
            support_points[xp] = []
        support_points[xp].append(yp)

    for k, v in support_points.items():
        support_points[k] = np.mean(np.array(support_points[k]))

    phi_nom_2_rad = sorted(support_points.keys())
    phi_corr_2_rad = [support_points[k] for k in phi_nom_2_rad]

    err_phi_2_rad = err_phi_1_rad - np.interp(phi_nominal_rad, phi_nom_2_rad, phi_corr_2_rad, period=2 * pi)

    phi_fitted_2_rad = phi_fitted_rad + np.interp(
        phi_nominal_rad, phi_nom_2_rad, phi_corr_2_rad, period=2 * pi
    )

    # combine first and second order fit, to get an ivertible function
    y_corr_rad = np.array(phi_corr_2_rad) + (a + np.array(phi_nom_2_rad) * b)

    if return_intermediate_results:

        return {
            "algorithm": "linfit+piecewise_interpolation",
            "midpoints": midpoints,
            "x": x_s,
            "y": y_s,
            "phi_nominal": phi_nominal_rad,
            "alpha_nominal" : alpha_nominal_deg,
            "beta_nominal" : beta_nominal_deg,
            "R_real": R_real,
            "xc": xc,
            "yc": yc,
            "R": R,
            "a": a,
            "b": b,
            "alpha0" : alpha_ref_deg,
            "beta0" : beta_ref_deg,
            "xp": phi_nom_2_rad,
            "yp": phi_corr_2_rad,
            "num_support_points": len(phi_nom_2_rad),
            "num_data_points": len(x_s),
            "y_corr": y_corr_rad,
            "fits": {
                0: (phi_nominal_rad, phi_real_rad, "real angle as function of nominal angle"),
                1: (
                    phi_nominal_rad,
                    phi_fitted_rad,
                    "first-order fitted angle as function of nominal angle",
                ),
                2: (
                    phi_nominal_rad,
                    phi_fitted_2_rad,
                    "second-order fitted angle as function of nominal angle",
                ),
            },
            "residuals": {
                1: (
                    phi_nominal_rad,
                    err_phi_1_rad,
                    "first-order residual angle as function of nominal angle",
                ),
                2: (
                    phi_nominal_rad,
                    err_phi_2_rad,
                    "second-order residual angle as function of nominal angle",
                ),
            },
        }
    else:
        return {
            "algorithm": "linfit+piecewise_interpolation",
            "xc": xc,
            "yc": yc,
            "R": R,
            "a": a,
            "b": b,
            "alpha0" : alpha_ref_deg,
            "beta0" : beta_ref_deg,
            "num_support_points": len(phi_nom_2_rad),
            "num_data_points": len(x_s),
            "xp": phi_nom_2_rad,
            "y_corr": y_corr_rad,
        }


def split_iterations(
    axis, midpoints, xc=None, yc=None, a=None, b=None, xp=None, yp=None
):
    d2r = np.deg2rad
    # get set of iteration indices
    # loop and select measurements for each iteration

    if axis == "alpha":
        directionlist = [0, 1]
    else:
        directionlist = [2, 3]

    for selected_iteration in set([k_[2] for k_ in midpoints.keys()]):
        for direction in directionlist:
            residual_ang = []
            nom_ang = []
            match_sweep = lambda key: (key[2] == selected_iteration) and (
                key[3] == direction
            )

            for key in filter(match_sweep, midpoints.keys()):

                if axis == "alpha":
                    phi_nominal = d2r(key[0])
                else:
                    phi_nominal = d2r(key[1])

                x, y = midpoints[key]

                phi_real, rho = cartesian2polar(x - xc, y - yc)

                phi_real = np.where(phi_real > pi / 4, phi_real - 2 * pi, phi_real)

                phi_fitted = a + b * phi_nominal

                err_phi_1 = phi_real - phi_fitted

                err_phi_2 = err_phi_1 - np.interp(phi_nominal, xp, yp, period=2 * pi)

                nom_ang.append(phi_nominal)
                residual_ang.append(err_phi_2)

            yield selected_iteration, direction, nom_ang, residual_ang


def plot_gearbox_calibration(
    fpu_id,
    axis,
    algorithm=None,
    midpoints=None,
    num_support_points=None,
    num_data_points=None,
    x=None,
    y=None,
    xc=None,
    yc=None,
    R=None,
    a=None,
    b=None,
    alpha0=None,
    beta0=None,
    R_real=None,
    phi_nominal=None,
    alpha_nominal=None,
    beta_nominal=None,
    xp=None,
    yp=None,
    y_corr=None,
    fits=None,
    residuals=None,
    plot_circle=False,
    plot_func=True,
    plot_fits=[0, 1, 2],
    plot_residuals=[0, 1, 2],
):

    r2d = np.rad2deg
    # get list of points to which circle is fitted
    if plot_circle:
        plot_data_circle(x - xc, y - yc, 0, 0, R, title=axis)

    if plot_func:
        plt.plot(r2d(fits[0][0]), r2d(fits[0][1]), "g.", label=fits[0][2])
        plt.title("FPU {}: real vs nominal angle for {}".format(fpu_id, axis))
        plt.legend(loc="best", labelspacing=0.1)
        plt.xlabel("nominal angle [degrees]")
        plt.ylabel("real angle [degrees]")
        plt.show()

    if 0 in plot_fits:
        plt.plot(r2d(fits[0][0]), r2d(fits[0][1]), "g.", label=fits[0][2])

    if 1 in plot_fits:
        plt.plot(r2d(fits[1][0]), r2d(fits[1][1]), "b+", label=fits[1][2])

    if 2 in plot_fits:
        plt.plot(r2d(fits[2][0]), r2d(fits[2][1]), "r.", label=fits[2][2])

    if plot_fits:
        plt.title("FPU {}: fitted real vs nominal angle for {}".format(fpu_id, axis))
        plt.legend(loc="best", labelspacing=0.1)
        plt.xlabel("nominal angle [degrees]")
        plt.ylabel("real angle [degrees]")
        plt.show()

    if 1 in plot_residuals:
        plt.plot(r2d(phi_nominal), R_real - R, "r.", label="radial delta")

        plt.title("FPU {}: first-order residual radius  for {}".format(fpu_id, axis))
        plt.legend(loc="best", labelspacing=0.1)
        plt.xlabel("nominal angle [degrees]")
        plt.ylabel("residual radius [millimeter]")
        plt.show()

    if 1 in plot_residuals:
        plt.plot(
            r2d(residuals[1][0]), r2d(residuals[1][1]), "r.", label=residuals[1][2]
        )

        plt.title(
            "FPU {}: first-order residual real vs nominal angle for {}".format(
                fpu_id, axis
            )
        )
        plt.legend(loc="best", labelspacing=0.1)
        plt.xlabel("nominal angle [degrees]")
        plt.ylabel("real angle deltas [degrees]")
        plt.show()

    if 2 in plot_residuals:
        plt.plot(
            r2d(residuals[2][0]), r2d(residuals[2][1]), "b+", label=residuals[2][2]
        )

        plt.title(
            "FPU {}: second-order residual real vs nominal angle for {}".format(
                fpu_id, axis
            )
        )
        plt.legend(loc="best", labelspacing=0.1)
        plt.xlabel("nominal angle [degrees]")
        plt.ylabel("real angle deltas [degrees]")
        plt.show()

        plt.title(
            "FPU {}: second-order residual vs nominal angle by iteration for {}".format(
                fpu_id, axis
            )
        )
        plt.xlabel("nominal angle [degrees]")
        plt.ylabel("real angle deltas [degrees]")

        for iteration, direction, nom_angles, residual_angles in split_iterations(
            axis, midpoints, xc=xc, yc=yc, a=a, b=b, xp=xp, yp=yp
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
                label="%s arm, direction=%s, iteration=%i" % (axis, dirlabel, iteration),
            )

        plt.legend(loc="best", labelspacing=0.1)
        plt.show()


def plot_correction(fpu_id, axis, fits=None, **coefs):

    """
    This applies the correction to the real (measured) angles, and
    plots the corrected angles vs the nominal angles. The result
    should be a (noisy) identity function without systematic error.
    """

    r2d = np.rad2deg

    real_angle_rad = fits[0][1]
    nominal_angle_rad = fits[0][0]
    corrected_angle_deg = [apply_gearbox_parameters(r2d(phi), **coefs) for phi in real_angle_rad]

    plt.plot(r2d(nominal_angle_rad), r2d(nominal_angle_rad), "b-", label="nominal/nominal")
    plt.plot(r2d(nominal_angle_rad), corrected_angle_deg, "g.", label="nominal/corrected")
    plt.title("FPU {}: nominal vs. corrected real angle for {}".format(fpu_id, axis))
    plt.legend(loc="best", labelspacing=0.1)
    plt.xlabel("nominal angle [degrees]")
    plt.ylabel("corrected angle [degrees]")
    plt.show()


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

    coeffs_alpha = fit_gearbox_parameters(
        "alpha",
        dict_of_coordinates_alpha,
        return_intermediate_results=return_intermediate_results,
    )

    coeffs_beta = fit_gearbox_parameters(
        "beta",
        dict_of_coordinates_beta,
        return_intermediate_results=return_intermediate_results,
    )

    if (coeffs_alpha is None) or (coeffs_beta is None):
        return {
            "version": GEARBOX_CORRECTION_VERSION,
            "coeffs": {"coeffs_alpha": coeffs_alpha, "coeffs_beta": coeffs_beta},
        }


    # find centers of alpha circle
    x_center = coeffs_alpha["xc"]
    y_center = coeffs_alpha["yc"]
    P0 = np.array([x_center, y_center])
    # find center of beta circles
    x_center_beta = coeffs_beta["xc"]
    y_center_beta = coeffs_beta["yc"]
    Pcb = np.array([x_center_beta, y_center_beta])
    # radius of alpha arm is distance from P0 to Pcb
    R_alpha = np.linalg.norm(Pcb - P0)
    # radius from beta center to weighted midpoint between metrology targets
    R_beta_midpoint = coeffs_beta["R"]
    alpha0 = coeffs_beta["alpha0"]
    beta0 = coeffs_alpha["beta0"]

    return {
        "version": GEARBOX_CORRECTION_VERSION,
        "coeffs": {"coeffs_alpha": coeffs_alpha, "coeffs_beta": coeffs_beta},
        "x_center": x_center,
        "y_center": y_center,
        "alpha0" : alpha0,
        "beta0" : beta0,
        "R_alpha": R_alpha,
        "R_beta_midpoint": R_beta_midpoint,
        "BLOB_WEIGHT_FACTOR": BLOB_WEIGHT_FACTOR,
    }


def apply_gearbox_parameters(
        angle_deg,
        a=None,
        b=None,
        xp=None,
        y_corr=None,
        algorithm=None,
        inverse_transform=False,
        wrap=False,
        **rest_coeffs
):

    assert (
        algorithm == "linfit+piecewise_interpolation"
    ), "no matching algorithm -- repeat fitting"

    xp = np.array(xp, dtype=float)
    y_corr = np.array(y_corr, dtype=float)

    if inverse_transform:
        x_points = xp
        y_points = y_corr
    else:
        x_points = y_corr
        y_points = xp

    if wrap:
        period = 360.0
        angle_deg = np.fmod(angle_deg + period * 1.5, period) - period * 0.5

    angle_rad = np.deg2rad(angle_deg)

    phi_corrected = np.interp(angle_rad, x_points, y_points, period=2 * pi)

    return np.rad2deg(phi_corrected)


def apply_gearbox_correction(incoords_deg, coeffs=None):
    alpha_angle_deg, beta_angle_deg = incoords_deg
    coeffs_alpha = coeffs["coeffs_alpha"]
    coeffs_beta = coeffs["coeffs_beta"]

    # transform from desired / real angle to required nominal (uncalibrated) angle
    alpha_corrected_deg = apply_gearbox_parameters(alpha_angle_deg, **coeffs_alpha)
    beta_corrected_deg = apply_gearbox_parameters(beta_angle_deg, **coeffs_beta)

    # transform from angle to steps
    alpha_steps = int(
        round((alpha_corrected_deg - ALPHA_DATUM_OFFSET) * StepsPerDegreeAlpha)
    )
    beta_steps = int(round((beta_corrected_deg - BETA_DATUM_OFFSET) * StepsPerDegreeBeta))

    return (alpha_steps, beta_steps)


def angle_to_point(
        alpha_nom_deg,
        beta_nom_deg,
        coeffs=None,
        x_center=None,
        y_center=None,
        R_alpha=None,
        R_beta_midpoint=None,
        alpha0=None,
        already_corrected=True,
):
    """convert nominal angle to expected coordinate in the image plane.
    This function is needed to derive the positional
    verification error, by performing a transformation
    from the nominal arm angles to the (x,y) image
    plane position where the image is expected.
    """

    r2d = np.rad2deg
    d2r = np.deg2rad

    # these offsets make up for the rotation of
    # the camera *and* for the +180 degree offset
    # for beta in respect for the Cartesian system
    coeffs_alpha = coeffs['coeffs_alpha']
    coeffs_beta = coeffs['coeffs_beta']
    a_alpha = coeffs_alpha['a']
    b_alpha = coeffs_alpha['b']
    a_beta = coeffs_beta['a']
    b_beta = coeffs['coeffs_beta']['b']
    print("offset alpha = ", r2d(a_alpha))
    print("offset beta = ", r2d(a_beta))
    print("R_alpha=", R_alpha)
    print("R_beta_midpoint=", R_beta_midpoint)
    if alpha0 is None:
        assert False
        # alpha reference point for deriving gamma
        warnings.warn("setting default alpha reference")
        alpha0 = -180.3 + 5.0 # alpha_min + pos_rep_safety_margin

    P0 = np.array([x_center, y_center])

    if already_corrected:
        # use only linear fit here (because nominal coordinates were
        # corrected during measurement)
        alpha_deg = r2d(b_alpha * d2r(alpha_nom_deg) + a_alpha)
        beta_deg = r2d(b_beta * d2r(beta_nom_deg) + a_beta)

        # add difference to alpha when the beta
        # correction was measured (these angles add up
        # because when the alpha arm is turned (clockwise),
        # this turns the beta arm (clockwise) as well).
        gamma_deg = r2d(d2r(beta_deg) + b_alpha * d2r(alpha_nom_deg - alpha0))

    else:
        # use full gearbox correction
        alpha_deg = apply_gearbox_parameters(alpha_nom_deg, inverse_transform=True, **coeffs_alpha)
        beta_deg = apply_gearbox_parameters(beta_nom_deg, inverse_transform=True, **coeffs_beta)
        alpha_ref_deg = apply_gearbox_parameters(alpha0, inverse_transform=True, **coeffs_alpha)
        gamma_deg = beta_deg + (alpha_deg - alpha_ref_deg)

    # compute expected Cartesian coordinate of observation
    pos_alpha = np.array(polar2cartesian(d2r(alpha_deg), R_alpha))
    pos_beta = np.array(polar2cartesian(d2r(gamma_deg), R_beta_midpoint))

    expected_point = P0 + pos_alpha + pos_beta
    print("alpha_nom=%f, beta_nom=%f" % (alpha_nom_deg, beta_nom_deg))
    print("alpha=%f, beta=%f, gamma=%f" % (alpha_deg, beta_deg, gamma_deg))
    print("p0=", P0)
    print("p_expected=",expected_point)
    print("p_a=", pos_alpha)
    print("p_b=", pos_beta)

    return expected_point



def plot_measured_vs_expected_points(serial_number,
                                     version=None,
                                     coeffs=None,
                                     x_center=None,
                                     y_center=None,
                                     alpha0=None,
                                     beta0=None,
                                     R_alpha=None,
                                     R_beta_midpoint=None,
                                     BLOB_WEIGHT_FACTOR=None,
):

    if (coeffs["coeffs_alpha"] is None) or (
            coeffs["coeffs_beta"] is None):
        return

    plt.figure(facecolor="white")  # figsize=(7, 5.4), dpi=72,
    plt.axis("equal")

    theta_fit = np.linspace(-pi, pi, 2 * 360)

    for lcoeffs, axis, color in [
            (coeffs["coeffs_alpha"], "alpha", "r"),
            (coeffs["coeffs_beta"], "beta", "b"),
    ]:
        xc = lcoeffs["xc"]
        yc = lcoeffs["yc"]
        x = lcoeffs["x"]
        y = lcoeffs["y"]
        R = lcoeffs["R"]
        alpha_nominal = lcoeffs["alpha_nominal"]
        beta_nominal = lcoeffs["beta_nominal"]


        x_fit = xc + R * np.cos(theta_fit)
        y_fit = yc + R * np.sin(theta_fit)

        if axis == "alpha":
            fc = "c-"
        else:
            fc= "g-"

        plt.plot(x_fit, y_fit, fc, label="{} fitted circle ".format(axis), lw=2)
        plt.plot([xc], [yc], color + "D", mec="y", mew=1, label="{} fitted center".format(axis))
        # plot data
        plt.plot(x, y, color + ".", label="{} measured point ".format(axis), mew=1)

        expected_points = []
        for alpha_nom, beta_nom in zip(alpha_nominal, beta_nominal):
            ep =  angle_to_point(
                alpha_nom,
                beta_nom,
                coeffs=coeffs,
                x_center=x_center,
                y_center=y_center,
                R_alpha=R_alpha,
                R_beta_midpoint=R_beta_midpoint,
                alpha0=alpha0,
                already_corrected=False,
            )
            expected_points.append(ep)
        xe, ye = np.array(expected_points).T
        plt.plot(xe, ye, color + "+", label="{} expected from nominal angle".format(axis), mew=1)

        plt.legend(loc="best", labelspacing=0.1)

    plt.grid()
    plt.title("FPU {}: measured vs expected points".format(serial_number))
    plt.xlabel("x")
    plt.ylabel("y")
    plt.show()
