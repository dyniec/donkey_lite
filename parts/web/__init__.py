import io
import json
import logging
import os
import random
import socket
import time
import threading

import tornado
import tornado.ioloop
import tornado.web
import tornado.gen

import numpy as np
import PIL.Image

from .. import base


logger = logging.getLogger(__name__ )


def get_ip_address():
    try:
        ip = ([l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1],
                               [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in
                                 [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0])
        return ip
    except OSError: #occurs when cannot connect to '8.8.8.8' 
        return "127.0.0.1" #loopback


def arr_to_binary(arr):
    """
    accepts: PIL image
    returns: binary stream (used to save to database)
    """
    arr = np.uint8(arr)
    img = PIL.Image.fromarray(arr)
    f = io.BytesIO()
    img.save(f, format='jpeg')
    return f.getvalue()

class WebStatus(tornado.web.Application):
    port = 8887

    def __init__(self):
        logger.info('Starting Donkey Server...')
        self.img_arr = np.zeros((160, 120, 3))
        self.status = {}
        self.recording = False
        self.drive_mode = "user"
        self.vehicle_running = False



        this_dir = os.path.dirname(os.path.realpath(__file__))
        self.static_file_path = os.path.join(this_dir, 'templates', 'static')

        handlers = [
            (r"/", tornado.web.RedirectHandler, dict(url="/status")),
            (r"/video", VideoAPI),
            (r"/status", StatusAPI),
            (r"/updates", UpdateAPI),
            (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": self.static_file_path}),
            ]

        settings = {'debug': True}
        super().__init__(handlers, **settings)
        
        self.listen(self.port)
        self.instance = tornado.ioloop.IOLoop.instance()
        self.instance.add_callback(self.say_hello)

        self._thread = threading.Thread(target=self.instance.start)
        self._thread.daemon = True
        self._thread.start()
    
    def say_hello(self):
        print("You can watch the camera stream at http://%s:8887/status" %
              (get_ip_address(), ))

    def stop(self):
        self.instance.stop()

    def __del__(self):
        pass
        # self.stop()

    def set_image(self, img_arr):
        self.img_arr = img_arr

    def set_car_status(self, status):
        self.status = status


class UpdateAPI(tornado.web.RequestHandler):
    def get(self):
        data = self.application.status
        if data:
            data = data._asdict()
        self.write(json.dumps(data))


class StatusAPI(tornado.web.RequestHandler):
    def get(self):
        data = {}
        self.render("templates/status.html", **data)

    def post(self):
        """
        Receive post requests as user changes the angle
        and throttle of the vehicle on a the index webpage
        """
        data = tornado.escape.json_decode(self.request.body)
        self.application.recording = data["recording"]
        self.application.drive_mode =  data["drive_mode"]
        self.application.vehicle_running = data["vehicle_running"]


class VideoAPI(tornado.web.RequestHandler):
    """
    Serves a MJPEG of the images posted from the vehicle.
    """
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):

        ioloop = tornado.ioloop.IOLoop.current()
        self.set_header("Content-type", "multipart/x-mixed-replace;boundary=--boundarydonotcross")

        self.served_image_timestamp = time.time()
        my_boundary = "--boundarydonotcross"
        while True:
            interval = .1
            if self.served_image_timestamp + interval < time.time():

                img = arr_to_binary(self.application.img_arr)

                self.write(my_boundary)
                self.write("Content-type: image/jpeg\r\n")
                self.write("Content-length: %s\r\n\r\n" % len(img))
                self.write(img)
                self.served_image_timestamp = time.time()
                yield tornado.gen.Task(self.flush)
            else:
                yield tornado.gen.Task(ioloop.add_timeout, ioloop.time() + interval)
