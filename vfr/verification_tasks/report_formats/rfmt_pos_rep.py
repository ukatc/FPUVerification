# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from inspect import cleandoc

POS_REP_NA = "positional repeatability: n/a"

POS_REP_CALPARS = (
    """Positional repeatability: calibration_pars = {calibration_pars!r}"""
)

POS_REP_GEARCOR = (
    """positional repeatability: gearbox correction = {gearbox_correction}"""
)

POS_REP_GEARALGO = cleandoc(
    """
    positional repeatability: gearbox correction algorithm version = {algorithm_version}"""
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

POS_REP_ERRMSG = (
    "Positional repeatability: message = {error_message}, time/record = {time:.16}/{record-count},"
    " version = {algorithm_version}"
)

POS_REP_IMAGES_ALPHA = "positional repeatability images alpha: {images_alpha!r}"

POS_REP_IMAGES_BETA = "positional repeatability images beta: {images_beta!r}"

POS_REP_WAVEFORM_PARS = (
    "positional repeatability images / waveform parameters: {waveform_pars!r}"
)
