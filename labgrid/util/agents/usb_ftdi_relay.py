"""
This module implements the communication protocol to switch the digital outputs
on a FT232 reprogramed for direct pin access. (TODO)

Supported Functionality:

- Turn digital output on and off
"""

import errno
from contextlib import contextmanager
from time import monotonic, sleep

import pyftdi.gpio
import usb.core
import usb.util

GET_REPORT = 0x1
SET_REPORT = 0x9
REPORT_TYPE_FEATURE = 3


class USBFTDIRelay:
    def __init__(self, **args):
        self._bus, self._address = args["bus"], args["address"]
        self._gpio = pyftdi.gpio.GpioAsyncController()

    @contextmanager
    def _claimed(self):
        timeout = monotonic() + 1.0
        while True:
            self._gpio.configure(f"ftdi://::{self._bus:x}:{self._address:x}/1", 0xff)
            try:
                usb.util.claim_interface(self._gpio.ftdi._usb_dev, 0)
                break
            except usb.core.USBError as e:
                if monotonic() > timeout:
                    self._gpio.close(freeze=True)
                    raise e
                if e.errno == errno.EBUSY:
                    sleep(0.01)
                else:
                    self._gpio.close(freeze=True)
                    raise e
        yield
        usb.util.release_interface(self._gpio.ftdi._usb_dev, 0)
        self._gpio.close(freeze=True)

    def _set_output_ftdi(self, number, status):
        assert 1 <= number <= 8
        state = self._gpio.read_port()
        mask = 1 << (number - 1)
        if status:
            state |= mask
        else:
            state &= 256+(~mask)
        state = self._gpio.write(state)

    def _get_output_ftdi(self, number):
        assert 1 <= number <= 8
        resp = self._gpio.read_port()
        return bool(resp & (1 << (number - 1)))

    def set_output(self, number, status):
        with self._claimed():
            self._set_output_ftdi(number, status)

    def get_output(self, number):
        with self._claimed():
            return self._get_output_ftdi(number)


_relays = {}


def _get_relay(busnum, devnum):
    if (busnum, devnum) not in _relays:
        _relays[(busnum, devnum)] = USBFTDIRelay(bus=busnum, address=devnum)
    return _relays[(busnum, devnum)]


def handle_set(busnum, devnum, number, status):
    relay = _get_relay(busnum, devnum)
    relay.set_output(number, status)


def handle_get(busnum, devnum, number):
    relay = _get_relay(busnum, devnum)
    return relay.get_output(number)


methods = {
    "set": handle_set,
    "get": handle_get,
}
