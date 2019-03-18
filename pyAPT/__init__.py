from __future__ import absolute_import

try:
    import pylibftdi

    _PRODUCT_IDS = pylibftdi.USB_PID_LIST
    _PRODUCT_IDS[:] = [0xFAF0]

except ImportError:
    print (
        ">>>>>>>>>>> Warning: Import of pylibftdi failed - probably dependency mismatch."
    )

from pyAPT import message, controller, mts50, prm1, cr1z7, nr360s

__version__ = "0.01"
__author__ = "Shuning Bian"

__all__ = [
    "Message",
    "Controller",
    "MTS50",
    "OutOfRangeError",
    "PRM1",
    "CR1Z7",
    "NR360S" "add_PID",
]

Message = message.Message
Controller = controller.Controller

MTS50 = mts50.MTS50
PRM1 = prm1.PRM1
CR1Z7 = cr1z7.CR1Z7
NR360S = nr360s.NR360S

OutOfRangeError = controller.OutOfRangeError


def add_PID(pid):
    """
    Adds a USB PID to the list of PIDs to look for when searching for APT
    controllers
    """
    _PRODUCT_IDS.append(pid)
