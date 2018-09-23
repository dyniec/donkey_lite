from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import keras as K

from . import base


class Keras(base.Part):
    def __init__(self, model_path):
        super(Keras, self).__init__()
        self.model = K.models.load_model(model_path)

    def __call__(self, img_arr):
        img_arr = img_arr.reshape((1,) + img_arr.shape)
        outputs = self.model.predict(img_arr)
        steering = outputs[0]
        throttle = outputs[1]
        return steering[0][0], throttle[0][0]
