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

from encoder import Encoder


class Controller:

    def __init__(self, name, valve, sensor, encoder, gauge):

        self._prev_timestamp = 0

        self._name = name
        self._valve = valve
        self._sensor = sensor
        self._encoder = encoder
        self._gauge = gauge

        self._open = False
        self._temp = 0
        self._flow = 0
        self._prev_flow = 0
        self._vol = 0

        self._enc_button = False
        self._enc_dblclick = False
        self._enc_change = False
        self._enc_val = 0

    def reset(self):

        print("{}: reset".format(self._name))

        self._open = False
        self._temp = 0
        self._flow = 0
        self._prev_flow = 0
        self._vol = 0

        self._enc_button = False
        self._enc_dblclick = False
        self._enc_change = False
        self._enc_val = 0

        self._valve.reset()
        self._encoder.reset()
        self._gauge.reset()
        self._sensor.reset()

    @property
    def name(self):
        return self._name

    @property
    def volume(self):
        return self._vol

    @volume.setter
    def volume(self, vol):
        self._vol = vol
        self._enc_val = vol

    def tick(self, timestamp):

        # Input ticks
        self._encoder.tick(timestamp)

        # Operation
        self._read_state()
        self._update_state(timestamp)
        self._write_state()

        # Output ticks
        self._gauge.tick(timestamp)
        self._sensor.tick(timestamp)

        self._prev_timestamp = timestamp

    def _read_state(self):

        # Read the valve state
        self._open = self._valve.is_open

        # Read the sensor values
        self._temp = self._sensor.temperature
        self._prev_flow = self._flow
        self._flow = self._sensor.flow_rate

        # Read the encoder state
        self._enc_button = self._encoder.button
        self._enc_dblclick = self._encoder.dblclick
        self._enc_change = self._encoder.change
        self._enc_val = self._encoder.value

    def _update_state(self, timestamp):

        # If there was a manual change to via the encoder, use the new value; Otherwise calculate the new volume.
        if self._enc_change:
            self._vol = self._enc_val
            print("{}: vol={}".format(self._name, self._enc_val))
        else:
            period = (timestamp - self._prev_timestamp) * pow(10, -9)  # NOTE: flow is in litre/min, work in secs
            flow = (self._flow + self._prev_flow)/120
            delta = flow * period
            self._vol -= delta

        # If the button was pushed toggle the valve
        if self._enc_button:
            self._open = not self._open
            if self._open:
                print("{}: start".format(self._name, self._open))
            print("{}: open={}".format(self._name, self._open))

        # If we have dispensed the configured volume, shut the valve
        if self._vol <= 0:
            self._vol = 0
            self._enc_val = 0
            if self._open:
                self._open = False
                print("{}: stop".format(self._name, self._open))
                print("{}: open={}".format(self._name, self._open))

        # If the encoder was double-clicked reset everything
        if self._enc_dblclick:
            self.reset()

    def _write_state(self):

        # Write the valve state
        if self._open:
            self._valve.open()
            self._encoder.led_color(Encoder.LED_BLUE)
        else:
            self._valve.close()
            self._encoder.led_color(Encoder.LED_GREEN)

        # Write the encoder state
        self._encoder.value = self._vol

        # Write the gauge state
        self._gauge.vol = self._vol
        self._gauge.flow = self._flow
        self._gauge.temp = self._temp
