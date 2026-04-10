from machine import I2C, Pin, SPI
import time
from epd_1in54 import EPD_1in54
from sht31 import SHT31


def draw_reading(epd, temperature, humidity, status="OK"):
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


def draw_error(epd, message):
    epd.clear(0xFF)
    epd.fill_rect(0, 0, epd.WIDTH, 28, 0x00)
    epd.text("Pico TH Monitor", 36, 10, 0xFF)
    epd.text("Sensor read failed", 12, 64, 0x00)
    epd.text(message[:24], 12, 86, 0x00)
    epd.text("Retrying in 15 sec", 12, 130, 0x00)
    epd.display()


def main():
    i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
    sensor = SHT31(i2c)

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

    while True:
        try:
            temperature, humidity = sensor.read()
            draw_reading(epd, temperature, humidity)
        except Exception as exc:
            draw_error(epd, str(exc))
        time.sleep(15)


main()
