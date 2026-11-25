from machine import ADC
import time


class ADKeyboard:
    def __init__(self, adc_pin=26):
        self.adc = ADC(adc_pin)

        self._raw_key = None
        self._stable_key = None
        self._last_change = time.ticks_ms()

    def read_raw(self):
        return self.adc.read_u16()

    def read_key(self):
        value = self.read_raw()

        if value < 8000:
            return "VOL+"

        if value < 13000:
            return "VOL-"

        if value < 18000:
            return "OK"

        if value < 24000:
            return "UP"

        if value < 30000:
            return "DOWN"

        return None

    def was_pressed(self, debounce_ms=20):
        key = self.read_key()

        if key != self._raw_key:
            self._raw_key = key
            self._last_change = time.ticks_ms()

        elapsed = time.ticks_diff(
            time.ticks_ms(),
            self._last_change
        )

        if (
            elapsed >= debounce_ms
            and key != self._stable_key
        ):
            self._stable_key = key

            if key is not None:
                return key

        return None