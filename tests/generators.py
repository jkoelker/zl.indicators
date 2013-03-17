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

import functools
import itertools
import random

import numpy as np
import pandas as pd


def to_events(df):
    return [row.to_dict() for _date, row in df.iterrows()]


def higher(value, factor=2, odds_same=5):
    h = value + (factor * random.random())
    if odds_same > 0:
        return random.choice([h] * odds_same + [value])
    return h


def lower(value, factor=2, odds_same=5, floor=0.1):
    l = floor
    while l <= floor:
        l = value - (factor * random.random())
    if odds_same > 0:
        return random.choice([l] * odds_same + [value])
    return l


def near(value):
    return random.choice([higher, lower])(value, factor=1)


def random_day(seed=20):
    c = random.choice([higher, lower])(seed * (1 + random.random()))
    o = random.choice([higher, lower])(c)
    return pd.DataFrame({'price': [c],
                         'open': [o],
                         'close': [c],
                         'high': [higher(np.max([o, c]))],
                         'low': [lower(np.min([o, c]))],
                         'volume': [1000]})


def random_days(length=6, seed=20):
    df = random_day(seed)
    for _i in xrange(length - 1):
        df = df.append(random_day(seed))
    return df.reset_index()


def days(closes):
    opens = [random.choice([higher, lower])(c) for c in closes]
    highs = [higher(np.max(x)) for x in itertools.izip(opens, closes)]
    lowes = [lower(np.min(x)) for x in itertools.izip(opens, closes)]
    volumes = np.random.random(len(closes)) * 1000

    return pd.DataFrame({'price': closes, 'open': opens, 'close': closes,
                         'high': highs, 'low': lowes, 'volume': volumes})


def flip(seed, functions):
    closes = [f(seed) for f in functions]
    return days(closes)


def bear_flip(seed=20, period=4):
    middle = [near] * (period - 2)
    functions = [lower, higher] + middle + [higher, lower]
    return flip(seed, functions)


def bull_flip(seed=20, period=4):
    middle = [near] * (period - 2)
    functions = [higher, lower] + middle + [lower, higher]
    return flip(seed, functions)


def setup(seed, lookback, functions):
    closes = [random_day(seed)['close']]
    for i, func in enumerate(functions):
        closes.append(func(closes[i]))
    return days(closes)


def sell_setup(seed=20, period=9, lookback=4):
    functions = [functools.partial(higher, odds_same=0)
                 for _i in xrange(period + lookback)]
    return setup(seed, lookback, functions)


def buy_setup(seed=20, period=9, lookback=4):
    functions = [functools.partial(lower, odds_same=0)
                 for _i in xrange(period + lookback)]
    return setup(seed, lookback, functions)
