from machine import Pin, I2C, ADC
from time import sleep_ms


#Si4703
rst = Pin(6, Pin.OUT)

rst.value(0)
sleep_ms(20)
rst.value(1)
sleep_ms(100)

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)


#Encoder
encoder_clk = Pin(14, Pin.IN, Pin.PULL_UP)
encoder_dt = Pin(15, Pin.IN, Pin.PULL_UP)
encoder_sw = Pin(13, Pin.IN, Pin.PULL_UP)


#ADKeyboard
adkeyboard = ADC(26)


encoder_delta = 0
last_sw = 1
last_adc_print = 0


def encoder_handler(pin):
    global encoder_delta

    if encoder_dt.value():
        encoder_delta += 1
    else:
        encoder_delta -= 1


encoder_clk.irq(
    trigger=Pin.IRQ_FALLING,
    handler=encoder_handler
)


print("TEST")

devices = i2c.scan()

print("I2C devices:", [hex(address) for address in devices])

if 0x10 in devices:
    print("Si4703: OK")
else:
    print("Si4703: NOT FOUND")

print("Turn encoder, press encoder button and ADKeyboard buttons.")
print()


try:
    while True:

        if encoder_delta != 0:
            delta = encoder_delta
            encoder_delta = 0

            if delta > 0:
                print("Encoder: RIGHT")
            else:
                print("Encoder: LEFT")


        current_sw = encoder_sw.value()

        if last_sw == 1 and current_sw == 0:
            print("Encoder button: PRESSED")

        last_sw = current_sw


        adc_value = adkeyboard.read_u16()

        if adc_value < 60000:
            if abs(adc_value - last_adc_print) > 500:
                print("ADKeyboard ADC:", adc_value)
                last_adc_print = adc_value

        sleep_ms(20)


except KeyboardInterrupt:
    print("\nTest stopped.")