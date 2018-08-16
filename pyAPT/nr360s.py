from __future__ import absolute_import, division
from .controller import Controller

class NR360S(Controller):
  """
  A controller for a NR360S rotation stage.

  This is a rotation stage using a BSC201 controller.
  It comes with an imperial and a metric-dimension mount
  (NR360S and NR360S/M), the distinction however
  does not seem to affect any protocol aspects.
  
  """
  def __init__(self,*args, **kwargs):
    super(NR360S, self).__init__(*args, **kwargs)

    # 
    # Note that these values should be pulled from the APT User software,
    # as they agree with the real limits of the stage better than
    # what the website or the user manual states
    self.max_velocity = 50.0 # degree/sec
    self.max_acceleration = 25.0 # degree/sec^2 

    # from the manual
    # These values are only valid for a trinamics controller such as
    # BSC201
    # encoder counts per revoultion of the output shaft: 
    # no load speed: n/a
    # microsteps per step: 2048
    # steps per turn : 200
    # max rotation velocity: 6 degree/s
    # min rotation velocity: 22 arcsec / s 
    # Gear ratio: 66 : 1 rounds/deg, 5.4546 degree / turn
    # to move 1 deg:  
    enccnt =  75093.33333333333 / ((360.0 - 0.0036)/ 360.0)# microstep per degree (from 5.4546 degree / turn)

    # these equations are taken from the APT protocol manual
    self.position_scale = enccnt  #the number of enccounts per deg
    self.velocity_scale = 4030885.0
    self.acceleration_scale = 826.0

    self.linear_range = (0,360)
    self.unit = "Degrees"
    # this controller does not respond to status requests
    self.provided_status = False

    self.checkmodel()


  def checkmodel(self):
    # this is a check function which should make
    # sure that we actually have the right piece
    # of hardware
    modelinfo = self.modelinfo
    assert(modelinfo.model == "SCC201")
    assert(modelinfo.hwtype == 16)


  def request_home_params(self, anti_clockwise=True, lswitch=None, velocity=5.0, offset=None, channel=1):
    # retrieve homing parameters from
    # controller, using the method of the super class
    (channel_id, homing_direction, _lswitch, homing_velocity,
     offset_distance) = Controller.request_home_params(self, channel=channel)
    # because these parameters do not work for the MTS50,
    # we try to adjust them
    print("setting home params for NR360s..")

    if anti_clockwise:
      homing_direction=2
      lswitch = 1
    else:
      homing_direction=1
      lswitch=4

    # override lswitch setting if set
    if lswitch != None:
      _lswitch = lswitch
      
    if velocity != None:
      print("setting speed %f with scale = %f" % (velocity, self.velocity_scale))
      homing_velocity = int(velocity * self.velocity_scale)
      
            

    # ignore offset
    offset_distance = int(0.5 * self.position_scale)
      
    return (channel_id, homing_direction, _lswitch, homing_velocity, offset_distance)
