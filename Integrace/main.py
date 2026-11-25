from machine import SPI, Pin
import time

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

# ADKeyboard
keyboard1 = ADKeyboard(adc_pin=26)
keyboard2 = ADKeyboard(adc_pin=27)

# FM modul
# Parametry: (i2c_objekt, i2c_adresa, reset_pin, irq_pin)
radio = si4703Radio(0, sda_pin=4, scl_pin=5, i2c_addr=0x10, reset_pin=21, irq_pin=22)

# Radio initial state
frequency = 995
volume = 10
muted = False
station = "MANUAL"

stations = []  # prázdný list na začátku
def add_station(name, freq):
    stations.append((name, freq))  # přidá dvojici (název, frekvence) na konec
    stations.sort(key=lambda x: x[1]) #srovnání podle od nejnižší frekvence k nejvyšší
    
add_station("KISS", 883)
add_station("EVROPA 2", 1055)


keyList = [
    [None, "volumeUp", "volumeDown", "stationDown", "stationUp", "mute"],#keyboard 1
    [None, "listUp", "listDown", "back", "save", "choose"]] #keyboard 2

#vrátí stisklou klávesu nebo "None"
def getKey():
    key = keyList[0][keyboard1.was_pressed()]
    if key == None:
        key = keyList[1][keyboard2.was_pressed()]
    return key

FM_MIN = 875   # 87.5 MHz (nebo 87.5, pokud používáte float)
FM_MAX = 1080  # 108.0 MHz (nebo 108.0)

#listování v seznamu stanic
def next_station(current_freq, current_station, direction):
    if not stations:
        return current_station, current_freq

    if direction == "up":
        # Seznam stations je seřazený vzestupně -> první vyšší je nejbližší vyšší
        for name, freq in stations:
            if FM_MIN <= freq <= FM_MAX and freq > current_freq:
                return name, freq
        # Žádná vyšší není -> vrať nejnižší platnou stanici
        for name, freq in stations:
            if FM_MIN <= freq <= FM_MAX:
                return name, freq
        return current_station, current_freq

    elif direction == "down":
        # Projdeme od konce -> první nižší je nejbližší nižší
        for name, freq in reversed(stations):
            if FM_MIN <= freq <= FM_MAX and freq < current_freq:
                return name, freq
        # Žádná nižší není -> vrať nejvyšší platnou stanici
        for name, freq in reversed(stations):
            if FM_MIN <= freq <= FM_MAX:
                return name, freq
        return current_station, current_freq

    return current_station, current_freq

def save_station(name, freq):
    global stations

    # Pojistka proti uložení mimo rozsah FM pásma
    if not (FM_MIN <= freq <= FM_MAX):
        return False

    # Ošetření prázdného/chybějícího názvu
    clean_name = name if name else "MANUAL"

    for i, (_, existing_freq) in enumerate(stations):
        if existing_freq == freq:
            # Stanice se stejnou frekvencí už existuje -> přepíšeme ji
            stations[i] = (clean_name, freq)
            return True

    # Jinak přidáme novou stanici
    stations.append((clean_name, freq))
    return True  

#Zjistí název stanice pomocí RDS, pokud nezjistí, tak vrátí název původní stanice
def getStation(oldStation):
    station = radio.si4703GetStationName(timeout_ms=2000)
    if station:
        return station
    else:
        return oldStation

#Updatuje hodnoty globálních proměnných
def UpdateData():
    global frequency
    frequency=radio.si4703GetChannel() / 10.0
    global station
    station = getStation(station)
    global volume
    volume = radio.si4703GetVolume()
    
    
#Obnovuje hodnoty na displeji
def update_display(updateData = True):
    if updateData:
        UpdateData()
    draw_radio_screen(
        lcd,
        freq=frequency,
        station=station,
        volume=volume,
        si4703_ok=True,
        muted=muted
    )

print("FM Radio")
print("Initializing Si4703...")


try:
    #inicializace rádia
    radio.si4703Init()
    radio.si4703SetChannel(987)  # 98.7 MHz
    radio.si4703SetVolume(8)
    UpdateData()


except Exception as error:
    print(
        "Si4703 error:",
        error
    )
    
print()
print("            Keyboard 26                           Keyboard 27          ")
print("   ________            ________          ________            ________  ")
print("  /        \          /        \        /        \          /        \ ")
print(" |  Volume  |        | Station  |      |   List   |        |   Save   |")
print(" |    UP    |        |    UP    |      |    UP    |        |          |")
print("  \________/ ________ \________/        \________/ ________ \________/ ")
print("            /        \                            /        \           ")
print("           |   Mute   |                          |  Choose  |          ")
print("           |          |                          |          |          ")
print("   ________ \________/ ________          ________ \________/ ________  ")
print("  /        \          /        \        /        \          /        \ ")
print(" |  Volume  |        | Station  |      |   List   |        |   Back   |")
print(" |   DOWN   |        |   DOWN   |      |   DOWN   |        |          |")
print("  \________/          \________/        \________/          \________/ ")
print()


update_display()


try:
    while True:
        
        time.sleep(0.1)
        # ADKeyboard
        key = getKey()

        # Volume +
        if key == "volumeUp":
            muted = False
            radio.si4703SetVolume(volume + 1)
            update_display()
            print("Volume:",volume)

        # Volume -
        elif key == "volumeDown":
            muted = False
            radio.si4703SetVolume(volume - 1)
            update_display()
            print("Volume:",volume)

        # tune frequency up
        elif key == "stationUp":
            radio.si4703SeekUp()
            update_display()
            print("Selected: ",station)
            
        # tune frequency down
        elif key == "stationDown":
            radio.si4703SeekDown()
            update_display()
            print("Selected: ",station)
        
        elif key == "mute":
            muted = not muted
            if muted:
                radio.si4703SetVolume(0)
            else:
                radio.si4703SetVolume(volume)
            update_display(updateData=False)
            print("Muted: ",muted)
            
        if key == "listUp":
            station, frequency = next_station(frequency, station, "up")
            update_display(updateData = False)
        elif key == "listDown":
            station, frequency = next_station(frequency, station, "down")
            update_display(updateData = False)

        elif key == "back":
            update_display()  
            
        elif key == "save":
            save_station(station, frequency)
            
        elif key == "choose":
            radio.si4703SetChannel(frequency)
            update_display()

except KeyboardInterrupt:

    radio.si4703ShutDown()

    lcd.fill(0)
    lcd.show()

    print("\nProgram stopped.")
