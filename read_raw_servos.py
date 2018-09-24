import datetime
import numpy as np

import parts

bluepill = parts.BluePill()
timer = parts.Timer(frequency=20)

try:
    while True:
        timer.tick()
        angle_duty, throttle_duty = bluepill.get_raw_duties()
        print("A: %d T: %d" % (angle_duty, throttle_duty))
finally:
    bluepill.stop_and_disengage_autonomy()
