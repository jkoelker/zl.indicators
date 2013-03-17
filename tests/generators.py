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

import itertools
import random

import numpy as np
import pandas as pd


def to_events(df):
    return [row.to_dict() for _date, row in df.iterrows()]


def higher(value, factor=2, odds_same=5):
    h = value + (factor * random.random())
    return random.choice([h] * odds_same + [value])


def lower(value, factor=2, odds_same=5):
    l = value - (factor * random.random())
    return random.choice([l] * odds_same + [value])


def near(value):
    return random.choice([higher, lower])(value, factor=1)


def random_day(seed=20):
    c = random.choice([higher, lower])(seed * random.random())
    o = random.choice([higher, lower])(c)
    return pd.DataFrame({'price': [c],
                         'open': [o],
                         'close': [c],
                         'high': [higher(np.max([o, c]))],
                         'low': [lower(np.min([o, c]))],
                         'volume': [1000]})


def flip(seed, period, functions):
    closes = [f(seed) for f in functions]
    opens = [random.choice([higher, lower])(c) for c in closes]
    highs = [higher(np.max(x)) for x in itertools.izip(opens, closes)]
    lowes = [lower(np.min(x)) for x in itertools.izip(opens, closes)]
    volumes = np.random.random(len(closes)) * 1000

    return pd.DataFrame({'price': closes, 'open': opens, 'close': closes,
                         'high': highs, 'low': lowes, 'volume': volumes})


def bear_flip(seed=20, period=4):
    middle = [near] * (period - 2)
    functions = [lower, higher] + middle + [higher, lower]
    return flip(seed, period, functions)


def bull_flip(seed=20, period=4):
    middle = [near] * (period - 2)
    functions = [higher, lower] + middle + [lower, higher]
    return flip(seed, period, functions)
