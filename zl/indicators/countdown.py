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


def countdown(direction, events, period, lookback, field):
    event_iter = itertools.izip(events[lookback:], events[:-lookback])
    signals = []
    compare_field = 'low'
    compare_op = operator.le

    if direction == SELL:
        compare_field = 'high'
        compare_op = operator.ge

    for position, (event, prior) in enumerate(event_iter):
        if compare_op(event[field], prior[compare_field]):
            signals.append(position)

    if len(signals) >= period:
        bars = [bar for bar in events[lookback:]]

        # TODO(jkoelker) Figure out if bar "8" should be determined by
        #                the period length
        qualifier = bars[signals[7]]
        ending = bars[signals[-1]]

        if compare_op(ending[compare_field], qualifier[field]):
            lowes = [bar['low'] for bar in bars]
            highs = [bar['high'] for bar in bars]

            high = np.max(highs)
            low = np.max(lowes)
            return Signal(direction, high, low, bars, signals)


class Signal(object):
    def __init__(self, direction, high, low, bars, signals):
        self.directin = direction
        self.high = high
        self.low = low
        self.bars = bars
        self.signals = signals

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


class Countdown(object):
    __metaclass__ = transforms.TransformMeta

    def __init__(self, period=13, lookback=2, field='close'):
        self.period = period
        self.lookback = lookback
        self.field = field
        self.sid_windows = collections.defaultdict(self.create_window)

    def create_window(self):
        return CountdownWindow(self.period, self.lookback, self.field)

    def update(self, event):
        window = self.sid_windows[event.sid]
        window.update(event)
        return window()


class CountdownWindow(transforms.EventWindow):
    def __init__(self, period, lookback, field, setup_signal=None):
        window_length = period + lookback
        transforms.EventWindow.__init__(self, window_length=window_length)

        self.period = period
        self.lookback = lookback
        self.field = field
        self.setup_signal = setup_signal
        self.signal = None

        # NOTE(jkoelker) Prime the window with the last event + lookback
        #                from the setup_signal
        if self.setup_signal is not None:
            for bar in self.setup_signal.bars[-(lookback + 1):]:
                self.update(bar)

    # TODO(jkoelker) There is probably a bug in the window expansion. Need
    #                to think aboot this more
    def handle_add(self, event):
        for field in (self.field, 'high', 'low'):
            assert field in event
            assert isinstance(event[field], numbers.Number)

        if len(self.ticks) >= self.window_length and self.setup_signal:
            self.signal = countdown(self.setup_signal.direct, self.ticks,
                                    self.period, self.lookback, self.field)

        # NOTE(jkoelker) Check if we need to expand the window
        if len(self.ticks) == self.window_length:
            self.window_length = self.window_length + 1

    def handle_remove(self, event):
        pass

    def _reset_window(self):
        self.window_length = self.period + self.lookback

    def __call__(self):
        if len(self.ticks) < self.window_length:
            return

        # NOTE(jkoelker) If tracking a Setup Signal, the signal is
        #                determined in the handle_add phase
        if self.signal:
            self._reset_window()
            return self.signal

        # NOTE(jkoelker) We are not tracking a Setup Signal
        signal = None
        if not self.setup_signal:
            signal = countdown(BUY, self.ticks, self.period, self.lookback,
                               self.field)
        if not self.setup_signal and not signal:
            signal = countdown(SELL, self.ticks, self.period, self.lookback,
                               self.field)

        self._reset_window()
        return signal
