# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from inspect import cleandoc

DAT_REP_NA = "datum repeatability       : n/a"
DAT_REP_NA_CSV = "datum repeatability,n/a"

DAT_REP_RESULT_TERSE = cleandoc(
    """
    datum repeatability     : {result},
    datum repeatability     : datum only 95 % percentile    = {datum_repeatability_datum_only.percentiles[95]:7.3} mm,
    datum repeatability     : datum only max residual count = {datum_repeatability_max_residual_datumed},
    datum repeatability     : datum+move 95 % percentile    = {datum_repeatability_moved.percentiles[95]:7.3} mm,
    datum repeatability     : datum+move max residual count = {datum_repeatability_max_residual_moved},
    datum repeatability     : time/record                   = {time:.16}/{record-count}, version = {algorithm_version}"""
)

DAT_REP_RESULT_COMPLETE = cleandoc(
    """
    datum repeatability     : {result},
    datum repeatability     : threshold                      = {pass_threshold_mm:8.4f}
    datum repeatability     : datum only mean error         = {datum_repeatability_datum_only.mean:7.3} mm,
    datum repeatability     : datum only 95 % percentile    = {datum_repeatability_datum_only.percentiles[95]:7.3} mm,
    datum repeatability     : datum only max error          = {datum_repeatability_datum_only.max:7.3} mm,
    datum repeatability     : datum only max residual count = {datum_repeatability_max_residual_datumed},
    datum repeatability     : datum+move mean error         = {datum_repeatability_moved.mean:7.3} mm,
    datum repeatability     : datum+move 95 % percentile    = {datum_repeatability_moved.percentiles[95]:7.3} mm,
    datum repeatability     : datum+move max error          = {datum_repeatability_moved.max:7.3} mm,
    datum repeatability     : datum+move max residual count = {datum_repeatability_max_residual_moved},
    datum repeatability     : datum only min quality        = {min_quality_datumed:8.4f}
    datum repeatability     : datum+move min quality        = {min_quality_moved:8.4f}
    datum repeatability     : time/record                   = {time:.16}/{record-count}
    datum repeatability     : git version                   = {git_version}
    datum repeatability     : image algorithm version       = {algorithm_version}"""
)

DAT_REP_RESULT_LONG = cleandoc(
    """
    datum repeatability     : {result},
    datum repeatability     : threshold                     = {pass_threshold_mm:8.4f}
    datum repeatability     : datum only mean error         = {datum_repeatability_datum_only.mean:7.3} mm,
    datum repeatability     : datum only 90 % percentile    = {datum_repeatability_datum_only.percentiles[90]:7.3} mm,
    datum repeatability     : datum only 95 % percentile    = {datum_repeatability_datum_only.percentiles[95]:7.3} mm,
    datum repeatability     : datum only max error          = {datum_repeatability_datum_only.max:7.3} mm,
    datum repeatability     : datum only max residual count = {datum_repeatability_max_residual_datumed},
    datum repeatability     : datum+move mean error         = {datum_repeatability_moved.mean:7.3} mm,
    datum repeatability     : datum+move 90 % percentile    = {datum_repeatability_moved.percentiles[90]:7.3} mm,
    datum repeatability     : datum+move 95 % percentile    = {datum_repeatability_moved.percentiles[95]:7.3} mm,
    datum repeatability     : datum+move max error          = {datum_repeatability_moved.max:7.3} mm,
    datum repeatability     : datum+move max residual count = {datum_repeatability_max_residual_moved},
    datum repeatability     : datum only min quality        = {min_quality_datumed:8.4f}
    datum repeatability     : datum+move min quality        = {min_quality_moved:8.4f}
    datum repeatability     : time/record                   = {time:.16}/{record-count}
    datum repeatability     : git version                   = {git_version}
    datum repeatability     : image algorithm version       = {algorithm_version}"""
)


