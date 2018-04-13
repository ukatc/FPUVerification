from __future__ import absolute_import, division
from .controller import Controller

class CR1Z7(Controller):
  """
  A controller for a CR1/MZ-7 rotation stage.

  This is a small rotation stage using a TDC001 controller.
  It is used for testing purposes.
  """
  def __init__(self,*args, **kwargs):
    super(CR1Z7, self).__init__(*args, **kwargs)

    # https://www.thorlabs.com/catalogpages/obsolete/2017/CR1_M-Z7.pdf
    # Note that these values should be pulled from the APT User software,
    # as they agree with the real limits of the stage better than
    # what the website or the user manual states
    self.max_velocity = 6.0 # degree/sec
    self.max_acceleration = 1.0 # degree/sec^2 - this value is guessed

    # from the manual
    # encoder counts per revoultion of the output shaft: 
    # no load speed: n/a
    # max rotation velocity: 6 degree/s
    # min rotation velocity: 22 arcsec / s 
    # Gear ratio: 48 rounds/deg
    # to move 1 deg:  12288 * 48 / 360 encoder steps
    enccnt = 12288 # = 48 * 256

    T = 2048/6e6

    # these equations are taken from the APT protocol manual
    self.position_scale = enccnt  #the number of enccounts per deg
    self.velocity_scale = enccnt * T * 65536
    self.acceleration_scale = enccnt * T * T * 65536

    self.linear_range = (-180,180)

