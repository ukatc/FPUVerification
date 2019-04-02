# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from argparse import Namespace
from inspect import cleandoc
from textwrap import TextWrapper
from numpy import array, Inf
import numpy as np

from vfr.db.base import TestResult

from vfr.db.colldect_limits import get_angular_limit
from vfr.db.datum import get_datum_result
from vfr.db.datum_repeatability import (
    get_datum_repeatability_images,
    get_datum_repeatability_result,
)
from vfr.db.metrology_calibration import (
    get_metrology_calibration_images,
    get_metrology_calibration_result,
)
from vfr.db.metrology_height import (
    get_metrology_height_images,
    get_metrology_height_result,
)
from vfr.db.positional_repeatability import (
    get_positional_repeatability_images,
    get_positional_repeatability_result,
)
from vfr.db.positional_verification import (
    get_positional_verification_images,
    get_positional_verification_result,
)
from vfr.db.pupil_alignment import (
    get_pupil_alignment_images,
    get_pupil_alignment_result,
)

tw = TextWrapper(
    width=120,
    initial_indent="",
    subsequent_indent=(" " * 10),
    break_long_words=False,
    break_on_hyphens=False,
)

fill = tw.fill


def get_data(dbe, fpu_id):
    serial_number = dbe.fpu_config[fpu_id]["serialnumber"]
    count = dbe.opts.record_count

    data = Namespace(
        serial_number=serial_number,
        datum_result=get_datum_result(dbe, fpu_id, count=count),
        alpha_min_result=get_angular_limit(dbe, fpu_id, "alpha_min", count=count),
        alpha_max_result=get_angular_limit(dbe, fpu_id, "alpha_max", count=count),
        beta_min_result=get_angular_limit(dbe, fpu_id, "beta_min", count=count),
        beta_max_result=get_angular_limit(dbe, fpu_id, "beta_max", count=count),
        beta_collision_result=get_angular_limit(
            dbe, fpu_id, "beta_collision", count=count
        ),
        datum_repeatability_result=get_datum_repeatability_result(
            dbe, fpu_id, count=count
        ),
        datum_repeatability_images=get_datum_repeatability_images(
            dbe, fpu_id, count=count
        ),
        metrology_calibration_result=get_metrology_calibration_result(
            dbe, fpu_id, count=count
        ),
        metrology_calibration_images=get_metrology_calibration_images(
            dbe, fpu_id, count=count
        ),
        metrology_height_result=get_metrology_height_result(dbe, fpu_id, count=count),
        metrology_height_images=get_metrology_height_images(dbe, fpu_id, count=count),
        positional_repeatability_result=get_positional_repeatability_result(
            dbe, fpu_id, count=count
        ),
        positional_repeatability_images=get_positional_repeatability_images(
            dbe, fpu_id, count=count
        ),
        positional_verification_result=get_positional_verification_result(
            dbe, fpu_id, count=count
        ),
        positional_verification_images=get_positional_verification_images(
            dbe, fpu_id, count=count
        ),
        pupil_alignment_result=get_pupil_alignment_result(dbe, fpu_id, count=count),
        pupil_alignment_images=get_pupil_alignment_images(dbe, fpu_id, count=count),
        outfile=dbe.opts.output_file,
    )

    return data


def get_rlist(
    serial_number=None,
    datum_result=None,
    alpha_min_result=None,
    alpha_max_result=None,
    beta_min_result=None,
    beta_max_result=None,
    beta_collision_result=None,
    datum_repeatability_result=None,
    metrology_calibration_result=None,
    metrology_height_result=None,
    positional_repeatability_result=None,
    positional_verification_result=None,
    pupil_alignment_result=None,
    datum_repeatability_images=None,
    metrology_calibration_images=None,
    metrology_height_images=None,
    positional_repeatability_images=None,
    positional_verification_images=None,
    pupil_alignment_images=None,
    outfile=None,
    skip_fibre=None,
):
    if datum_result is None:
        datum_alpha = TestResult.NA
        datum_beta = TestResult.NA
    else:
        datum_alpha = TestResult.OK if datum_result["datumed"][0] else TestResult.FAILED
        datum_beta = TestResult.OK if datum_result["datumed"][1] else TestResult.FAILED

    if beta_collision_result is None:
        beta_collision = TestResult.NA
    else:
        beta_collision = beta_collision_result["result"]

    if alpha_min_result is None:
        alpha_min = TestResult.NA
    else:
        alpha_min = alpha_min_result["result"]

    if alpha_max_result is None:
        alpha_max = TestResult.NA
    else:
        alpha_max = alpha_max_result["result"]

    if beta_min_result is None:
        beta_min = TestResult.NA
    else:
        beta_min = beta_min_result["result"]

    if beta_max_result is None:
        beta_max = TestResult.NA
    else:
        beta_max = beta_max_result["result"]

    if datum_repeatability_result is None:
        datum_repeatability = TestResult.NA
    else:
        datum_repeatability = datum_repeatability_result["result"]

    if metrology_height_result is None:
        metrology_height = TestResult.NA
    else:
        metrology_height = (
            TestResult.OK
            if not (metrology_height_result["error_message"])
            else TestResult.FAILED
        )

    if positional_repeatability_result is None:
        positional_repeatability = TestResult.NA
    else:
        positional_repeatability = positional_repeatability_result["result"]

    if positional_verification_result is None:
        positional_verification = TestResult.NA
    else:
        positional_verification = positional_verification_result["result"]

    if skip_fibre:
        rlist = [
            (datum_alpha, "datum_alpha"),
            (datum_beta, "datum_beta"),
            (beta_collision, "beta_collision"),
            (alpha_min, "alpha min"),
            (beta_min, "beta min"),
            (alpha_max, "alpha max"),
            (beta_max, "beta max"),
            (datum_repeatability, "datum repeatability"),
            (metrology_height, "metrology height"),
            (positional_repeatability, "positional_repeatability"),
            (positional_verification, "positional verification"),
        ]

    else:
        if metrology_calibration_result is None:
            metrology_calibration = TestResult.NA
        else:
            metrology_calibration = (
                TestResult.OK
                if not (metrology_calibration_result["error_message"])
                else TestResult.FAILED
            )

        if pupil_alignment_result is None:
            pupil_alignment = TestResult.NA
        else:
            pupil_alignment = pupil_alignment_result["result"]

        rlist = [
            (datum_alpha, "datum_alpha"),
            (datum_beta, "datum_beta"),
            (beta_collision, "beta_collision"),
            (alpha_min, "alpha min"),
            (beta_min, "beta min"),
            (alpha_max, "alpha max"),
            (beta_max, "beta max"),
            (datum_repeatability, "datum repeatability"),
            (metrology_height, "metrology height"),
            (metrology_calibration, "metrology calibration"),
            (pupil_alignment, "pupil alignment"),
            (positional_repeatability, "positional_repeatability"),
            (positional_verification, "positional verification"),
        ]

    return rlist


