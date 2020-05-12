# coding=iso-8859-1
import time
import random
import microcontroller
import struct

from board import SCL, SDA, TX, RX, D2, D3
from busio import I2C, UART

from encoder import Encoder
from valve import Valve
from gauge import Gauge
from controller import Controller
from mock_sensor import Sensor

REFRESH_FREQ = 10000000  # Overall system freq. (100th sec)
STATE_FREQ = 2000000000  # Persist state to NVM freq. (2 secs)
NVM_STATE_FORMAT = "ff"  # Left and right volume
NVM_STATE_LENGTH = struct.calcsize(NVM_STATE_FORMAT)


def load_controller_state():
    try:
        state = struct.unpack(NVM_STATE_FORMAT, microcontroller.nvm[0:NVM_STATE_LENGTH])
        print("loaded state {}".format(state))
        return state
    except Exception as ex:
        print("Unable to load controller state. {}.".format(ex))
        return 0, 0


def save_controller_state(state):
    try:
        microcontroller.nvm[0:NVM_STATE_LENGTH] = struct.pack(NVM_STATE_FORMAT, state[0], state[1])
        print("saving state {}".format(state))
    except Exception as ex:
        print("Unable to save controller state. {}.".format(ex))


with I2C(SCL, SDA, frequency=100000) as i2c, UART(TX, RX, baudrate=115200) as uart:

    # Initialise random
    random.seed(time.monotonic_ns())

    # Setup the valves
    valve_left = Valve(D2)
    valve_right = Valve(D3)

    # Setup the rotary encoders
    enc_left = Encoder(i2c, 0x78)
    enc_right = Encoder(i2c, 0x70)

    # Setup the gauges
    gauge_left = Gauge(uart, "p0", "vol0", "flow0", "tmp0")
    gauge_right = Gauge(uart, "p1", "vol1", "flow1", "tmp1")

    # Setup the sensors
    sensor_left = Sensor(10, 1, valve_left)
    sensor_right = Sensor(10, 1, valve_right)

    # Setup the controllers
    ctlr_left = Controller("left", valve_left, sensor_left, enc_left, gauge_left)
    ctlr_right = Controller("right", valve_right, sensor_right, enc_right, gauge_right)

    volumes = load_controller_state()
    ctlr_left.volume = volumes[0]
    ctlr_right.volume = volumes[1]

    # Main loop - ticks the controllers at the configured frequency
    refresh_timestamp = time.monotonic_ns()
    state_timestamp = time.monotonic_ns()
    try:
        while True:
            if time.monotonic_ns() - refresh_timestamp > REFRESH_FREQ:
                refresh_timestamp = time.monotonic_ns()
                ctlr_left.tick(refresh_timestamp)
                ctlr_right.tick(refresh_timestamp)
            if time.monotonic_ns() - state_timestamp > STATE_FREQ:
                state_timestamp = time.monotonic_ns()
                save_controller_state((ctlr_left.volume, ctlr_right.volume))
    finally:
        if valve_left:
            valve_left.close()
        if valve_right:
            valve_right.close()
        if enc_left:
            enc_left.led_color(Encoder.LED_RED)
        if enc_right:
            enc_right.led_color(Encoder.LED_RED)
