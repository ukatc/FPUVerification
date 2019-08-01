# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from textwrap import TextWrapper
import termcolor

from vfr.db.base import TestResult
from vfr.db.retrieval import get_data

from vfr.output.report_formats import (
    rfmt_datum,
    rfmt_dat_rep,
    rfmt_cdect,
    rfmt_met_cal,
    rfmt_met_hgt,
    rfmt_pos_rep,
    rfmt_pos_ver,
    rfmt_pup_aln,
)
from vfr.output.report_formats.rfmt_pos_rep import MIN_GEARBOX_CORRECTION_VERSION_REPORT

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


def color_result(val):
    colored = termcolor.colored
    if val == TestResult.OK:
        return colored(val, "blue")
    elif val == val == TestResult.FAILED:
        return colored(val, "red")
    else:
        return colored(val, "cyan")


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
        yield "FPU %s : %s" % (serial_number, color_result(sum_status))
    else:
        yield (
            "FPU %s : %s (failed in %s)"
            % (serial_number, color_result(sum_status), failed_name)
        )


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
        yield "{}    {:25.25s}: {}".format(serial_number, name, color_result(val))


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
            yield rfmt_met_cal.MET_CAL_ERRMSG.format(**metrology_calibration_result)

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

            if positional_repeatability_result["gearbox_correction_version"] < MIN_GEARBOX_CORRECTION_VERSION_REPORT:
                yield (
                    rfmt_pos_rep.POS_REP_GEARCOR_OLD.format(**positional_repeatability_result)
                )
            else:
                yield (
                    rfmt_pos_rep.POS_REP_GEARCOR_TERSE.format(**positional_repeatability_result)
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
            yield rfmt_met_cal.MET_CAL_ERRMSG.format(**metrology_calibration_result)

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

            if positional_repeatability_result["gearbox_correction_version"] < MIN_GEARBOX_CORRECTION_VERSION_REPORT:
                yield (
                    rfmt_pos_rep.POS_REP_GEARCOR_OLD.format(**positional_repeatability_result)
                )
            else:
                yield (
                    rfmt_pos_rep.POS_REP_GEARCOR_COMPLETE.format(**positional_repeatability_result)
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


def list_posrep_angle_errors(name, error_by_angle, error_arg_max, csv=False):
    if csv:
        hdr = """\npositional repeatability,max error by {}"""
        fmt = """Positional repeatability,{angle:7.2f},{val:8.4f},{tag}"""
    else:
        hdr = ("""\npositional repeatability: max error by {}"""
               """\npositional repeatability:     [degrees]   [mm]""" )
        fmt = """Positional repeatability:     {angle:7.2f} = {val:8.4f} {tag}"""

    yield hdr.format(name)

    for angle in sorted(error_by_angle.keys()):
        val = error_by_angle[angle]
        tag = " <<<" if angle == error_arg_max else ""
        yield (fmt.format(angle=angle, val=val, tag=tag))


def list_posver_err_by_coord(error_by_coords, error_argmax, csv=False):
    if csv:
        hdr = """positional verification,max error by coordinate"""
        fmt = """Positional verification,{coord[0]:03d},{coord[1]:+8.2f},{coord[2]:+8.2f},{val:8.4f},{tag}"""
    else:
        hdr = ("""positional verification : max error by coordinate\n"""
               """positional verification :     ([1], degrees, degrees)       [mm]""")
        fmt = """Positional verification :     # {coord[0]:03d} ({coord[1]:+8.2f}, {coord[2]:+8.2f}) = {val:8.4f} {tag}"""

    yield hdr
    for coord in sorted(error_by_coords.keys()):
        val = error_by_coords[coord]
        tag = " <<<" if coord == error_argmax else ""
        yield (fmt.format(coord=coord, val=val, tag=tag))


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
            yield rfmt_met_cal.MET_CAL_ERRMSG.format(**metrology_calibration_result)

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

            if positional_repeatability_result["gearbox_correction_version"] < MIN_GEARBOX_CORRECTION_VERSION_REPORT:
                yield (
                    rfmt_pos_rep.POS_REP_GEARCOR_OLD.format(**positional_repeatability_result)
                )
            else:
                yield (
                    rfmt_pos_rep.POS_REP_GEARCOR_LONG.format(**positional_repeatability_result)
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

            error_by_coords = positional_verification_result["posver_error_by_angle"]
            error_argmax = positional_verification_result["arg_max_error"]
            for line in list_posver_err_by_coord(error_by_coords, error_argmax):
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

            yield fill(rfmt_dat_rep.DAT_REP_COORDS.format(**datum_repeatability_result))

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
            yield rfmt_met_cal.MET_CAL_ERRMSG.format(**metrology_calibration_result)

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

            if positional_repeatability_result["gearbox_correction_version"] < MIN_GEARBOX_CORRECTION_VERSION_REPORT:
                yield (
                    rfmt_pos_rep.POS_REP_GEARCOR_OLD.format(**positional_repeatability_result)
                )
            else:
                yield (
                    rfmt_pos_rep.POS_REP_GEARCOR_EXTENDED.format(**positional_repeatability_result)
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

            error_by_coords = positional_verification_result["posver_error_by_angle"]
            error_argmax = positional_verification_result["arg_max_error"]
            for line in list_posver_err_by_coord(error_by_coords, error_argmax):
                yield line

            yield fill(
                rfmt_pos_ver.POS_VER_ERRVALS.format(**positional_verification_result)
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


def format_report_csv(
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
        yield rfmt_datum.DATUM_RESULT_NA_CSV
    else:
        yield (rfmt_datum.DATUM_RESULT_CSV.format(**datum_result))

    yield EMPTY_LINE

    if beta_collision_result is None:
        yield rfmt_cdect.CDECT_RESULT_NA_CSV
    else:
        yield (rfmt_cdect.CDECT_RESULT_CSV.format(**beta_collision_result))

    yield EMPTY_LINE

    if alpha_min_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA_CSV.format(limit_name="alpha_min")
    else:
        yield rfmt_cdect.LIMIT_RESULT_CSV.format(**alpha_min_result)

    if alpha_max_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA_CSV.format(limit_name="alpha_max")
    else:
        yield rfmt_cdect.LIMIT_RESULT_CSV.format(**alpha_max_result)

    if beta_min_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA_CSV.format(limit_name="beta_min")
    else:
        yield rfmt_cdect.LIMIT_RESULT_CSV.format(**beta_min_result)

    if beta_max_result is None:
        yield rfmt_cdect.LIMIT_RESULT_NA_CSV.format(limit_name="beta_max")
    else:
        yield rfmt_cdect.LIMIT_RESULT_CSV.format(**beta_max_result)

    yield EMPTY_LINE

    if datum_repeatability_result is None:
        yield rfmt_dat_rep.DAT_REP_NA_CSV
    else:
        err_msg = datum_repeatability_result["error_message"]
        if not err_msg:
            yield rfmt_dat_rep.DAT_REP_RESULT_CSV.format(**datum_repeatability_result)

            yield rfmt_dat_rep.DAT_REP_COORDS_CSV.format(**datum_repeatability_result)

        else:
            yield rfmt_dat_rep.DAT_REP_ERRMSG_CSV.format(**datum_repeatability_result)

    yield EMPTY_LINE
    if datum_repeatability_images is not None:
        for k, ipath in enumerate(
            datum_repeatability_images["images"]["datumed_images"]
        ):
            yield "datumed,%i,%s" % (k, ipath)
        yield EMPTY_LINE
        for k, ipath in enumerate(datum_repeatability_images["images"]["moved_images"]):
            yield "moved,%i,%s" % (k, ipath)
    yield EMPTY_LINE

    if metrology_calibration_result is None:
        yield rfmt_met_cal.MET_CAL_NA_CSV
    else:
        err_msg = metrology_calibration_result["error_message"]
        if not err_msg:
            yield rfmt_met_cal.MET_CAL_RESULT_CSV.format(**metrology_calibration_result)
        else:
            yield rfmt_met_cal.MET_CAL_ERRMSG_CSV.format(**metrology_calibration_result)

    yield EMPTY_LINE

    if metrology_height_result is None:
        yield rfmt_met_hgt.MET_HEIGHT_NA_CSV
    else:
        err_msg = metrology_height_result["error_message"]
        if not err_msg:
            yield rfmt_met_hgt.MET_HEIGHT_RESULT_CSV.format(**metrology_height_result)

        else:
            yield rfmt_met_hgt.MET_HEIGHT_ERRMSG.format(**metrology_height_result)

    yield EMPTY_LINE

    if positional_repeatability_result is None:
        yield rfmt_pos_rep.POS_REP_NA_CSV
    else:
        err_msg = positional_repeatability_result["error_message"]
        if not err_msg:
            yield rfmt_pos_rep.POS_REP_RESULT_CSV.format(
                **positional_repeatability_result
            )

            yield EMPTY_LINE
            error_by_alpha = positional_repeatability_result[
                "posrep_alpha_max_at_angle"
            ]
            alpha_error_max = positional_repeatability_result["arg_max_alpha_error"]

            for line in list_posrep_angle_errors(
                "alpha angle", error_by_alpha, alpha_error_max, csv=True
            ):
                yield line

            error_by_beta = positional_repeatability_result["posrep_beta_max_at_angle"]
            beta_error_max = positional_repeatability_result["arg_max_beta_error"]

            for line in list_posrep_angle_errors(
                "beta angle", error_by_beta, beta_error_max, csv=True
            ):
                yield line

            yield "alpha max,angle"
            for amax, alpha in positional_repeatability_result[
                "posrep_alpha_max_at_angle"
            ].items():
                yield "%r,%r" % (amax, alpha)
            yield ""
            yield "beta max,angle"
            for bmax, beta in positional_repeatability_result[
                "posrep_beta_max_at_angle"
            ].items():
                yield "%r,%r" % (amax, alpha)

            yield ""
            yield "analysis results alpha"
            yield "alpha,beta,i,j,k,xl,yl,ql,xs,ys,qs"
            for (
                (alpha, beta, i, j, k),
                (xl, yl, q1, xs, ys, q2),
            ) in positional_repeatability_result["analysis_results_alpha"].items():
                yield "%f,%f,%i,%i,%i,%f,%f,%f,%f,%f,%f" % (
                    alpha,
                    beta,
                    i,
                    j,
                    k,
                    xl,
                    yl,
                    q1,
                    xs,
                    ys,
                    q2,
                )

            yield "analysis results beta"
            yield "alpha,beta,i,j,k,xl,yl,ql,xs,ys,qs"
            for (
                (alpha, beta, i, j, k),
                (xl, yl, q1, xs, ys, q2),
            ) in positional_repeatability_result["analysis_results_beta"].items():
                yield "%f,%f,%i,%i,%i,%f,%f,%f,%f,%f,%f" % (
                    alpha,
                    beta,
                    i,
                    j,
                    k,
                    xl,
                    yl,
                    q1,
                    xs,
                    ys,
                    q2,
                )

            yield (
                rfmt_pos_rep.POS_REP_CALPARS_CSV.format(
                    **positional_repeatability_result
                )
            )

            yield EMPTY_LINE

            yield (
                rfmt_pos_rep.POS_REP_GEARCOR_CSV.format(
                    **positional_repeatability_result
                )
            )

            yield rfmt_pos_rep.POS_REP_GEARALGO_CSV.format(
                **positional_repeatability_result
            )

            if positional_repeatability_images:
                yield "images_alpha"
                yield "alpha,beta,i,j,k,asteps,bsteps,ipath"
                for (
                    (alpha, beta, i, j, k),
                    (asteps, bsteps, ipath),
                ) in positional_repeatability_images["images_alpha"].items():
                    yield "%f,%f,%i,%i,%i,%i,%i,%s" % (
                        alpha,
                        beta,
                        i,
                        j,
                        k,
                        asteps,
                        bsteps,
                        ipath,
                    )
                yield EMPTY_LINE
                yield "images_beta"
                yield "alpha,beta,i,j,k,asteps,bsteps,ipath"
                for (
                    (alpha, beta, i, j, k),
                    (asteps, bsteps, ipath),
                ) in positional_repeatability_images["images_beta"].items():
                    yield "%f,%f,%i,%i,%i,%i,%i,%s" % (
                        alpha,
                        beta,
                        i,
                        j,
                        k,
                        asteps,
                        bsteps,
                        ipath,
                    )

        else:
            yield rfmt_pos_rep.POS_REP_ERRMSG.format(**positional_repeatability_result)

    yield EMPTY_LINE

    if positional_verification_result is None:
        yield rfmt_pos_ver.POS_VER_NA_CSV
    else:
        err_msg = positional_verification_result["error_message"]
        if not err_msg:
            yield rfmt_pos_ver.POS_VER_RESULT_CSV.format(
                **positional_verification_result
            )

            yield (
                rfmt_pos_ver.POS_VER_CALPARS_CSV.format(
                    **positional_verification_result
                )
            )

            error_by_coords = positional_verification_result["posver_error_by_angle"]
            yield ""
            yield "posver errors"
            yield "i,alpha,beta,err"
            for (i, alpha, beta), err in error_by_coords.items():
                yield "%i,%f,%f,%f" % (i, alpha, beta, err)

        else:
            yield rfmt_pos_ver.POS_VER_ERRMSG_CSV.format(
                **positional_verification_result
            )

        if positional_verification_images:
            yield EMPTY_LINE
            yield "i,alpha,beta,ipath"
            for (k, alpha, beta), ipath in positional_verification_images[
                "images"
            ].items():
                yield "%i,%f,%f,%s" % (k, alpha, beta, ipath)
            yield EMPTY_LINE

    if pupil_alignment_result is None:
        yield rfmt_pup_aln.PUP_ALN_NA_CSV
    else:
        err_msg = pupil_alignment_result["error_message"]
        if not err_msg:
            yield rfmt_pup_aln.PUP_ALN_RESULT_CSV.format(**pupil_alignment_result)

            yield rfmt_pup_aln.PUP_ALN_CALPARS_CSV.format(**pupil_alignment_result)

            yield "alpha,beta,x,y,q"
            for (alpha, beta), (x, y, q) in pupil_alignment_result["coords"].items():
                yield "%f,%f,%f,%f,%f" % (alpha, beta, x, y, q)

        else:
            yield rfmt_pup_aln.PUP_ALN_ERRMSG.format(**pupil_alignment_result)

        if pupil_alignment_images:
            yield "alpha,beta,ipath"
            for (alpha, beta), ipath in pupil_alignment_images["images"].items():
                yield "%f,%f,%s" % (alpha, beta, ipath)
            yield EMPTY_LINE


def colorize(ddict):
    for record in [
        "datum_result",
        "alpha_min_result",
        "alpha_max_result",
        "beta_min_result",
        "beta_max_result",
        "beta_collision_result",
        "datum_repeatability_result",
        "metrology_calibration_result",
        "metrology_height_result",
        "positional_repeatability_result",
        "positional_verification_result",
        "pupil_alignment_result",
    ]:
        if (ddict is not None) and (record in ddict):
            if (ddict[record] is not None) and ("result" in ddict[record]):
                ddict[record]["result"] = color_result(ddict[record]["result"])

    return ddict


def report(dbe, opts):

    report_format = dbe.opts.report_format
    for count, fpu_id in enumerate(dbe.eval_fpuset):
        ddict = vars(get_data(dbe, fpu_id))

        if opts.colorize and report_format not in ["status", "brief", "csv"]:
            ddict = colorize(ddict)

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
        elif report_format == "extended":
            lines = format_report_extended(**ddict)
        else:
            lines = format_report_csv(**ddict)
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