def format_report_status(
    serial_number=None,
    datum_result=None,
    alpha_min_result=None,
    alpha_max_result=None,
    beta_min_result=None,
    beta_max_result=None,
    beta_collision_result=None,
    datum_repeatability_result=None,
    metrology_calibration_result=None,
    metrology_height_result=None,
    positional_repeatability_result=None,
    positional_verification_result=None,
    pupil_alignment_result=None,
    datum_repeatability_images=None,
    metrology_calibration_images=None,
    metrology_height_images=None,
    positional_repeatability_images=None,
    positional_verification_images=None,
    pupil_alignment_images=None,
    outfile=None,
    skip_fibre=None,
):

    rlist = get_rlist(**locals())
    sum_status = TestResult.OK
    failed_name = ""
    for test, name in rlist:
        if test == TestResult.OK:
            continue
        elif test == TestResult.NA:
            if sum_status == TestResult.OK:
                sum_status = TestResult.NA
                failed_name = name
        else:
            if sum_status == TestResult.NA:
                sum_status = TestResult.FAILED
                failed_name = name

    if sum_status == TestResult.OK:
        yield "FPU %s : %s" % (serial_number, sum_status)
    else:
        yield ("FPU %s : %s (failed in %s)" % (serial_number, sum_status, failed_name))


def format_report_brief(
    serial_number=None,
    datum_result=None,
    alpha_min_result=None,
    alpha_max_result=None,
    beta_min_result=None,
    beta_max_result=None,
    beta_collision_result=None,
    datum_repeatability_result=None,
    metrology_calibration_result=None,
    metrology_height_result=None,
    positional_repeatability_result=None,
    positional_verification_result=None,
    pupil_alignment_result=None,
    datum_repeatability_images=None,
    metrology_calibration_images=None,
    metrology_height_images=None,
    positional_repeatability_images=None,
    positional_verification_images=None,
    pupil_alignment_images=None,
    outfile=None,
    skip_fibre=None,
):

    rlist = get_rlist(**locals())
    for val, name in rlist:
        yield "{}    {:25.25s}: {}".format(serial_number, name, val)


def format_report_terse(
    serial_number=None,
    datum_result=None,
    alpha_min_result=None,
    alpha_max_result=None,
    beta_min_result=None,
    beta_max_result=None,
    beta_collision_result=None,
    datum_repeatability_result=None,
    metrology_calibration_result=None,
    metrology_height_result=None,
    positional_repeatability_result=None,
    positional_verification_result=None,
    pupil_alignment_result=None,
    datum_repeatability_images=None,
    metrology_calibration_images=None,
    metrology_height_images=None,
    positional_repeatability_images=None,
    positional_verification_images=None,
    pupil_alignment_images=None,
    outfile=None,
):

    yield ("*" * 60)
    yield ("FPU %s" % serial_number)
    yield ""
    if datum_result is None:
        yield ("Datum test               : n/a")
    else:
        yield (
            cleandoc(
                """
                datum test              : alpha datumed = {datumed[0]}
                datum test              : beta datumed = {datumed[1]}
                datum test              : fpu_id/FPU state = {fpuid} / {result_state}
                datum test              : counter deviations = {counter_deviation!r}
                datum test              : time/record = {time:.16}/{record-count}
                datum test              : result = {diagnostic}"""
            ).format(**datum_result)
        )

    yield ""

    if beta_collision_result is None:
        yield ("beta collision  test     : n/a")
    else:
        yield (
            "collision detection     : result ="
            " {result} ({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **beta_collision_result
            )
        )

    yield ""

    if alpha_min_result is None:
        yield ("limit test            :  alpha min n/a")
    else:
        yield (
            "Limit test              : alpha min = {result}, "
            "limit = {val:+8.4f} ({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **alpha_min_result
            )
        )

    if alpha_max_result is None:
        yield ("limit test            :  alpha max n/a")
    else:
        yield (
            "limit test              : alpha max = {result}, limit = {val:+8.4f}"
            " ({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **alpha_max_result
            )
        )

    if beta_min_result is None:
        yield ("limit test            : beta min n/a")
    else:
        yield (
            "limit test              : beta min  = {result}, limit = {val:+8.4f} "
            "({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **beta_min_result
            )
        )

    if beta_max_result is None:
        yield ("Limit test            : beta max n/a")
    else:
        yield (
            "limit test              : beta max  = {result}, limit = {val:+8.4f}"
            " ({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **beta_max_result
            )
        )

    yield ""

    if datum_repeatability_result is None:
        yield ("datum repeatability       : n/a")
    else:
        err_msg = datum_repeatability_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
                    """
                datum repeatability     : {result},
                datum repeatability     : datum only max                = {datum_repeatability_only_max_mm:7.3} mm,
                datum repeatability     : datum only std                = {datum_repeatability_only_std_mm:7.3} mm,
                datum repeatability     : datum only max residual count = {datum_repeatability_max_residual_datumed},
                datum repeatability     : datum+move max                = {datum_repeatability_move_max_mm:7.3} mm,
                datum repeatability     : datum+move std                = {datum_repeatability_move_std_mm:7.3} mm,
                datum repeatability     : datum+move max residual count = {datum_repeatability_max_residual_moved},
                datum repeatability     : time/record                   = {time:.16}/{record-count}, version = {algorithm_version}""".format(
                        **datum_repeatability_result
                    )
                )
            )

        #            yield(fill(
        #                "Datum repeatability     : coords = {coords}".format(
        #                    **datum_repeatability_result
        #                ))
        #
        #            )
        else:
            yield (
                "Datum repeatability     : {error_message}, time/record = {time:.16}/{record-count},"
                " version = TBD".format(**datum_repeatability_result)
            )

    yield ""

    if metrology_calibration_result is None:
        yield ("metrology calibration     : n/a")
    else:
        err_msg = metrology_calibration_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
                    """
                metrology calibration   : metcal_fibre_large_target_distance = {metcal_fibre_large_target_distance_mm:8.4f} mm,
                metrology calibration   : metcal_fibre_small_target_distance = {metcal_fibre_small_target_distance_mm:8.4f} mm,
                metrology calibration   : metcal_target_vector_angle         = {metcal_target_vector_angle_deg:8.4f} degrees,
                metrology calibration   : time/record={time:.16}/{record-count}, version = {algorithm_version}""".format(
                        **metrology_calibration_result
                    )
                )
            )
        else:
            yield (
                "Metrology calibration   : {error_message}, time/record = {time:.16}/{record-count}, "
                "version = {algorithm_version}".format(metrology_calibration_result)
            )

    #    yield(fill("metrology calibration images: {!r}".format(metrology_calibration_images)))

    yield ""

    if metrology_height_result is None:
        yield ("metrology_height          : n/a")
    else:
        err_msg = metrology_height_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
                    """
                metrology height        : small target = {small_target_height_mm:8.4f} mm,
                metrology height        : large target = {small_target_height_mm:8.4f} mm,
                metrology height        : time/record = {time:.16}/{record-count}, version = {algorithm_version}""".format(
                        **metrology_height_result
                    )
                )
            )
        #            yield("metrology height images : {!r}".format(metrology_height_images))
        else:
            yield (
                "Metrology height      : fibre_distance = {error_message}, time/record = {time:.16}/{record-count},"
                " version = {algorithm_version}".format(**metrology_height_result)
            )

    yield ""

    if positional_repeatability_result is None:
        yield ("positional repeatability: n/a")
    else:
        err_msg = positional_repeatability_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
                    """
                    positional repeatability: passed        = {result},
                    positional repeatability: alpha_max     = {posrep_alpha_max_mm:8.4f} mm,
                    positional repeatability: beta_max      = {posrep_beta_max_mm:8.4f} mm,
                    positional repeatability: posrep_rss_mm = {posrep_rss_mm:8.4f} mm,
                    positional repeatability: time/record   = {time:.16}/{record-count}, version = {algorithm_version}"""
                ).format(**positional_repeatability_result)
            )
            yield (
                fill(
                    """Positional repeatability: calibration_pars = {calibration_pars!r}""".format(
                        **positional_repeatability_result
                    )
                )
            )
            yield ""
            yield (
                fill(
                    """positional repeatability: gearbox correction = {gearbox_correction}""".format(
                        **positional_repeatability_result
                    )
                )
            )
            yield (
                cleandoc(
                    """
                    positional repeatability: gearbox correction algorithm version = {algorithm_version}"""
                ).format(**positional_repeatability_result)
            )
        #            yield(
        #                fill(
        #                    """Positional repeatability: alpha_max_at_angle = {posrep_alpha_max_at_angle!r}"""
        #                .format(**positional_repeatability_result))
        #
        #            )
        #            yield(
        #                fill(
        #                    """Positional repeatability: beta_max_at_angle = {posrep_beta_max_at_angle!r}"""
        #                .format(**positional_repeatability_result))
        #
        #            )
        #            yield(
        #                fill(
        #                    """Positional repeatability: analysis_results_alpha = {analysis_results_alpha!r}"""
        #                .format(**positional_repeatability_result))
        #
        #            )
        #            yield(
        #                fill(
        #                    """Positional repeatability: analysis_results_beta = {analysis_results_beta!r}"""
        #                .format(**positional_repeatability_result))
        #
        #            )
        #            yield(
        #                fill(
        #                    """Positional repeatability: gearbox_correction = {gearbox_correction!r}"""
        #                .format(**positional_repeatability_result))
        #
        #            )
        #            yield(fill("positional repeatability images: {images_alpha!r}".format(
        #                    **positional_repeatability_images))
        #
        #            )
        #            yield(fill("positional repeatability images: {images_beta!r}".format(
        #                    **positional_repeatability_images))
        #
        #            )
        #            yield(fill("positional repeatability images: {waveform_pars!r}".format(
        #                    **positional_repeatability_images))
        #
        #            )
        else:
            yield (
                "Positional repeatability: message = {error_message}, time/record = {time:.16}/{record-count},"
                " version = {algorithm_version}".format(
                    **positional_repeatability_result
                )
            )

    yield ""

    if positional_verification_result is None:
        yield ("positional verification : n/a")
    else:
        err_msg = positional_verification_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
                    """
                    positional verification : passed           = {result},
                    positional verification : posver_error_max = {posver_error_max_mm:8.4f} mm,
                    positional verification : time/record      = {time:.16}/{record-count}, version = {algorithm_version}"""
                ).format(**positional_verification_result)
            )
            yield (
                fill(
                    """Positional verification : calibration_pars = {calibration_pars}""".format(
                        **positional_verification_result
                    )
                )
            )
        #           yield(
        #               fill(
        #                   """Positional verification : posver_errors = {posver_error}"""
        #               .format(**positional_verification_result))
        #
        #           )
        #           yield(
        #               fill(
        #                   """Positional verification : analysis_results = {analysis_results}"""
        #               .format(**positional_verification_result))
        #
        #           )
        #           if "gearbox_correction" not in positional_verification_images:
        #               positional_verification_images["gearbox_correction"] = None
        #           yield(
        #               fill(
        #               "positional verification images : {images!r}".format(
        #                   **positional_verification_images
        #               ))
        #           )
        #           yield(
        #               fill(
        #               "gearbox correction = {gearbox_correction!r}".format(
        #                   **positional_verification_images
        #               ))
        #           )
        else:
            yield (
                "Positional verification : message = {error_message}, time/record = {time:.16}/{record-count},"
                " version = {algorithm_version}".format(
                    **positional_verification_result
                )
            )

    yield ""

    if pupil_alignment_result is None:
        yield ("pupil_alignment test    : n/a")
    else:
        err_msg = pupil_alignment_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
                    """
                    pupil alignment         : passed        = {result},
                    pupil alignment         : chassis error =  {measures[chassis_error]} mm,
                    pupil alignment         : alpha error   =  {measures[alpha_error]} mm,
                    pupil alignment         : beta error    =  {measures[beta_error]} mm,
                    pupil alignment         : total error   =  {measures[total_error]} mm,
                    pupil alignment         : time/record   = {time:.16}/{record-count}"""
                ).format(**pupil_alignment_result)
            )
            yield (
                fill(
                    """pupil alignment    : calibration_pars = {calibration_pars!r}""".format(
                        **pupil_alignment_result
                    )
                )
            )
        #            yield(
        #                fill(
        #                    """pupil alignment    : coords = {coords!r}"""
        #                .format(**pupil_alignment_result))
        #
        #            )
        #            yield(fill("pupil alignment images: {!r}".format(pupil_alignment_images)))
        else:
            yield (
                "pupil alignment: message = {error_message}, time/record = {time:.16}/{record-count}".format(
                    **pupil_alignment_result
                )
            )


