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


def flip(events, field):
    events = list(events)
    Yp = events[-1][field]
    Xp = events[-2][field]
    X = events[0][field]
    Y = events[1][field]

    if (Xp > X) and (Yp < Y):
        return Signal(BEAR, events)
    if (Xp < X) and (Yp > Y):
        return Signal(BULL, events)


class Signal(dict):
    def __init__(self, direction, bars):
        self['direction'] = direction
        self['bars'] = bars


class Flip(object):
    __metaclass__ = transforms.TransformMeta

    def __init__(self, period=4, field='close'):
        self.period = period
        self.field = field
        self.sid_windows = collections.defaultdict(self.create_window)

    def create_window(self):
        return FlipWindow(self.period, self.field)

    def update(self, event):
        window = self.sid_windows[event.sid]
        window.update(event)
        return window()


class FlipWindow(transforms.EventWindow):
    def __init__(self, period, field):
        transforms.EventWindow.__init__(self, window_length=period + 2)

        self.period = period
        self.field = field

    def handle_add(self, event):
        assert self.field in event, "%s not in event" % self.field
        assert isinstance(event[self.field], numbers.Number)

    def handle_remove(self, event):
        pass

    def __call__(self):
        if len(self.ticks) < self.window_length:
            return

        return flip(self.ticks, self.field)
