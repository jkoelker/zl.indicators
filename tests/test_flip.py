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


class TestFlip(tests.Base):
    def test_bear_flip(self):
        df = generators.bear_flip()
        events = generators.to_events(df)
        signal = flip.flip(events, 'close')

        self.assertIsNotNone(signal)
        self.assertEqual(signal['direction'], flip.BEAR)
        self.assertEqual(signal['bars'], events)

    def test_bull_flip(self):
        df = generators.bull_flip()
        events = generators.to_events(df)
        signal = flip.flip(events, 'close')

        self.assertIsNotNone(signal)
        self.assertEqual(signal['direction'], flip.BULL)
        self.assertEqual(signal['bars'], events)

    # TODO(jkoelker) create better tests for no flip ;(
    def test_no_flip(self):
        same = generators.random_day()
        df = same.append(same)
        df = df.append(same)
        df = df.append(generators.random_days(2))
        df = df.append(same)
        df = df.append(same)
        df = df.reset_index()

        events = generators.to_events(df)
        signal = flip.flip(events, 'close')

        self.assertIsNone(signal)
