import datetime
import numpy as np

from parts import camera
from parts import data
from parts import sleep
from parts import web

sleep = sleep.SmartSleep(frequency=20)
#cam = camera.PiCamera()
cam = camera.FakeCamera()
stream = web.CameraStream()

# add tub to save data
inputs = ['cam/image_array', 'timestamp']
types = ['image_array', 'str']

# single tub
tub = data.TubWriter(path='./testtub', inputs=inputs, types=types)

while True:
    sleep()
    timestamp = str(datetime.datetime.utcnow())
    img = cam()
    stream(img)
    tub(img, timestamp)
