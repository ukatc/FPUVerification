# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from inspect import cleandoc

PUP_ALN_NA = "pupil_alignment test    : n/a"

PUP_ALN_CALPARS = """pupil alignment    : calibration_pars = {calibration_pars!r}"""

PUP_ALN_ERRMSG = "pupil alignment: message = {error_message}, time/record = {time:.16}/{record-count}"

PUP_ALN_RESULT_TERSE = cleandoc(
    """
    pupil alignment         : passed        = {result},
    pupil alignment         : chassis error =  {measures[chassis_error]} mm,
    pupil alignment         : alpha error   =  {measures[alpha_error]} mm,
    pupil alignment         : beta error    =  {measures[beta_error]} mm,
    pupil alignment         : total error   =  {measures[total_error]} mm,
    pupil alignment         : time/record   = {time:.16}/{record-count}"""
)


PUP_ALN_RESULT_COMPLETE = cleandoc(
    """
    pupil alignment         : passed            = {result}
    pupil alignment         : pass_threshold    = {pass_threshold_mm:8.4f}
    pupil alignment         : chassis error     = {measures[chassis_error]:8.4f} mm
    pupil alignment         : alpha error       = {measures[alpha_error]:8.4f} mm
    pupil alignment         : beta error        = {measures[beta_error]:8.4f} mm
    pupil alignment         : total error       = {measures[total_error]:8.4f} mm
    pupil alignment         : time/record       = {time:.16}/{record-count}
    pupil alignment         : algorithm version = {algorithm_version}
    pupil alignment         : git version       = {git_version}"""
)


PUP_ALN_RESULT_LONG = cleandoc(
    """
    pupil alignment         : passed            = {result}
    pupil alignment         : pass_threshold    = {pass_threshold_mm:8.4f}
    pupil alignment         : chassis error     = {measures[chassis_error]:8.4f} mm
    pupil alignment         : alpha error       = {measures[alpha_error]:8.4f} mm
    pupil alignment         : beta error        = {measures[beta_error]:8.4f} mm
    pupil alignment         : total error       = {measures[total_error]:8.4f} mm
    pupil alignment         : time/record       = {time:.16}/{record-count}
    pupil alignment         : algorithm version = {algorithm_version}
    pupil alignment         : git version       = {git_version}"""
)


PUP_ALN_RESULT_EXTENDED = cleandoc(
    """
    pupil alignment         : passed            = {result}
    pupil alignment         : pass_threshold    = {pass_threshold_mm:8.4f}
    pupil alignment         : chassis error     = {measures[chassis_error]:8.4f} mm
    pupil alignment         : alpha error       = {measures[alpha_error]:8.4f} mm
    pupil alignment         : beta error        = {measures[beta_error]:8.4f} mm
    pupil alignment         : total error       = {measures[total_error]:8.4f} mm
    pupil alignment         : time/record       = {time:.16}/{record-count}
    pupil alignment         : algorithm version = {algorithm_version}
    pupil alignment         : git version       = {git_version}"""
)
