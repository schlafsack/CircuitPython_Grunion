# coding=iso-8859-1
from digitalio import DigitalInOut, Direction, Pull


class Valve:

    _pin = 0
    _relay = None

    def __init__(self, pin):
        self._pin = pin
        self._relay = DigitalInOut(pin)
        self._relay.direction = Direction.OUTPUT

    def reset(self):
        self.close()

    def open(self):
        self._relay.value = True

    def close(self):
        self._relay.value = False

    @property
    def is_open(self):
        return self._relay.value
