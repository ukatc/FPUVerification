# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from inspect import cleandoc

MIN_GEARBOX_CORRECTION_VERSION_REPORT = (5, 0, 2)

POS_REP_NA = "positional repeatability  : n/a"
POS_REP_NA_CSV = "positional repeatability,n/a"

POS_REP_CALPARS = (
    """positional repeatability: calibration_pars = {calibration_pars!r}"""
)

POS_REP_GEARCOR_OLD = cleandoc(
    """positional repeatability: gearbox correction alpha algorithm                 = {gearbox_correction[coeffs][coeffs_alpha][algorithm]}
       positional repeatability: gearbox correction alpha num support / data points = {gearbox_correction[coeffs][coeffs_alpha][num_support_points]} / {gearbox_correction[coeffs][coeffs_alpha][num_data_points]}
       positional repeatability: gearbox correction alpha R                         = {gearbox_correction[coeffs][coeffs_alpha][R]:6.5} mm
       positional repeatability: gearbox correction beta algorithm                  = {gearbox_correction[coeffs][coeffs_beta][algorithm]}
       positional repeatability: gearbox correction beta num support / data points  = {gearbox_correction[coeffs][coeffs_beta][num_support_points]} / {gearbox_correction[coeffs][coeffs_beta][num_data_points]}
       positional repeatability: gearbox correction beta R midpoint                 = {gearbox_correction[coeffs][coeffs_beta][R]:6.5} mm

"""
)

POS_REP_GEARCOR_TERSE = cleandoc(
    """positional repeatability: gearbox correction alpha num support / data points      = {gearbox_correction[coeffs][coeffs_alpha][num_support_points]} / {gearbox_correction[coeffs][coeffs_alpha][num_data_points]}
       positional repeatability: gearbox correction beta num support / data points       = {gearbox_correction[coeffs][coeffs_beta][num_support_points]} / {gearbox_correction[coeffs][coeffs_beta][num_data_points]}

       positional repeatability: gearbox correction alpha RMS fit                        = {gearbox_correction[expected_vals][alpha][RMS]:7.2f} μm
       positional repeatability: gearbox correction alpha fit error 95 % percentile:     = {gearbox_correction[expected_vals][alpha][pcdict][95]:7.2f} μm
       positional repeatability: gearbox correction beta RMS fit                         = {gearbox_correction[expected_vals][beta][RMS]:7.2f} μm
       positional repeatability: gearbox correction beta fit error 95 % percentile:      = {gearbox_correction[expected_vals][beta][pcdict][95]:7.2f} μm

"""
)

POS_REP_GEARCOR_COMPLETE = cleandoc(
    """positional repeatability: gearbox correction alpha algorithm                      = {gearbox_correction[coeffs][coeffs_alpha][algorithm]}
       positional repeatability: gearbox correction alpha num support / data points      = {gearbox_correction[coeffs][coeffs_alpha][num_support_points]} / {gearbox_correction[coeffs][coeffs_alpha][num_data_points]}
       positional repeatability: gearbox correction beta num support / data points       = {gearbox_correction[coeffs][coeffs_beta][num_support_points]} / {gearbox_correction[coeffs][coeffs_beta][num_data_points]}

       positional repeatability: gearbox correction alpha RMS fit                        = {gearbox_correction[expected_vals][alpha][RMS]:7.2f} μm
       positional repeatability: gearbox correction alpha fit error 50 % percentile:     = {gearbox_correction[expected_vals][alpha][pcdict][50]:7.2f} μm
       positional repeatability: gearbox correction alpha fit error 90 % percentile:     = {gearbox_correction[expected_vals][alpha][pcdict][90]:7.2f} μm
       positional repeatability: gearbox correction alpha fit error 95 % percentile:     = {gearbox_correction[expected_vals][alpha][pcdict][95]:7.2f} μm
       positional repeatability: gearbox correction alpha maximum fit error              = {gearbox_correction[expected_vals][alpha][max_val]:7.2f} μm

       positional repeatability: gearbox correction beta RMS fit                         = {gearbox_correction[expected_vals][beta][RMS]:7.2f} μm
       positional repeatability: gearbox correction beta fit error 50 % percentile:      = {gearbox_correction[expected_vals][beta][pcdict][50]:7.2f} μm
       positional repeatability: gearbox correction beta fit error 90 % percentile:      = {gearbox_correction[expected_vals][beta][pcdict][90]:7.2f} μm
       positional repeatability: gearbox correction beta fit error 95 % percentile:      = {gearbox_correction[expected_vals][beta][pcdict][95]:7.2f} μm
       positional repeatability: gearbox correction beta maximum fit error               = {gearbox_correction[expected_vals][beta][max_val]:7.2f} μm


"""
    )
