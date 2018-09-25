import datetime
import time

import car_config
import parts


MY_CAR = '10'
bluepill = parts.BluePill(**car_config.bluepill_configs[MY_CAR])
kp = parts.KerasPilot('model')
timer = parts.Timer(frequency=20)
cam = parts.PiCamera()


DIST_THRESHOLD = 750
FORWARD_SPEED = 0.15
BACKWARD_SPEED = -0.3
back_counter = 0

try:
    while True:
        timer.tick()
        car_status = bluepill.get_status()
        im = cam.get_image() / 255.0
        ang, thr = kp.get_steering(im)
        bluepill.drive(ang, car_status.user_throttle)
        print(ang, car_status.user_throttle)
finally:
    bluepill.stop_and_disengage_autonomy()
