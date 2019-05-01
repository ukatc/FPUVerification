from __future__ import absolute_import, division, print_function

import os
import errno
import logging

from vfr.conf import VERIFICATION_ROOT_FOLDER

class Filter_FPU(logging.Filter):
    def __init__(self, name=""):
        self.name = name

    def filter(self, record):
        return record.name.startswith(self.name)

def addLoggingLevel(levelName, levelNum, methodName=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
       raise AttributeError('{} already defined in logging module'.format(levelName))
    if hasattr(logging, methodName):
       raise AttributeError('{} already defined in logging module'.format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
       raise AttributeError('{} already defined in logger class'.format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)
    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)



def configure_logs(measure_fpuset, fpu_config):
    logpath = os.path.join(VERIFICATION_ROOT_FOLDER, "logs")
    try:
        os.makedirs(logpath)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise

    addLoggingLevel("AUDIT", logging.DEBUG + 5)
    addLoggingLevel("TRACE", logging.DEBUG - 5)

    # create root logger
    logger = logging.getLogger("")
    logger.setLevel(logging.DEBUG)
    logging.captureWarnings(True)

    logname = os.path.join(logpath, "verification.log")
    filehandler = logging.FileHandler(logname)
    filehandler.setLevel(logging.DEBUG)
    logger.addHandler(filehandler)
    streamhandler = logging.StreamHandler()
    streamhandler.setLevel(logging.INFO)
    # create formatter
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s : %(message)s', "%H:%M:%S")

    # add formatter to ch
    filehandler.setFormatter(file_formatter)
    streamhandler.setFormatter(console_formatter)

    logger.addHandler(streamhandler)

    # add one audit logger for each FPU which is _measured_.
    # We don't create an audit log for all evaluated FPUs,
    # because this can result in a very large
    # number of files opened
    for fpu_id in measure_fpuset:
        ser_num = fpu_config[fpu_id]["serialnumber"]
        fpu_logfile = os.path.join(logpath, ser_num + "_audit.log")

        #audit_filter = Filter_FPU("FPU01")
        audit_handler = logging.FileHandler(fpu_logfile)
        audit_handler.setLevel(logging.AUDIT)

        # add formatter to ch
        audit_handler.setFormatter(file_formatter)
        #f1_handler.addFilter(audit_filter)
        print("adding logger for FPU %r" % ser_num)
        audit_log = logging.getLogger(ser_num)
        audit_log.setLevel(logging.DEBUG)
        audit_log.addHandler(audit_handler)


def get_fpuLogger(fpu_id, fpu_config, *args):
    try:
        serial_number = fpu_config[fpu_id]["serialnumber"]
        targs = (serial_number,) + args
    except KeyError:
        targs = args

    lname = ".".join(targs)
    fpu_logger = logging.getLogger(lname)

    return fpu_logger
