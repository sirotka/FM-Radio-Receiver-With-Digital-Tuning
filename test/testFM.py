import time
from machine import Pin, I2C
from Si4703Library import si4703Radio

def main():
    
    # Parametry: (i2c_objekt, i2c_adresa, reset_pin, irq_pin)
    radio = si4703Radio(0, sda_pin=4, scl_pin=5, i2c_addr=0x10, reset_pin=21, irq_pin=22)
    
    print("Inicializace rádia...")
    radio.si4703Init()
    
    radio.si4703SetChannel(987)  # 98.7 MHz
    radio.si4703SetVolume(8)
    
    print("Aktuální kanál:", radio.si4703GetChannel() / 10.0, "MHz")
    print("Aktuální hlasitost:", radio.si4703GetVolume())

    try:
        while True:
            kb_input = input("Příkaz (1=SeekDown, 2=SeekUp, 3=Reset 98.7, +=Vol+, -=Vol-): ")

            if kb_input == "1":
                radio.si4703SeekDown()
                print("Naladěno:", radio.si4703GetChannel() / 10.0, "MHz")
                



            elif kb_input == "2":
                radio.si4703SeekUp()
                print("Naladěno:", radio.si4703GetChannel() / 10.0, "MHz")
                



            elif kb_input == "3":
                radio.si4703SetChannel(987)
                print("Naladěno:", radio.si4703GetChannel() / 10.0, "MHz")
            elif kb_input == "+":
                radio.si4703SetVolume(radio.si4703GetVolume() + 1)
                print("Hlasitost:", radio.si4703GetVolume())
            elif kb_input == "-":
                radio.si4703SetVolume(radio.si4703GetVolume() - 1)
                print("Hlasitost:", radio.si4703GetVolume())
                
            nazev = radio.si4703GetStationName(timeout_ms=2000)
            if nazev:
                print("Stanice:", nazev)
            else:
                print("Čekám na RDS název...")
            
            
    except KeyboardInterrupt:
        print("\nUkončování programu...")[cite: 2]
        
    print("Vypínám rádio...")[cite: 2]
    radio.si4703ShutDown()

if __name__ == "__main__":
    main()