def format_report_short(
    serial_number=None,
    datum_result=None,
    alpha_min_result=None,
    alpha_max_result=None,
    beta_min_result=None,
    beta_max_result=None,
    beta_collision_result=None,
    datum_repeatability_result=None,
    metrology_calibration_result=None,
    metrology_height_result=None,
    positional_repeatability_result=None,
    positional_verification_result=None,
    pupil_alignment_result=None,
    datum_repeatability_images=None,
    metrology_calibration_images=None,
    metrology_height_images=None,
    positional_repeatability_images=None,
    positional_verification_images=None,
    pupil_alignment_images=None,
    outfile=None,
):

    yield ("*" * 60)
    yield ("FPU %s" % serial_number)
    yield ""
    if datum_result is None:
        yield ("datum test              : n/a")
    else:
        yield (
            cleandoc(
                """
                datum test              : result = {result} / {diagnostic}
                datum test              : alpha datumed = {datumed[0]}
                datum test              : beta datumed = {datumed[1]}
                datum test              : fpu_id/FPU state = {fpuid} / {result_state}
                datum test              : counter deviations = {counter_deviation!r}
                datum test              : time/record = {time:.16}/{record-count}"""
            ).format(**datum_result)
        )

    yield ""

    if beta_collision_result is None:
        yield ("beta collision  test     : n/a")
    else:
        yield (
            "collision detection     : result ="
            " {result} @ {val:+8.4f} ({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **beta_collision_result
            )
        )

    yield ""

    if alpha_min_result is None:
        yield ("limit test            :  alpha min n/a")
    else:
        yield (
            "Limit test              : alpha min = {result}, "
            "limit = {val:+8.4f} ({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **alpha_min_result
            )
        )

    if alpha_max_result is None:
        yield ("limit test            :  alpha max n/a")
    else:
        yield (
            "limit test              : alpha max = {result}, limit = {val:+8.4f}"
            " ({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **alpha_max_result
            )
        )

    if beta_min_result is None:
        yield ("limit test            : beta min n/a")
    else:
        yield (
            "limit test              : beta min  = {result}, limit = {val:+8.4f} "
            "({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **beta_min_result
            )
        )

    if beta_max_result is None:
        yield ("Limit test            : beta max n/a")
    else:
        yield (
            "limit test              : beta max  = {result}, limit = {val:+8.4f}"
            " ({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **beta_max_result
            )
        )

    yield ""

    if datum_repeatability_result is None:
        yield ("datum repeatability       : n/a")
    else:
        err_msg = datum_repeatability_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
                    """
                datum repeatability     : {result},
                datum repeatability     : threshold                      = {pass_threshold_mm:8.4f}
                datum repeatability     : datum only max                 = {datum_repeatability_only_max_mm:7.3} mm
                datum repeatability     : datum only std                 = {datum_repeatability_only_std_mm:7.3} mm
                datum repeatability     : datum only max residual count  = {datum_repeatability_max_residual_datumed}
                datum repeatability     : datum+move max                 = {datum_repeatability_move_max_mm:7.3} mm
                datum repeatability     : datum+move std                 = {datum_repeatability_move_std_mm:7.3} mm
                datum repeatability     : datum+move max residual count  = {datum_repeatability_max_residual_moved}
                datum repeatability     : datum only min quality         = {min_quality_datumed:8.4f}
                datum repeatability     : datum+move min quality         = {min_quality_moved:8.4f}
                datum repeatability     : time/record                    = {time:.16}/{record-count}
                datum repeatability     : git version                    = {git_version}
                datum repeatability     : image algorithm version        = {algorithm_version}""".format(
                        **datum_repeatability_result
                    )
                )
            )

        #            yield(fill(
        #                "Datum repeatability     : coords = {coords}".format(
        #                    **datum_repeatability_result
        #                ))
        #
        #            )
        else:
            yield (
                "datum repeatability     : {error_message}, time/record = {time:.16}/{record-count},"
                " version = TBD".format(**datum_repeatability_result)
            )

    yield ""

    if metrology_calibration_result is None:
        yield ("metrology calibration     : n/a")
    else:
        err_msg = metrology_calibration_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
                    """
                metrology calibration   : metcal_fibre_large_target_distance = {metcal_fibre_large_target_distance_mm:8.4f} mm
                metrology calibration   : metcal_fibre_small_target_distance = {metcal_fibre_small_target_distance_mm:8.4f} mm
                metrology calibration   : metcal_target_vector_angle         = {metcal_target_vector_angle_deg:8.4f} degrees
                metrology calibration   : coords large target                = {coords[target_big_xy]!r}
                metrology calibration   : coords small target                = {coords[target_small_xy]!r}
                metrology calibration   : quality small target               = {coords[target_small_q]:8.4f}
                metrology calibration   : quality large target               = {coords[target_big_q]:8.4f}
                    metrology calibration   : quality fibre                      = {coords[fibre_q]:8.4f}
                metrology calibration   : git version                        = {git_version}
                metrology calibration   : time/record={time:.16}/{record-count}, version = {algorithm_version}""".format(
                        **metrology_calibration_result
                    )
                )
            )
        else:
            yield (
                "metrology calibration   : {error_message}, time/record = {time:.16}/{record-count}, "
                "version = {algorithm_version}".format(metrology_calibration_result)
            )

    #    yield(fill("metrology calibration images: {!r}".format(metrology_calibration_images)))

    yield ""

    if metrology_height_result is None:
        yield ("metrology_height          : n/a")
    else:
        err_msg = metrology_height_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
                    """
                metrology height        : small target = {small_target_height_mm:8.4f} mm
                metrology height        : large target = {small_target_height_mm:8.4f} mm
                metrology height        : test result  = {test_result} mm
                metrology height        : git version  = {git_version}
                metrology height        : time/record  = {time:.16}/{record-count}, version = {algorithm_version}""".format(
                        **metrology_height_result
                    )
                )
            )
        #            yield("metrology height images : {!r}".format(metrology_height_images))
        else:
            yield (
                "Metrology height      : fibre_distance = {error_message}, time/record = {time:.16}/{record-count},"
                " version = {algorithm_version}".format(**metrology_height_result)
            )

    yield ""

    if positional_repeatability_result is None:
        yield ("positional repeatability: n/a")
    else:
        err_msg = positional_repeatability_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
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
                ).format(**positional_repeatability_result)
            )
            yield (
                fill(
                    """Positional repeatability: calibration_pars = {calibration_pars!r}""".format(
                        **positional_repeatability_result
                    )
                )
            )
            yield ""
            yield (
                fill(
                    """positional repeatability: gearbox correction = {gearbox_correction}""".format(
                        **positional_repeatability_result
                    )
                )
            )
            yield (
                cleandoc(
                    """
                    positional repeatability: gearbox correction algorithm version = {algorithm_version}"""
                ).format(**positional_repeatability_result)
            )
        #            yield(
        #                fill(
        #                    """Positional repeatability: alpha_max_at_angle = {posrep_alpha_max_at_angle!r}"""
        #                .format(**positional_repeatability_result))
        #
        #            )
        #            yield(
        #                fill(
        #                    """Positional repeatability: beta_max_at_angle = {posrep_beta_max_at_angle!r}"""
        #                .format(**positional_repeatability_result))
        #
        #            )
        #            yield(
        #                fill(
        #                    """Positional repeatability: analysis_results_alpha = {analysis_results_alpha!r}"""
        #                .format(**positional_repeatability_result))
        #
        #            )
        #            yield(
        #                fill(
        #                    """Positional repeatability: analysis_results_beta = {analysis_results_beta!r}"""
        #                .format(**positional_repeatability_result))
        #
        #            )
        #            yield(
        #                fill(
        #                    """Positional repeatability: gearbox_correction = {gearbox_correction!r}"""
        #                .format(**positional_repeatability_result))
        #
        #            )
        #            yield(fill("positional repeatability images: {images_alpha!r}".format(
        #                    **positional_repeatability_images))
        #
        #            )
        #            yield(fill("positional repeatability images: {images_beta!r}".format(
        #                    **positional_repeatability_images))
        #
        #            )
        #            yield(fill("positional repeatability images: {waveform_pars!r}".format(
        #                    **positional_repeatability_images))
        #
        #            )
        else:
            yield (
                "Positional repeatability: message = {error_message}, time/record = {time:.16}/{record-count},"
                " version = {algorithm_version}".format(
                    **positional_repeatability_result
                )
            )

    yield ""

    if positional_verification_result is None:
        yield ("positional verification : n/a")
    else:
        err_msg = positional_verification_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
                    """
                    positional verification : passed                       = {result}
                    positional verification : pass_threshold               = {pass_threshold_mm}
                    positional verification : posver_error_max             = {posver_error_max_mm:8.4f} mm
                    positional verification : arg_max_error (count, α, β)  = {arg_max_error}
                    positional verification : min image quality            = {min_quality:8.4f}
                    positional verification : time/record                  = {time:.16}/{record-count}
                    positional verification : analysis version             = {algorithm_version}
                    positional verification : git version                  = {git_version}"""
                ).format(**positional_verification_result)
            )
            yield (
                fill(
                    """Positional verification : calibration_pars             = {calibration_pars}""".format(
                        **positional_verification_result
                    )
                )
            )
        #           yield(
        #               fill(
        #                   """Positional verification : posver_errors = {posver_error}"""
        #               .format(**positional_verification_result))
        #
        #           )
        #           yield(
        #               fill(
        #                   """Positional verification : analysis_results = {analysis_results}"""
        #               .format(**positional_verification_result))
        #
        #           )
        #           if "gearbox_correction" not in positional_verification_images:
        #               positional_verification_images["gearbox_correction"] = None
        #           yield(
        #               fill(
        #               "positional verification images : {images!r}".format(
        #                   **positional_verification_images
        #               ))
        #           )
        #           yield(
        #               fill(
        #               "gearbox correction = {gearbox_correction!r}".format(
        #                   **positional_verification_images
        #               ))
        #           )
        else:
            yield (
                "Positional verification : message = {error_message}, time/record = {time:.16}/{record-count},"
                " version = {algorithm_version}".format(
                    **positional_verification_result
                )
            )

    yield ""

    if pupil_alignment_result is None:
        yield ("pupil_alignment test    : n/a")
    else:
        err_msg = pupil_alignment_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
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
                ).format(**pupil_alignment_result)
            )
            yield (
                fill(
                    """pupil alignment         : calibration_pars  = {calibration_pars!r}""".format(
                        **pupil_alignment_result
                    )
                )
            )
        #            yield(
        #                fill(
        #                    """pupil alignment    : coords = {coords!r}"""
        #                .format(**pupil_alignment_result))
        #
        #            )
        #            yield(fill("pupil alignment images: {!r}".format(pupil_alignment_images)))
        else:
            yield (
                "pupil alignment: message = {error_message}, time/record = {time:.16}/{record-count}".format(
                    **pupil_alignment_result
                )
            )


