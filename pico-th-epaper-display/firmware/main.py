"""Main application for showing SHT31 readings on a 1.54-inch e-paper display."""

from machine import I2C, Pin, SPI
import time
from epd_1in54 import EPD_1in54
from sht31 import SHT31

DONE_PIN = 15


def draw_reading(epd, temperature, humidity, status="OK"):
    """Render the normal temperature and humidity view."""
    epd.clear(0xFF)

    epd.fill_rect(0, 0, epd.WIDTH, 28, 0x00)
    epd.text("Pico TH Monitor", 36, 10, 0xFF)

    epd.text("Temperature", 12, 48, 0x00)
    epd.text("{:.1f} C".format(temperature), 24, 66, 0x00)

    epd.text("Humidity", 12, 108, 0x00)
    epd.text("{:.1f} %RH".format(humidity), 24, 126, 0x00)

    epd.hline(12, 160, 176, 0x00)
    epd.text("Updated", 12, 172, 0x00)
    epd.text(status, 92, 172, 0x00)

    epd.display()


def draw_error(epd, message, detail=""):
    """Render an error screen with optional I2C scan details."""
    epd.clear(0xFF)
    epd.fill_rect(0, 0, epd.WIDTH, 28, 0x00)
    epd.text("Pico TH Monitor", 36, 10, 0xFF)
    epd.text("Sensor read failed", 12, 64, 0x00)
    epd.text(message[:24], 12, 86, 0x00)
    if detail:
        epd.text(detail[:24], 12, 108, 0x00)
    epd.text("Retrying in 15 sec", 12, 130, 0x00)
    epd.display()


def signal_done(done_pin):
    """Pulse the TPL5110 DONE pin high to request power-off."""
    done_pin.value(1)
    time.sleep_ms(150)
    done_pin.value(0)


def main():
    """Initialize peripherals, update the display, and notify the TPL5110."""
    i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
    sensor = None
    done_pin = Pin(DONE_PIN, Pin.OUT, value=0)

    spi = SPI(
        1,
        baudrate=2_000_000,
        polarity=0,
        phase=0,
        sck=Pin(10),
        mosi=Pin(11),
        miso=None,
    )

    epd = EPD_1in54(
        spi=spi,
        cs=Pin(9),
        dc=Pin(8),
        rst=Pin(12),
        busy=Pin(13),
    )

    try:
        if sensor is None:
            sensor = SHT31(i2c)
        temperature, humidity = sensor.read()
        draw_reading(epd, temperature, humidity)
    except Exception as exc:
        scan = i2c.scan()
        detail = "I2C: none"
        if scan:
            detail = "I2C: {}".format(",".join("0x{:02X}".format(addr) for addr in scan[:3]))
        print("SHT31 error:", exc)
        print("I2C scan:", [hex(addr) for addr in scan])
        draw_error(epd, str(exc), detail)

    epd.sleep()
    signal_done(done_pin)
    while True:
        time.sleep(1)


main()
