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

from vfr.verification_tasks.report_formats import (
    rfmt_datum,
    rfmt_dat_rep,
    rfmt_cdect,
    rfmt_datum,
    rfmt_met_cal,
    rfmt_met_hgt,
    rfmt_pos_rep,
    rfmt_pos_ver,
    rfmt_pup_aln,
)


tw = TextWrapper(
    width=120,
    initial_indent="",
    subsequent_indent=(" " * 25),
    break_long_words=False,
    break_on_hyphens=False,
)

fill = tw.fill

FPU_SEPERATOR_LINE = "*" * 60
EMPTY_LINE = ""


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
):

    yield FPU_SEPERATOR_LINE
    yield ("FPU %s" % serial_number)
    yield EMPTY_LINE
    if datum_result is None:
        yield rfmt_datum.DATUM_RESULT_NA
    else:
        yield rfmt_datum.DATUM_RESULT_TERSE.format(**datum_result)

    yield EMPTY_LINE

    if beta_collision_result is None:
        yield rfmt_cdect.CDECT_RESULT_NA
    else:
        yield (rfmt_cdect.CDECT_RESULT_TERSE.format(**beta_collision_result))

    yield EMPTY_LINE

    if alpha_min_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA.format(limit_name="alpha_min")
    else:
        yield rfmt_cdect.LIMIT_RESULT_TERSE.format(**alpha_min_result)

    if alpha_max_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA.format(limit_name="alpha_max")
    else:
        yield rfmt_cdect.LIMIT_RESULT_TERSE.format(**alpha_max_result)

    if beta_min_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA.format(limit_name="beta_min")
    else:
        yield rfmt_cdect.LIMIT_RESULT_TERSE.format(**beta_min_result)

    if beta_max_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA.format(limit_name="beta_max")
    else:
        yield rfmt_cdect.LIMIT_RESULT_TERSE.format(**beta_max_result)

    yield EMPTY_LINE

    if datum_repeatability_result is None:
        yield rfmt_dat_rep.DAT_REP_NA
    else:
        err_msg = datum_repeatability_result["error_message"]
        if not err_msg:
            yield rfmt_dat_rep.DAT_REP_RESULT_TERSE.format(**datum_repeatability_result)

        else:
            yield rfmt_dat_rep.DAT_REP_ERRMSG.format(**datum_repeatability_result)

    yield EMPTY_LINE

    if metrology_calibration_result is None:
        yield rfmt_met_cal.MET_CAL_NA
    else:
        err_msg = metrology_calibration_result["error_message"]
        if not err_msg:
            yield rfmt_met_cal.MET_CAL_RESULT_TERSE.format(
                **metrology_calibration_result
            )
        else:
            yield rfmt_met_cal.MET_CAL_ERRMSG.format(metrology_calibration_result)

    yield EMPTY_LINE

    if metrology_height_result is None:
        yield rfmt_met_hgt.MET_HEIGHT_NA
    else:
        err_msg = metrology_height_result["error_message"]
        if not err_msg:
            yield rfmt_met_hgt.MET_HEIGHT_RESULT_TERSE.format(**metrology_height_result)

        else:
            yield rfmt_met_hgt.MET_HEIGHT_ERRMSG.format(**metrology_height_result)

    yield EMPTY_LINE

    if positional_repeatability_result is None:
        yield rfmt_pos_rep.POS_REP_NA
    else:
        err_msg = positional_repeatability_result["error_message"]
        if not err_msg:
            yield rfmt_pos_rep.POS_REP_RESULT_TERSE.format(
                **positional_repeatability_result
            )

            yield EMPTY_LINE

            yield fill(
                rfmt_pos_rep.POS_REP_GEARCOR.format(**positional_repeatability_result)
            )

            yield rfmt_pos_rep.POS_REP_GEARALGO.format(
                **positional_repeatability_result
            )
        else:
            yield rfmt_pos_rep.POS_REP_ERRMSG.format(**positional_repeatability_result)

    yield EMPTY_LINE

    if positional_verification_result is None:
        yield rfmt_pos_ver.POS_VER_NA
    else:
        err_msg = positional_verification_result["error_message"]
        if not err_msg:
            yield rfmt_pos_ver.POS_VER_RESULT_TERSE.format(
                **positional_verification_result
            )

            yield fill(
                rfmt_pos_ver.POS_VER_CALPARS.format(**positional_verification_result)
            )
        else:
            yield rfmt_pos_ver.POS_VER_ERRMSG.format(**positional_verification_result)

    yield EMPTY_LINE

    if pupil_alignment_result is None:
        yield rfmt_pup_aln.PUP_ALN_NA
    else:
        err_msg = pupil_alignment_result["error_message"]
        if not err_msg:
            yield rfmt_pup_aln.PUP_ALN_RESULT_TERSE.format(**pupil_alignment_result)

        else:
            yield rfmt_pup_aln.PUP_ALN_ERRMSG.format(**pupil_alignment_result)


