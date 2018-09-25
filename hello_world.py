import time
import parts
import car_config
from parts.actuator import BluePill
import numpy as np

DIST_THRESHOLD = 200
FORWARD_SPEED = 0.20
BACKWARD_SPEED = -0.30
ZERO_ANGLE = 0.02
ZERO_ANGLE = 0.15666666666666668

class Clock:
    def __init__(self):
        self._tick_start = time.time()

    def tick(self, herz):
        if time.time() - self._tick_start < 1 / herz:
            time.sleep(1 / herz - (time.time() - self._tick_start))  # Maybe while True loop with sleep(0.0001) ?

        else:
            print("WARNING: Main loop too slow")
        self._tick_start = time.time()

MY_CAR = '01'
bluepill_controller = parts.BluePill(**car_config.bluepill_configs[MY_CAR])
#bluepill_controller = BluePill("/dev/ttyACM0")
            
clock = Clock()
clock.tick(10)
cam = parts.PiCamera()
web_stream = parts.WebStatus()
force=False

import cv2
#while True:
#    status = bluepill_controller.get_status()
#    print(status)
#    clock.tick(10)

def green(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    
    lower_green=np.array([42,55,58])
    upper_green=np.array([82,245,245])
    mask=cv2.inRange(hsv, lower_green, upper_green)
    mask=mask==255
    return mask
def predict(img):
    h,w=img.shape
    sum,cnt=0,0
    for i in range(h):
      for j in range(w):
        sum+=img[i,j]*(j-w//2)
        cnt+=img[i,j]
    if cnt==0:
      return 0
    return -sum/cnt/(w/2)
try:

    while True:
        status = bluepill_controller.get_status()
        print(status)
        distance = status.distance
        img = cam.get_image()
        img=img.copy()
        print(img.shape)
        img=img[-50:]
        web_stream.set_car_status(status)
        mask=green(img)
        angle=predict(mask)
        web_stream.set_image(img)
        #continue

        if distance > DIST_THRESHOLD:
            bluepill_controller.drive(angle, FORWARD_SPEED,force_mode=force)

        elif distance :
            print('breaking starting')
            bluepill_controller.drive(angle, BACKWARD_SPEED,force_mode=force)
            clock.tick(10)
            bluepill_controller.drive(angle, 0,force_mode=force)
            clock.tick(10)

        clock.tick(10)
finally:
    bluepill_controller.stop_and_disengage_autonomy()


