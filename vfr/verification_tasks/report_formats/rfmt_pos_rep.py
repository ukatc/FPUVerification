# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from inspect import cleandoc

POS_REP_NA = "positional repeatability  : n/a"
POS_REP_NA_CSV = "positional repeatability,n/a"

POS_REP_CALPARS = (
    """positional repeatability: calibration_pars = {calibration_pars!r}"""
)

POS_REP_GEARCOR = cleandoc(
    """positional repeatability: gearbox correction alpha algorithm                 = {gearbox_correction[coeffs_alpha][algorithm]}
       positional repeatability: gearbox correction alpha num support / data points = {gearbox_correction[coeffs_alpha][num_support_points]} / {gearbox_correction[coeffs_alpha][num_data_points]}
       positional repeatability: gearbox correction alpha coefs                     a = {gearbox_correction[coeffs_alpha][a]:7.5}, b={gearbox_correction[coeffs_alpha][b]:7.5}
       positional repeatability: gearbox correction alpha R                         = {gearbox_correction[coeffs_alpha][R]:6.5}
       positional repeatability: gearbox correction beta algorithm                  = {gearbox_correction[coeffs_beta][algorithm]}
       positional repeatability: gearbox correction beta num support / data points  = {gearbox_correction[coeffs_beta][num_support_points]} / {gearbox_correction[coeffs_beta][num_data_points]}
       positional repeatability: gearbox correction beta coefs                      a = {gearbox_correction[coeffs_beta][a]:7.5}, b={gearbox_correction[coeffs_beta][b]:7.5}
       positional repeatability: gearbox correction beta R                          = {gearbox_correction[coeffs_beta][R]:6.5}

"""
)

POS_REP_GEARALGO = cleandoc(
    """positional repeatability: gearbox correction algorithm version               = {gearbox_correction[version]}"""
)

POS_REP_CALPARS_CSV = (
    """positional repeatability,calibration_pars,{calibration_pars!r}"""
)

POS_REP_GEARCOR_CSV = (
    """positional repeatability,gearbox correction,{gearbox_correction}"""
)

POS_REP_GEARALGO_CSV = cleandoc(
    """
    positional repeatability,gearbox correction algorithm version,{algorithm_version}"""
)

POS_REP_RESULT_TERSE = cleandoc(
    """
    positional repeatability: passed        = {result},
    positional repeatability: alpha_max     = {posrep_alpha_max_mm:8.4f} mm,
    positional repeatability: beta_max      = {posrep_beta_max_mm:8.4f} mm,
    positional repeatability: posrep_rss_mm = {posrep_rss_mm:8.4f} mm,
    positional repeatability: time/record   = {time:.16}/{record-count}, version = {algorithm_version}"""
)

POS_REP_RESULT_COMPLETE = cleandoc(
    """
    positional repeatability: passed          = {result}
    positional repeatability: pass_threshold  = {pass_threshold_mm:8.4f} mm
    positional repeatability: alpha_max       = {posrep_alpha_max_mm:8.4f} mm
    positional repeatability: beta_max        = {posrep_beta_max_mm:8.4f} mm
    positional repeatability: posrep_rss_mm   = {posrep_rss_mm:8.4f} mm
    positional repeatability: arg_max_alpha   = {arg_max_alpha_error:8.4f}
    positional repeatability: arg_max_beta    = {arg_max_beta_error:8.4f}
    positional repeatability: alpha quality   = {min_quality_alpha:8.4f}
    positional repeatability: beta quality    = {min_quality_beta:8.4f}
    positional repeatability: time/record     = {time:.16}/{record-count}
    positional repeatability: anlysis version = {algorithm_version}
    positional repeatability: git version     = {git_version}"""
)