POS_REP_GEARCOR_LONG = cleandoc(
    """positional repeatability: gearbox correction alpha algorithm                      = {gearbox_correction[coeffs][coeffs_alpha][algorithm]}
       positional repeatability: gearbox correction alpha num support / data points      = {gearbox_correction[coeffs][coeffs_alpha][num_support_points]} / {gearbox_correction[coeffs][coeffs_alpha][num_data_points]}
       positional repeatability: gearbox correction beta num support / data points       = {gearbox_correction[coeffs][coeffs_beta][num_support_points]} / {gearbox_correction[coeffs][coeffs_beta][num_data_points]}

       positional repeatability: gearbox correction alpha RMS fit                        = {gearbox_correction[expected_vals][alpha][RMS]:7.2f} μm
       positional repeatability: gearbox correction alpha fit error 50 % percentile:     = {gearbox_correction[expected_vals][alpha][pcdict][50]:7.2f} μm
       positional repeatability: gearbox correction alpha fit error 90 % percentile:     = {gearbox_correction[expected_vals][alpha][pcdict][90]:7.2f} μm
       positional repeatability: gearbox correction alpha fit error 95 % percentile:     = {gearbox_correction[expected_vals][alpha][pcdict][95]:7.2f} μm
       positional repeatability: gearbox correction alpha maximum fit error              = {gearbox_correction[expected_vals][alpha][max_val]:7.2f} μm
       positional repeatability: gearbox correction alpha radius RMS error               = {gearbox_correction[expected_vals][alpha][radius_RMS]:7.5f} mm

       positional repeatability: gearbox correction beta RMS fit                         = {gearbox_correction[expected_vals][beta][RMS]:7.2f} μm
       positional repeatability: gearbox correction beta fit error 50 % percentile:      = {gearbox_correction[expected_vals][beta][pcdict][50]:7.2f} μm
       positional repeatability: gearbox correction beta fit error 90 % percentile:      = {gearbox_correction[expected_vals][beta][pcdict][90]:7.2f} μm
       positional repeatability: gearbox correction beta fit error 95 % percentile:      = {gearbox_correction[expected_vals][beta][pcdict][95]:7.2f} μm
       positional repeatability: gearbox correction beta maximum fit error               = {gearbox_correction[expected_vals][beta][max_val]:7.2f} μm
       positional repeatability: gearbox correction beta radius RMS error                = {gearbox_correction[expected_vals][beta][radius_RMS]:7.5f} mm


"""
    )
