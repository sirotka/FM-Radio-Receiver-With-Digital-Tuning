from machine import Pin
import time
import framebuf


class Nokia5110:
    def __init__(self, spi, cs, dc, rst, rotate_180=False):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.rotate_180 = rotate_180

        self.buffer = bytearray(84 * 48 // 8)
        self.framebuf = framebuf.FrameBuffer(
            self.buffer,
            84,
            48,
            framebuf.MONO_VLSB
        )

        self.cs.init(Pin.OUT, value=1)
        self.dc.init(Pin.OUT, value=0)
        self.rst.init(Pin.OUT, value=1)

        self.rst.value(0)
        time.sleep_ms(20)
        self.rst.value(1)
        time.sleep_ms(20)

        self.write_cmd(0x21)
        self.write_cmd(0xB8)
        self.write_cmd(0x04)
        self.write_cmd(0x14)
        self.write_cmd(0x20)
        self.write_cmd(0x0C)

    def write_cmd(self, cmd):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([cmd]))
        self.cs.value(1)

    def write_data(self, data):
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(data)
        self.cs.value(1)

    def show(self):
        self.write_cmd(0x40)
        self.write_cmd(0x80)

        if not self.rotate_180:
            self.write_data(self.buffer)
            return

        rotated = bytearray(84 * 48 // 8)

        for x in range(84):
            for y in range(48):
                if self.framebuf.pixel(x, y):
                    index = ((47 - y) // 8) * 84 + (83 - x)
                    rotated[index] |= 1 << ((47 - y) % 8)

        self.write_data(rotated)

    def fill(self, col):
        self.framebuf.fill(col)

    def text(self, string, x, y, col=1):
        self.framebuf.text(string, x, y, col)

    def pixel(self, x, y, col):
        self.framebuf.pixel(x, y, col)

    def line(self, x1, y1, x2, y2, col):
        self.framebuf.line(x1, y1, x2, y2, col)

    def rect(self, x, y, w, h, col):
        self.framebuf.rect(x, y, w, h, col)

    def fill_rect(self, x, y, w, h, col):
        self.framebuf.fill_rect(x, y, w, h, col)


def draw_bar(lcd, x, y, width, value, maximum):
    if width < 3:
        raise ValueError("Bar width must be at least 3 pixels")

    if maximum <= 0:
        raise ValueError("Maximum must be greater than zero")

    value = max(0, min(value, maximum))

    inner_width = width - 2
    filled_width = int(inner_width * value / maximum)

    lcd.rect(x, y, width, 8, 1)
    lcd.fill_rect(x + 1, y + 1, inner_width, 6, 0)

    if filled_width > 0:
        lcd.fill_rect(
            x + 1,
            y + 1,
            filled_width,
            6,
            1
        )


def draw_radio_screen(
    lcd,
    freq,
    station,
    volume,
    si4703_ok=True,
    muted=False
):
    lcd.fill(0)

    status = "FM: ON" if si4703_ok else "FM: OFF"
    lcd.text(status, 0, 0, 1)

    lcd.text("Freq:", 0, 10, 1)
    lcd.text("{:.1f}".format(freq), 42, 10, 1)

    lcd.fill_rect(0, 21, 84, 9, 1)
    lcd.text(station[:10], 2, 22, 0)

    if muted:
        lcd.text("MUTE", 0, 32, 1)
    else:
        lcd.text("Vol:{}".format(volume), 0, 32, 1)
        draw_bar(
            lcd,
            49,
            31,
            34,
            volume,
            15
        )

    lcd.show()

