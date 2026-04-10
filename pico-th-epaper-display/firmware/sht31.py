import time


class SHT31:
    DEFAULT_ADDRESS = 0x44
    MEASURE_HIGH_REPEATABILITY = b"\x24\x00"

    def __init__(self, i2c, address=DEFAULT_ADDRESS):
        self.i2c = i2c
        self.address = address

    def _crc8(self, data):
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
