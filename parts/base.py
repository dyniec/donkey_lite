from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import threading


logger = logging.getLogger(__name__)


class Part(object):
    pass

class ThreadedPart(Part):
    def __init__(self):
        self.running = False
        self._thread = None
    
    def start(self):
        if self.running:
            return
        self._thread = threading.Thread(target=self.update, args=())
        self._thread.daemon = True
        self.running = True
        self._thread.start()
    
    def stop(self):
        self.running = False
        if self._thread is None:
            return
        self.running = False
        self._thread.join(0.5)
        if self._thread.is_alive():
            logger.warn("Couldn't kill thread for class %s",
                        self.__class__.__name__)
        else:
            self._thread = None

    def __del__(self):
        self.stop()

    def update(self):
        pass
