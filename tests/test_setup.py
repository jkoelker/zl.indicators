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

import tests
from tests import generators

from zl.indicators import flip
# NOTE(jkoelker) nose likes to run things named setup ;)
from zl.indicators import setup as module


class TestSetup(tests.Base):
    def test_sell_setup(self):
        flip_signal = {'direction': flip.BULL}

        df = generators.sell_setup()
        events = generators.to_events(df)
        signal = module.setup(events, 'close', 9, 4, flip_signal)

        self.assertIsNotNone(signal)
        self.assertEqual(signal['direction'], module.SELL)

    def test_buy_setup(self):
        flip_signal = {'direction': flip.BEAR}

        df = generators.buy_setup()
        events = generators.to_events(df)
        signal = module.setup(events, 'close', 9, 4, flip_signal)

        self.assertIsNotNone(signal)
        self.assertEqual(signal['direction'], module.BUY)
