# coding=iso-8859-1
from board import SCL, SDA, TX, RX
from busio import I2C, UART

from encoder import Encoder
from gauge import Gauge

with I2C(SCL, SDA, frequency=100000) as i2c, UART(TX, RX, baudrate=115200) as uart:
    # Setup the rotary encoders
    encLeft = Encoder(i2c, 0x78)
    encRight = Encoder(i2c, 0x70)

    # Setup the gauges
    gaugeLeft = Gauge(uart, "p0", "vol0", "flow0", "tmp0")
    gaugeRight = Gauge(uart, "p1", "vol1", "flow1", "tmp1")

    def reset_encoder(encoder):
        print("Resetting encoder")
        encoder.value = 0.0

    # Main loop
    while True:

        encLeft.tick(on_change=lambda value: print("left: {}".format(value)),
                     on_doubleclick=lambda: reset_encoder(encLeft))

        encRight.tick(on_change=lambda value: print("right: {}".format(value)),
                      on_doubleclick=lambda: reset_encoder(encRight))

        gaugeLeft.vol = encLeft.value
        gaugeRight.vol = encRight.value

        if encLeft.value > 10:
            gaugeLeft.mode = Gauge.COUNT_DOWN
        else:
            gaugeLeft.mode = Gauge.COUNT_UP

        gaugeLeft.tick()
        gaugeRight.tick()