POS_REP_GEARCOR_EXTENDED = cleandoc(
    """positional repeatability: gearbox correction alpha algorithm                      = {gearbox_correction[coeffs][coeffs_alpha][algorithm]}
       positional repeatability: gearbox correction alpha num support / data points      = {gearbox_correction[coeffs][coeffs_alpha][num_support_points]} / {gearbox_correction[coeffs][coeffs_alpha][num_data_points]}

       positional repeatability: gearbox correction alpha RMS fit                        = {gearbox_correction[expected_vals][alpha][RMS]:7.2f} μm
       positional repeatability: gearbox correction alpha fit error 50 % percentile:     = {gearbox_correction[expected_vals][alpha][pcdict][50]:7.2f} μm
       positional repeatability: gearbox correction alpha fit error 90 % percentile:     = {gearbox_correction[expected_vals][alpha][pcdict][90]:7.2f} μm
       positional repeatability: gearbox correction alpha fit error 95 % percentile:     = {gearbox_correction[expected_vals][alpha][pcdict][95]:7.2f} μm
       positional repeatability: gearbox correction alpha maximum fit error              = {gearbox_correction[expected_vals][alpha][max_val]:7.2f} μm
       positional repeatability: gearbox correction alpha radius RMS error               = {gearbox_correction[expected_vals][alpha][radius_RMS]:7.5f} mm

       positional repeatability: gearbox correction beta RMS fit                         = {gearbox_correction[expected_vals][beta][RMS]:7.2f} μm
       positional repeatability: gearbox correction beta fit error 50 % percentile:      = {gearbox_correction[expected_vals][beta][pcdict][50]:7.2f} μm
       positional repeatability: gearbox correction beta fit error 90 % percentile:      = {gearbox_correction[expected_vals][beta][pcdict][90]:7.2f} μm
       positional repeatability: gearbox correction beta fit error 95 % percentile:      = {gearbox_correction[expected_vals][beta][pcdict][95]:7.2f} μm
       positional repeatability: gearbox correction beta maximum fit error               = {gearbox_correction[expected_vals][beta][max_val]:7.2f} μm
       positional repeatability: gearbox correction beta radius RMS error                = {gearbox_correction[expected_vals][beta][radius_RMS]:7.5f} mm


       positional repeatability: gearbox correction alpha coefs camera_offset_rad        = {gearbox_correction[coeffs][coeffs_alpha][camera_offset_rad]:7.2f}
       positional repeatability: gearbox correction beta fixpoint_rad                    =  {gearbox_correction[coeffs][coeffs_alpha][beta_fixpoint_rad]:7.2f}
       positional repeatability: gearbox correction alpha ellipsis angle                 =   {gearbox_correction[coeffs][coeffs_alpha][psi]:7.2f} rad
       positional repeatability: gearbox correction alpha ellipsis stretch               =  {gearbox_correction[coeffs][coeffs_alpha][stretch]:7.2f} [1]
       positional repeatability: gearbox correction alpha R                              =  {gearbox_correction[coeffs][coeffs_alpha][R]:6.5} mm
       positional repeatability: gearbox correction beta algorithm                       = {gearbox_correction[coeffs][coeffs_beta][algorithm]}
       positional repeatability: gearbox correction beta num support / data points       = {gearbox_correction[coeffs][coeffs_beta][num_support_points]} / {gearbox_correction[coeffs][coeffs_beta][num_data_points]}
       positional repeatability: gearbox correction beta coefs beta0_rad                 = {gearbox_correction[coeffs][coeffs_beta][beta0_rad]:7.2f}
       positional repeatability: gearbox correction alpha fixpoint_rad                   = {gearbox_correction[coeffs][coeffs_beta][alpha_fixpoint_rad]:7.2f}
       positional repeatability: gearbox correction beta ellipsis angle                  =  {gearbox_correction[coeffs][coeffs_beta][psi]:7.2f} rad
       positional repeatability: gearbox correction beta ellipsis stretch                = {gearbox_correction[coeffs][coeffs_beta][stretch]:7.2f} [1]
       positional repeatability: gearbox correction beta R midpoint                      = {gearbox_correction[coeffs][coeffs_beta][R]:6.5} mm

"""
    )


