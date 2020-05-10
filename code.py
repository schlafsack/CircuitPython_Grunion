#coding=iso-8859-1
import time
import random

from board import SCL, SDA, TX, RX, D2, D3
from busio import I2C, UART

from encoder import Encoder
from valve import Valve
from gauge import Gauge
from controller import Controller
from mock_sensor import Sensor

# Overall system frequency
REFRESH_FREQ = 10000000

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

    # Main loop - ticks the controllers at the configured frequency
    timestamp = time.monotonic_ns()
    try:
        while True:
            if time.monotonic_ns() - timestamp > REFRESH_FREQ:
                timestamp = time.monotonic_ns()
                ctlr_left.tick(timestamp)
                ctlr_right.tick(timestamp)
    finally:
        if valve_left:
            valve_left.close()
        if valve_right:
            valve_right.close()
        if enc_left:
            enc_left.led_color(Encoder.LED_RED)
        if enc_right:
            enc_right.led_color(Encoder.LED_RED)
