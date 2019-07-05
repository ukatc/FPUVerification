# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from inspect import cleandoc

POS_VER_NA = "positional verification   : n/a"
POS_VER_NA_CSV = "positional verification,n/a"

POS_VER_CALPARS = """positional verification : calibration_pars = {calibration_pars}"""

POS_VER_CALPARS_CSV = """positional verification,calibration_pars,{calibration_pars}"""

POS_VER_ERRMSG = (
    "positional verification : message = {error_message}, time/record = {time:.16}/{record-count},"
    " version = {algorithm_version}"
)

POS_VER_ERRMSG_CSV = (
    "positional verification,message,{error_message}, time,{time:.16},record,{record-count},"
    "version,{algorithm_version}"
)

POS_VER_RESULT_TERSE = cleandoc(
    """
    positional verification : passed           = {result},
    positional verification : posver_error 95 % perc.      = {posver_error_measures.percentiles[95]:8.4f} mm
    positional verification : time/record      = {time:.16}/{record-count}, version = {algorithm_version}"""
)

POS_VER_RESULT_COMPLETE = cleandoc(
    """
    positional verification : passed                        = {result}
    positional verification : pass_threshold                = {pass_threshold_mm} mm
    positional verification : posver_error 95 % perc.       = {posver_error_measures.percentiles[95]:8.4f} mm
    positional verification : posver_error max              = {posver_error_measures.max:8.4f} mm
    positional verification : arg_max_error (count, α, β)   = {arg_max_error}
    positional verification : min image quality             = {min_quality:5.3f}
    positional verification : time/record                   = {time:.16}/{record-count}
    positional verification : calibration algorithm version = {algorithm_version}
    positional verification : git version                   = {git_version}"""
)


POS_VER_RESULT_LONG = cleandoc(
    """
    positional verification : passed                        = {result}
    positional verification : pass_threshold                = {pass_threshold_mm} mm
    positional verification : posver_error mean             = {posver_error_measures.mean:8.4f} mm
    positional verification : posver_error 95 % perc.       = {posver_error_measures.percentiles[95]:8.4f} mm
    positional verification : posver_error max              = {posver_error_measures.max:8.4f} mm
    positional verification : arg_max_error (count, α, β)   = {arg_max_error}
    positional verification : min image quality             = {min_quality:5.3f}
    positional verification : time/record                   = {time:.16}/{record-count}
    positional verification : calibration algorithm version = {algorithm_version}
    positional verification : git version                   = {git_version}"""
)

POS_VER_RESULT_EXTENDED = cleandoc(
    """
    positional verification : passed                        = {result}
    positional verification : pass_threshold                = {pass_threshold_mm} mm
    positional verification : posver_error mean             = {posver_error_measures.mean:8.4f} mm
    positional verification : posver_error 50 % perc.       = {posver_error_measures.percentiles[50]:8.4f} mm
    positional verification : posver_error 90 % perc.       = {posver_error_measures.percentiles[90]:8.4f} mm
    positional verification : posver_error 95 % perc.       = {posver_error_measures.percentiles[95]:8.4f} mm
    positional verification : posver_error max              = {posver_error_measures.max:8.4f} mm
    positional verification : arg_max_error (count, α, β)   = {arg_max_error} ([1], degree, degree)
    positional verification : min image quality             = {min_quality:5.3f}
    positional verification : time/record                   = {time:.16}/{record-count}
    positional verification : calibration algorithm version = {algorithm_version}
    positional verification : git version                   = {git_version}"""
)

POS_VER_RESULT_CSV = cleandoc(
    """
    positional verification,passed,{result}
    positional verification,pass_threshold,{pass_threshold_mm}
    positional verification,posver_error mean      ,{posver_error_measures.mean:8.4f}
    positional verification,posver_error 50 % perc.,{posver_error_measures.percentiles[50]:8.4f}
    positional verification,posver_error 90 % perc.,{posver_error_measures.percentiles[90]:8.4f}
    positional verification,posver_error 95 % perc.,{posver_error_measures.percentiles[95]:8.4f}
    positional verification,posver_error max       ,{posver_error_measures.max:8.4f}
    positional verification,arg_max_error,count,{arg_max_error[0]},α,{arg_max_error[1]},β,{arg_max_error[2]}
    positional verification,min image quality,{min_quality:5.3f}
    positional verification,time,{time:.16},record,{record-count}
    positional verification,calibration algorithm version,{algorithm_version}
    positional verification,git version,{git_version}"""
)

POS_VER_ERRVALS = "positional verification : posver_errors = {posver_error_measures}"

POS_VER_IMAGES = """\
positional verification calibration algorithm version for images: {gearbox_algorithm_version!r}
positional verification images : {images!r}"""

POS_VER_IMAGES_MAPFILE = (
    "positional verification calibration file: {calibration_mapfile!r}"
)

POS_VER_NOIMAGES = "positional verification images : {!r}"

POS_VER_GEARCORR = "gearbox correction = {gearbox_correction!r}"
