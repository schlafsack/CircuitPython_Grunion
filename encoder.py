import time
from i2c_encoder.encoder import Encoder as I2CEncoder


class Encoder:

    REFRESH_FREQ = 100000000
    MIN_VALUE = 0.0
    MAX_VALUE = 80.0

    @staticmethod
    def _build_i2c_encoder(i2c, address):
        enc = I2CEncoder(i2c, address)
        enc.gconf_rst = 1  # Reset the encoder
        time.sleep(0.5)
        enc.gconf_etype = 1  # Set the type to RGB encoder
        enc.gconf_dtype = 1  # Set the datatype to float
        enc.gconf_wrape = 1  # Enable encoder value wrapping
        enc.dpperiod = 200  # Enable double click
        enc.cmin_float = Encoder.MIN_VALUE  # Set the min, max and step for encoder 0
        enc.cmax_float = Encoder.MAX_VALUE
        enc.cval_float = 0
        enc.istep_float = 0.25
        enc.rled = 0x00  # Turn the LEDs blue
        enc.gled = 0x00
        enc.bled = 0x50
        enc.gp1conf_mode = 0b11  # Configure the GPIO inputs
        enc.gp1conf_pul = 1
        return enc

    def __init__(self, i2c, address):
        self.enc = self._build_i2c_encoder(i2c, address)
        self._t1 = time.monotonic_ns()  # timer used for state refresh
        self._value = 0.0
        self._value_refresh = True

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

    def tick(self, on_change=None, on_click=None, on_doubleclick=None, on_status=None):
        timestamp = time.monotonic_ns()

        if timestamp - self._t1 > self.REFRESH_FREQ:
            self._t1 = timestamp

            #Update the encoder value if required
            if self._value_refresh:
                self.enc.cval_float = self._value
                if on_change:
                    on_change(self._value)
                self._value_refresh = False

            #Make status callbacks
            status = self.enc.estatus
            if status > 0 and on_status:
                on_status(status)
            if status & (1 << 2) and on_doubleclick:
                on_doubleclick()

            #Update value
            if status & (1 << 3) or status & (1 << 4):
                self._value = self.enc.cval_float
                if on_change:
                    on_change(self._value)
