from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import time

import numpy as np

from . import base

from donkeycar.parts import datastore


class TubWriter(datastore.Tub):
    def __init__(self, *args, **kwargs):
        super(TubWriter, self).__init__(*args, **kwargs)

    def __call__(self, *args):
        """
        Accepts values, pairs them with their input keys and saves them
        to disk.
        """
        assert len(self.inputs) == len(args)
        record = dict(zip(self.inputs, args))
        self.put_record(record)


class TubReader(datastore.Tub):
    def __init__(self, *args, **kwargs):
        super(TubReader, self).__init__(*args, **kwargs)
        self.read_ix = 0

    def __call__(self, *args):
        """
        Accepts keys to read from the tub and retrieves them sequentially.
        """
        if self.read_ix >= self.current_ix:
            return None

        record_dict = self.get_record(self.read_ix)
        self.read_ix += 1
        record = [record_dict[key] for key in args ]
        return record
