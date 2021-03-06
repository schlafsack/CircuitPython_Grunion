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

import time
from i2c_encoder.encoder import Encoder as I2CEncoder


class Encoder:

    REFRESH_FREQ = 100000000
    MIN_VALUE = 0
    MAX_VALUE = 80

    LED_RED = 1
    LED_GREEN = 2
    LED_BLUE = 3
    LED_AMBER = 4

    @staticmethod
    def _build_i2c_encoder(i2c, address):
        enc = I2CEncoder(i2c, address)
        enc.gconf_rst = 1  # Reset the encoder
        time.sleep(0.5)
        enc.gconf_etype = 1  # Set the type to RGB encoder
        enc.gconf_dtype = 1  # Set the datatype to float
        enc.gconf_wrape = 0  # Disable encoder value wrapping
        enc.dpperiod = 200  # Enable double click
        enc.cmin_float = Encoder.MIN_VALUE  # Set the min, max and step for encoder 0
        enc.cmax_float = Encoder.MAX_VALUE
        enc.cval_float = 0  # Initial value
        enc.istep_float = 0.25  # Encoder step size
        enc.rled = 0x00  # Turn the LEDs black
        enc.gled = 0x00
        enc.bled = 0x00
        enc.gp1conf_mode = 0b11  # Configure the GPIO inputs
        enc.gp1conf_pul = 1
        return enc

    def __init__(self, i2c, address):
        self.enc = self._build_i2c_encoder(i2c, address)
        self._t1 = 0  # timer used for state refresh
        self._value = 0
        self._value_refresh = True
        self._dblclick = False
        self._button = False
        self._button_down = False
        self._button_up = False
        self._change = False

    def reset(self):
        self._t1 = 0  # timer used for state refresh
        self._value = 0
        self._value_refresh = True
        self._button = False
        self._dblclick = False
        self._button = False
        self._button_down = False
        self._button_up = False
        self._change = False

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value < Encoder.MIN_VALUE:
            self._value = Encoder.MIN_VALUE
        elif value > Encoder.MAX_VALUE:
            self._value = Encoder.MAX_VALUE
        else:
            self._value = value
        self._value_refresh = True

    @property
    def dblclick(self):
        result = self._dblclick
        self._dblclick = False
        return result

    @property
    def button(self):
        result = self._button
        self._button = False
        return result

    @property
    def change(self):
        result = self._change
        self._change = False
        return result

    def led_color(self, color):
        if self.LED_AMBER == color:
            self.enc.rled = 0x25  # Turn the LEDs green
            self.enc.gled = 0x15
            self.enc.bled = 0x00
        elif self.LED_GREEN == color:
            self.enc.rled = 0x00  # Turn the LEDs green
            self.enc.gled = 0x25
            self.enc.bled = 0x00
        elif self.LED_RED == color:
            self.enc.rled = 0x25  # Turn the LEDs red
            self.enc.gled = 0x00
            self.enc.bled = 0x00
        else:
            self.enc.rled = 0x00  # Turn the LEDs blue
            self.enc.gled = 0x00
            self.enc.bled = 0x25


    def tick(self, timestamp):

        if timestamp - self._t1 > self.REFRESH_FREQ:
            self._t1 = timestamp
            status = self.enc.estatus
            gp1 = self.enc.gp1

            # Update the encoder value if required
            if status & (1 << 3) or status & (1 << 4):
                self._value = self.enc.cval_float
                if not self._change:
                    self._change = True
            elif self._value_refresh:
                self.enc.cval_float = self._value
            self._value_refresh = False

            # Update the double click flag
            if status & (1 << 2) and not self._dblclick:
                self._dblclick = True

            # Update the button click latch
            if gp1 == 0:
                self._button_down = True
                self._button |= self._button_up
                self._button_up = False
            else:
                self._button_up = True
                self._button_down = False
