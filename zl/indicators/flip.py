# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Jason Koelker
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import collections
import numbers

from zipline.transforms import utils as transforms


BULL = 'Bull'
BEAR = 'Bear'


class Flip(object):
    __metaclass__ = transforms.TransformMeta

    def __init__(self, period=4, setup_price='close_price'):
        self.period = period
        self.setup_price = setup_price
        self.sid_windows = collections.defaultdict(self.create_window)

    def create_window(self):
        return FlipWindow(self.period, self.setup_price)

    def update(self, event):
        window = self.sid_windows[event.sid]
        window.update(event)
        return window()


class FlipWindow(transforms.EventWindow):
    def __init__(self, period, setup_price):
        transforms.EventWindow.__init__(self, window_length=period + 2)

        self.period = period
        self.setup_price = setup_price

    def handle_add(self, event):
        assert hasattr(event, self.setup_price)
        value = getattr(event, self.setup_price, None)
        assert isinstance(value, numbers.Number)

    def handle_remove(self, event):
        pass

    def __call__(self):
        if len(self.ticks) < self.window_length:
            return

        Yp = getattr(self.ticks[-1], self.setup_price)
        Xp = getattr(self.ticks[-2], self.setup_price)
        X = getattr(self.ticks[0], self.setup_price)
        Y = getattr(self.ticks[1], self.setup_price)

        if (Xp > X) and (Yp < Y):
            return BEAR
        if (Xp < X) and (Yp > Y):
            return BULL
