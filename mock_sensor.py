# coding=iso-8859-1

# The MIT License (MIT)
#
# Copyright (c) 2020 Tom Greasley
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import math
import random
from sgfilter import SGFilter


# A mock water flow/temperature sensor.
class Sensor:

    SAMPLE_SIZE = 1024
    XMAX = 2.5

    def __init__(self, flow_rate, variance, valve):
        self._flow_rate = flow_rate
        self._variance = variance
        self._valve = valve
        self._tick = 0
        self._value = 0

        # Setup the sensor filter
        self._sensor_buf = []
        self._sensor_filter = SGFilter(nr=25, nl=25)


    def reset(self):
        self._tick = 0
        self._value = 0

    # noinspection PyUnusedLocal
    def tick(self, timestamp):
        value = 0
        while value == 0:
            value = self._read_flow_rate()
        self._value = value

    @property
    def flow_rate(self):
        if self._valve.is_open:
            return self._value
        else:
            return 0.0

    @property
    def temperature(self):
        return random.uniform(10, 11)

    def _read_flow_rate(self):

        # Fill the sample window
        while len(self._sensor_buf) < 51:
            self._sensor_buf.append(self._next_value())

        # Add the current sensor flow rate to the buffer
        self._sensor_buf.pop(0)
        self._sensor_buf.append(self._next_value())

        # Filter the values and return the midpoint value
        f = self._sensor_filter.filter(self._sensor_buf)
        return f[26] if f[26] > 0 else 0.0

    def _next_value(self):
        x1 = self.XMAX * self._tick / (self.SAMPLE_SIZE - 1)
        x2 = self.XMAX * (self._tick + 1) / (self.SAMPLE_SIZE - 1)
        u = random.random()
        v = random.random()

        if u > 0.0:  # Apply the Box--Muller algorithm on |u| and |v|
            f = math.sqrt(-2 * math.log(u))
            z = (math.pi * 2) * v
            u = f * math.cos(z)  # Normally distributed with E(|u|)=0 and Var(|u|)=1
            v = f * math.sin(z)  # Normally distributed with E(|u|)=0 and Var(|u|)=1
            r1 = Sensor._func(x1) + self._variance * u  # $f(x_1)$
            r2 = Sensor._func(x2) + self._variance * v  # $f(x_2)$
            value = self._flow_rate + random.choice([r1, r2])
        else:
            value = 0

        if self._tick > 1024:
            self._tick = 0

        return value

    @staticmethod
    def _gauss(x, w, xa):
        return math.exp((-pow(((x - xa) / w), 2)))

    @staticmethod
    def _func(x):
        value = Sensor._gauss(x, 0.007, 0.2)
        value += Sensor._gauss(x, 0.01, 0.4)
        value += Sensor._gauss(x, 0.02, 0.6)
        value += Sensor._gauss(x, 0.04, 0.8)
        value *= 4.0
        value += math.cos(3.0 * x) * pow(math.sin(pow(x, 3)), 2)
        return value