def format_report_long(
    serial_number=None,
    datum_result=None,
    alpha_min_result=None,
    alpha_max_result=None,
    beta_min_result=None,
    beta_max_result=None,
    beta_collision_result=None,
    datum_repeatability_result=None,
    metrology_calibration_result=None,
    metrology_height_result=None,
    positional_repeatability_result=None,
    positional_verification_result=None,
    pupil_alignment_result=None,
    datum_repeatability_images=None,
    metrology_calibration_images=None,
    metrology_height_images=None,
    positional_repeatability_images=None,
    positional_verification_images=None,
    pupil_alignment_images=None,
    outfile=None,
):

    yield ("*" * 60)
    yield ("FPU %s" % serial_number)
    yield ""
    if datum_result is None:
        yield ("datum test              : n/a")
    else:
        yield (
            cleandoc(
                """
                datum test              : result = {result} / {diagnostic}
                datum test              : alpha datumed = {datumed[0]}
                datum test              : beta datumed = {datumed[1]}
                datum test              : fpu_id/FPU state = {fpuid} / {result_state}
                datum test              : counter deviations = {counter_deviation!r}
                datum test              : time/record = {time:.16}/{record-count}"""
            ).format(**datum_result)
        )

    yield ""

    if beta_collision_result is None:
        yield ("beta collision  test     : n/a")
    else:
        yield (
            "collision detection     : result ="
            " {result} @ {val:+8.4f} ({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **beta_collision_result
            )
        )

    yield ""

    if alpha_min_result is None:
        yield ("limit test            :  alpha min n/a")
    else:
        yield (
            "Limit test              : alpha min = {result}, "
            "limit = {val:+8.4f} ({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **alpha_min_result
            )
        )

    if alpha_max_result is None:
        yield ("limit test            :  alpha max n/a")
    else:
        yield (
            "limit test              : alpha max = {result}, limit = {val:+8.4f}"
            " ({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **alpha_max_result
            )
        )

    if beta_min_result is None:
        yield ("limit test            : beta min n/a")
    else:
        yield (
            "limit test              : beta min  = {result}, limit = {val:+8.4f} "
            "({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **beta_min_result
            )
        )

    if beta_max_result is None:
        yield ("Limit test            : beta max n/a")
    else:
        yield (
            "limit test              : beta max  = {result}, limit = {val:+8.4f}"
            " ({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **beta_max_result
            )
        )

    yield ""

    if datum_repeatability_result is None:
        yield ("datum repeatability       : n/a")
    else:
        err_msg = datum_repeatability_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
                    """
                datum repeatability     : {result},
                datum repeatability     : threshold                      = {pass_threshold_mm:8.4f}
                datum repeatability     : datum only max                 = {datum_repeatability_only_max_mm:7.3} mm
                datum repeatability     : datum only std                 = {datum_repeatability_only_std_mm:7.3} mm
                datum repeatability     : datum only max residual count  = {datum_repeatability_max_residual_datumed}
                datum repeatability     : datum+move max                 = {datum_repeatability_move_max_mm:7.3} mm
                datum repeatability     : datum+move std                 = {datum_repeatability_move_std_mm:7.3} mm
                datum repeatability     : datum+move max residual count  = {datum_repeatability_max_residual_moved}
                datum repeatability     : datum only min quality         = {min_quality_datumed:8.4f}
                datum repeatability     : datum+move min quality         = {min_quality_moved:8.4f}
                datum repeatability     : time/record                    = {time:.16}/{record-count}
                datum repeatability     : git version                    = {git_version}
                datum repeatability     : image algorithm version        = {algorithm_version}""".format(
                        **datum_repeatability_result
                    )
                )
            )

        #            yield(fill(
        #                "Datum repeatability     : coords = {coords}".format(
        #                    **datum_repeatability_result
        #                ))
        #
        #            )
        else:
            yield (
                "datum repeatability     : {error_message}, time/record = {time:.16}/{record-count},"
                " version = TBD".format(**datum_repeatability_result)
            )

    yield ""

    if metrology_calibration_result is None:
        yield ("metrology calibration     : n/a")
    else:
        err_msg = metrology_calibration_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
                    """
                metrology calibration   : metcal_fibre_large_target_distance = {metcal_fibre_large_target_distance_mm:8.4f} mm
                metrology calibration   : metcal_fibre_small_target_distance = {metcal_fibre_small_target_distance_mm:8.4f} mm
                metrology calibration   : metcal_target_vector_angle         = {metcal_target_vector_angle_deg:8.4f} degrees
                metrology calibration   : coords large target                = {coords[target_big_xy]!r}
                metrology calibration   : coords small target                = {coords[target_small_xy]!r}
                metrology calibration   : quality small target               = {coords[target_small_q]:8.4f}
                metrology calibration   : quality large target               = {coords[target_big_q]:8.4f}
                    metrology calibration   : quality fibre                      = {coords[fibre_q]:8.4f}
                metrology calibration   : git version                        = {git_version}
                metrology calibration   : time/record={time:.16}/{record-count}, version = {algorithm_version}""".format(
                        **metrology_calibration_result
                    )
                )
            )
        else:
            yield (
                "metrology calibration   : {error_message}, time/record = {time:.16}/{record-count}, "
                "version = {algorithm_version}".format(metrology_calibration_result)
            )

    #    yield(fill("metrology calibration images: {!r}".format(metrology_calibration_images)))

    yield ""

    if metrology_height_result is None:
        yield ("metrology_height          : n/a")
    else:
        err_msg = metrology_height_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
                    """
                metrology height        : small target = {small_target_height_mm:8.4f} mm
                metrology height        : large target = {small_target_height_mm:8.4f} mm
                metrology height        : test result  = {test_result} mm
                metrology height        : git version  = {git_version}
                metrology height        : time/record  = {time:.16}/{record-count}, version = {algorithm_version}""".format(
                        **metrology_height_result
                    )
                )
            )
        #            yield("metrology height images : {!r}".format(metrology_height_images))
        else:
            yield (
                "Metrology height      : fibre_distance = {error_message}, time/record = {time:.16}/{record-count},"
                " version = {algorithm_version}".format(**metrology_height_result)
            )

    yield ""

    if positional_repeatability_result is None:
        yield ("positional repeatability: n/a")
    else:
        err_msg = positional_repeatability_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
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
                ).format(**positional_repeatability_result)
            )
            error_by_alpha = positional_repeatability_result[
                "posrep_alpha_max_at_angle"
            ]
            yield ("""\nPositional repeatability: max error by alpha angle""")
            error_max = positional_repeatability_result["arg_max_alpha_error"]
            for alpha in sorted(error_by_alpha.keys()):
                val = error_by_alpha[alpha]
                tag = " <<<" if val == error_max else ""
                yield (
                    """Positional repeatability:     {alpha:7.2f} = {val:8.4f} {tag}""".format(
                        alpha=alpha, val=val, tag=tag
                    )
                )
            error_by_beta = positional_repeatability_result["posrep_beta_max_at_angle"]
            yield ("error_by_beta= {}".format(error_by_beta))
            yield ("""\nPositional repeatability: max error by beta angle""")
            error_max = positional_repeatability_result["arg_max_beta_error"]
            for beta in sorted(error_by_beta.keys()):
                val = error_by_beta[beta]
                tag = " <<<" if val == error_max else ""
                yield (
                    """Positional repeatability:     {beta:7.2f} = {val:8.4f} {tag}""".format(
                        beta=beta, val=val, tag=tag
                    )
                )

            yield (
                fill(
                    """Positional repeatability: calibration_pars = {calibration_pars!r}""".format(
                        **positional_repeatability_result
                    )
                )
            )
            yield ""
            yield (
                fill(
                    """positional repeatability: gearbox correction = {gearbox_correction}""".format(
                        **positional_repeatability_result
                    )
                )
            )
            yield (
                cleandoc(
                    """
                    positional repeatability: gearbox correction algorithm version = {algorithm_version}"""
                ).format(**positional_repeatability_result)
            )
        #            yield(
        #                fill(
        #                    """Positional repeatability: alpha_max_at_angle = {posrep_alpha_max_at_angle!r}"""
        #                .format(**positional_repeatability_result))
        #
        #            )
        #            yield(
        #                fill(
        #                    """Positional repeatability: beta_max_at_angle = {posrep_beta_max_at_angle!r}"""
        #                .format(**positional_repeatability_result))
        #
        #            )
        #            yield(
        #                fill(
        #                    """Positional repeatability: analysis_results_alpha = {analysis_results_alpha!r}"""
        #                .format(**positional_repeatability_result))
        #
        #            )
        #            yield(
        #                fill(
        #                    """Positional repeatability: analysis_results_beta = {analysis_results_beta!r}"""
        #                .format(**positional_repeatability_result))
        #
        #            )
        #            yield(
        #                fill(
        #                    """Positional repeatability: gearbox_correction = {gearbox_correction!r}"""
        #                .format(**positional_repeatability_result))
        #
        #            )
        #            yield(fill("positional repeatability images: {images_alpha!r}".format(
        #                    **positional_repeatability_images))
        #
        #            )
        #            yield(fill("positional repeatability images: {images_beta!r}".format(
        #                    **positional_repeatability_images))
        #
        #            )
        #            yield(fill("positional repeatability images: {waveform_pars!r}".format(
        #                    **positional_repeatability_images))
        #
        #            )
        else:
            yield (
                "Positional repeatability: message = {error_message}, time/record = {time:.16}/{record-count},"
                " version = {algorithm_version}".format(
                    **positional_repeatability_result
                )
            )

    yield ""

    if positional_verification_result is None:
        yield ("positional verification : n/a")
    else:
        err_msg = positional_verification_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
                    """
                    positional verification : passed                       = {result}
                    positional verification : pass_threshold               = {pass_threshold_mm}
                    positional verification : posver_error_max             = {posver_error_max_mm:8.4f} mm
                    positional verification : arg_max_error (count, α, β)  = {arg_max_error}
                    positional verification : min image quality            = {min_quality:8.4f}
                    positional verification : time/record                  = {time:.16}/{record-count}
                    positional verification : analysis version             = {algorithm_version}
                    positional verification : git version                  = {git_version}"""
                ).format(**positional_verification_result)
            )
            error_by_coords = positional_verification_result["posver_error"]
            yield ("""Positional verification : max error by coordinate""")
            error_max = positional_verification_result["posver_error_max_mm"]
            for coord in sorted(error_by_coords.keys()):
                val = error_by_coords[coord]
                tag = " <<<" if val == error_max else ""
                yield (
                    """Positional verification :     # {coord[0]:03d} ({coord[1]:+8.2f}, {coord[2]:+8.2f}) = {val:8.4f} {tag}""".format(
                        coord=coord, val=val, tag=tag
                    )
                )
            yield (
                fill(
                    """Positional verification : calibration_pars             = {calibration_pars}""".format(
                        **positional_verification_result
                    )
                )
            )
        #           yield(
        #               fill(
        #                   """Positional verification : posver_errors = {posver_error}"""
        #               .format(**positional_verification_result))
        #
        #           )
        #           yield(
        #               fill(
        #                   """Positional verification : analysis_results = {analysis_results}"""
        #               .format(**positional_verification_result))
        #
        #           )
        #           if "gearbox_correction" not in positional_verification_images:
        #               positional_verification_images["gearbox_correction"] = None
        #           yield(
        #               fill(
        #               "positional verification images : {images!r}".format(
        #                   **positional_verification_images
        #               ))
        #           )
        #           yield(
        #               fill(
        #               "gearbox correction = {gearbox_correction!r}".format(
        #                   **positional_verification_images
        #               ))
        #           )
        else:
            yield (
                "Positional verification : message = {error_message}, time/record = {time:.16}/{record-count},"
                " version = {algorithm_version}".format(
                    **positional_verification_result
                )
            )

    yield ""

    if pupil_alignment_result is None:
        yield ("pupil_alignment test    : n/a")
    else:
        err_msg = pupil_alignment_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
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
                ).format(**pupil_alignment_result)
            )
            yield (
                fill(
                    """pupil alignment         : calibration_pars  = {calibration_pars!r}""".format(
                        **pupil_alignment_result
                    )
                )
            )
        #            yield(
        #                fill(
        #                    """pupil alignment    : coords = {coords!r}"""
        #                .format(**pupil_alignment_result))
        #
        #            )
        #            yield(fill("pupil alignment images: {!r}".format(pupil_alignment_images)))
        else:
            yield (
                "pupil alignment: message = {error_message}, time/record = {time:.16}/{record-count}".format(
                    **pupil_alignment_result
                )
            )


