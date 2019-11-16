# coding=iso-8859-1
import time
import math


class Gauge:

    MODE_VOL_TEMP_REFRESH_FREQ = 100000000
    DIAL_FLOW_REFRESH_FREQ = 500000000
    FLOAT_FORMAT = "{:05.2f}"
    TEMP_FORMAT = "{:05.2f} °C"

    COUNT_DOWN = 0
    COUNT_UP = 1

    COLOR_RED = "RED"
    COLOR_GREEN = "GREEN"

    @staticmethod
    def _write_cmd(uart, cmd, sleep=False):
        #print(cmd)
        data = bytearray(cmd.encode('iso-8859-1'))
        data.append(0xFF)
        data.append(0xFF)
        data.append(0xFF)
        uart.write(data)
        if sleep:
            time.sleep(0.01)

    @staticmethod
    def _write_text(uart, target, value, sleep=False):
        Gauge._write_cmd(uart, "{}.txt=\"{}\"".format(target, value), sleep)

    @staticmethod
    def _write_fg_color(uart, target, color, sleep=False):
        Gauge._write_cmd(uart, "{}.pco={}".format(target, color), sleep)

    @staticmethod
    def _write_dial(uart, target, value, sleep=False):
        Gauge._write_cmd(uart, "{}.pic={}".format(target, value), sleep)

    def __init__(self, uart, dial_id, vol_id, flow_id, temp_id):
        self._uart = uart
        self._dial_id = dial_id
        self._vol_id = vol_id
        self._flow_id = flow_id
        self._temp_id = temp_id

        Gauge._write_cmd(self._uart, "bkcmd=0")
        Gauge._write_cmd(self._uart, "dim=100")

        self._mode = Gauge.COUNT_UP
        self._dial = 0
        self._vol = 0.0
        self._temp = 0.0
        self._flow = 0.0

        self._dial_refresh = True
        self._vol_refresh = True
        self._temp_refresh = True
        self._flow_refresh = True

        self._t1 = time.monotonic_ns()  # timer used for vol/temp refresh
        self._t2 = time.monotonic_ns()  # timer used for dial/flow refresh

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        self._mode = mode
        self._mode_refresh = True

    @property
    def vol(self):
        return self._vol

    @vol.setter
    def vol(self, vol):
        if vol < 0:
            self._vol = 0.0
        else:
            self._vol = vol
        self._vol_refresh = True

    @property
    def temp(self):
        return self._temp

    @temp.setter
    def temp(self, temp):
        if temp < 0:
            self._temp = 0.0
        else:
            self._temp = temp
        self._temp_refresh = True

    @property
    def flow(self):
        return self._flow

    @flow.setter
    def flow(self, flow):
        if flow < 0:
            self._flow = 0.0
        else:
            self._flow = flow
        self._flow_refresh = True
        dial = int(math.floor(flow*2))
        if dial > 30:
            dial = 31
        if dial != self._dial:
            self._dial = dial
            self._dial_refresh = True

    def tick(self):
        timestamp = time.monotonic_ns()

        # if we've exceeded the mode/vol/temp refresh frequency, do a refresh
        if timestamp - self._t1 > self.MODE_VOL_TEMP_REFRESH_FREQ:
            self._t1 = timestamp
            if self._vol_refresh:
                flow_color = Gauge.COLOR_GREEN
                if self._mode == Gauge.COUNT_DOWN:
                    flow_color = Gauge.COLOR_RED
                Gauge._write_fg_color(self._uart, self._vol_id, flow_color)
                Gauge._write_text(self._uart, self._vol_id, self.FLOAT_FORMAT.format(self._vol))
                self._vol_refresh = False
            if self._temp_refresh:
                Gauge._write_text(self._uart, self._temp_id, self.TEMP_FORMAT.format(self._temp))
                self._temp_refresh = False    
        
        # if we've exceeded the dial/flow refresh frequency, do a refresh
        if timestamp - self._t2 > self.DIAL_FLOW_REFRESH_FREQ:
            self._t2 = timestamp
            if self._dial_refresh:
                # shenanigans required because the flow value overlaps the dial.
                Gauge._write_cmd(self._uart, "ref_stop")
                Gauge._write_dial(self._uart, self._dial_id, self._dial)
                Gauge._write_cmd(self._uart, "ref {}".format(self._flow_id), True)
                Gauge._write_cmd(self._uart, "ref_star", True)
                self._dial_refresh = False
            if self._flow_refresh:
                Gauge._write_text(self._uart, self._flow_id, self.FLOAT_FORMAT.format(self._flow))
                self._flow_refresh = False