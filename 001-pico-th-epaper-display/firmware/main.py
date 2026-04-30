"""Main application for showing SHT31 readings on a 1.54-inch e-paper display."""

from machine import I2C, Pin, SPI
import time
from epd_1in54 import EPD_1in54
from sht31 import SHT31

DONE_PIN = 28
LED_PIN = "LED"
STARTUP_DELAY_MS = 1000
HISTORY_FILE = "history.csv"
HISTORY_LENGTH = 16
MID_X = 100
MID_Y = 100
QUADRANT_SIZE = 100
SEGMENT_THICKNESS = 7
DIGIT_WIDTH = 30
DIGIT_HEIGHT = 56
DIGIT_SPACING = 6
GRAPH_PADDING = 6
GRAPH_LABEL_HEIGHT = 10

SEGMENTS = {
    "-": "g",
    "0": "abcfed",
    "1": "bc",
    "2": "abged",
    "3": "abgcd",
    "4": "fgbc",
    "5": "afgcd",
    "6": "afgecd",
    "7": "abc",
    "8": "abcdefg",
    "9": "abcfgd",
}


def load_history():
    """Load temperature and humidity history from local storage."""
    readings = []
    try:
        with open(HISTORY_FILE, "r") as history_file:
            for line in history_file:
                parts = line.strip().split(",")
                if len(parts) != 2:
                    continue
                try:
                    readings.append((float(parts[0]), float(parts[1])))
                except ValueError:
                    continue
    except OSError:
        return []

    if len(readings) > HISTORY_LENGTH:
        return readings[-HISTORY_LENGTH:]
    return readings


def save_history(readings):
    """Persist the latest readings so the next wake can draw trend lines."""
    trimmed = readings[-HISTORY_LENGTH:]
    with open(HISTORY_FILE, "w") as history_file:
        for temperature, humidity in trimmed:
            history_file.write("{:.2f},{:.2f}\n".format(temperature, humidity))


def append_history(temperature, humidity):
    """Append the latest sample to the stored reading history."""
    readings = load_history()
    readings.append((temperature, humidity))
    save_history(readings)
    return readings[-HISTORY_LENGTH:]


def draw_grid(epd):
    """Draw the 2x2 quadrant layout."""
    epd.rect(0, 0, epd.WIDTH, epd.HEIGHT, 0x00)
    epd.vline(MID_X, 0, epd.HEIGHT, 0x00)
    epd.hline(0, MID_Y, epd.WIDTH, 0x00)


