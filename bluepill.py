import serial
import struct
import time


class BluePill:
    """
    Control and read user commands from the 
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


    def __init__(self, port,
                 angle_neutral=4350, angle_gain=900,
                 throttle_neutral=4368, throttle_gain=1000, throttle_clip=1.0):
        self.s = serial.Serial(port)
        self.angle_neutral = angle_neutral
        self.angle_gain= angle_gain * 1.0
        self.throttle_neutral = throttle_neutral
        self.throttle_gain = throttle_gain * 1.0
        self.throttle_max = throttle_clip * throttle_gain + throttle_neutral
        self.last_mode = None

        self.previous_args = 0, 0, 'user'  # for use in wrappers

    def run(self, pilot_angle, pilot_throttle, mode):
        auto_enable = 0
        auto_nreset = 0
        if mode != self.last_mode:
            auto_enable = self.MODES[mode]
            auto_nreset = ~auto_enable & 0x03
            self.last_mode = mode
        if pilot_angle is None:
            pilot_angle = 0.0
        if pilot_angle < -1:
            pilot_angle = -1
        if pilot_angle > 1:
            pilot_angle = 1
        if pilot_throttle is None:
            pilot_throttle = 0.0
        if pilot_throttle < -1:
            pilot_throttle = -1
        if pilot_throttle > 1:
            pilot_throttle = 1
        pilot_angle = pilot_angle * self.angle_gain + self.angle_neutral
        pilot_throttle = pilot_throttle * self.throttle_gain + self.throttle_neutral
        pilot_throttle = min(pilot_throttle, self.throttle_max)
        
        # print("BP debug tx: ", pilot_angle, pilot_throttle, auto_enable, auto_nreset)
        msg = self.TX.pack(int(pilot_angle), int(pilot_throttle),
                           self.CMD_SET_SERVOS,
                           auto_enable, auto_nreset)
        self.s.write(msg)
        RX = self.RX
        msg = self.s.read(RX.size)
        user_angle, user_throttle, dist, user_mode = RX.unpack(msg)
        user_angle = (user_angle - self.angle_neutral) / self.angle_gain
        user_throttle = (user_throttle - self.throttle_neutral) / self.throttle_gain
        user_mode = self.MODES_INV[user_mode]
        # print("BP ret: %10f %10f %10s %10d" %(user_angle, user_throttle, user_mode, dist))
        return user_angle, user_throttle, user_mode, dist

    def shutdown(self):
        self.run(0, 0, 'user')


class Robot:
    """Actually usable wrapper over BluePill class. Is not compatible with donkey library"""

    def __init__(self, port='/dev/ttyACM0', autonomy_warnings=True):

        self.autonomy_warnings = autonomy_warnings

        self.bp = BluePill(port=port,  # Wartości określone na podstawie pilota (tego pierwszego)
                           angle_neutral=4417, angle_gain=1000,
                           throttle_neutral=4380, throttle_gain=500)  # To jest ograniczające pełny potencjał to throttle_gain=1700
        self.bp.run(0, 0, 'user')
        time.sleep(0.1)
        self.bp.run(0, 0, 'local')  # Jest z  jakiegoś powodu potrzebne, żebt BluePill włączył tryb 'local'

        self.previous_angle = 0
        self.previous_throttle = 0

    def get_sensors(self):
        return self.bp.run(self.previous_angle, self.previous_throttle, 'local')

    def get_distance(self):
        return self.get_sensors()[3]

    def get_controls(self):
        return self.get_sensors()[:2]

    def set_throttle(self, throttle):
        _, _, mode, _ =self.bp.run(self.previous_angle, throttle, 'local')
        if self.autonomy_warnings and mode != 'local':
            print("WARNING: Autonomy is disabled. Only remote control will have effect on the car")
        self.previous_throttle = throttle

    def set_angle(self, angle):
        _, _, mode, _ = self.bp.run(angle, self.previous_throttle, 'local')
        if self.autonomy_warnings and mode != 'local':
            print("WARNING: Autonomy is disabled. Only remote control will have effect on the car")
        self.previous_angle = angle

    def set_controls(self, angle, throttle):
        _, _, mode, _ = self.bp.run(angle, throttle, 'local')
        if self.autonomy_warnings and mode != 'local':
            print("WARNING: Autonomy is disabled. Only remote control will have effect on the car")
        self.previous_angle, self.previous_throttle = angle, throttle
