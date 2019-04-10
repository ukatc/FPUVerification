# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from inspect import cleandoc

POS_VER_NA = "positional verification   : n/a"

POS_VER_CALPARS = """positional verification : calibration_pars = {calibration_pars}"""

POS_VER_ERRMSG = (
    "positional verification : message = {error_message}, time/record = {time:.16}/{record-count},"
    " version = {algorithm_version}"
)

POS_VER_RESULT_TERSE = cleandoc(
    """
    positional verification : passed           = {result},
    positional verification : posver_error_max = {posver_error_max_mm:8.4f} mm,
    positional verification : time/record      = {time:.16}/{record-count}, version = {algorithm_version}"""
)

POS_VER_RESULT_COMPLETE = cleandoc(
    """
    positional verification : passed                       = {result}
    positional verification : pass_threshold               = {pass_threshold_mm}
    positional verification : posver_error_max             = {posver_error_max_mm:8.4f} mm
    positional verification : arg_max_error (count, α, β)  = {arg_max_error}
    positional verification : min image quality            = {min_quality:8.4f}
    positional verification : time/record                  = {time:.16}/{record-count}
    positional verification : analysis version             = {algorithm_version}
    positional verification : git version                  = {git_version}"""
)


POS_VER_RESULT_LONG = cleandoc(
    """
    positional verification : passed                       = {result}
    positional verification : pass_threshold               = {pass_threshold_mm}
    positional verification : posver_error_max             = {posver_error_max_mm:8.4f} mm
    positional verification : arg_max_error (count, α, β)  = {arg_max_error}
    positional verification : min image quality            = {min_quality:8.4f}
    positional verification : time/record                  = {time:.16}/{record-count}
    positional verification : analysis version             = {algorithm_version}
    positional verification : git version                  = {git_version}"""
)

POS_VER_RESULT_EXTENDED = cleandoc(
    """
    positional verification : passed                       = {result}
    positional verification : pass_threshold               = {pass_threshold_mm}
    positional verification : posver_error_max             = {posver_error_max_mm:8.4f} mm
    positional verification : arg_max_error (count, α, β)  = {arg_max_error}
    positional verification : min image quality            = {min_quality:8.4f}
    positional verification : time/record                  = {time:.16}/{record-count}
    positional verification : analysis version             = {algorithm_version}
    positional verification : git version                  = {git_version}"""
)

POS_VER_ERRVALS = "positional verification : posver_errors = {posver_error}"

POS_VER_ARESULTS = "positional verification : posver_errors = {posver_error}"

POS_VER_IMAGES = "positional verification images : {images!r}"

POS_VER_IMAGES_MAPFILE = (
    "positional verification calibration file: {calibration_mapfile!r}"
)

POS_VER_NOIMAGES = "positional verification images : {!r}"

POS_VER_GEARCORR = "gearbox correction = {gearbox_correction!r}"
