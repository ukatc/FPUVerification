"""Module to control the Lamps via MCCDAQ.

Largely simplifies the interface to the uldaq library. The Factory function generators the Lamp Controller object and the context managers can be used to access the lamp functionality of the Controller object. This is to manage the connection to the DAQ, keeping it stable over a period and letting it be easy to mock.

It is possible to update this interface to operate the lamps simultaneously or to work with a specific DAQ.

Created on 20/03/2019

@author: Alan O'Brien

:History:
206 Mar 2019: Initial commit and release version.

"""

__version__ = "1.0"
__author__ = "Alan O'Brien"

from __future__ import print_function, division
from contextlib import contextmanager
import time

from uldaq import get_daq_device_inventory, DaqDevice, InterfaceType, AOutFlag, DigitalDirection, DigitalPortIoType

from vfr.conf import LAMP_WARMING_TIME_MILLISECONDS

# Exceptions to raise if there is an error related to the Lamp


class LampDAQError(Exception):
    pass


DAQ_DEVICE_INDEX = 0 # Assuming there is one device connected.
SILHOUETTE_PORT_INDEX = 0 #Using 1stPortA
AMBIENT_PORT_INDEX = 0 #Using 1stPortA

# If lamps are swapped, the plugs may have been swapped, either swap plugs back or change these values
SILHOUETTE_WRITE_VALUE = 2 
AMBIENT_WRITE_VALUE = 1 

BACKLIGHT_CHANNEL = 0

# here a nice explanation how the context managers work:
# https://jeffknupp.com/blog/2016/03/07/python-with-context-managers/


class lampController():
    """ Class to control lamps through an attached DAQ.
    
    The connected ports are
        AO0       : Fibre backlight lamp
        1stPortA0 : Ambient 
        1stPortA1 : Silhouette lamp
    """
    
    def __init__(self):
        """ Connect to the first DAQ device found, configure digital ports and retrieve needed information about analog ports.
        """
        
        # Connect to DAQ device as in examples 
        # Get descriptors for all of the available DAQ devices.
        devices = get_daq_device_inventory(InterfaceType.USB)
        number_of_devices = len(devices)
        if number_of_devices == 0:
            raise LampDAQError('Error: No DAQ devices found')
        if number_of_devices < 1:
            raise LampDAQError('Error: Too many DAQs devices found')
            
        self.daq_device = DaqDevice(devices[DAQ_DEVICE_INDEX])
        self.daq_device.connect()
        # TODO: work out how to connect to a specific DAQwith
        self.digital_device = self.daq_device.get_dio_device()
        if self.digital_device is None:
            raise LampDAQError('Error: The connected device does not support digital output')
        self.analog_device = self.daq_device.get_ao_device()
        if self.analog_device is None:
            raise LampDAQError('Error: The connected device does not support analog output')
        
        # Now connected to the DAQ device, configure the needed ports.
        
        # Set up Digital ports
        
        self.silhouette_port = self.digital_device.get_info().get_port_types()[SILHOUETTE_PORT_INDEX]
        self.ambient_port = self.digital_device.get_info().get_port_types()[AMBIENT_PORT_INDEX]
        
        self.digital_device.d_config_port(self.silhouette_port, DigitalDirection.OUTPUT)
        self.digital_device.d_config_port(self.ambient_port, DigitalDirection.OUTPUT)
                
        # Storing values for use in Analog mode
        
        self.analog_output_range = self.analog_device.get_info().get_ranges()[0]

    def _switch_fibre_backlight(self, state, manual_lamp_control=False):
        if manual_lamp_control:
            raw_input("switch state of backlight to %r and presse <enter>" % state)
        else:
            self.analog_device.a_out(BACKLIGHT_CHANNEL,self.analog_output_range, AOutFlag.DEFAULT, 0)

    def _switch_fibre_backlight_voltage(self, voltage, manual_lamp_control=False):
        if manual_lamp_control:
            raw_input("switch state of backlight to %r and presse <enter>" % state)
        else:
            self.analog_device.a_out(BACKLIGHT_CHANNEL,self.analog_output_range, AOutFlag.DEFAULT, voltage)

    def _switch_ambientlight(self, state, manual_lamp_control=False):
        if manual_lamp_control:
            raw_input("switch state of ambient light to %r and presse <enter>" % state)
        else:
            if state == "on":
                value = AMBIENT_WRITE_VALUE
            elif state == "off":
                value = 0
            else:
                raise LampDAQError("Bad state value, should be on or off, recivievd {}".format(state))
            self.digital_device.d_out(self.ambient_port, value)

    def _switch_silhouettelight(self, state, manual_lamp_control=False):
        if manual_lamp_control:
            raw_input("switch state of silhouette light to %r and presse <enter>" % state)
        else:
            if state == "on":
                value = SILHOUETTE_WRITE_VALUE
            elif state == "off":
                value = 0
            else:
                raise LampDAQError("Bad state value, should be on or off, recivievd {}".format(state))
            self.digital_device.d_out(self.silhouette_port, value)

    @contextmanager
    def use_silhouettelight(self, manual_lamp_control=False):
        self._switch_silhouettelight("on", manual_lamp_control=manual_lamp_control)
        time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)
        try:
            yield None
            
        finally:
            self._switch_silhouettelight("off", manual_lamp_control=manual_lamp_control)
            time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)

    @contextmanager
    def use_backlight(self, voltage, manual_lamp_control=False):
        self._switch_fibre_backlight_voltage(voltage, manual_lamp_control=manual_lamp_control)
        time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)
        try:
            yield None
            
        finally:
            self._switch_fibre_backlight("off", manual_lamp_control=manual_lamp_control)
            time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)

    @contextmanager
    def use_ambientlight(self, manual_lamp_control=False):
        self._switch_ambientlight("on", manual_lamp_control=manual_lamp_control)
        time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)
        try:
            yield None
            
        finally:
            self._switch_ambientlight("off", manual_lamp_control=manual_lamp_control)
            time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)
