"""Standalone I2C scanner for checking devices on GP4/GP5."""

from machine import I2C, Pin
import time


def format_devices(devices):
    """Format scan results as a short human-readable string."""
    if not devices:
        return "No I2C devices found"

    return "Found: " + ", ".join("0x{:02X}".format(device) for device in devices)


def main():
    """Continuously scan the I2C bus and print any detected addresses."""
    i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)

    print("Scanning I2C bus on GP4/GP5...")
    while True:
        devices = i2c.scan()
        print(format_devices(devices))
        time.sleep(2)


main()
