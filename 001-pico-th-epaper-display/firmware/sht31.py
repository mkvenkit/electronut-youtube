"""Driver helpers for reading temperature and humidity from an SHT31 sensor."""

import time


class SHT31:
    """Minimal SHT31 driver with address detection and CRC validation."""
    DEFAULT_ADDRESS = 0x44
    VALID_ADDRESSES = (0x44, 0x45)
    MEASURE_HIGH_REPEATABILITY = b"\x24\x00"

    def __init__(self, i2c, address=None):
        """Create an SHT31 driver on the given I2C bus."""
        self.i2c = i2c
        self.address = address if address is not None else self.detect(i2c)

    @classmethod
    def detect(cls, i2c):
        """Find a supported SHT31 address on the I2C bus."""
        devices = i2c.scan()
        for address in cls.VALID_ADDRESSES:
            if address in devices:
                return address

        if devices:
            found = ", ".join("0x{:02X}".format(device) for device in devices)
            raise OSError("SHT31 not found, saw {}".format(found))

        raise OSError("SHT31 not found, I2C scan empty")

    def _crc8(self, data):
        """Calculate the CRC used by SHT3x measurement responses."""
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0x31) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc

    def read(self):
        """Read one temperature and humidity sample from the sensor."""
        self.i2c.writeto(self.address, self.MEASURE_HIGH_REPEATABILITY)
        time.sleep_ms(20)
        data = self.i2c.readfrom(self.address, 6)

        temp_raw = data[0:2]
        hum_raw = data[3:5]

        if self._crc8(temp_raw) != data[2]:
            raise OSError("SHT31 temperature CRC mismatch")
        if self._crc8(hum_raw) != data[5]:
            raise OSError("SHT31 humidity CRC mismatch")

        temperature = -45 + (175 * int.from_bytes(temp_raw, "big") / 65535)
        humidity = 100 * int.from_bytes(hum_raw, "big") / 65535
        return temperature, humidity