def draw_segment(epd, x, y, segment, color=0x00):
    """Draw one seven-segment bar for a large numeric glyph."""
    if segment == "a":
        epd.fill_rect(x + SEGMENT_THICKNESS, y, DIGIT_WIDTH - (2 * SEGMENT_THICKNESS), SEGMENT_THICKNESS, color)
    elif segment == "b":
        epd.fill_rect(x + DIGIT_WIDTH - SEGMENT_THICKNESS, y + SEGMENT_THICKNESS, SEGMENT_THICKNESS, (DIGIT_HEIGHT // 2) - SEGMENT_THICKNESS, color)
    elif segment == "c":
        epd.fill_rect(x + DIGIT_WIDTH - SEGMENT_THICKNESS, y + (DIGIT_HEIGHT // 2), SEGMENT_THICKNESS, (DIGIT_HEIGHT // 2) - SEGMENT_THICKNESS, color)
    elif segment == "d":
        epd.fill_rect(x + SEGMENT_THICKNESS, y + DIGIT_HEIGHT - SEGMENT_THICKNESS, DIGIT_WIDTH - (2 * SEGMENT_THICKNESS), SEGMENT_THICKNESS, color)
    elif segment == "e":
        epd.fill_rect(x, y + (DIGIT_HEIGHT // 2), SEGMENT_THICKNESS, (DIGIT_HEIGHT // 2) - SEGMENT_THICKNESS, color)
    elif segment == "f":
        epd.fill_rect(x, y + SEGMENT_THICKNESS, SEGMENT_THICKNESS, (DIGIT_HEIGHT // 2) - SEGMENT_THICKNESS, color)
    elif segment == "g":
        epd.fill_rect(x + SEGMENT_THICKNESS, y + (DIGIT_HEIGHT // 2) - (SEGMENT_THICKNESS // 2), DIGIT_WIDTH - (2 * SEGMENT_THICKNESS), SEGMENT_THICKNESS, color)


def draw_big_value(epd, x, y, value, label, unit):
    """Draw a large rounded reading with a compact quadrant label."""
    text = str(int(round(value)))
    total_width = (len(text) * DIGIT_WIDTH) + ((len(text) - 1) * DIGIT_SPACING)
    digit_x = x + max(6, (QUADRANT_SIZE - total_width) // 2)

    epd.text(label, x + 6, y + 6, 0x00)
    for character in text:
        for segment in SEGMENTS.get(character, ""):
            draw_segment(epd, digit_x, y + 24, segment)
        digit_x += DIGIT_WIDTH + DIGIT_SPACING


def draw_graph(epd, x, y, values, label, unit):
    """Draw a sparkline-style graph within a quadrant."""
    graph_x = x + GRAPH_PADDING
    graph_y = y + GRAPH_LABEL_HEIGHT + 6
    graph_w = QUADRANT_SIZE - (2 * GRAPH_PADDING)
    graph_h = QUADRANT_SIZE - (graph_y - y) - GRAPH_PADDING

    epd.text(label, x + 6, y + 6, 0x00)
    if not values:
        epd.text("No data", x + 20, y + 46, 0x00)
        return

    if len(values) == 1:
        mid_y = graph_y + (graph_h // 2)
        epd.hline(graph_x, mid_y, graph_w, 0x00)
        return

    min_value = min(values)
    max_value = max(values)
    span = max_value - min_value
    if span < 0.5:
        min_value -= 0.25
        max_value += 0.25
        span = max_value - min_value

    last_x = graph_x
    last_y = graph_y + graph_h - 1 - int(((values[0] - min_value) * (graph_h - 2)) / span)
    for index in range(1, len(values)):
        next_x = graph_x + int((index * (graph_w - 1)) / (len(values) - 1))
        next_y = graph_y + graph_h - 1 - int(((values[index] - min_value) * (graph_h - 2)) / span)
        epd.line(last_x, last_y, next_x, next_y, 0x00)
        last_x = next_x
        last_y = next_y


def split_history(readings):
    """Split combined reading tuples into per-signal history arrays."""
    temperatures = []
    humidities = []
    for temperature, humidity in readings:
        temperatures.append(temperature)
        humidities.append(humidity)
    return temperatures, humidities


def draw_reading(epd, temperature, humidity, history):
    """Render the quadrant-based temperature and humidity dashboard."""
    epd.clear(0xFF)
    temperatures, humidities = split_history(history)
    draw_grid(epd)
    draw_big_value(epd, 0, 0, temperature, "T(C)", "C")
    draw_graph(epd, MID_X, 0, temperatures, "T", "C")
    draw_graph(epd, 0, MID_Y, humidities, "H", "%")
    draw_big_value(epd, MID_X, MID_Y, humidity, "H(%)", "%")
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


def refresh_display(epd, led, render, *args):
    """Turn on the LED during a display refresh, then turn it off afterward."""
    # Temporary debug indicator: comment out these LED lines later if you do not need them.
    #led.value(1)
    render(epd, *args)
    #led.value(0)


def startup_wait(led, delay_ms):
    """Pause after power-up so peripherals can settle before initialization."""
    # Temporary debug indicator: comment out this LED blink later if you do not need it.
    end_time = time.ticks_add(time.ticks_ms(), delay_ms)
    led_state = 0
    while time.ticks_diff(end_time, time.ticks_ms()) > 0:
        led_state = 0 if led_state else 1
        led.value(led_state)
        time.sleep_ms(150)
    led.value(0)


def main():
    """Initialize peripherals, update the display, and notify the TPL5110."""
    i2c = I2C(0, scl=Pin(21), sda=Pin(20), freq=100000)
    sensor = None
    done_pin = Pin(DONE_PIN, Pin.OUT, value=0)
    led = Pin(LED_PIN, Pin.OUT, value=0)

    startup_wait(led, STARTUP_DELAY_MS)

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
        history = append_history(temperature, humidity)
        refresh_display(epd, led, draw_reading, temperature, humidity, history)
    except Exception as exc:
        scan = i2c.scan()
        detail = "I2C: none"
        if scan:
            detail = "I2C: {}".format(",".join("0x{:02X}".format(addr) for addr in scan[:3]))
        print("SHT31 error:", exc)
        print("I2C scan:", [hex(addr) for addr in scan])
        refresh_display(epd, led, draw_error, str(exc), detail)

    epd.sleep()
    signal_done(done_pin)
    while True:
        time.sleep(1)


main()
