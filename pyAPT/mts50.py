from __future__ import absolute_import, division
from .controller import Controller

class MTS50(Controller):
  """
  A controller for a MTS50/M-Z8 stage.
  """
  def __init__(self,*args, **kwargs):
    super(MTS50, self).__init__(*args, **kwargs)

    # http://www.thorlabs.co.uk/thorProduct.cfm?partNumber=MTS50/M-Z8
    # Note that these values are pulled from the APT User software,
    # as they agree with the real limits of the stage better than
    # what the website or the user manual states
    self.max_velocity = 0.45
    self.max_acceleration = 0.45

    # from private communication with thorlabs tech support:
    # steps per revolution: 48
    # gearbox ratio: 256
    # pitch: 0.5 mm
    # thus to advance 1 mm you need to turn 48*256*2 times
    enccnt = 48*256*2
    T = 2048/6e6

    # these equations are taken from the APT protocol manual
    self.position_scale = enccnt
    self.velocity_scale = enccnt * T * 65536
    self.acceleration_scale = enccnt * T * T * 65536

    self.linear_range = (0,50)



  def request_home_params(self, negative_direction=True, lswitch=None, velocity=2):
    # retrieve homing parameters from
    # controller, using the method of the super class
    channel_id, homing_direction, _lswitch, homing_velocity, offset_distance = Controller.request_home_params(self)
    
    print("setting home params for MTS50..")
    if negative_direction:
      homing_direction=2
      lswitch = 1
    else:
      homing_direction=1
      lswitch=4

    # override lswitch setting if set
    if lswitch != None:
      _lswitch = lswitch

    if velocity != None:
      homing_velocity = velocity
      
    return (channel_id, homing_direction, _lswitch, homing_velocity, offset_distance)
  
