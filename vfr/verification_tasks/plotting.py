# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
from vfr.db.retrieval import get_data


import numpy as np
import types
import matplotlib.pyplot as plt


def plot_pos_rep(fpu_id, analysis_results_alpha, analysis_results_beta):
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
            x, y = np.array(sweep_series).T[3:5]
            ax.scatter(x, y, c=color, label="%s %s" % (label, direction),
                       alpha=0.7, edgecolors='none')

            ax.legend()
            ax.grid(True)
            plt.title(fpu_id)

        plt.show()


def plot(dbe, opts):

    plot_selection = dbe.opts.plot_selection
    for count, fpu_id in enumerate(dbe.eval_fpuset):
        ddict = vars(get_data(dbe, fpu_id))
        if type(fpu_id) == types.IntType:
            fpu_id = dbe.fpu_config[fpu_id]["serialnumber"]

        if "A" in plot_selection:
            pos_rep_result = ddict["positional_repeatability_result"]
            result_alpha = pos_rep_result["analysis_results_alpha"]
            result_beta = pos_rep_result["analysis_results_beta"]

            lines = plot_pos_rep(fpu_id, result_alpha, result_beta)
