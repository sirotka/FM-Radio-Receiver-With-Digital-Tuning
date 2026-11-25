from machine import Pin
import time


class Button:
    def init(self, pin_number):
        self.pin = Pin(pin_number, Pin.IN, Pin.PULL_UP)

        self._raw_value = self.pin.value()
        self._stable_value = self._raw_value
        self._last_change = time.ticks_ms()

    def is_pressed(self):
        return not self.pin.value()

    def is_released(self):
        return self.pin.value() == 1

    def was_pressed(self, debounce_ms=20):
        raw_value = self.pin.value()

        if raw_value != self._raw_value:
            self._raw_value = raw_value
            self._last_change = time.ticks_ms()

        elapsed = time.ticks_diff(
            time.ticks_ms(),
            self._last_change
        )

        if (
            elapsed >= debounce_ms
            and raw_value != self._stable_value
        ):
            self._stable_value = raw_value
            return raw_value == 0

        return False


class RotaryEncoder:
    def init(self, clk_pin=14, dt_pin=15, sw_pin=13):
        self.clk = Pin(clk_pin, Pin.IN, Pin.PULL_UP)
        self.dt = Pin(dt_pin, Pin.IN, Pin.PULL_UP)

        self.button = Button(sw_pin)

        self._delta = 0
        self._last_irq = time.ticks_ms()

        self.clk.irq(
            trigger=Pin.IRQ_FALLING,
            handler=self._encoder_handler
        )

    def _encoder_handler(self, pin):
        now = time.ticks_ms()

        if time.ticks_diff(now, self._last_irq) < 5:
            return

        self._last_irq = now

        if self.dt.value():
            self._delta += 1
        else:
            self._delta -= 1

    def get_delta(self):
        delta = self._delta
        self._delta = 0

        return delta

    def was_pressed(self, debounce_ms=20):
        return self.button.was_pressed(debounce_ms)

    def deinit(self):
        self.clk.irq(handler=None)


def main():
    encoder = RotaryEncoder(
        clk_pin=14,
        dt_pin=15,
        sw_pin=13
    )

    print("Encoder test")
    print("Rotate encoder or press SW")

    try:
        while True:
            delta = encoder.get_delta()

            if delta > 0:
                print("RIGHT", delta)

            elif delta < 0:
                print("LEFT", delta)

            if encoder.was_pressed():
                print("SW PRESSED")

            time.sleep_ms(1)

    except KeyboardInterrupt:
        encoder.deinit()
        print("\nTest stopped.")


if name == "main":
    main()