POS_REP_RESULT_LONG = cleandoc(
    """
    positional repeatability: passed          = {result}
    positional repeatability: pass_threshold  = {pass_threshold_mm:8.4f} mm
    positional repeatability: alpha_max       = {posrep_alpha_max_mm:8.4f} mm
    positional repeatability: beta_max        = {posrep_beta_max_mm:8.4f} mm
    positional repeatability: posrep_rss_mm   = {posrep_rss_mm:8.4f} mm
    positional repeatability: arg_max_alpha   = {arg_max_alpha_error:8.4f}
    positional repeatability: arg_max_beta    = {arg_max_beta_error:8.4f}
    positional repeatability: alpha quality   = {min_quality_alpha:8.4f}
    positional repeatability: beta quality    = {min_quality_beta:8.4f}
    positional repeatability: time/record     = {time:.16}/{record-count}
    positional repeatability: anlysis version = {algorithm_version}
    positional repeatability: git version     = {git_version}"""
)

POS_REP_RESULT_EXTENDED = cleandoc(
    """
    positional repeatability: passed          = {result}
    positional repeatability: pass_threshold  = {pass_threshold_mm:8.4f} mm
    positional repeatability: alpha_max       = {posrep_alpha_max_mm:8.4f} mm
    positional repeatability: beta_max        = {posrep_beta_max_mm:8.4f} mm
    positional repeatability: posrep_rss_mm   = {posrep_rss_mm:8.4f} mm
    positional repeatability: arg_max_alpha   = {arg_max_alpha_error:8.4f}
    positional repeatability: arg_max_beta    = {arg_max_beta_error:8.4f}
    positional repeatability: alpha quality   = {min_quality_alpha:8.4f}
    positional repeatability: beta quality    = {min_quality_beta:8.4f}
    positional repeatability: time/record     = {time:.16}/{record-count}
    positional repeatability: anlysis version = {algorithm_version}
    positional repeatability: git version     = {git_version}"""
)

POS_REP_RESULT_CSV = cleandoc(
    """
    positional repeatability,passed,{result}
    positional repeatability,pass_threshold,{pass_threshold_mm:8.4f},mm
    positional repeatability,alpha_max,{posrep_alpha_max_mm:8.4f},mm
    positional repeatability,beta_max,{posrep_beta_max_mm:8.4f},mm
    positional repeatability,posrep_rss_mm,{posrep_rss_mm:8.4f},mm
    positional repeatability,arg_max_alpha,{arg_max_alpha_error:8.4f}
    positional repeatability,arg_max_beta,{arg_max_beta_error:8.4f}
    positional repeatability,alpha quality,{min_quality_alpha:8.4f}
    positional repeatability,beta quality,{min_quality_beta:8.4f}
    positional repeatability,time,{time:.16},record,{record-count}
    positional repeatability,anlysis version,{algorithm_version}
    positional repeatability,git version,{git_version}"""
)

POS_REP_ERRMSG = (
    "Positional repeatability: message = {error_message}, time/record = {time:.16}/{record-count},"
    " version = {algorithm_version}"
)

POS_REP_IMAGES = "positional repeatability images: {!r}"


POS_REP_IMAGES_MAPFILE = (
    "positional repeatability calibration file: {calibration_mapfile!r}"
)

POS_REP_IMAGES_ALPHA = "positional repeatability images alpha: {images_alpha!r}"

POS_REP_IMAGES_BETA = "positional repeatability images beta: {images_beta!r}"

POS_REP_WAVEFORM_PARS = (
    "positional repeatability images / waveform parameters: {waveform_pars!r}"
)


ALPHA_MAX_ANGLE = (
    "positional repeatability: alpha_max_at_angle = {posrep_alpha_max_at_angle!r}"
)

BETA_MAX_ANGLE = (
    "positional repeatability: beta_max_at_angle = {posrep_beta_max_at_angle!r}"
)

AN_RESULTS_ALPHA = (
    "positional repeatability: analysis_results_alpha = {analysis_results_alpha!r}"
)

AN_RESULTS_BETA = (
    "positional repeatability: analysis_results_beta = {analysis_results_beta!r}"
)
