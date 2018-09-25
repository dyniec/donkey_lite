from . import base

class KerasPilot(base.Part):
    def __init__(self, model_path):
        super(KerasPilot, self).__init__()
        import keras as K
        self.model = K.models.load_model(model_path)

    def get_steering(self, img_arr):
        img_arr = img_arr.reshape((1,) + img_arr.shape)
        outputs = self.model.predict(img_arr)
        return tuple(o[0][0] for o in outputs)