def format_report_complete(
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
):

    yield FPU_SEPERATOR_LINE
    yield ("FPU %s" % serial_number)
    yield EMPTY_LINE
    if datum_result is None:
        yield rfmt_datum.DATUM_RESULT_NA
    else:
        yield rfmt_datum.DATUM_RESULT_COMPLETE.format(**datum_result)

    yield EMPTY_LINE

    if beta_collision_result is None:
        yield rfmt_cdect.CDECT_RESULT_NA
    else:
        yield rfmt_cdect.CDECT_RESULT_COMPLETE.format(**beta_collision_result)

    yield EMPTY_LINE

    if beta_collision_result is None:
        yield rfmt_cdect.CDECT_RESULT_NA
    else:
        yield (rfmt_cdect.CDECT_RESULT_COMPLETE.format(**beta_collision_result))

    yield EMPTY_LINE

    if alpha_min_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA.format(limit_name="alpha_min")
    else:
        yield rfmt_cdect.LIMIT_RESULT_COMPLETE.format(**alpha_min_result)

    if alpha_max_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA.format(limit_name="alpha_max")
    else:
        yield rfmt_cdect.LIMIT_RESULT_COMPLETE.format(**alpha_max_result)

    if beta_min_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA.format(limit_name="beta_min")
    else:
        yield rfmt_cdect.LIMIT_RESULT_COMPLETE.format(**beta_min_result)

    if beta_max_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA.format(limit_name="beta_max")
    else:
        yield rfmt_cdect.LIMIT_RESULT_COMPLETE.format(**beta_max_result)

    yield EMPTY_LINE

    if datum_repeatability_result is None:
        yield rfmt_dat_rep.DAT_REP_NA
    else:
        err_msg = datum_repeatability_result["error_message"]
        if not err_msg:
            yield rfmt_dat_rep.DAT_REP_RESULT_COMPLETE.format(
                **datum_repeatability_result
            )
        else:
            yield rfmt_dat_rep.DAT_REP_ERRMSG.format(**datum_repeatability_result)

    yield EMPTY_LINE

    if metrology_calibration_result is None:
        yield rfmt_met_cal.MET_CAL_NA
    else:
        err_msg = metrology_calibration_result["error_message"]
        if not err_msg:
            yield rfmt_met_cal.MET_CAL_RESULT_COMPLETE.format(
                **metrology_calibration_result
            )
        else:
            yield rfmt_met_cal.MET_CAL_ERRMSG.format(metrology_calibration_result)

    yield EMPTY_LINE

    if metrology_height_result is None:
        yield rfmt_met_hgt.MET_HEIGHT_NA
    else:
        err_msg = metrology_height_result["error_message"]
        if not err_msg:
            yield rfmt_met_hgt.MET_HEIGHT_RESULT_COMPLETE.format(
                **metrology_height_result
            )

        else:
            yield rfmt_met_hgt.MET_HEIGHT_ERRMSG.format(**metrology_height_result)

    yield EMPTY_LINE

    if positional_repeatability_result is None:
        yield rfmt_pos_rep.POS_REP_NA
    else:
        err_msg = positional_repeatability_result["error_message"]
        if not err_msg:
            yield rfmt_pos_rep.POS_REP_RESULT_COMPLETE.format(
                **positional_repeatability_result
            )

            yield EMPTY_LINE

            yield fill(
                rfmt_pos_rep.POS_REP_GEARCOR.format(**positional_repeatability_result)
            )

            yield rfmt_pos_rep.POS_REP_GEARALGO.format(
                **positional_repeatability_result
            )
        else:
            yield rfmt_pos_rep.POS_REP_ERRMSG.format(**positional_repeatability_result)

    yield EMPTY_LINE

    if positional_verification_result is None:
        yield rfmt_pos_ver.POS_VER_NA
    else:
        err_msg = positional_verification_result["error_message"]
        if not err_msg:
            yield rfmt_pos_ver.POS_VER_RESULT_COMPLETE.format(
                **positional_verification_result
            )

            yield fill(
                rfmt_pos_ver.POS_VER_CALPARS.format(**positional_verification_result)
            )

        else:
            yield rfmt_pos_ver.POS_VER_ERRMSG.format(**positional_verification_result)

    yield EMPTY_LINE

    if pupil_alignment_result is None:
        yield rfmt_pup_aln.PUP_ALN_NA
    else:
        err_msg = pupil_alignment_result["error_message"]
        if not err_msg:
            yield rfmt_pup_aln.PUP_ALN_RESULT_COMPLETE.format(**pupil_alignment_result)

        else:
            yield rfmt_pup_aln.PUP_ALN_ERRMSG.format(**pupil_alignment_result)


