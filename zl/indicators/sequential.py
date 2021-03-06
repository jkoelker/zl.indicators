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
import functools

from zl.indicators import countdown
from zl.indicators import setup
from zipline.transforms import utils as transforms


BUY = 'Buy'
SELL = 'Sell'


class Sequential(object):
    __metaclass__ = transforms.TransformMeta

    def __init__(self, flip_period=4, flip_field='close',
                 setup_period=9, setup_lookback=4,
                 setup_field=None, setup_reverse_cancel=True,
                 countdown_period=13, countdown_lookback=2,
                 countdown_field=None):

        if setup_field is None:
            setup_field = flip_field

        if countdown_field is None:
            countdown_field = setup_field

        self.flip_period = flip_period
        self.flip_field = flip_field

        self.setup_period = setup_period
        self.setup_lookback = setup_lookback
        self.setup_field = setup_field
        self.setup_reverse_cancel = setup_reverse_cancel

        self.countdown_period = countdown_period
        self.countdown_lookback = countdown_lookback
        self.countdown_field = countdown_field

        self.sid_windows = collections.defaultdict(self.create_window)

    def create_window(self):
        args = (self.flip_period, self.flip_field,
                self.setup_period, self.setup_lookback,
                self.setup_field, self.setup_reverse_cancel,
                self.countdown_period, self.countdown_lookback,
                self.countdown_field)
        return SequentialWindow(*args)

    def update(self, event):
        window = self.sid_windows[event.sid]
        window.update(event)
        return window()


class SequentialWindow(object):
    def __init__(self, flip_period, flip_field,
                 setup_period, setup_lookback,
                 setup_field, setup_reverse_cancel,
                 countdown_period, countdown_lookback,
                 countdown_field):
        self.windows = []

        self.setup_reverse_cancel = setup_reverse_cancel

        self.countdown_period = countdown_period,
        self.countdown_lookback = countdown_lookback
        self.countdown_field = countdown_field

        self.setup = setup.SetupWindow(setup_period,
                                       setup_lookback,
                                       setup_field,
                                       flip_period,
                                       flip_field)
        self.windows.append(self.setup)

        self.countdown = None
        self.setup_signal = None
        self.start_countdown = functools.partial(countdown.CountdownWindow,
                                                 countdown_period,
                                                 countdown_lookback,
                                                 countdown_field)

    def update(self, event):
        for window in self.windows:
            window.update(event)

        if self.setup_signal:
            self.setup_signal.check_perfection(event)

    def _handle_setup(self, signal):
        if not self.setup_signal and not self.countdown:
            self.setup_signal = signal
            self.countdown = self.start_countdown(setup_signal=signal)
            self.windows.append(self.countdown)

    def __call__(self):
        setup_signal = self.setup()
        if setup_signal is not None:
            self._handle_setup(setup_signal)

        if not self.setup_signal or not self.countdown:
            return

        countdown = self.countdown()
        return countdown

#        if setup_signal.direction == setup.BUY:
#            self._start_countdown(countdown.BUY, setup_signal)
#        elif setup_signal.direction == setup.SELL:
#            self._start_countdown(countdown.SELL, setup_signal)