def format_report_extended(
    serial_number=None,
    datum_result=None,
    alpha_min_result=None,
    alpha_max_result=None,
    beta_min_result=None,
    beta_max_result=None,
    beta_collision_result=None,
    datum_repeatability_result=None,
    metrology_calibration_result=None,
    metrology_height_result=None,
    positional_repeatability_result=None,
    positional_verification_result=None,
    pupil_alignment_result=None,
    datum_repeatability_images=None,
    metrology_calibration_images=None,
    metrology_height_images=None,
    positional_repeatability_images=None,
    positional_verification_images=None,
    pupil_alignment_images=None,
    outfile=None,
):

    yield ("*" * 60)
    yield ("FPU %s" % serial_number)
    yield ""
    if datum_result is None:
        yield ("datum test              : n/a")
    else:
        yield (
            cleandoc(
                """
                datum test              : result = {result} / {diagnostic}
                datum test              : alpha datumed = {datumed[0]}
                datum test              : beta datumed = {datumed[1]}
                datum test              : fpu_id/FPU state = {fpuid} / {result_state}
                datum test              : counter deviations = {counter_deviation!r}
                datum test              : time/record = {time:.16}/{record-count}"""
            ).format(**datum_result)
        )

    yield ""

    if beta_collision_result is None:
        yield ("beta collision  test     : n/a")
    else:
        yield (
            "collision detection     : result ="
            " {result} @ {val:+8.4f} ({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **beta_collision_result
            )
        )

    yield ""

    if alpha_min_result is None:
        yield ("limit test            :  alpha min n/a")
    else:
        yield (
            "Limit test              : alpha min = {result}, "
            "limit = {val:+8.4f} ({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **alpha_min_result
            )
        )

    if alpha_max_result is None:
        yield ("limit test            :  alpha max n/a")
    else:
        yield (
            "limit test              : alpha max = {result}, limit = {val:+8.4f}"
            " ({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **alpha_max_result
            )
        )

    if beta_min_result is None:
        yield ("limit test            : beta min n/a")
    else:
        yield (
            "limit test              : beta min  = {result}, limit = {val:+8.4f} "
            "({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **beta_min_result
            )
        )

    if beta_max_result is None:
        yield ("Limit test            : beta max n/a")
    else:
        yield (
            "limit test              : beta max  = {result}, limit = {val:+8.4f}"
            " ({diagnostic}), time/record = {time:.16}/{record-count}".format(
                **beta_max_result
            )
        )

    yield ""

    if datum_repeatability_result is None:
        yield ("datum repeatability       : n/a")
    else:
        err_msg = datum_repeatability_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
                    """
                datum repeatability     : {result},
                datum repeatability     : threshold                      = {pass_threshold_mm:8.4f}
                datum repeatability     : datum only max                 = {datum_repeatability_only_max_mm:7.3} mm
                datum repeatability     : datum only std                 = {datum_repeatability_only_std_mm:7.3} mm
                datum repeatability     : datum only max residual count  = {datum_repeatability_max_residual_datumed}
                datum repeatability     : datum+move max                 = {datum_repeatability_move_max_mm:7.3} mm
                datum repeatability     : datum+move std                 = {datum_repeatability_move_std_mm:7.3} mm
                datum repeatability     : datum+move max residual count  = {datum_repeatability_max_residual_moved}
                datum repeatability     : datum only min quality         = {min_quality_datumed:8.4f}
                datum repeatability     : datum+move min quality         = {min_quality_moved:8.4f}
                datum repeatability     : time/record                    = {time:.16}/{record-count}
                datum repeatability     : git version                    = {git_version}
                datum repeatability     : image algorithm version        = {algorithm_version}""".format(
                        **datum_repeatability_result
                    )
                )
            )

            yield (
                fill(
                    "Datum repeatability     : coords = {coords}".format(
                        **datum_repeatability_result
                    )
                )
            )
        else:
            yield (
                "datum repeatability     : {error_message}, time/record = {time:.16}/{record-count},"
                " version = TBD".format(**datum_repeatability_result)
            )

    yield ""

    if metrology_calibration_result is None:
        yield ("metrology calibration     : n/a")
    else:
        err_msg = metrology_calibration_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
                    """
                metrology calibration   : metcal_fibre_large_target_distance = {metcal_fibre_large_target_distance_mm:8.4f} mm
                metrology calibration   : metcal_fibre_small_target_distance = {metcal_fibre_small_target_distance_mm:8.4f} mm
                metrology calibration   : metcal_target_vector_angle         = {metcal_target_vector_angle_deg:8.4f} degrees
                metrology calibration   : coords large target                = {coords[target_big_xy]!r}
                metrology calibration   : coords small target                = {coords[target_small_xy]!r}
                metrology calibration   : quality small target               = {coords[target_small_q]:8.4f}
                metrology calibration   : quality large target               = {coords[target_big_q]:8.4f}
                    metrology calibration   : quality fibre                      = {coords[fibre_q]:8.4f}
                metrology calibration   : git version                        = {git_version}
                metrology calibration   : time/record={time:.16}/{record-count}, version = {algorithm_version}""".format(
                        **metrology_calibration_result
                    )
                )
            )
        else:
            yield (
                "metrology calibration   : {error_message}, time/record = {time:.16}/{record-count}, "
                "version = {algorithm_version}".format(metrology_calibration_result)
            )

    yield (
        fill("metrology calibration images: {!r}".format(metrology_calibration_images))
    )

    yield ""

    if metrology_height_result is None:
        yield ("metrology_height          : n/a")
    else:
        err_msg = metrology_height_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
                    """
                metrology height        : small target = {small_target_height_mm:8.4f} mm
                metrology height        : large target = {small_target_height_mm:8.4f} mm
                metrology height        : test result  = {test_result} mm
                metrology height        : git version  = {git_version}
                metrology height        : time/record  = {time:.16}/{record-count}, version = {algorithm_version}""".format(
                        **metrology_height_result
                    )
                )
            )
            yield ("metrology height images : {!r}".format(metrology_height_images))
        else:
            yield (
                "Metrology height      : fibre_distance = {error_message}, time/record = {time:.16}/{record-count},"
                " version = {algorithm_version}".format(**metrology_height_result)
            )

    yield ""

    if positional_repeatability_result is None:
        yield ("positional repeatability: n/a")
    else:
        err_msg = positional_repeatability_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
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
                ).format(**positional_repeatability_result)
            )
            error_by_alpha = positional_repeatability_result[
                "posrep_alpha_max_at_angle"
            ]
            yield ("""\nPositional repeatability: max error by alpha angle""")
            error_max = positional_repeatability_result["arg_max_alpha_error"]
            for alpha in sorted(error_by_alpha.keys()):
                val = error_by_alpha[alpha]
                tag = " <<<" if val == error_max else ""
                yield (
                    """Positional repeatability:     {alpha:7.2f} = {val:8.4f} {tag}""".format(
                        alpha=alpha, val=val, tag=tag
                    )
                )
            error_by_beta = positional_repeatability_result["posrep_beta_max_at_angle"]
            yield ("error_by_beta={}".format(error_by_beta))
            yield ("""\nPositional repeatability: max error by beta angle""")
            error_max = positional_repeatability_result["arg_max_beta_error"]
            for beta in sorted(error_by_beta.keys()):
                val = error_by_beta[beta]
                tag = " <<<" if val == error_max else ""
                yield (
                    """Positional repeatability:     {beta:7.2f} = {val:8.4f} {tag}""".format(
                        beta=beta, val=val, tag=tag
                    )
                )

            yield (
                fill(
                    """Positional repeatability: calibration_pars = {calibration_pars!r}""".format(
                        **positional_repeatability_result
                    )
                )
            )
            yield ""
            yield (
                fill(
                    """positional repeatability: gearbox correction = {gearbox_correction}""".format(
                        **positional_repeatability_result
                    )
                )
            )
            yield (
                cleandoc(
                    """
                    positional repeatability: gearbox correction algorithm version = {algorithm_version}"""
                ).format(**positional_repeatability_result)
            )
            yield (
                fill(
                    """Positional repeatability: alpha_max_at_angle = {posrep_alpha_max_at_angle!r}""".format(
                        **positional_repeatability_result
                    )
                )
            )
            yield (
                fill(
                    """Positional repeatability: beta_max_at_angle = {posrep_beta_max_at_angle!r}""".format(
                        **positional_repeatability_result
                    )
                )
            )
            yield (
                fill(
                    """Positional repeatability: analysis_results_alpha = {analysis_results_alpha!r}""".format(
                        **positional_repeatability_result
                    )
                )
            )
            yield (
                fill(
                    """Positional repeatability: analysis_results_beta = {analysis_results_beta!r}""".format(
                        **positional_repeatability_result
                    )
                )
            )
            yield (
                fill(
                    """Positional repeatability: gearbox_correction = {gearbox_correction!r}""".format(
                        **positional_repeatability_result
                    )
                )
            )
            yield (
                fill(
                    "positional repeatability images: {images_alpha!r}".format(
                        **positional_repeatability_images
                    )
                )
            )
            yield (
                fill(
                    "positional repeatability images: {images_beta!r}".format(
                        **positional_repeatability_images
                    )
                )
            )
            yield (
                fill(
                    "positional repeatability images / waveform parameters: {waveform_pars!r}".format(
                        **positional_repeatability_images
                    )
                )
            )
        else:
            yield (
                "Positional repeatability: message = {error_message}, time/record = {time:.16}/{record-count},"
                " version = {algorithm_version}".format(
                    **positional_repeatability_result
                )
            )

    yield ""

    if positional_verification_result is None:
        yield ("positional verification : n/a")
    else:
        err_msg = positional_verification_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
                    """
                    positional verification : passed                       = {result}
                    positional verification : pass_threshold               = {pass_threshold_mm}
                    positional verification : posver_error_max             = {posver_error_max_mm:8.4f} mm
                    positional verification : arg_max_error (count, α, β)  = {arg_max_error}
                    positional verification : min image quality            = {min_quality:8.4f}
                    positional verification : time/record                  = {time:.16}/{record-count}
                    positional verification : analysis version             = {algorithm_version}
                    positional verification : git version                  = {git_version}"""
                ).format(**positional_verification_result)
            )
            error_by_coords = positional_verification_result["posver_error"]
            yield ("""Positional verification : max error by coordinate""")
            error_max = positional_verification_result["posver_error_max_mm"]
            for coord in sorted(error_by_coords.keys()):
                val = error_by_coords[coord]
                tag = " <<<" if val == error_max else ""
                yield (
                    """Positional verification :     # {coord[0]:03d} ({coord[1]:+8.2f}, {coord[2]:+8.2f}) = {val:8.4f} {tag}""".format(
                        coord=coord, val=val, tag=tag
                    )
                )
            yield (
                fill(
                    """Positional verification : calibration_pars             = {calibration_pars}""".format(
                        **positional_verification_result
                    )
                )
            )
            yield (
                fill(
                    """Positional verification : posver_errors = {posver_error}""".format(
                        **positional_verification_result
                    )
                )
            )
            yield (
                fill(
                    """Positional verification : analysis_results = {analysis_results}""".format(
                        **positional_verification_result
                    )
                )
            )
            if "gearbox_correction" not in positional_verification_images:
                positional_verification_images["gearbox_correction"] = None
            yield (
                fill(
                    "positional verification images : {images!r}".format(
                        **positional_verification_images
                    )
                )
            )
            yield (
                fill(
                    "gearbox correction = {gearbox_correction!r}".format(
                        **positional_verification_images
                    )
                )
            )
        else:
            yield (
                "Positional verification : message = {error_message}, time/record = {time:.16}/{record-count},"
                " version = {algorithm_version}".format(
                    **positional_verification_result
                )
            )

    yield ""

    if pupil_alignment_result is None:
        yield ("pupil_alignment test    : n/a")
    else:
        err_msg = pupil_alignment_result["error_message"]
        if not err_msg:
            yield (
                cleandoc(
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
                ).format(**pupil_alignment_result)
            )
            yield (
                fill(
                    """pupil alignment         : calibration_pars  = {calibration_pars!r}""".format(
                        **pupil_alignment_result
                    )
                )
            )
            yield (
                fill(
                    """pupil alignment    : coords = {coords!r}""".format(
                        **pupil_alignment_result
                    )
                )
            )
            yield (fill("pupil alignment images: {!r}".format(pupil_alignment_images)))
        else:
            yield (
                "pupil alignment: message = {error_message}, time/record = {time:.16}/{record-count}".format(
                    **pupil_alignment_result
                )
            )


