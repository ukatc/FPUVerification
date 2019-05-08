from __future__ import absolute_import, division, print_function

import os
import errno
import logging
import logging.handlers

from vfr.conf import VERIFICATION_ROOT_FOLDER
from vfr.tests_common import timestamp

class Filter_FPU(logging.Filter):
    def __init__(self, name=""):
        self.name = name

    def filter(self, record):
        return record.name.startswith(self.name)

class Filter_Level(logging.Filter):
    def __init__(self, level=logging.INFO):
        self.levelno = level

    def filter(self, record):
        return record.levelno >= self.levelno

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

# create root logger
# this needs to happen soon enough, otherwise a default
# stderr handler is created which logs with level
# debug to console, which we don't want.


logger = logging.getLogger("")
logger.setLevel(logging.DEBUG)
#logger.addHandler(logging.NullHandler())
logging.captureWarnings(True)
streamhandler = logging.StreamHandler()
logger.addHandler(streamhandler)


def configure_logs(measure_fpuset, fpu_config, loglevel=logging.INFO):
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


    logname = os.path.join(logpath, "verification-%s.log" % timestamp())
    filehandler = logging.FileHandler(logname)
    filehandler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
    filehandler.setFormatter(file_formatter)
    logger.addHandler(filehandler)

    print("setting log level for streamhandler to %s" % loglevel)
    streamhandler.setLevel(loglevel)
    logger.setLevel(min(logging.DEBUG, loglevel))
    # create formatter
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s : %(message)s', "%H:%M:%S")

    # add formatter to ch
    streamhandler.setFormatter(console_formatter)
    #stream_filter = Filter_Level(level=loglevel)
    #streamhandler.addFilter(stream_filter)


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


def add_email_handler(
        toaddrs,
        subject="critical errors in verification rig",

):
    if not toaddrs:
        return

    mailhost="outlook.office365.com"
    mailport=993
    fromaddress="verificationrig@hotmail.com"
    credentials=("verificationrig@hotmail.com", "ApQ353K!")

    mail_handler = logging.handlers.SMTPHandler(
        (mailhost, mailport),
        fromaddress,
        toaddrs,
        subject,
        credentials=credentials)

    mail_handler.setLevel(logging.CRITICAL)
    logger.addHandler(mail_handler)
