"""Minimal SPI driver for a 200x200 Waveshare 1.54-inch e-paper display."""

from machine import Pin
import framebuf
import time


class EPD_1in54(framebuf.FrameBuffer):
    """Framebuffer-backed driver for the 1.54-inch monochrome e-paper panel."""
    WIDTH = 200
    HEIGHT = 200
    POWER_ON_DELAY_MS = 200
    RESET_LOW_MS = 10
    RESET_HIGH_MS = 200

    DRIVER_OUTPUT_CONTROL = 0x01
    BOOSTER_SOFT_START_CONTROL = 0x0C
    DEEP_SLEEP_MODE = 0x10
    DATA_ENTRY_MODE_SETTING = 0x11
    SW_RESET = 0x12
    MASTER_ACTIVATION = 0x20
    DISPLAY_UPDATE_CONTROL_2 = 0x22
    WRITE_RAM = 0x24
    WRITE_VCOM_REGISTER = 0x2C
    SET_DUMMY_LINE_PERIOD = 0x3A
    SET_GATE_TIME = 0x3B
    SET_RAM_X_ADDRESS_START_END_POSITION = 0x44
    SET_RAM_Y_ADDRESS_START_END_POSITION = 0x45
    SET_RAM_X_ADDRESS_COUNTER = 0x4E
    SET_RAM_Y_ADDRESS_COUNTER = 0x4F
    TERMINATE_FRAME_READ_WRITE = 0xFF

    def __init__(self, spi, cs, dc, rst, busy):
        """Create and initialize the e-paper display driver."""
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.busy = busy

        self.cs.init(Pin.OUT, value=1)
        self.dc.init(Pin.OUT, value=0)
        self.rst.init(Pin.OUT, value=1)
        self.busy.init(Pin.IN)

        self.buffer = bytearray(self.WIDTH * self.HEIGHT // 8)
        super().__init__(self.buffer, self.WIDTH, self.HEIGHT, framebuf.MONO_HLSB)

        self._delay_ms(self.POWER_ON_DELAY_MS)
        self._init_display()

    def _delay_ms(self, delay):
        """Pause briefly between controller operations."""
        time.sleep_ms(delay)

    def _send_command(self, command):
        """Send a single command byte to the display controller."""
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([command]))
        self.cs.value(1)

    def _send_data(self, data):
        """Send one or more data bytes to the display controller."""
        self.dc.value(1)
        self.cs.value(0)
        if isinstance(data, int):
            self.spi.write(bytearray([data]))
        else:
            self.spi.write(data)
        self.cs.value(1)

    def _wait_until_idle(self):
        """Block until the display controller reports it is idle."""
        while self.busy.value() == 1:
            self._delay_ms(10)

    def _hardware_reset(self):
        """Pulse the reset line to restart the display controller."""
        self.rst.value(1)
        self._delay_ms(self.RESET_HIGH_MS)
        self.rst.value(0)
        self._delay_ms(self.RESET_LOW_MS)
        self.rst.value(1)
        self._delay_ms(self.RESET_HIGH_MS)

    def _set_window(self, x_start, y_start, x_end, y_end):
        """Set the active RAM window on the display controller."""
        self._send_command(self.SET_RAM_X_ADDRESS_START_END_POSITION)
        self._send_data(x_start >> 3)
        self._send_data(x_end >> 3)

        self._send_command(self.SET_RAM_Y_ADDRESS_START_END_POSITION)
        self._send_data(y_start & 0xFF)
        self._send_data((y_start >> 8) & 0xFF)
        self._send_data(y_end & 0xFF)
        self._send_data((y_end >> 8) & 0xFF)

    def _set_cursor(self, x, y):
        """Move the controller RAM cursor to the given pixel position."""
        self._send_command(self.SET_RAM_X_ADDRESS_COUNTER)
        self._send_data(x >> 3)

        self._send_command(self.SET_RAM_Y_ADDRESS_COUNTER)
        self._send_data(y & 0xFF)
        self._send_data((y >> 8) & 0xFF)
        self._wait_until_idle()

    def _init_display(self):
        """Run the controller initialization sequence."""
        self._hardware_reset()
        self._wait_until_idle()

        self._send_command(self.SW_RESET)
        self._wait_until_idle()

        self._send_command(self.DRIVER_OUTPUT_CONTROL)
        self._send_data((self.HEIGHT - 1) & 0xFF)
        self._send_data(((self.HEIGHT - 1) >> 8) & 0xFF)
        self._send_data(0x00)

        self._send_command(self.BOOSTER_SOFT_START_CONTROL)
        self._send_data(0xD7)
        self._send_data(0xD6)
        self._send_data(0x9D)

        self._send_command(self.WRITE_VCOM_REGISTER)
        self._send_data(0xA8)

        self._send_command(self.SET_DUMMY_LINE_PERIOD)
        self._send_data(0x1A)

        self._send_command(self.SET_GATE_TIME)
        self._send_data(0x08)

        self._send_command(self.DATA_ENTRY_MODE_SETTING)
        self._send_data(0x03)

        self._set_window(0, 0, self.WIDTH - 1, self.HEIGHT - 1)
        self._set_cursor(0, 0)
        self.clear()

    def clear(self, color=0xFF):
        """Fill the local framebuffer with the requested color."""
        self.buffer[:] = bytes([color]) * len(self.buffer)

    def display(self):
        """Transfer the local framebuffer to the e-paper panel."""
        self._set_window(0, 0, self.WIDTH - 1, self.HEIGHT - 1)
        self._set_cursor(0, 0)

        self._send_command(self.WRITE_RAM)
        self._send_data(self.buffer)

        self._send_command(self.DISPLAY_UPDATE_CONTROL_2)
        self._send_data(0xF7)
        self._send_command(self.MASTER_ACTIVATION)
        self._send_command(self.TERMINATE_FRAME_READ_WRITE)
        self._wait_until_idle()

    def sleep(self):
        """Put the display controller into deep sleep mode."""
        self._send_command(self.DEEP_SLEEP_MODE)
        self._send_data(0x01)
        self._delay_ms(50)

    def wake(self):
        """Wake the display by re-running its initialization sequence."""
        self._init_display()