POS_REP_GEARALGO = cleandoc(
    """positional repeatability: gearbox correction algorithm version                    = {gearbox_correction[version]}"""
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
    positional repeatability: alpha 95% perc. = {posrep_alpha_measures.percentiles[95]:6.4f} mm
    positional repeatability: beta 95% perc.  = {posrep_beta_measures.percentiles[95]:6.4f} mm
    positional repeatability: time/record   = {time:.16}/{record-count}, version = {algorithm_version}"""
)

POS_REP_RESULT_COMPLETE = cleandoc(
    """
    positional repeatability: passed          = {result}
    positional repeatability: pass_threshold  = {pass_threshold_mm:6.4f} mm
    positional repeatability: alpha_mean      = {posrep_alpha_measures.mean:6.4f} mm
    positional repeatability: alpha 95% perc. = {posrep_alpha_measures.percentiles[95]:6.4f} mm
    positional repeatability: alpha_max       = {posrep_alpha_measures.max:6.4f} mm
    positional repeatability: beta_mean       = {posrep_beta_measures.mean:6.4f} mm
    positional repeatability: beta 95% perc.  = {posrep_beta_measures.percentiles[95]:6.4f} mm
    positional repeatability: beta_max        = {posrep_beta_measures.max:6.4f} mm
    positional repeatability: arg_max_alpha   = {arg_max_alpha_error:+9.4f} degrees
    positional repeatability: arg_max_beta    = {arg_max_beta_error:+9.4f} degrees
    positional repeatability: alpha quality   = {min_quality_alpha:5.3f}
    positional repeatability: beta quality    = {min_quality_beta:5.3f}
    positional repeatability: time/record     = {time:.16}/{record-count}
    positional repeatability: anlysis version = {algorithm_version}
    positional repeatability: git version     = {git_version}"""
)


POS_REP_RESULT_LONG = cleandoc(
    """
    positional repeatability: passed          = {result}
    positional repeatability: pass_threshold  = {pass_threshold_mm:6.4f} mm
    positional repeatability: alpha_mean      = {posrep_alpha_measures.mean:6.4f} mm
    positional repeatability: alpha 50% perc. = {posrep_alpha_measures.percentiles[50]:6.4f} mm
    positional repeatability: alpha 90% perc. = {posrep_alpha_measures.percentiles[90]:6.4f} mm
    positional repeatability: alpha 95% perc. = {posrep_alpha_measures.percentiles[95]:6.4f} mm
    positional repeatability: alpha_max       = {posrep_alpha_measures.max:6.4f} mm
    positional repeatability: beta_mean       = {posrep_beta_measures.mean:6.4f} mm
    positional repeatability: beta 50% perc.  = {posrep_beta_measures.percentiles[50]:6.4f} mm
    positional repeatability: beta 90% perc.  = {posrep_beta_measures.percentiles[90]:6.4f} mm
    positional repeatability: beta 95% perc.  = {posrep_beta_measures.percentiles[95]:6.4f} mm
    positional repeatability: beta_max        = {posrep_beta_measures.max:6.4f} mm
    positional repeatability: arg_max_alpha   = {arg_max_alpha_error:+9.4f} degrees
    positional repeatability: arg_max_beta    = {arg_max_beta_error:+9.4f} degrees
    positional repeatability: alpha quality   = {min_quality_alpha:5.3f}
    positional repeatability: beta quality    = {min_quality_beta:5.3f}
    positional repeatability: time/record     = {time:.16}/{record-count}
    positional repeatability: anlysis version = {algorithm_version}
    positional repeatability: git version     = {git_version}"""
)

POS_REP_RESULT_EXTENDED = cleandoc(
    """
    positional repeatability: passed          = {result}
    positional repeatability: pass_threshold  = {pass_threshold_mm:6.4f} mm
    positional repeatability: alpha_mean      = {posrep_alpha_measures.mean:6.4f} mm
    positional repeatability: alpha 50% perc. = {posrep_alpha_measures.percentiles[50]:6.4f} mm
    positional repeatability: alpha 90% perc. = {posrep_alpha_measures.percentiles[90]:6.4f} mm
    positional repeatability: alpha 95% perc. = {posrep_alpha_measures.percentiles[95]:6.4f} mm
    positional repeatability: alpha_max       = {posrep_alpha_measures.max:6.4f} mm
    positional repeatability: beta_mean       = {posrep_beta_measures.mean:6.4f} mm
    positional repeatability: beta 50% perc.  = {posrep_beta_measures.percentiles[50]:6.4f} mm
    positional repeatability: beta 90% perc.  = {posrep_beta_measures.percentiles[90]:6.4f} mm
    positional repeatability: beta 95% perc.  = {posrep_beta_measures.percentiles[95]:6.4f} mm
    positional repeatability: beta_max        = {posrep_beta_measures.max:6.4f} mm
    positional repeatability: arg_max_alpha   = {arg_max_alpha_error:+9.4f} degrees
    positional repeatability: arg_max_beta    = {arg_max_beta_error:+9.4f} degrees
    positional repeatability: alpha quality   = {min_quality_alpha:5.3f}
    positional repeatability: beta quality    = {min_quality_beta:5.3f}
    positional repeatability: time/record     = {time:.16}/{record-count}
    positional repeatability: anlysis version = {algorithm_version}
    positional repeatability: git version     = {git_version}"""
)

POS_REP_RESULT_CSV = cleandoc(
    """
    positional repeatability,passed,{result}
    positional repeatability,pass_threshold,{pass_threshold_mm:6.4f}
    positional repeatability,alpha_mean     ,{posrep_alpha_measures.mean:6.4f}
    positional repeatability,alpha 50% perc.,{posrep_alpha_measures.percentiles[50]:6.4f}
    positional repeatability,alpha 90% perc.,{posrep_alpha_measures.percentiles[90]:6.4f}
    positional repeatability,alpha 95% perc.,{posrep_alpha_measures.percentiles[95]:6.4f}
    positional repeatability,alpha_max      ,{posrep_alpha_measures.max:6.4f}
    positional repeatability,beta_mean      ,{posrep_beta_measures.mean:6.4f}
    positional repeatability,beta 50% perc.,{posrep_beta_measures.percentiles[50]:6.4f}
    positional repeatability,beta 90% perc.,{posrep_beta_measures.percentiles[90]:6.4f}
    positional repeatability,beta 95% perc.,{posrep_beta_measures.percentiles[95]:6.4f}
    positional repeatability,beta_max       ,{posrep_beta_measures.max:6.4f}
    positional repeatability,alpha quality,{min_quality_alpha:5.3f}
    positional repeatability,beta quality,{min_quality_beta:5.3f}
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
