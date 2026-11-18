# SI4703 MicroPython Library
# Přepsáno pro MicroPython (machine.I2C a machine.Pin)

import time
from machine import Pin

class si4703Radio:

    # Registry
    SI4703_DEVICEID = 0x00
    SI4703_CHIPID = 0x01
    SI4703_POWERCFG = 0x02
    SI4703_CHANNEL = 0x03
    SI4703_SYSCONFIG1 = 0x04
    SI4703_SYSCONFIG2 = 0x05
    SI4703_SYSCONFIG3 = 0x06
    SI4703_TEST1 = 0x07
    SI4703_TEST2 = 0x08
    SI4703_BOOTCONFIG = 0x09
    SI4703_STATUSRSSI = 0x0A
    SI4703_READCHAN = 0x0B
    SI4703_RDSA = 0x0C
    SI4703_RDSB = 0x0D
    SI4703_RDSC = 0x0E
    SI4703_RDSD = 0x0F

    # Bitové masky a pozice (POWERCFG)
    SI4703_SMUTE = 15
    SI4703_DMUTE = 14
    SI4703_SKMODE = 10
    SI4703_SEEKUP = 9
    SI4703_SEEK = 8
    SI4703_ENABLE = 0

    # CHANNEL
    SI4703_TUNE = 15

    # SYSCONFIG1
    SI4703_RDSIEN = 15
    SI4703_STCIEN = 14
    SI4703_RDS = 12
    SI4703_DE = 11
    SI4703_BLNDADJ = 6
    SI4703_GPIO3 = 4
    SI4703_GPIO2 = 2
    SI4703_GPIO1 = 0

    # SYSCONFIG2
    SI4703_SEEKTH = 8
    SI4703_SPACE1 = 5
    SI4703_SPACE0 = 4
    SI4703_VOLUME_MASK = 0x000F

    # SYSCONFIG3
    SI4703_SKSNR = 4
    SI4703_SKCNT = 0

    # TEST1
    SI4703_AHIZEN = 14
    SI4703_XOSCEN = 15

    # STATUSRSSI
    SI4703_RDSR = 15
    SI4703_STC = 14
    SI4703_SFBL = 13
    SI4703_AFCRL = 12
    SI4703_RDSS = 11
    SI4703_STEREO = 8

    # READCHAN
    SI4703_READCHAN_MASK = 0x03FF

    # RDS Constants
    SI4703_GROUPTYPE_OFFST = 11
    SI4703_TYPE0_INDEX_MASK = 0x0003
    SI4703_TYPE2_INDEX_MASK = 0x000F

    SI4703_SEEK_DOWN = 0
    SI4703_SEEK_UP = 1

    def __init__(self, i2c_id, sda_pin, scl_pin, i2c_addr=0x10, reset_pin=15, irq_pin=None):
        self.i2c_id = i2c_id
        self.sda_pin_num = sda_pin
        self.scl_pin_num = scl_pin
        self.i2c_addr = i2c_addr
        self.i2c = None
        
        self.reset_pin = Pin(reset_pin, Pin.OUT) if reset_pin is not None else None
        self.irq_pin = Pin(irq_pin, Pin.IN, Pin.PULL_UP) if irq_pin is not None else None

        self.si4703_registers = [0] * 16
        self.si4703_rds_ps = [''] * 8
        self.si4703_rds_rt = [''] * 64

    def si4703Init(self):
        from machine import I2C
        
        # 1. Nastavení stavů pro 2-wire (I2C) režim před resetem: SDA=0, SCL=1
        sda_temp = Pin(self.sda_pin_num, Pin.OUT, value=0)
        scl_temp = Pin(self.scl_pin_num, Pin.OUT, value=1)
        time.sleep_ms(10)

        # 2. Hardwarový reset čipu
        if self.reset_pin:
            self.reset_pin.value(0)
            time.sleep_ms(100)
            self.reset_pin.value(1)
            time.sleep_ms(100)

        # 3. Uvolnění pinů před předáním hardwarové I2C periferii
        Pin(self.sda_pin_num, Pin.IN, Pin.PULL_UP)
        Pin(self.scl_pin_num, Pin.IN, Pin.PULL_UP)
        time.sleep_ms(10)

        # 4. Spuštění I2C na standardních 100 kHz (100000)
        self.i2c = I2C(self.i2c_id, sda=Pin(self.sda_pin_num), scl=Pin(self.scl_pin_num), freq=100000)
        time.sleep_ms(50)

        # 2. PŮVODNÍ ZBYTEK FUNKCE (zůstává beze změny):
        self.si4703ReadRegisters()
        self.si4703_registers[self.SI4703_TEST1] = 0x8100  # Zapnutí oscilátoru
        self.si4703WriteRegisters()
        time.sleep_ms(500)

        self.si4703ReadRegisters()
        self.si4703_registers[self.SI4703_POWERCFG] = 0x4001  # Zapnutí čipu

        self.si4703_registers[self.SI4703_SYSCONFIG1] |= (1 << self.SI4703_RDS)  # Zapnutí RDS
        self.si4703_registers[self.SI4703_SYSCONFIG1] |= (1 << self.SI4703_DE)   # 50us De-emphasis (Evropa)
        self.si4703_registers[self.SI4703_SYSCONFIG1] |= (1 << self.SI4703_GPIO2)
        
        if self.irq_pin:
            self.si4703_registers[self.SI4703_SYSCONFIG1] |= (1 << self.SI4703_STCIEN)

        self.si4703_registers[self.SI4703_SYSCONFIG2] |= (0x19 << self.SI4703_SEEKTH)
        self.si4703_registers[self.SI4703_SYSCONFIG2] |= (1 << self.SI4703_SPACE0)  # 100 kHz krok (Evropa)
        self.si4703_registers[self.SI4703_SYSCONFIG2] &= 0xFFF0
        self.si4703_registers[self.SI4703_SYSCONFIG2] |= 0x0001  # Minimální hlasitost

        self.si4703_registers[self.SI4703_SYSCONFIG3] |= (0x04 << self.SI4703_SKSNR)
        self.si4703_registers[self.SI4703_SYSCONFIG3] |= (0x08 << self.SI4703_SKCNT)

        self.si4703WriteRegisters()
        time.sleep_ms(110)

    def si4703SeekUp(self):
        self.si4703Seek(self.SI4703_SEEK_UP)

    def si4703SeekDown(self):
        self.si4703Seek(self.SI4703_SEEK_DOWN)

    def si4703Seek(self, seek_direction):
        self.si4703ReadRegisters()
        self.si4703_registers[self.SI4703_POWERCFG] |= (1 << self.SI4703_SKMODE)
        
        if seek_direction == self.SI4703_SEEK_DOWN:
            self.si4703_registers[self.SI4703_POWERCFG] &= ~(1 << self.SI4703_SEEK)
        else:
            self.si4703_registers[self.SI4703_POWERCFG] |= (1 << self.SI4703_SEEK)
            
        self.si4703_registers[self.SI4703_POWERCFG] |= (1 << self.SI4703_SEEK)
        self.si4703WriteRegisters()

        start_time = time.ticks_ms()
        while True:
            self.si4703ReadRegisters()
            if (self.si4703_registers[self.SI4703_STATUSRSSI] & (1 << self.SI4703_STC)) != 0:
                break
            if time.ticks_diff(time.ticks_ms(), start_time) > 5000:
                break
            time.sleep_ms(20)

        self.si4703ReadRegisters()
        self.si4703_registers[self.SI4703_POWERCFG] &= ~(1 << self.SI4703_SEEK)
        self.si4703WriteRegisters()

    def si4703SetChannel(self, channel):
        new_channel = int((channel * 10 - 8750) / 10)

        self.si4703ReadRegisters()
        self.si4703_registers[self.SI4703_CHANNEL] &= 0xFE00
        self.si4703_registers[self.SI4703_CHANNEL] |= new_channel
        self.si4703_registers[self.SI4703_CHANNEL] |= (1 << self.SI4703_TUNE)
        self.si4703WriteRegisters()

        start_time = time.ticks_ms()
        while True:
            self.si4703ReadRegisters()
            if (self.si4703_registers[self.SI4703_STATUSRSSI] & (1 << self.SI4703_STC)) != 0:
                break
            if time.ticks_diff(time.ticks_ms(), start_time) > 5000:
                break
            time.sleep_ms(20)

        self.si4703ReadRegisters()
        self.si4703_registers[self.SI4703_CHANNEL] &= ~(1 << self.SI4703_TUNE)
        self.si4703WriteRegisters()

    def si4703SetVolume(self, volume):
        self.si4703ReadRegisters()
        volume = max(0, min(15, volume))
        self.si4703_registers[self.SI4703_SYSCONFIG2] &= 0xFFF0
        self.si4703_registers[self.SI4703_SYSCONFIG2] |= volume
        self.si4703WriteRegisters()

    def si4703GetVolume(self):
        self.si4703ReadRegisters()
        return self.si4703_registers[self.SI4703_SYSCONFIG2] & self.SI4703_VOLUME_MASK

    def si4703GetChannel(self):
        self.si4703ReadRegisters()
        return (self.si4703_registers[self.SI4703_READCHAN] & self.SI4703_READCHAN_MASK) + 875

    def si4703ShutDown(self):
        self.si4703ReadRegisters()
        self.si4703_registers[self.SI4703_TEST1] = 0x7C04
        self.si4703_registers[self.SI4703_POWERCFG] = 0x002A
        self.si4703_registers[self.SI4703_SYSCONFIG1] = 0x0041
        self.si4703WriteRegisters()

    def si4703WriteRegisters(self):
        # Si4703 zapisuje registry od 0x02 do 0x07 (6 16-bitových slov = 12 bajtů)
        buf = bytearray(12)
        for i in range(6):
            val = self.si4703_registers[i + 2]
            buf[i * 2] = (val >> 8) & 0xFF
            buf[i * 2 + 1] = val & 0xFF
        self.i2c.writeto(self.i2c_addr, buf)

    def si4703ReadRegisters(self):
        # Si4703 čte 32 bajtů (od 0x0A do 0x0F, potom přeteče na 0x00 až 0x09)
        data = self.i2c.readfrom(self.i2c_addr, 32)
        reg_index = 0x0A
        for i in range(16):
            self.si4703_registers[reg_index] = (data[i * 2] << 8) | data[i * 2 + 1]
            reg_index += 1
            if reg_index == 0x10:
                reg_index = 0

