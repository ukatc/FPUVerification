# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
from vfr.db.retrieval import get_data

from math import pi
import numpy as np
import types
#import matplotlib.pyplot as plt

#import numpy as np
from scipy import optimize
from matplotlib import pyplot as plt, cm, colors

def cartesian2polar(x, y):
    rho = np.sqrt(x**2 + y**2)
    phi = np.arctan2(y, x)
    return (phi, rho)

def polar2cartesian(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return (x, y)

def calc_R(x,y, xc, yc):
    """ calculate the distance of each 2D points from the center (xc, yc) """
    return np.sqrt((x-xc)**2 + (y-yc)**2)

def f(c, x, y):
    """ calculate the algebraic distance between the data points and the mean circle centered at c=(xc, yc) """
    Ri = calc_R(x, y, *c)
    return Ri - Ri.mean()

def leastsq_circle(x,y):
    # coordinates of the barycenter
    x_m = np.mean(x)
    y_m = np.mean(y)
    center_estimate = x_m, y_m
    center, ier = optimize.leastsq(f, center_estimate, args=(x,y), ftol=1.5e-10, xtol=1.5e-10)
    xc, yc = center
    Ri       = calc_R(x, y, *center)
    R        = Ri.mean()
    residu   = np.sum((Ri - R)**2)
    return xc, yc, R, residu

def plot_data_circle(x,y, xc, yc, R, title):
    f = plt.figure( facecolor='white')  #figsize=(7, 5.4), dpi=72,
    plt.axis('equal')

    theta_fit = np.linspace(-pi, pi, 10 * 360)

    x_fit = xc + R*np.cos(theta_fit)
    y_fit = yc + R*np.sin(theta_fit)
    plt.plot(x_fit, y_fit, 'b-' , label="fitted circle", lw=2)
    plt.plot([xc], [yc], 'bD', mec='y', mew=1)
    plt.xlabel('x')
    plt.ylabel('y')
    # plot data
    plt.plot(x, y, 'r.', label='data', mew=1)

    plt.legend(loc='best',labelspacing=0.1 )
    plt.grid()
    plt.title('Least Squares Circle ' + title)
    plt.show()

def fit_gearbox_calibration(fpu_id, par, analysis_results,
                            plot_circle=False,
                            plot_func=False,
                            plot_residuals=[1, 2]):
    if analysis_results is None:
        return None
    # get list of points to which circle is fitted
    nominal_angles = []
    circle_points = []
    #print("results = ", analysis_results)
    for k, v in analysis_results.items():
        alpha_nom, beta_nom, i, j, k = k
        x1, y1, q1, x2, y2, q2 = v

        x = (x1 + x2) * 0.5
        y = (y1 + y2) * 0.5
        circle_points.append((x, y))
        nominal_angles.append((alpha_nom, beta_nom))
    x, y = np.array(circle_points).T
    alpha, beta = np.array(nominal_angles).T

    xc, yc, R, residual = leastsq_circle(x,y)

    # print("xc = {}, yc = {}, R = {}, residual = {}".format(xc, yc, R, residual))

    #plot_data_circle(x, y, xc, yc, R, title=par)
    if plot_circle:
        plot_data_circle(x-xc, y-yc, 0, 0, R, title=par)

    phi_real, rho = cartesian2polar(y-yc, x-xc)

    # change wrapping point to match it to nominal angle
    # (reaching a piecewise linear function)
    phi_real = np.where(phi_real > pi / 4, phi_real - 2 * pi, phi_real)
    C = 180.0 / pi
    phi_real = phi_real * C
    if par == "alpha":
        phi_nominal = alpha
    else:
        phi_nominal = beta


    if plot_func:
        plt.plot(phi_nominal, phi_real, 'g.', label='real angle as function of nominal angle')
        plt.title('FPU {}: real vs nominal angle for {}'.format(fpu_id, par))
        plt.show()

    # fit data to a linear curve
    a0 = np.mean(phi_real - phi_nominal)
    b0 = 1.0
    print("a0=", a0)

    def f(x, a, b):
        return a + b*x

    a, b = optimize.curve_fit(f, phi_nominal, phi_real, (a0, b0))[0]

    phi_fitted = a + b * phi_nominal

    err_phi_1 = phi_real - phi_fitted

    if 0 in plot_residuals:
        plt.plot(phi_nominal, phi_real, 'g.', label='real angle as function of nominal angle')
        plt.plot(phi_nominal, phi_fitted, 'r-', label='fitted angle as function of nominal angle')
        plt.title('FPU {}: fitted real vs nominal angle for {}'.format(fpu_id, par))
        plt.show()

    support_points = {}
    for (x, y) in zip(phi_nominal, err_phi_1):
        if x not in support_points:
            support_points[x] = []
        support_points[x].append(y)

    for k, v in support_points.items():
        support_points[k] = np.mean(np.array(support_points[k]))

    phi_nom_2 = sorted(support_points.keys())
    phi_corr_2 = [support_points[k] for k in phi_nom_2]


    if 1 in plot_residuals:
        plt.plot(phi_nominal, err_phi_1, 'r.', label='residual angle as function of nominal angle')
        plt.plot(phi_nom_2, phi_corr_2, 'b+', label='mean residual angle as function of nominal angle')

        plt.title('FPU {}: first-order residual real vs nominal angle for {}'.format(fpu_id, par))
        plt.show()

    err_phi_2 = err_phi_1 - np.interp(phi_nominal, phi_nom_2, phi_corr_2, period=360)

    if 2 in plot_residuals:
        plt.plot(phi_nominal, err_phi_2, 'b+', label='mean residual angle as function of nominal angle')

        plt.title('FPU {}: second-order residual real vs nominal angle for {}'.format(fpu_id, par))
        plt.show()


def plot_pos_rep(fpu_id, analysis_results_alpha, analysis_results_beta, opts):
    if opts.blob_type == "large":
        blob_idx = slice(3,5)
    else:
        blob_idx = slice(0,2)

    colorcode = ['blue', 'red', 'green', 'cyan']
    for label, series, sweeps in [('alpha arm', analysis_results_alpha, [0,1]),
                                  ('beta arm', analysis_results_beta, [2, 3])]:

        if series is None:
            print("no data found for FPU %s, %s" % (fpu_id, label))
            continue

        fig, ax = plt.subplots()

        for sweep_idx in sweeps:
            direction = "up" if sweep_idx in [0, 2] else "down"

            color = colorcode[sweep_idx]
            sweep_series = [ v for k, v in series.items() if (k[3] == sweep_idx)]
            x, y = np.array(sweep_series).T[blob_idx]
            ax.scatter(x, y, c=color, label="%s %s" % (label, direction),
                       alpha=0.7, edgecolors='none')

            ax.legend()
            ax.grid(True)
            plt.title("%s : positional repetability" % fpu_id)

        plt.show()

def plot_dat_rep(fpu_id, datumed_coords, moved_coords, opts):
    if opts.blob_type == "large":
        blob_idx = slice(3,5)
    else:
        blob_idx = slice(0,2)

    fig, ax = plt.subplots()
    for label, series, color in [('datum only', datumed_coords, 'red'),
                                 ('moved + datumed', moved_coords, 'blue')]:

        if series is None:
            print("no data found for FPU %s, %s" % (fpu_id, label))
            continue


        x, y = np.array(series).T[blob_idx]
        ax.scatter(x, y, c=color, label=label,
                   alpha=0.7, edgecolors='none')

    ax.legend()

    ax.grid(True)
    plt.title("%s : datum repeatability" % fpu_id)

    plt.show()


def plot(dbe, opts):

    plot_selection = dbe.opts.plot_selection
    for count, fpu_id in enumerate(dbe.eval_fpuset):
        ddict = vars(get_data(dbe, fpu_id))
        if type(fpu_id) == types.IntType:
            fpu_id = dbe.fpu_config[fpu_id]["serialnumber"]

        if "A" in plot_selection:
            dat_rep_result = ddict["datum_repeatability_result"]["coords"]
            coords_datumed = dat_rep_result["datumed_coords"]
            coords_moved = dat_rep_result["moved_coords"]

            plot_dat_rep(fpu_id, coords_datumed, coords_moved, opts)


        if "B" in plot_selection:
            pos_rep_result = ddict["positional_repeatability_result"]
            result_alpha = pos_rep_result["analysis_results_alpha"]
            result_beta = pos_rep_result["analysis_results_beta"]

            plot_pos_rep(fpu_id, result_alpha, result_beta, opts)

        if "C" in plot_selection:
            pos_rep_result = ddict["positional_repeatability_result"]
            result_alpha = pos_rep_result["analysis_results_alpha"]
            result_beta = pos_rep_result["analysis_results_beta"]
            fit_gearbox_calibration(fpu_id, "alpha", result_alpha)
            fit_gearbox_calibration(fpu_id, "beta", result_beta)
