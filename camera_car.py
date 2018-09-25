import datetime
import numpy as np

import parts

timer = parts.Timer(frequency=20)
cam = parts.PiCamera()
# cam = parts.FakeCamera()
web_stream = parts.WebStatus()

# add tub to save data
inputs = ['image_array', 'timestamp']
types = ['image_array', 'str']
tub = parts.TubWriter(path='./testtub', inputs=inputs, types=types)

try:
    while True:
        timer.tick()
        timestamp = str(datetime.datetime.utcnow())
        img = cam.get_image()
        web_stream.set_image(img)
        tub.write(img, timestamp)
finally:
    pass