def report(dbe, opts):

    report_format = dbe.opts.report_format
    for count, fpu_id in enumerate(dbe.eval_fpuset):
        ddict = vars(get_data(dbe, fpu_id))

        if (count > 0) and report_format != "status":
            dbe.opts.output_file.write("\n")

        if report_format == "status":
            lines = format_report_status(skip_fibre=opts.skip_fibre, **ddict)
        elif report_format == "brief":
            lines = format_report_brief(**ddict)
        elif report_format == "terse":
            lines = format_report_terse(**ddict)
        elif report_format == "short":
            lines = format_report_short(**ddict)
        elif report_format == "long":
            lines = format_report_long(**ddict)
        else:
            lines = format_report_extended(**ddict)
        try:
            #dbe.opts.output_file.writelines(line + "\n" for line in lines)
            for line in lines:
                dbe.opts.output_file.write(line + "\n")
        except TypeError:
            print("error in line = %r" % repr(line))
            raise


def dump_data(dbe):

    print("{", file=dbe.opts.output_file)
    for count, fpu_id in enumerate(dbe.eval_fpuset):
        ddict = vars(get_data(dbe, fpu_id))
        if count > 0:
            print("\n\n", file=dbe.opts.output_file)
        print("%r : %r," % (fpu_id, ddict), file=dbe.opts.output_file)

    print("}", file=dbe.opts.output_file)
