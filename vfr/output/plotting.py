# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
from vfr.db.retrieval import get_data

import numpy as np
import types

# import matplotlib.pyplot as plt

# import numpy as np
from matplotlib import pyplot as plt

from Gearbox.gear_correction import (
    fit_gearbox_parameters,
    plot_gearbox_calibration,
    plot_correction,
    angle_to_point,
)


def plot_pos_rep(fpu_id, analysis_results_alpha, analysis_results_beta, opts):
    if opts.blob_type == "large":
        blob_idx = slice(3, 5)
    else:
        blob_idx = slice(0, 2)

    colorcode = ["blue", "red", "green", "cyan"]
    for label, series, sweeps in [
        ("alpha arm", analysis_results_alpha, [0, 1]),
        ("beta arm", analysis_results_beta, [2, 3]),
    ]:

        if series is None:
            print("no data found for FPU %s, %s" % (fpu_id, label))
            continue

        fig, ax = plt.subplots()

        for sweep_idx in sweeps:
            direction = "up" if sweep_idx in [0, 2] else "down"

            color = colorcode[sweep_idx]
            sweep_series = [v for k, v in series.items() if (k[3] == sweep_idx)]
            x, y = np.array(sweep_series).T[blob_idx]
            ax.scatter(
                x,
                y,
                c=color,
                label="%s %s" % (label, direction),
                alpha=0.7,
                edgecolors="none",
            )

            ax.legend()
            ax.grid(True)
            plt.title("%s : positional repeatability" % fpu_id)

        plt.show()


def plot_dat_rep(fpu_id, datumed_coords, moved_coords, opts):
    if opts.blob_type == "large":
        blob_idx = slice(3, 5)
    else:
        blob_idx = slice(0, 2)

    fig, ax = plt.subplots()
    for label, series, color in [
        ("datum only", datumed_coords, "red"),
        ("moved + datumed", moved_coords, "blue"),
    ]:

        if series is None:
            print("no data found for FPU %s, %s" % (fpu_id, label))
            continue

        coords = np.array(series).T
        coords_zeroed = coords - np.mean(coords, axis=1)[:, np.newaxis]
        x, y = coords_zeroed[blob_idx]
        ax.scatter(x, y, c=color, label=label, alpha=0.7, edgecolors="none")

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

            gear_correction = fit_gearbox_correction(
                result_alpha,
                result_beta,
                return_intermediate_results=True,
            )
            fit_alpha = gear_correction["coeffs"]["coeffs_alpha"]
            plot_circle = "D" in plot_selection
            if fit_alpha is None:
                print("no parameters found for FPU %s, %s arm" % (fpu_id, "alpha"))
            else:
                plot_gearbox_calibration(
                    fpu_id,
                    "alpha",
                    plot_circle=plot_circle,
                    plot_fits=[0, 1, 2],
                    plot_residuals=[1, 2],
                    **fit_alpha
                )

                plot_correction(fpu_id, "alpha", **fit_alpha)

            fit_alpha = gear_correction["coeffs"]["coeffs_alpha"]
            if fit_beta is None:
                print("no parameters found for FPU %s, %s arm" % (fpu_id, "beta"))
            else:
                plot_gearbox_calibration(
                    fpu_id,
                    "beta",
                    plot_circle=plot_circle,
                    plot_fits=[0, 1, 2],
                    plot_residuals=[1, 2],
                    **fit_beta
                )
                plot_correction(fpu_id, "beta", **fit_beta)
