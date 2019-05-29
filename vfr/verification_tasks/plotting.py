# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
from vfr.db.retrieval import get_data


import numpy as np
import matplotlib.pyplot as plt


def plot_pos_rep(analysis_results_alpha, analysis_results_beta):
    fig, ax = plt.subplots()
    for color in ['tab:blue', 'tab:orange', 'tab:green']:
        n = 750
        x, y = np.random.rand(2, n)
        scale = 200.0 * np.random.rand(n)
        ax.scatter(x, y, c=color, s=scale, label=color,
                   alpha=0.3, edgecolors='none')

    ax.legend()
    ax.grid(True)

    plt.show()


def plot(dbe, opts):

    plot_selection = dbe.opts.plot_selection
    for count, fpu_id in enumerate(dbe.eval_fpuset):
        ddict = vars(get_data(dbe, fpu_id))

        if "A" in plot_selection:
            pos_rep_result = ddict["positional_repeatability_result"]
            result_alpha = pos_rep_result["analysis_results_alpha"]
            result_beta = pos_rep_result["analysis_results_beta"]

            lines = plot_pos_rep(result_alpha, result_beta)