DAT_REP_RESULT_EXTENDED = cleandoc(
    """
    datum repeatability     : {result},
    datum repeatability     : threshold                     = {pass_threshold_mm:8.4f}
    datum repeatability     : datum only mean error         = {datum_repeatability_datum_only.mean:7.3} mm,
    datum repeatability     : datum only 50 % percentile    = {datum_repeatability_datum_only.percentiles[50]:7.3} mm,
    datum repeatability     : datum only 90 % percentile    = {datum_repeatability_datum_only.percentiles[90]:7.3} mm,
    datum repeatability     : datum only 95 % percentile    = {datum_repeatability_datum_only.percentiles[95]:7.3} mm,
    datum repeatability     : datum only percentiles        = {datum_repeatability_datum_only.percentiles} mm,
    datum repeatability     : datum only max error          = {datum_repeatability_datum_only.max:7.3} mm,
    datum repeatability     : datum only max residual count = {datum_repeatability_max_residual_datumed},
    datum repeatability     : datum+move mean error         = {datum_repeatability_moved.mean:7.3} mm,
    datum repeatability     : datum+move 50 % percentile    = {datum_repeatability_moved.percentiles[50]:7.3} mm,
    datum repeatability     : datum+move 90 % percentile    = {datum_repeatability_moved.percentiles[90]:7.3} mm,
    datum repeatability     : datum+move 95 % percentile    = {datum_repeatability_moved.percentiles[95]:7.3} mm,
    datum repeatability     : datum+move percentiles        = {datum_repeatability_moved.percentiles} mm,
    datum repeatability     : datum+move max error          = {datum_repeatability_moved.max:7.3} mm,
    datum repeatability     : datum+move max residual count = {datum_repeatability_max_residual_moved},
    datum repeatability     : datum only min quality        = {min_quality_datumed:8.4f}
    datum repeatability     : datum+move min quality        = {min_quality_moved:8.4f}
    datum repeatability     : time/record                   = {time:.16}/{record-count}
    datum repeatability     : git version                   = {git_version}
    datum repeatability     : image algorithm version       = {algorithm_version}"""
)

DAT_REP_RESULT_CSV = cleandoc(
    """
    datum repeatability,{result},
    datum repeatability,threshold,{pass_threshold_mm:8.4f}
    datum repeatability,datum only mean error     ,{datum_repeatability_datum_only.mean:7.3}
    datum repeatability,datum only 50 % percentile,{datum_repeatability_datum_only.percentiles[50]:7.3}
    datum repeatability,datum only 90 % percentile,{datum_repeatability_datum_only.percentiles[90]:7.3}
    datum repeatability,datum only 95 % percentile,{datum_repeatability_datum_only.percentiles[95]:7.3}
    datum repeatability,datum+move mean error     ,{datum_repeatability_moved.mean:7.3}
    datum repeatability,datum+move 50 % percentile,{datum_repeatability_moved.percentiles[50]:7.3}
    datum repeatability,datum+move 90 % percentile,{datum_repeatability_moved.percentiles[90]:7.3}
    datum repeatability,datum+move 95 % percentile,{datum_repeatability_moved.percentiles[95]:7.3}
    datum repeatability,datum only min quality,{min_quality_datumed:8.4f}
    datum repeatability,datum+move min quality,{min_quality_moved:8.4f}
    datum repeatability,time,{time:.16},record,{record-count}
    datum repeatability,git version,{git_version}
    datum repeatability,image algorithm version,{algorithm_version}"""
)

DAT_REP_ERRMSG = (
    "datum repeatability     : {error_message}, time/record = {time:.16}/{record-count},"
    " version = TBD"
)

DAT_REP_ERRMSG_CSV = (
    "datum repeatability,{error_message},time,{time:.16},record,{record-count},"
    "version,TBD"
)


DAT_REP_IMAGES = "datum repeatability images : {!r}"

DAT_REP_COORDS = "datum repeatability coordinates : {coords}"

DAT_REP_COORDS_CSV = "datum repeatability coordinates,{coords}"
