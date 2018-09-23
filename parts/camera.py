from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import time

import numpy as np

from . import base

class FakeCamera(base.Part):
    def __init__(self, resolution=(120, 160)):
        self.imsize = (resolution[0], resolution[1], 3)
        self.i = 0
    
    def __call__(self):
        img = np.zeros(self.imsize) + self.i
        self.i += 1
        if self.i > 255:
            self.i=0
        return img

class PiCamera(base.ThreadedPart):
    def __init__(self, resolution=(120, 160), framerate=20):
        # do the imports here, to pravent the import from failing when there is 
        # no rasberry
        import picamera
        import picamera.array
        super(PiCamera, self).__init__()
        resolution = tuple(resolution)
        self.camera = picamera.PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.rawCapture = picamera.array.PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture,
                                                     format="rgb",
                                                     use_video_port=True)
        self.frame = None
        print('PiCamera loaded.. .warming camera')
        time.sleep(2)
        # start grabbing frames in the background
        self.start()

    def __call__(self):
        return self.frame

    def update(self):
        # keep looping infinitely until the thread is stopped
        for f in self.stream:
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            self.frame = f.array
            self.rawCapture.truncate(0)

            # if the thread indicator variable is set, stop the thread
            if not self.running:
                self.frame = None
                break

    def __del__(self):
        super(PiCamera, self).__del__()
        self.stream.close()
        self.rawCapture.close()
        self.camera.close()
