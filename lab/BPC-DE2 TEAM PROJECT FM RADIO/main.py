from machine import SPI, Pin
import time

from encoder import RotaryEncoder
from adkeyboard import ADKeyboard
from nokia5110 import Nokia5110, draw_radio_screen
from Si4703Library import si4703Radio


# Display
spi = SPI(
    0,
    baudrate=1_000_000,
    polarity=0,
    phase=0,
    sck=Pin(18),
    mosi=Pin(19)
)

lcd = Nokia5110(
    spi,
    Pin(17, Pin.OUT),
    Pin(16, Pin.OUT),
    Pin(20, Pin.OUT),
    rotate_180=False
)


# Encoder
encoder = RotaryEncoder(
    clk_pin=14,
    dt_pin=15,
    sw_pin=13
)


# ADKeyboard
keyboard = ADKeyboard(
    adc_pin=26
)


# Si4703
radio = si4703Radio(0, sda_pin=4, scl_pin=5, i2c_addr=0x10, reset_pin=21, irq_pin=22)


# Presets
presets = [
    ("EVROPA 2", 88.2),
    ("RADIO Z", 89.6),
    ("KISS", 90.0),
    ("FREKVENCE1", 91.0),
    ("IMPULS", 96.6)
]


# Radio state
frequency = 995
volume = 5
muted = False

station = "MANUAL"

selected_preset = 0
preset_selection = False

si4703_ok = False

last_rds_ms = time.ticks_ms()
last_rds_station = None

RDS_INTERVAL_MS = 400


def update_display():
    draw_radio_screen(
        lcd,
        freq=frequency,
        station=station,
        volume=volume,
        si4703_ok=si4703_ok,
        muted=muted
    )


def reset_rds_state():
    global last_rds_station
    global last_rds_ms

    last_rds_station = None
    last_rds_ms = time.ticks_ms()

    radio.clearRDS()


print("FM Radio")
print("Initializing Si4703...")


try:
    radio.si4703Init()

    si4703_ok = radio.isConnected()

    if si4703_ok:
        print("Si4703: OK")

        frequency = radio.setFrequency(
            frequency
        )

        radio.setVolume(
            volume
        )

        radio.setMute(
            False
        )

        volume = radio.getVolume()

    else:
        print("Si4703: NOT FOUND")


except Exception as error:
    print(
        "Si4703 error:",
        error
    )

    si4703_ok = False


print()
print("Encoder: manual tuning")
print("Encoder SW: mute")
print("VOL+ / VOL-: volume")
print("UP / DOWN: select preset")
print("OK: confirm preset")
print("RDS polling: 400 ms")

update_display()


try:
    while True:

        now_ms = time.ticks_ms()


        # Encoder - manual tuning
        delta = encoder.get_delta()

        if delta != 0:

            if delta < 0:
                radio.si4703SeekDown()
            else:
            
                radio.si4703SeekUp()
            time.sleep(1)
            

            
            station = "MANUAL"
            preset_selection = False

            print(
                "Frequency:",radio.si4703GetChannel() / 10.0,"MHz")

            update_display()


        # Encoder SW - mute
        if encoder.was_pressed():

            muted = not muted

            if si4703_ok:
                radio.setMute(
                    muted
                )

            if muted:
                print("Mute ON")
            else:
                print("Mute OFF")

            update_display()


        # ADKeyboard
        key = keyboard.was_pressed()


        # Volume +
        if key == "VOL+":

            if volume < 15:
                volume += 1

            if si4703_ok:

                radio.setVolume(
                    volume
                )

                volume = radio.getVolume()

            print(
                "Volume:",
                volume
            )

            update_display()


        # Volume -
        elif key == "VOL-":

            if volume > 0:
                volume -= 1

            if si4703_ok:

                radio.setVolume(
                    volume
                )

                volume = radio.getVolume()

            print(
                "Volume:",
                volume
            )

            update_display()


        # Next preset
        elif key == "UP":

            preset_selection = True

            selected_preset += 1

            if selected_preset >= len(presets):
                selected_preset = 0

            station = presets[
                selected_preset
            ][0]

            print(
                "Selected:",
                station,
                "- press OK to confirm"
            )

            update_display()


        # Previous preset
        elif key == "DOWN":

            preset_selection = True

            selected_preset -= 1

            if selected_preset < 0:
                selected_preset = (
                    len(presets) - 1
                )

            station = presets[
                selected_preset
            ][0]

            print(
                "Selected:",
                station,
                "- press OK to confirm"
            )

            update_display()


        # Confirm preset
        elif key == "OK":

            if preset_selection:

                station = presets[
                    selected_preset
                ][0]

                preset_frequency = presets[
                    selected_preset
                ][1]

                if si4703_ok:

                    frequency = radio.setFrequency(
                        preset_frequency
                    )

                    reset_rds_state()

                else:
                    frequency = preset_frequency

                preset_selection = False

                print(
                    "Preset confirmed:",
                    station,
                    frequency,
                    "MHz"
                )

                update_display()

            else:

                print(
                    "OK ignored - no preset selected"
                )


        # RDS polling
        if (
            si4703_ok
            and not preset_selection
            and time.ticks_diff(
                now_ms,
                last_rds_ms
            ) >= RDS_INTERVAL_MS
        ):

            last_rds_ms = now_ms

            rds_station = radio.si4703ReadRDS()

            if (
                rds_station is not None
                and rds_station != last_rds_station
            ):

                last_rds_station = rds_station
                station = rds_station

                print(
                    "RDS PS:",
                    station
                )

                update_display()


        time.sleep_ms(1)


except KeyboardInterrupt:

    encoder.deinit()

    if si4703_ok:
        radio.si4703ShutDown()

    lcd.fill(0)
    lcd.show()

    print("\nProgram stopped.")