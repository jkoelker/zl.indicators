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

from zl.indicators import countdown
from zl.indicators import flip
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

        self.flip_period = flip_period
        self.flip_field = flip_field

        self.setup_period = setup_period
        self.setup_lookback = setup_lookback
        self.setup_field = setup_field
        self.setup_reverse_cancel = setup_reverse_cancel

        self.countdown_period = countdown_period,
        self.countdown_lookback = countdown_lookback
        self.countdown_field = countdown_field

        self.flip = flip.FlipWindow(self.flip_period, self.flip_field)
        self.windows.append(self.flip)

        self.setups = {setup.BUY: None, setup.SELL: None}

    def update(self, event):
        for window in self.windows:
            window.update(event)

    def _clear_setup(self, direction):
        existing_setup = self.setups.get(direction)
        if existing_setup is None:
            return

        if existing_setup in self.windows:
            self.windows.remove(existing_setup)

        self.setups[direction] = None

    def _add_setup(self, direction):
        existing_setup = self.setups.get(direction)

        # NOTE(jkoelker) We are already tracking a setup in this direction
        if existing_setup is not None:
            return

        new_setup = setup.SetupWindow(self.setup_period,
                                      self.setup_lookback,
                                      self.setup_field)
        self.windows.append(new_setup)
        self.setups[direction] = new_setup
        return self.setups[direction]

    def _start_setup(self, direction):
        if direction == setup.BUY:
            self._clear_setup(setup.SELL)
            return self._add_setup(setup.BUY)

        elif direction == setup.SELL:
            self._clear_setup(setup.BUY)
            return self._add_setup(setup.SELL)

    def _check_setups(self):
        for direction, setup_window in self.setups.iteritems():
            if setup_window is None:
                continue
            return setup_window()

    def _start_countdown(self, direction, setup_signal):
        pass

    def __call__(self):
        flip_signal = self.flip()

        if not flip_signal:
            return

        if flip_signal == flip.BEAR:
            self._start_setup(setup.BUY)
        elif flip_signal == flip.BULL:
            self._start_setup(setup.SELL)

        setup_signal = self._check_setups()
        if not setup_signal:
            return

        if setup_signal.direction == setup.BUY:
            self._start_countdown(countdown.BUY, setup_signal)
        elif setup_signal.direction == setup.SELL:
            self._start_countdown(countdown.SELL, setup_signal)
