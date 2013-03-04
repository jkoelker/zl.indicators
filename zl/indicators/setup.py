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
from zl.indicators import utils


BUY = 'Buy'
SELL = 'Sell'


def setup(events, field, period, lookback):
    values = [e[field] for e in events]

    direction = None

    if any(itertools.imap(operator.lt,
                          values[lookback:],
                          values[:period])):
        direction = BUY

    elif any(itertools.imap(operator.gt,
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

    return Signal(direction, high, low, bars, perfection)


class Signal(object):
    def __init__(self, direction, high, low, bars, perfection):
        self.directin = direction
        self.high = high
        self.low = low
        self.bars = bars
        self.perfection = perfection

    def check_perfection(self, event):
        if self.direction == BUY:
            return event['low'] <= self.perfection
        return event['high'] >= self.perfection

    @utils.cached_property
    def is_perfect(self):
        return any([self.check_perfection(b) for b in self.bars[-2:]])

    @utils.cached_property
    def risk_level(self):
        for bar in self.bars:
            if self.direction == BUY:
                if bar['low'] == self.low:
                    return self.low - (bar['high'] - bar['low'])

            elif self.direction == SELL:
                if bar['high'] == self.hight:
                    return self.high + (bar['high'] - bar['low'])

        assert False, "Signal extreme not found in bars!"


class Setup(object):
    __metaclass__ = transforms.TransformMeta

    def __init__(self, period=9, lookback=4, field='close'):
        self.period = period
        self.lookback = lookback
        self.field = field
        self.sid_windows = collections.defaultdict(self.create_window)

    def create_window(self):
        return SetupWindow(self.period, self.lookback, self.field)

    def update(self, event):
        window = self.sid_windows[event.sid]
        window.update(event)
        return window()


class SetupWindow(transforms.EventWindow):
    def __init__(self, period, lookback, field):
        window_length = period + lookback
        transforms.EventWindow.__init__(self, window_length=window_length)

        self.period = period
        self.lookback = lookback
        self.field = field

    def handle_add(self, event):
        for field in (self.field, 'high', 'low'):
            assert field in event
            assert isinstance(event[field], numbers.Number)

    def handle_remove(self, event):
        pass

    def __call__(self):
        if len(self.ticks) < self.window_length:
            return

        return setup(self.ticks, self.field, self.period, self.lookback)
