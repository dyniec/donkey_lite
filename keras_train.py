#!/usr/bin/env python

import argparse
import json
import os
from scipy import ndimage
import zipfile

import numpy as np

import keras as K
import keras.layers as KL

def read_zipfile(file_name):
    records = []
    with zipfile.ZipFile(file_name) as archive:
        for fileinfo in archive.filelist:
            filename = fileinfo.filename
            if not filename.endswith('.json') or filename.endswith('meta.json'):
                continue
            with archive.open(filename) as f:
                data = json.load(f)
            basename = os.path.basename(filename)
            dirname = os.path.dirname(filename)
            # ucinamy 'record_' z przodu i '.json' z tylu
            step_number = int(basename[7:-5])
            with archive.open(dirname + '/' + data['image_array']) as image_file:
                image = ndimage.imread(image_file) / 255.0
            records.append((step_number, image, 
                            data['user_angle'], data['user_throttle']))
    records.sort(key=lambda x: x[0])
    images = np.array([r[1] for r in records], dtype='float32')
    angles = np.array([r[2] for r in records], dtype='float32')[:, None]
    throttles = np.array([r[3] for r in records], dtype='float32')[:, None]
    return images, angles, throttles


def build_model():
    img_in = KL.Input(shape=(120, 160, 3), name='img_in')
    x = img_in

    # Convolution2D class name is an alias for Conv2D
    x = KL.Convolution2D(filters=24, kernel_size=(5, 5), strides=(2, 2), activation='relu')(x)
    x = KL.Convolution2D(filters=32, kernel_size=(5, 5), strides=(2, 2), activation='relu')(x)
    x = KL.Convolution2D(filters=64, kernel_size=(5, 5), strides=(2, 2), activation='relu')(x)
    x = KL.Convolution2D(filters=64, kernel_size=(3, 3), strides=(2, 2), activation='relu')(x)
    x = KL.Convolution2D(filters=64, kernel_size=(3, 3), strides=(1, 1), activation='relu')(x)

    x = KL.Flatten(name='flattened')(x)
    x = KL.Dense(units=100, activation='linear')(x)
    x = KL.Dropout(rate=.1)(x)
    x = KL.Dense(units=50, activation='linear')(x)
    x = KL.Dropout(rate=.1)(x)
    # categorical output of the angle
    angle_out = KL.Dense(units=1, activation='linear', name='angle_out')(x)

    # continous output of throttle
    throttle_out = KL.Dense(units=1, activation='linear', name='throttle_out')(x)

    model = K.Model(inputs=[img_in], outputs=[angle_out, throttle_out])

    model.compile(optimizer='adam',
                  loss={'angle_out': 'mean_squared_error',
                        'throttle_out': 'mean_squared_error'},
                  loss_weights={'angle_out': 0.5, 'throttle_out': .5})

    return model


def train_model(savepath, model, images, angles, throttles):
    train_images, valid_images, test_images = np.split(images, [-1000, -500])
    train_angles, valid_angles, test_angles = np.split(angles, [-1000, -500])
    (train_throttles, valid_throttles, test_throttles
    ) = np.split(throttles, [-1000, -500])

    callbacks = [
        K.callbacks.ModelCheckpoint(savepath, save_best_only=True),
        K.callbacks.EarlyStopping(monitor='val_loss',
                                  min_delta=.0005,
                                  patience=5,
                                  verbose=True,
                                  mode='auto')
    ]

    # Model uczymy na danych uczących.
    # Po każdej epoce (ang. epoch) policzymy błąd na danych walidacyjnych i jeśli
    # model jest lepszy (błąd jest mniejszy), zapisujemy go.
    hist = model.fit(train_images, [train_angles, train_throttles], 
                     epochs=200, 
                     validation_data=(valid_images, [valid_angles, valid_throttles]), 
                     callbacks=callbacks)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('zipfile')
    parser.add_argument('savepath')
    args = parser.parse_args()

    images, angles, throttles = read_zipfile(args.zipfile)
    model = build_model()
    train_model(args.savepath, model, images, angles, throttles)

