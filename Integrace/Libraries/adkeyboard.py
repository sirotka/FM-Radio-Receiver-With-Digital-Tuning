from machine import ADC
import time


class ADKeyboard:
    def __init__(self, adc_pin):
        self.adc = ADC(adc_pin)

        self._raw_key = None
        self._stable_key = None
        self._last_change = time.ticks_ms()

    def read_raw(self):
        return self.adc.read_u16()

    def read_key(self):
        value = self.read_raw()
        print(value)

        if value < 51000:
            return 1

        elif value < 53000:
            return 2

        elif value < 55000:
            return 3

        elif value < 58000:
            return 4

        elif value < 62000:
            return 5
        else:
            return 0


    def was_pressed(self, debounce_ms=20):
        key = self.read_key()
        return key



