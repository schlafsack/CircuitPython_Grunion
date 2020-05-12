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

from ncd_pr33_15.receiver import Receiver, GAIN_2X, SAMPLE_RATE_16_BIT, CHANNEL_1, CHANNEL_2, CHANNEL_3, CHANNEL_4
from sgfilter import SGFilter

"""

See https://store.ncd.io/product/4-channel-i2c-4-20ma-current-receiver-with-i2c-interface/

Current = input voltage * 0.00401
ohm's law - V = I*R
I = V/R - in this case R is 249

The voltage will depend on gain and vref ( 2.048V).

Voltage = (raw_adc/32767) * (2.048/Gain) * 5.45( op-amp gain)

I * R = (raw_adc/32767) * (2.048/Gain) * 5.45

4 * 249 = (raw/32767) * (2.048/2) * 5.45


Maximum n-bit code = 2N-1 - 1
Minimum n-bit code = -1 x 2N-1

12 = 2047
14 = 8191
16 = 32767

(((I * 249) / 5.45) / (2.048/2)) * (pow(2, bit_rate) - 1) = raw_adc

(((.004 * 249) / 5.45) / (2.048/2)) * 2047 = 365.3261181193
(((.020 * 249) / 5.45) / (2.048/2)) * 2047 = 1,826.6305905963

(((.004 * 249) / 5.45) / (2.048/2)) * 8191 = 1,461.8398795872
(((.020 * 249) / 5.45) / (2.048/2)) * 8191 = 7,309.1993979358

(((.004 * 249) / 5.45) / (2.048/2)) * 32767 = 5,847.8949254587
(((.020 * 249) / 5.45) / (2.048/2)) * 32767 = 29,239.4746272936

4_12 = 365.3261181193
20_12 = 1826.6305905963

4_14 = 1461.8398795872
20_14 = 7309.1993979358

4_16 = 5847.8949254587
20_16 29239.4746272936

m = (Y2-Y1)/(X2-X1)
y = mx + c


16-bit
--------

mt_16 = (125 - (-25)) / (29239.4746272936 - 5847.8949254587) = 0.006412563919
mf_16 = (15 - 0.9) / (29239.4746272936 - 5847.8949254587) = 0.0006027810084

ct_16 = 0 - ((0.006412563919 * 29239.4746272936) - 125) = -62.5000000055
cf_16 = 0 - ((0.0006027810084 * 29239.4746272936) - 15) = -2.6250000009

12-bit
--------
mt_12 = (125 - (-25)) / (1826.6305905963 - 365.3261181193) = 0.1026480127
mf_12 = (15 - 0.9) / (1826.6305905963 - 365.3261181193) = 0.009648913191

ct_12 = 0 - ((0.1026480127 * 1826.6305905963) - 125) = -62.5000000617
cf_12 = 0 - ((0.009648913191 * 1826.6305905963) - 15) = -2.6250000007

"""


class Sensor:

    # We can do a max of 15 samples/sec at 16-bits, so lets try 10/s to give ourselves breathing room.
    SAMPLE_FREQ = 100000000

    TEMP_M_16 = 0.006412563919
    FLOW_M_16 = 0.0006027810084

    TEMP_C_16 = -62.5000000055
    FLOW_C_16 = -2.6250000009

    TEMP_BUFFER_SIZE = 7
    FLOW_BUFFER_SIZE = 15

    CH_1 = CHANNEL_1
    CH_2 = CHANNEL_2
    CH_3 = CHANNEL_3
    CH_4 = CHANNEL_4

    def __init__(self, i2c, flow_ch, temp_ch):
        self._t1 = 0
        self._receiver = self._create_reveiver(i2c)
        self._flow_ch = flow_ch
        self._temp_ch = temp_ch
        self._flow = 0
        self._temp = 0

        self._temp_buffer = []
        self._temp_filter = SGFilter(nr=Sensor.TEMP_BUFFER_SIZE, nl=Sensor.TEMP_BUFFER_SIZE)

        self._flow_buffer = []
        self._flow_filter = SGFilter(nr=Sensor.FLOW_BUFFER_SIZE, nl=Sensor.FLOW_BUFFER_SIZE)

        return

    def reset(self):
        return

    def tick(self, timestamp):
        if timestamp - self._t1 > self.SAMPLE_FREQ:
            self._t1 = timestamp
            self._flow = self._read_flow()
            self._temp = self._read_temp()

    @property
    def temperature(self):
        return self._temp

    @property
    def flow_rate(self):
        return self._flow

    def _read_temp(self):

        self._receiver.channel = self._temp_ch

        # Ensure that the buffer is full
        self._fill_buffer(self._temp_buffer, Sensor.TEMP_BUFFER_SIZE, "temp", self._temp_ch)

        # Read the next filtered value
        self._temp_buffer.pop(0)
        raw = self._receiver.raw_value()
        self._temp_buffer.append(raw)
        filtered_data = self._temp_filter.filter(self._temp_buffer)
        raw_filtered = filtered_data[Sensor.TEMP_BUFFER_SIZE]
        temp = (Sensor.TEMP_M_16 * raw_filtered) + Sensor.TEMP_C_16
        return temp if temp > 0 else 0

    def _read_flow(self):
        self._receiver.channel = self._flow_ch

        # Ensure that the buffer is full
        self._fill_buffer(self._flow_buffer, Sensor.FLOW_BUFFER_SIZE, "flow", self._flow_ch)

        # Read the next filtered value
        self._flow_buffer.pop(0)
        raw = self._receiver.raw_value()
        self._flow_buffer.append(raw)
        filtered_data = self._flow_filter.filter(self._flow_buffer)
        raw_filtered = filtered_data[Sensor.FLOW_BUFFER_SIZE]
        flow = (Sensor.FLOW_M_16 * raw_filtered) + Sensor.FLOW_C_16
        return flow if flow > 0 else 0

    def _fill_buffer(self, buffer, size, name, ch):
        if len(buffer) < (size * 2) + 1:
            print("buffering {} on ch {}".format(name, ch), end="")
            while len(buffer) < (size * 2) + 1:
                print(".", end="")
                buffer.append(self._receiver.raw_value())
            print("")

    @staticmethod
    def _create_reveiver(i2c):
        receiver = Receiver(i2c)
        receiver.gain = GAIN_2X
        receiver.sample_rate = SAMPLE_RATE_16_BIT
        receiver.continuous = False
        return receiver
