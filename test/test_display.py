from machine import SPI, Pin, I2C
import time
import framebuf

class Nokia5110:
    """
    Driver class for Nokia 5110 graphic LCD (PCD8544 controller).
    Handles SPI communication, buffer management, and hardware reset.
    """
    def __init__(self, spi, cs, dc, rst):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.buffer = bytearray(84 * 48 // 8)
        self.framebuf = framebuf.FrameBuffer(self.buffer, 84, 48, framebuf.MONO_VLSB)
        
        self.cs.init(Pin.OUT, value=1)
        self.dc.init(Pin.OUT, value=0)
        self.rst.init(Pin.OUT, value=1)
        
        # Hardware reset sequence
        self.rst.value(0)
        time.sleep_ms(20)
        self.rst.value(1)
        time.sleep_ms(20)
        
        # PCD8544 proper initialization with correct contrast (0xB8)
        self.write_cmd(0x21)  # Extended instruction set
        self.write_cmd(0xB8)  # Set Contrast (CONTRAST = 0xB8)
        self.write_cmd(0x04)  # Temperature coefficient
        self.write_cmd(0x14)  # Bias system
        self.write_cmd(0x20)  # Basic instruction set
        self.write_cmd(0x0C)  # Normal display mode

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
        # Rotate framebuffer 180 degrees to match physical mounting
        rotated = bytearray(84 * 48 // 8)
        for x in range(84):
            for y in range(48):
                if self.framebuf.pixel(x, y):
                    index = ((47 - y) // 8) * 84 + (83 - x)
                    rotated[index] |= 1 << ((47 - y) % 8)

        self.write_cmd(0x40)
        self.write_cmd(0x80)
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
    """Draws a horizontal progress bar (e.g., for volume level)."""
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
        lcd.fill_rect(x + 1, y + 1, filled_width, 6, 1)

def draw_radio_screen(lcd, freq, station, volume, si4703_ok):
    """Renders the radio user interface elements onto the display buffer."""
    status = "FM: OK" if si4703_ok else "FM: OFF"
    lcd.text(status, 0, 0, 1)
    
    lcd.text("Freq:", 0, 10, 1)
    lcd.text(f"{freq:.1f}", 42, 10, 1)
    
    lcd.fill_rect(0, 21, 84, 9, 1)
    lcd.text(f"{station}", 2, 22, 0)
    
    lcd.text(f"Vol:{volume:1d}", 0, 32, 1)
    draw_bar(lcd, 49, 31, 34, volume, 15)

def main():
    # Initialize SPI0 for Nokia 5110 display (1 MHz baudrate for physical stability)
    spi = SPI(0, baudrate=1_000_000, polarity=0, phase=0,
              sck=Pin(18), mosi=Pin(19))
    cs = Pin(17, Pin.OUT)
    dc = Pin(16, Pin.OUT)  # MISO pin used for Data/Command
    rst = Pin(20, Pin.OUT) # Digital pin for hardware reset
    
    lcd = Nokia5110(spi, cs, dc, rst)
    
    # Check connection with Si4703 FM tuner on I2C0
    si4703_connected = False
    try:
        i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)
        devices = i2c.scan()
        if 0x10 in devices:
            si4703_connected = True
            print("Si4703 FM tuner detected on I2C0!")
    except Exception as e:
        print(f"I2C error: {e}")

    print("Nokia 5110 Display Test Started")
    print("-----------------------------")

    # ==========================================
    # GRAPHICAL TEST SEQUENCE (Console logs status)
    # ==========================================
    
    # Test 1: Clear screen
    print("Test 1: Clear screen")
    lcd.fill(0)
    lcd.show()
    time.sleep(2.0)
    
    # Test 2: Full screen fill
    print("Test 2: Full screen fill")
    lcd.fill(1)
    lcd.show()
    time.sleep(1.5)
    lcd.fill(0)
    lcd.show()
    time.sleep(0.5)

    # Test 3: Dots pattern test
    print("Test 3: Dots pattern")
    lcd.fill(0)
    for x in range(0, 84, 4):
        for y in range(0, 48, 4):
            lcd.pixel(x, y, 1)
    lcd.show()
    time.sleep(2.0)

    # Test 4: Horizontal stripes test
    print("Test 4: Horizontal stripes")
    lcd.fill(0)
    for y in range(0, 48, 4):
        lcd.fill_rect(0, y, 84, 2, 1)
    lcd.show()
    time.sleep(2.0)

    # Test 5: Vertical stripes test
    print("Test 5: Vertical stripes")
    lcd.fill(0)
    for x in range(0, 84, 4):
        lcd.fill_rect(x, 0, 2, 48, 1)
    lcd.show()
    time.sleep(2.0)

    # Test 6: Grid / Cross lines test
    print("Test 6: Grid and cross lines")
    lcd.fill(0)
    for y in range(0, 48, 8):
        lcd.line(0, y, 83, y, 1)
    for x in range(0, 84, 12):
        lcd.line(x, 0, x, 47, 1)
    lcd.show()
    time.sleep(2.0)

    # Test 7: Three nested rectangles with diagonal cross
    print("Test 7: Nested rectangles with diagonal cross")
    lcd.fill(0)
    lcd.rect(0, 0, 84, 48, 1)
    lcd.line(0, 0, 83, 47, 1)
    lcd.line(83, 0, 0, 47, 1)
    lcd.rect(6, 6, 72, 36, 1)
    lcd.rect(12, 12, 60, 24, 1)
    lcd.show()
    time.sleep(2.5)
    
    print("DISPLAY TEST PASSED!")
    print("-----------------------------")
    # ==========================================

    test_freq = 105.5
    test_vol = 3
    test_station = "EVROPA 2"

    try:
        while True:
            lcd.fill(0)
            draw_radio_screen(lcd, test_freq, test_station, test_vol, si4703_connected)
            lcd.show()
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nProgram stopped. Exiting...")
        lcd.fill(0)
        lcd.show()

if __name__ == "__main__":
    main()