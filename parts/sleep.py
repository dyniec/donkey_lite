from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import time

from . import base


class SmartSleep(base.Part):
    def __init__(self, frequency=20):
        self.period = 1.0 / frequency
        self.last_start = 0

    def __call__(self):
        needed_sleep = self.period + self.last_start - time.time()
        if needed_sleep > 0:
            time.sleep(needed_sleep)
        self.last_start = time.time()
