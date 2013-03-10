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

import pylab

from matplotlib import finance
from matplotlib import transforms


def offset(ax, x, y):
    return transforms.offset_copy(ax.transData, x=x, y=y, units='dots')


def label_bar(ax, label, bar, above=False):
    trans = offset(ax, 0, -12.5)
    x = bar[0]
    y = bar[4]
    if above:
        trans = offset(ax, 0, 5)
        y = bar[3]
        ax.text(x, y, label, transform=trans)


def plot_setup(signal, date_strfmt='%b-%d'):
    fig = pylab.figure(figsize=(16, 9))
    fig.subplots_adjust(bottom=0.2)

    ax = fig.add_subplot(111)
    ax.margins(0.05, 0.05)

    bars = signal['flip']['bars'] + signal['bars']
    bars = [[b['dt'].to_pydatetime(), b['open'],
             b['close'], b['high'], b['low']] for b in bars]

    ax.set_xticks(range(0, len(bars)))
    ax.set_xticklabels([bars[i][0].strftime(date_strfmt)
                        for i in ax.get_xticks()])

    plot_bars = [[i] + bar[1:] for i, bar in enumerate(bars)]

    finance.plot_day_summary(ax, plot_bars)

    flip_end = len(signal['flip']['bars']) - 1
    label_bar(ax, 'X', plot_bars[0], True)
    label_bar(ax, 'Y', plot_bars[1], True)
    label_bar(ax, "X'", plot_bars[flip_end - 1], True,)
    label_bar(ax, "Y'", plot_bars[flip_end], True)

    for i, bar in enumerate(plot_bars[flip_end:], 1):
        label_bar(ax, i, bar)

    ax.autoscale_view()
    pylab.setp(pylab.gca().get_xticklabels(), rotation=45,
               horizontalalignment='right')
    pylab.show()
