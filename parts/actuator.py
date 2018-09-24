from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import atexit
import collections
import serial
import struct
import time

from . import base


CarStatus = collections.namedtuple(
    "CarStatus", 
    ["user_angle", "user_throttle", "pilot_angle", "pilot_throttle",
     "distance", "mode"])


def clip(v, _min, _max):
    if v < _min:
        v = _min
    elif v > _max:
        v = _max
    return v


class BluePill(base.Part):
    """
    Control and read user commands from the BluePill.
    """
    MASK_ANGLE = 0x01
    MASK_THROTTLE = 0x02
    MODES = {
        'user': 0x00,
        'local_angle': MASK_ANGLE,
        'local_throttle': MASK_THROTTLE,
        'local': MASK_THROTTLE + MASK_ANGLE
    }
    MODES_INV = {v:k for k,v in MODES.items()}
    # Format of recieved mesages: SteerDuty, ThrottleDuty, Distance, AutosteerMask
    RX = struct.Struct("<HHHBx")
    # Format of recieved mesages: SteerDuty, ThrottleDuty, Command, AutoEnable, AutoNReset
    TX = struct.Struct("<HHBBB")
    CMD_NOOP = 0x00
    CMD_SET_SERVOS = 0x01
    CMD_SET_STEER_LIMITS = 0x02
    CMD_SET_THROTTLE_LIMITS = 0x03


    def __init__(self,
                 port="/dev/ttyACM0",
                 steer_min=3000,
                 steer_mid=4500,
                 steer_max=6000,
                 throttle_min=2800,
                 throttle_mid=4500,
                 throttle_max=6400,
                 ):
        self.s = serial.Serial(port)
        self.angle_neutral = steer_mid
        self.angle_gain = max(steer_mid - steer_min,
                              steer_max - steer_mid)
        self.angle_clip = min(steer_mid - steer_min,
                              steer_max - steer_mid
                              ) / self.angle_gain
        self.throttle_neutral = throttle_mid
        self.throttle_gain = max(throttle_mid - throttle_min,
                                 throttle_max - throttle_mid)
        self.throttle_clip = min(throttle_mid - steer_min,
                                 throttle_max - throttle_mid
                                ) / self.throttle_gain
        self.last_mode = None
        self.pilot_state = (0, 0)
        atexit.register(self.stop_and_disengage_autonomy)

    def _recieve(self):
        RX = self.RX
        msg = self.s.read(RX.size)
        user_angle, user_throttle, dist, mode = RX.unpack(msg)
        user_angle = (user_angle - self.angle_neutral) / self.angle_gain
        user_throttle = (user_throttle - self.throttle_neutral) / self.throttle_gain
        mode = self.MODES_INV[mode]
        # print("BP ret: %10f %10f %10s %10d" %(user_angle, user_throttle, user_mode, dist))
        return CarStatus(
            user_angle, user_throttle,
            self.pilot_state[0], self.pilot_state[1],
            dist, mode)

    def get_raw_duties(self):
        """Read raw servo values form the BluePill controller."""
        msg = self.TX.pack(0, 0, self.CMD_NOOP, 0, 0)
        self.s.write(msg)
        RX = self.RX
        msg = self.s.read(RX.size)
        user_angle, user_throttle, unused_dist, unused_mode = RX.unpack(msg)
        return user_angle, user_throttle
    
    def get_status(self):
        """Read the RC values, pilot values, distance and mode."""
        msg = self.TX.pack(0, 0, self.CMD_NOOP, 0, 0)
        self.s.write(msg)
        return self._recieve()

    def drive(self, pilot_angle, pilot_throttle, mode="local", force_mode=False):
        """Steer the car and select autonomy."""
        auto_enable = 0
        auto_nreset = 0
        if (mode != self.last_mode) or force_mode:
            auto_enable = self.MODES[mode]
            auto_nreset = ~auto_enable & 0x03
            self.last_mode = mode
        pilot_angle = clip(pilot_angle,
                           -self.angle_clip, self.angle_clip)
        pilot_throttle = clip(pilot_throttle,
                              -self.throttle_clip, self.throttle_clip)
        self.pilot_state = (pilot_angle, pilot_throttle)
        pilot_angle = pilot_angle * self.angle_gain + self.angle_neutral
        pilot_throttle = pilot_throttle * self.throttle_gain + self.throttle_neutral
        
        # print("BP debug tx: ", pilot_angle, pilot_throttle, auto_enable, auto_nreset)
        msg = self.TX.pack(int(pilot_angle), int(pilot_throttle),
                           self.CMD_SET_SERVOS,
                           auto_enable, auto_nreset)
        self.s.write(msg)
        ret = self._recieve()
        if mode != ret.mode:
            print("Warning: The desired mode %s was not set!\n"
                  "Probably the autopilot was disengaged by breaking. "
                  "To re-enable use the parameter force_mode." % mode)

    def stop_and_disengage_autonomy(self):
        """Stop the car and disengage the autopilot."""
        msg = self.TX.pack(self.angle_neutral, self.throttle_neutral,
                           self.CMD_SET_SERVOS, 0, self.MODES["local"])
        self.s.write(msg)
        return self._recieve()