def list_posrep_angle_errors(name, error_by_angle, error_max):
    yield """\npositional repeatability: max error by {}""".format(name)
    for angle in sorted(error_by_angle.keys()):
        val = error_by_angle[angle]
        tag = " <<<" if val == error_max else ""
        yield (
            """Positional repeatability:     {angle:7.2f} = {val:8.4f} {tag}""".format(
                angle=angle, val=val, tag=tag
            )
        )


def list_posver_err_by_coord(error_by_coords, error_max):
    yield ("""positional verification : max error by coordinate""")
    for coord in sorted(error_by_coords.keys()):
        val = error_by_coords[coord]
        tag = " <<<" if val == error_max else ""
        yield (
            """Positional verification :     # {coord[0]:03d} ({coord[1]:+8.2f}, {coord[2]:+8.2f}) = {val:8.4f} {tag}""".format(
                coord=coord, val=val, tag=tag
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
):

    yield FPU_SEPERATOR_LINE
    yield ("FPU %s" % serial_number)
    yield EMPTY_LINE
    if datum_result is None:
        yield rfmt_datum.DATUM_RESULT_NA
    else:
        yield (rfmt_datum.DATUM_RESULT_LONG.format(**datum_result))

    yield EMPTY_LINE

    if beta_collision_result is None:
        yield rfmt_cdect.CDECT_RESULT_NA
    else:
        yield (rfmt_cdect.CDECT_RESULT_LONG.format(**beta_collision_result))

    yield EMPTY_LINE

    if alpha_min_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA.format(limit_name="alpha_min")
    else:
        yield rfmt_cdect.LIMIT_RESULT_LONG.format(**alpha_min_result)

    if alpha_max_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA.format(limit_name="alpha_max")
    else:
        yield rfmt_cdect.LIMIT_RESULT_LONG.format(**alpha_max_result)

    if beta_min_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA.format(limit_name="beta_min")
    else:
        yield rfmt_cdect.LIMIT_RESULT_LONG.format(**beta_min_result)

    if beta_max_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA.format(limit_name="beta_max")
    else:
        yield rfmt_cdect.LIMIT_RESULT_LONG.format(**beta_max_result)

    yield EMPTY_LINE

    if datum_repeatability_result is None:
        yield rfmt_dat_rep.DAT_REP_NA
    else:
        err_msg = datum_repeatability_result["error_message"]
        if not err_msg:
            yield rfmt_dat_rep.DAT_REP_RESULT_LONG.format(**datum_repeatability_result)
        else:
            yield rfmt_dat_rep.DAT_REP_ERRMSG.format(**datum_repeatability_result)

    yield EMPTY_LINE

    if metrology_calibration_result is None:
        yield rfmt_met_cal.MET_CAL_NA
    else:
        err_msg = metrology_calibration_result["error_message"]
        if not err_msg:
            yield rfmt_met_cal.MET_CAL_RESULT_LONG.format(
                **metrology_calibration_result
            )
        else:
            yield rfmt_met_cal.MET_CAL_ERRMSG.format(metrology_calibration_result)

    yield EMPTY_LINE

    if metrology_height_result is None:
        yield rfmt_met_hgt.MET_HEIGHT_NA
    else:
        err_msg = metrology_height_result["error_message"]
        if not err_msg:
            yield rfmt_met_hgt.MET_HEIGHT_RESULT_LONG.format(**metrology_height_result)

        else:
            yield rfmt_met_hgt.MET_HEIGHT_ERRMSG.format(**metrology_height_result)

    yield EMPTY_LINE

    if positional_repeatability_result is None:
        yield rfmt_pos_rep.POS_REP_NA
    else:
        err_msg = positional_repeatability_result["error_message"]
        if not err_msg:
            yield rfmt_pos_rep.POS_REP_RESULT_LONG.format(
                **positional_repeatability_result
            )

            yield EMPTY_LINE

            error_by_alpha = positional_repeatability_result[
                "posrep_alpha_max_at_angle"
            ]
            alpha_error_max = positional_repeatability_result["arg_max_alpha_error"]

            for line in list_posrep_angle_errors(
                "alpha angle", error_by_alpha, alpha_error_max
            ):
                yield line

            error_by_beta = positional_repeatability_result["posrep_beta_max_at_angle"]
            beta_error_max = positional_repeatability_result["arg_max_beta_error"]

            for line in list_posrep_angle_errors(
                "beta angle", error_by_beta, beta_error_max
            ):
                yield line

            yield fill(
                rfmt_pos_rep.POS_REP_CALPARS.format(**positional_repeatability_result)
            )

            yield EMPTY_LINE

            yield fill(
                rfmt_pos_rep.POS_REP_GEARCOR.format(**positional_repeatability_result)
            )

            yield rfmt_pos_rep.POS_REP_GEARALGO.format(
                **positional_repeatability_result
            )

        else:
            yield rfmt_pos_rep.POS_REP_ERRMSG.format(**positional_repeatability_result)

    yield EMPTY_LINE

    if positional_verification_result is None:
        yield rfmt_pos_ver.POS_VER_NA
    else:
        err_msg = positional_verification_result["error_message"]
        if not err_msg:
            yield rfmt_pos_ver.POS_VER_RESULT_LONG.format(
                **positional_verification_result
            )

            yield fill(
                rfmt_pos_ver.POS_VER_CALPARS.format(**positional_verification_result)
            )

            error_by_coords = positional_verification_result["posver_error"]
            error_max = positional_verification_result["posver_error_max_mm"]
            for line in list_posver_err_by_coord(error_by_coords, error_max):
                yield line

        else:
            yield rfmt_pos_ver.POS_VER_ERRMSG.format(**positional_verification_result)

    yield EMPTY_LINE

    if pupil_alignment_result is None:
        yield rfmt_pup_aln.PUP_ALN_NA
    else:
        err_msg = pupil_alignment_result["error_message"]
        if not err_msg:
            yield rfmt_pup_aln.PUP_ALN_RESULT_LONG.format(**pupil_alignment_result)

            yield fill(rfmt_pup_aln.PUP_ALN_CALPARS.format(**pupil_alignment_result))
        else:
            yield rfmt_pup_aln.PUP_ALN_ERRMSG.format(**pupil_alignment_result)


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
):

    yield FPU_SEPERATOR_LINE
    yield ("FPU %s" % serial_number)
    yield EMPTY_LINE
    if datum_result is None:
        yield rfmt_datum.DATUM_RESULT_NA
    else:
        yield (rfmt_datum.DATUM_RESULT_EXTENDED.format(**datum_result))

    yield EMPTY_LINE

    if beta_collision_result is None:
        yield rfmt_cdect.CDECT_RESULT_NA
    else:
        yield (rfmt_cdect.CDECT_RESULT_EXTENDED.format(**beta_collision_result))

    yield EMPTY_LINE

    if alpha_min_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA.format(limit_name="alpha_min")
    else:
        yield rfmt_cdect.LIMIT_RESULT_EXTENDED.format(**alpha_min_result)

    if alpha_max_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA.format(limit_name="alpha_max")
    else:
        yield rfmt_cdect.LIMIT_RESULT_EXTENDED.format(**alpha_max_result)

    if beta_min_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA.format(limit_name="beta_min")
    else:
        yield rfmt_cdect.LIMIT_RESULT_EXTENDED.format(**beta_min_result)

    if beta_max_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA.format(limit_name="beta_max")
    else:
        yield rfmt_cdect.LIMIT_RESULT_EXTENDED.format(**beta_max_result)

    yield EMPTY_LINE

    if datum_repeatability_result is None:
        yield rfmt_dat_rep.DAT_REP_NA
    else:
        err_msg = datum_repeatability_result["error_message"]
        if not err_msg:
            yield rfmt_dat_rep.DAT_REP_RESULT_EXTENDED.format(
                **datum_repeatability_result
            )

        else:
            yield rfmt_dat_rep.DAT_REP_ERRMSG.format(**datum_repeatability_result)

    if datum_repeatability_images:
        yield fill(rfmt_dat_rep.DAT_REP_IMAGES.format(datum_repeatability_images))
    else:
        yield fill(rfmt_dat_rep.DAT_REP_IMAGES.format("no images found"))

    yield EMPTY_LINE

    if metrology_calibration_result is None:
        yield rfmt_met_cal.MET_CAL_NA
    else:
        err_msg = metrology_calibration_result["error_message"]
        if not err_msg:
            yield rfmt_met_cal.MET_CAL_RESULT_EXTENDED.format(
                **metrology_calibration_result
            )
        else:
            yield rfmt_met_cal.MET_CAL_ERRMSG.format(metrology_calibration_result)

    if metrology_calibration_images:
        yield (fill(rfmt_met_cal.MET_CAL_IMAGES.format(metrology_calibration_images)))
    else:
        yield (fill(rfmt_met_cal.MET_CAL_IMAGES.format("no images found")))

    yield EMPTY_LINE

    if metrology_height_result is None:
        yield rfmt_met_hgt.MET_HEIGHT_NA
    else:
        err_msg = metrology_height_result["error_message"]
        if not err_msg:
            yield rfmt_met_hgt.MET_HEIGHT_RESULT_EXTENDED.format(
                **metrology_height_result
            )

        else:
            yield rfmt_met_hgt.MET_HEIGHT_ERRMSG.format(**metrology_height_result)

    if metrology_height_images:
        yield (rfmt_met_hgt.MET_HEIGHT_IMAGES.format(metrology_height_images))
    else:
        yield (rfmt_met_hgt.MET_HEIGHT_IMAGES.format("no images found"))

    yield EMPTY_LINE

    if positional_repeatability_result is None:
        yield rfmt_pos_rep.POS_REP_NA
    else:
        err_msg = positional_repeatability_result["error_message"]
        if not err_msg:
            yield rfmt_pos_rep.POS_REP_RESULT_EXTENDED.format(
                **positional_repeatability_result
            )

            yield EMPTY_LINE
            error_by_alpha = positional_repeatability_result[
                "posrep_alpha_max_at_angle"
            ]
            alpha_error_max = positional_repeatability_result["arg_max_alpha_error"]

            for line in list_posrep_angle_errors(
                "alpha angle", error_by_alpha, alpha_error_max
            ):
                yield line

            error_by_beta = positional_repeatability_result["posrep_beta_max_at_angle"]
            beta_error_max = positional_repeatability_result["arg_max_beta_error"]

            for line in list_posrep_angle_errors(
                "beta angle", error_by_beta, beta_error_max
            ):
                yield line

            yield fill(
                rfmt_pos_rep.ALPHA_MAX_ANGLE.format(**positional_repeatability_result)
            )
            yield fill(
                rfmt_pos_rep.BETA_MAX_ANGLE.format(**positional_repeatability_result)
            )

            yield fill(
                rfmt_pos_rep.AN_RESULTS_ALPHA.format(**positional_repeatability_result)
            )

            yield fill(
                rfmt_pos_rep.AN_RESULTS_BETA.format(**positional_repeatability_result)
            )

            yield fill(
                rfmt_pos_rep.POS_REP_CALPARS.format(**positional_repeatability_result)
            )

            yield EMPTY_LINE

            yield fill(
                rfmt_pos_rep.POS_REP_GEARCOR.format(**positional_repeatability_result)
            )

            yield rfmt_pos_rep.POS_REP_GEARALGO.format(
                **positional_repeatability_result
            )

            yield fill(
                rfmt_pos_rep.POS_REP_IMAGES_ALPHA.format(
                    **positional_repeatability_images
                )
            )

            yield fill(
                rfmt_pos_rep.POS_REP_IMAGES_BETA.format(
                    **positional_repeatability_images
                )
            )

            yield fill(
                rfmt_pos_rep.POS_REP_WAVEFORM_PARS.format(
                    **positional_repeatability_images
                )
            )

        else:
            yield rfmt_pos_rep.POS_REP_ERRMSG.format(**positional_repeatability_result)

    if positional_repeatability_images:
        yield fill(
            rfmt_pos_rep.POS_REP_IMAGES_ALPHA.format(**positional_repeatability_images)
        )

        yield fill(
            rfmt_pos_rep.POS_REP_IMAGES_BETA.format(**positional_repeatability_images)
        )
    else:
        yield fill(rfmt_pos_rep.POS_REP_IMAGES.format("no images found"))

    yield EMPTY_LINE

    if positional_verification_result is None:
        yield rfmt_pos_ver.POS_VER_NA
    else:
        err_msg = positional_verification_result["error_message"]
        if not err_msg:
            yield rfmt_pos_ver.POS_VER_RESULT_EXTENDED.format(
                **positional_verification_result
            )

            yield fill(
                rfmt_pos_ver.POS_VER_CALPARS.format(**positional_verification_result)
            )

            error_by_coords = positional_verification_result["posver_error"]
            error_max = positional_verification_result["posver_error_max_mm"]
            for line in list_posver_err_by_coord(error_by_coords, error_max):
                yield line

            yield fill(
                rfmt_pos_ver.POS_VER_ERRVALS.format(**positional_verification_result)
            )

            yield fill(
                rfmt_pos_ver.POS_VER_ARESULTS.format(**positional_verification_result)
            )

        else:
            yield rfmt_pos_ver.POS_VER_ERRMSG.format(**positional_verification_result)

    if positional_verification_images:
        if "gearbox_correction" not in positional_verification_images:
            positional_verification_images["gearbox_correction"] = None

            yield fill(
                rfmt_pos_ver.POS_VER_IMAGES.format(**positional_verification_images)
            )

            yield fill(
                rfmt_pos_ver.POS_VER_GEARCORR.format(**positional_verification_images)
            )

    else:
        yield rfmt_pos_ver.POS_VER_NOIMAGES.format("no images found")

    yield EMPTY_LINE

    if pupil_alignment_result is None:
        yield rfmt_pup_aln.PUP_ALN_NA
    else:
        err_msg = pupil_alignment_result["error_message"]
        if not err_msg:
            yield rfmt_pup_aln.PUP_ALN_RESULT_EXTENDED.format(**pupil_alignment_result)

            yield fill(rfmt_pup_aln.PUP_ALN_CALPARS.format(**pupil_alignment_result))

            yield fill(rfmt_pup_aln.PUP_ALN_COORDS.format(**pupil_alignment_result))

        else:
            yield rfmt_pup_aln.PUP_ALN_ERRMSG.format(**pupil_alignment_result)

        if pupil_alignment_images:
            yield (fill(rfmt_pup_aln.PUP_ALN_IMAGES.format(pupil_alignment_images)))
        else:
            yield (fill(rfmt_pup_aln.PUP_ALN_IMAGES.format("no images found")))


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
        elif report_format == "complete":
            lines = format_report_complete(**ddict)
        elif report_format == "long":
            lines = format_report_long(**ddict)
        else:
            lines = format_report_extended(**ddict)
        try:
            # dbe.opts.output_file.writelines(line + "\n" for line in lines)
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
