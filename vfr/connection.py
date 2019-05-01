from __future__ import absolute_import, division, print_function

import os
import logging

import FpuGridDriver
from FpuGridDriver import ProtectionError, LOG_GRIDSTATE
from vfr.tests_common import flush


def check_ping_ok(ipaddr):
    rv = os.system("ping -q -c 1 -W 3 >/dev/null %s" % ipaddr)
    return rv == 0


def check_connection(opts, name, address):
    logger = logging.getLogger(__name__)
    logger.info("testing connection to %s ..." % name)

    pok = check_ping_ok(address)
    if not pok:
        logger.critical("network connection to %s FAILED - aborting" % name)
        raise AssertionError(
            "network connection to %s at address %r not alive" % (name, address)
        )
    else:
        logger.info("testing connection to %s ... OK" % name)


def init_driver(opts, N, env=None, protected=True):
    logger = logging.getLogger(__name__)
    logger.debug("initializing for %i FPUs" % N)
    if protected:
        try:
            rd = FpuGridDriver.GridDriver(N, env=env, logLevel=LOG_GRIDSTATE)
        except ProtectionError as e:
            logger.critical(
                "protectionError exception raised -- maybe the"
                " postion database needs to be initialized with 'init' ?\n\n" %
                str(e)
            )
    else:
        rd = FpuGridDriver.UnprotectedGridDriver(N, logLevel=LOG_GRIDSTATE)

    gateway_adr = [
        FpuGridDriver.GatewayAddress(opts.gateway_address, opts.gateway_port)
    ]

    logger.info("connecting grid: %r" % rd.connect(address_list=gateway_adr))

    grid_state = rd.getGridState()

    return rd, grid_state


def check_can_connection(rd, grid_state, opts, fpu_id):
    logger = logging.getLogger(__name__)

    logger.debug("checking CAN connection to FPU %i ..." % fpu_id)
    flush()

    rv = rd.pingFPUs(grid_state, fpuset=[fpu_id])

    if rv != FpuGridDriver.ethercanif.DE_OK:
        logger.critical("CAN connection to FPU %i does not work! aborting." % fpu_id)
    else:
        logger.debug("checking CAN connection to FPU %i ... OK" % fpu_id)


    assert rv == FpuGridDriver.ethercanif.DE_OK

    return rv  # # pylint: disable=no-member


def ping_fpus(gd, grid_state, opts):
    logger = logging.getLogger(__name__)

    gd.pingFPUs(grid_state)

    if opts.resetFPUs:
        logger.info("resetting FPUs ..")
        gd.resetFPUs(grid_state)
        logger.info("resetting FPUs ... OK")

    return grid_state
