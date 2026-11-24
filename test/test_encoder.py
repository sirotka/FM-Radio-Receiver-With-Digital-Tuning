from encoder import RotaryEncoder
from adkeyboard import ADKeyboard
from si4703Library import si4703Radio
import time


def main():

    encoder = RotaryEncoder(
        clk_pin=14,
        dt_pin=15,
        sw_pin=13
    )

    keyboard = ADKeyboard(
        adc_pin=26
    )

    radio = si4703Radio(
        0,
        sda_pin=4,
        scl_pin=5,
        i2c_addr=0x10,
        reset_pin=6,
        irq_pin=None,
        simulation=False
    )


    print("test")
  

    try:
        radio.si4703Init()

        if radio.isConnected():
            print("Si4703: OK")
        else:
            print("Si4703: NOT FOUND")

    except Exception as error:
        print("Si4703 error:", error)


    print()
    print("Turn encoder or press buttons.")
    print("Ctrl+C to stop.")
    print()


    try:
        while True:

            delta = encoder.get_delta()

            if delta > 0:
                print("Encoder: RIGHT")

            elif delta < 0:
                print("Encoder: LEFT")


            if encoder.was_pressed():
                print("Encoder SW: PRESSED")

            key = keyboard.was_pressed()

            if key is not None:
                print(
                    "ADKeyboard:",
                    key,
                    "ADC:",
                    keyboard.read_raw()
                )


            time.sleep_ms(1)


    except KeyboardInterrupt:

        encoder.deinit()

        print()
        print("Test stopped.")


if __name__ == "__main__":
    main()
