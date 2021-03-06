# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
from vfr.db.retrieval import get_data

import numpy as np
import types
import logging

# import matplotlib.pyplot as plt

# import numpy as np
from matplotlib import pyplot as plt

from Gearbox.gear_correction import fit_gearbox_correction

from Gearbox.plot_gear_correction import (
    plot_gearbox_calibration,
    plot_correction,
    plot_measured_vs_expected_points,
    CALIBRATION_PLOTSET,
    PLOT_FIT,
    PLOT_CORR,
    PLOT_CAL_DEFAULT,
    PLOT_CAL_ALL,
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
                -y,
                c=color,
                label="%s %s" % (label, direction),
                alpha=0.7,
                edgecolors="none",
            )

            ax.legend()
            ax.grid(True)
            plt.xlabel("x [millimeter], Cartesian camera coordinates")
            plt.ylabel("y [millimeter], Cartesian camera coordinates")
            plt.title("%s plot B: positional repeatability" % fpu_id)

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
    plt.xlabel("x [millimeter], Cartesian camera coordinates")
    plt.ylabel("y [millimeter], Cartesian camera coordinates")
    plt.title("%s plot A: datum repeatability" % fpu_id)

    plt.show()


PLOT_DEFAULT_SELECTION = PLOT_CAL_DEFAULT | set("ABR")
PLOT_ALL = set("ABR") | PLOT_CAL_ALL

def plot_pos_ver(fpu_id, pos_ver_result, pos_rep_result, opts):
    logger = logging.getLogger(__name__)

    measured_points = pos_ver_result["measured_points"]
    if not measured_points:
        logger.info("FPU {}: no data for plotting pos-ver result - skipped".format(fpu_id))
        return

    eval_version = pos_ver_result["evaluation_version"]
    if eval_version < (1, 0, 0):
        logger.info("FPU {:s}: positional verification data evaluation "
                    "version is too old ({:s}) - plot skipped.".format(fpu_id, eval_version))
        return

    if pos_rep_result is None:
        logger.info("FPU {:s}: positional repeatability data"
                    " is missing, plot skipped.".format(fpu_id))
        return

    x_center = pos_rep_result["gearbox_correction"]["x_center"]
    y_center = pos_rep_result["gearbox_correction"]["y_center"]


    x_measured, y_measured = np.array(measured_points.values()).T

    expected_points = pos_ver_result["expected_points"]
    x_expected, y_expected = np.array(expected_points.values()).T

    plt.plot([x_center], [y_center], "mD", label="alpha arm center point")
    error_95_percentile_micron = pos_ver_result["posver_error_measures"].percentiles[95] * 1000
    plt.plot(x_measured, y_measured, "r.", label="measured points, 95 % percentile ="
             " {:5.0f} $\mu$m".format(error_95_percentile_micron)
    #         " {posver_error_measures.percentiles[95]:8.4f}".format(**pos_ver_result)
    )
    plt.plot(x_expected, y_expected, "b+", label="expected points")
    plt.legend(loc="best", labelspacing=0.1)
    plt.grid()
    plt.title("FPU {} plot R: positional verification -- measured and expected points".format(fpu_id))
    plt.xlabel("x [millimeter], Cartesian camera coordinates")
    plt.ylabel("y [millimeter], Cartesian camera coordinates")
    plt.show()


def plot(dbe, opts):
    logger = logging.getLogger(__name__)

    plot_selection = dbe.opts.plot_selection
    for count, fpu_id in enumerate(dbe.eval_fpuset):
        ddict = vars(get_data(dbe, fpu_id))
        if ddict is None:
            logger.info("FPU %r: no plot data found" % fpu_id)
            continue
        if plot_selection == "*":
            plot_selection = PLOT_ALL
        else:
            plot_selection = set(plot_selection)

        if type(fpu_id) == types.IntType:
            fpu_id = dbe.fpu_config[fpu_id]["serialnumber"]

        if "A" in plot_selection:
            if ddict["datum_repeatability_result"] is None:
                logger.info(
                    "FPU %r: no plot data for datum repeatability found" % fpu_id
                )
            else:
                dat_rep_result = ddict["datum_repeatability_result"]["coords"]
                coords_datumed = dat_rep_result["datumed_coords"]
                coords_moved = dat_rep_result["moved_coords"]

                plot_dat_rep(fpu_id, coords_datumed, coords_moved, opts)

        if ddict["positional_repeatability_result"] is None:
            logger.info(
                "FPU %r: no plot data for positional repeatability found" % fpu_id
            )
            continue

        if "B" in plot_selection:
            pos_rep_result = ddict["positional_repeatability_result"]
            result_alpha = pos_rep_result["analysis_results_alpha"]
            result_beta = pos_rep_result["analysis_results_beta"]

            plot_pos_rep(fpu_id, result_alpha, result_beta, opts)

        if (CALIBRATION_PLOTSET | set(PLOT_FIT)) & plot_selection:
            pos_rep_result = ddict["positional_repeatability_result"]
            result_alpha = pos_rep_result["analysis_results_alpha"]
            result_beta = pos_rep_result["analysis_results_beta"]

            gear_correction = fit_gearbox_correction(
                fpu_id, result_alpha, result_beta, return_intermediate_results=True
            )
            fit_alpha = gear_correction["coeffs"]["coeffs_alpha"]
            if CALIBRATION_PLOTSET & plot_selection:
                if fit_alpha is None:
                    print("no parameters found for FPU %s, %s arm" % (fpu_id, "alpha"))
                else:
                    plot_gearbox_calibration(
                        fpu_id, "alpha", plot_selection=plot_selection, **fit_alpha
                    )

                    if PLOT_CORR in plot_selection:
                        plot_correction(fpu_id, "alpha", **fit_alpha)

            fit_beta = gear_correction["coeffs"]["coeffs_beta"]
            if CALIBRATION_PLOTSET & plot_selection:
                if fit_beta is None:
                    print("no parameters found for FPU %s, %s arm" % (fpu_id, "beta"))
                else:
                    plot_gearbox_calibration(
                        fpu_id, "beta", plot_selection=plot_selection, **fit_beta
                    )
                    if PLOT_CORR in plot_selection:
                        plot_correction(fpu_id, "beta", **fit_beta)

            if PLOT_FIT in plot_selection:
                plot_measured_vs_expected_points(fpu_id, **gear_correction)

        if "R" in plot_selection:
            pos_ver_result = ddict["positional_verification_result"]
            pos_rep_result = ddict["positional_repeatability_result"]

            if pos_ver_result is not None:
                plot_pos_ver(fpu_id, pos_ver_result, pos_rep_result, opts)
