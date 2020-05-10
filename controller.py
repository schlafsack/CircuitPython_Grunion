# coding=iso-8859-1
from encoder import Encoder
from sgfilter import SGFilter


class Controller:

    def __init__(self, name, valve, sensor, encoder, gauge):

        self._prev_timestamp = 0

        self._name = name
        self._valve = valve
        self._sensor = sensor
        self._encoder = encoder
        self._gauge = gauge

        self._open = False
        self._temp = 0.0
        self._flow = 0.0
        self._vol = 0.0

        self._enc_button = False
        self._enc_dblclick = False
        self._enc_change = False
        self._enc_val = 0.0

        # Setup the sensor filter
        self._sensor_buf = []
        self._sensor_filter = SGFilter(nr=25, nl=25)

    def reset(self):

        print("resetting {}.".format(self._name))

        self._open = False
        self._temp = 0.0
        self._flow = 0.0
        self._vol = 0.0

        self._enc_button = False
        self._enc_dblclick = False
        self._enc_change = False
        self._enc_val = 0.0

        self._valve.reset()
        self._encoder.reset()
        self._gauge.reset()
        self._sensor.reset()

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

    def _read_flow_rate(self):

        # Fill the sample window
        while len(self._sensor_buf) < 51:
            self._sensor_buf.append(self._sensor.flow_rate)

        # Add the current sensor flow rate to the buffer
        self._sensor_buf.pop(0)
        self._sensor_buf.append(self._sensor.flow_rate)

        # Filter the values and return the midpoint value
        f = self._sensor_filter.filter(self._sensor_buf)
        return f[26] if f[26] > 0 else 0.0

    def _read_state(self):

        # Read the valve state
        self._open = self._valve.is_open

        # Read the sensor values
        self._temp = self._sensor.temperature
        self._flow = self._read_flow_rate()

        # Read the encoder state
        self._enc_button = self._encoder.button
        self._enc_dblclick = self._encoder.dblclick
        self._enc_change = self._encoder.change
        self._enc_val = self._encoder.value

    def _update_state(self, timestamp):

        # If there was a manual change to via the encoder, use the new value; Otherwise calculate the new volume.
        if self._enc_change:
            self._vol = self._enc_val
        else:
            period = (timestamp - self._prev_timestamp) * pow(10, -9)  # NOTE: flow is in litre/min, work in secs
            delta = (self._flow/60) * period
            self._vol -= delta

        # If the button was pushed toggle the valve
        if self._enc_button:
            self._open = not self._open

        # If we have dispensed the configured volume, shut the valve
        if self._vol <= 0:
            self._vol = 0.0
            self._enc_val = 0.0
            self._open = False

        # If the encoder was double-clicked reset everything
        if self._enc_dblclick:
            self.reset()

    def _write_state(self):

        # Write the valve state
        if self._open:
            self._valve.open()
            self._encoder.led_color(Encoder.LED_GREEN)
        else:
            self._valve.close()
            self._encoder.led_color(Encoder.LED_BLUE)

        # Write the encoder state
        self._encoder.value = self._vol

        # Write the gauge state
        self._gauge.vol = self._vol
        self._gauge.flow = self._flow
        self._gauge.temp = self._temp

