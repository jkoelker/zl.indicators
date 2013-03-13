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
import itertools
import numbers
import operator

import numpy as np
from zipline.transforms import utils as transforms
from zl.indicators import flip
from zl.indicators import utils


BUY = 'Buy'
SELL = 'Sell'


def setup(events, field, period, lookback, flip_signal):
    events = list(events)
    values = [e[field] for e in events]

    direction = None
    flip_dir = flip_signal['direction']

    if flip_dir == flip.BEAR and all(itertools.imap(operator.lt,
                                                    values[lookback:],
                                                    values[:period])):
        direction = BUY

    elif flip_dir == flip.BULL and all(itertools.imap(operator.gt,
                                                      values[lookback:],
                                                      values[:period])):
        direction = SELL

    if not direction:
        return

    bars = events[lookback:]
    lowes = [bar['low'] for bar in bars]
    highs = [bar['high'] for bar in bars]

    high = np.max(highs)
    low = np.max(lowes)

    if direction == BUY:
        perfection = np.min(lowes[-4:-2])
    else:
        perfection = np.max(highs[-4:-2])

    return Signal(direction, high, low, bars, perfection, flip_signal)


class Signal(dict):
    def __init__(self, direction, high, low, bars, perfection,
                 flip_signal):
        self['direction'] = direction
        self['high'] = high
        self['low'] = low
        self['bars'] = bars
        self['flip'] = flip_signal
        self['perfection'] = perfection
        self._perfect = False

    def check_perfection(self, event):
        if self['direction'] == BUY:
            self._perfect = event['low'] <= self['perfection']
            return self._perfect
        self._perfect = event['high'] >= self['perfection']
        return self._perfect

    @property
    def is_perfect(self):
        return self._perfect or any([self.check_perfection(b)
                                     for b in self['bars'][-2:]])

    @utils.cached_property
    def risk_level(self):
        for bar in self['bars']:
            if self['direction'] == BUY:
                if bar['low'] == self['low']:
                    return self['low'] - (bar['high'] - bar['low'])

            elif self['direction'] == SELL:
                if bar['high'] == self['high']:
                    return self['high'] + (bar['high'] - bar['low'])

        assert False, "Signal extreme not found in bars!"


class Setup(object):
    __metaclass__ = transforms.TransformMeta

    def __init__(self, period=9, lookback=4, field='close',
                 flip_period=None, flip_field=None):
        if flip_period is None:
            flip_period = lookback

        if flip_field is None:
            flip_field = field

        self.period = period
        self.lookback = lookback
        self.field = field
        self.flip_period = flip_period
        self.flip_field = flip_field
        self.sid_windows = collections.defaultdict(self.create_window)

    def create_window(self):
        return SetupWindow(self.period, self.lookback, self.field,
                           self.flip_period, self.flip_field)

    def update(self, event):
        window = self.sid_windows[event.sid]
        window.update(event)
        return window()


class SetupWindow(transforms.EventWindow):
    def __init__(self, period, lookback, field, flip_period, flip_field):
        window_length = period + lookback - 1
        transforms.EventWindow.__init__(self, window_length=window_length)

        self.period = period
        self.lookback = lookback
        self.field = field

        self.flip = flip.FlipWindow(flip_period, flip_field)
        self.flip_signal = None
        self._counter = 0

    def update(self, *args, **kwargs):
        self.flip.update(*args, **kwargs)
        transforms.EventWindow.update(self, *args, **kwargs)

    def handle_add(self, event):
        for field in (self.field, 'high', 'low'):
            assert field in event
            assert isinstance(event[field], numbers.Number)

    def handle_remove(self, event):
        pass

    def __call__(self):
        flip_signal = self.flip()
        self._counter = self._counter + 1

        if flip_signal and not self.flip_signal:
            self.flip_signal = flip_signal
            self._counter = 1

        if len(self.ticks) < self.window_length:
            return

        if not self.flip_signal:
            return

        if self._counter > self.period:
            self._counter = 0
            return

        if self._counter == self.period:
            signal = setup(self.ticks, self.field, self.period,
                           self.lookback, self.flip_signal)
            self.flip_signal = None
            return signal
