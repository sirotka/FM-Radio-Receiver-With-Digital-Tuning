# FM radio receiver with digital tuning

Členové týmu

1. Ekaterina Krupenko (zodpovědná za simulaci ve Wokwi)
2. Rostislav Lacek (zodpovědný za )
4. Vojtěch Kudela (zodpovědný za)



# Teoretický popis

Běžné analogové FM přijímače postrádají přesné digitální ladění frekvence, vizuální zpětnou vazbu o naladěné stanici, dekódování doplňkových textových informací a pohodlnou správu uložených předvoleb. Návrh digitálního rádia vyžaduje přesnou časovou koordinaci mezi různými typy sběrnic a vstupů v reálném čase – konkrétně rychlé zpracování kvadraturních signálů z rotačního enkodéru, čtení analogových napěťových úrovní z tlačítkové matice, komunikaci s tunerem přes I2C a vykreslování grafiky přes SPI, aniž by docházelo ke zpoždění uživatelského rozhraní nebo výpadkům zvukového výstupu.

Tento projekt realizuje plně digitální FM přijímač postavený na mikrokontroléru Raspberry Pi Pico W (RP2040) naprogramovaném v jazyce MicroPython. Architektura systému odděluje hardwarovou obsluhu vstupů od aktualizace displeje a řízení tuneru, což zajišťuje okamžitou odezvu na uživatelské povely.



## Komponenty

| Komponenta | Popis / Specifikace | Rozhraní / Protokol | Poznámky |
| :--- | :--- | :--- | :--- |
| **Raspberry Pi Pico** | RP2040 mikrokontrolér | RP2040 dvoujádrový ARM Cortex-M0+ | 3.3V logická úroveň |
| **FM modul** | Si4703 FM Tuner | I2C + 3,5mm Jack | součástí je zesilovač/ anténa pro sluchátka |
| **displej** | Nokia 5110 Display (PCD8544) | SPI (84x48 Graphic LCD) | podsvícený grafický LCD  |
| **rotační enkodér** | KY-040 | N/A | 3,3V až 5V logická úroveň/ 2 pull-up rezistory|
| **tlačítka** | ADKeyboard v3 | pasivní analogový obvod (odporový dělič napětí) | obsahuje pull-up rezistory |
| **3,5mm sluchátka** | 3,5mm jack | analogové audio | slouží jako anténa |
| **nepájivé pole** | Breadboard a propojovací vodiče | N/A | propojení komponent |



## Popis jednotlivý komponent


### _Příjem a zpracování FM signálu_
Srdcem rádiové části je integrovaný digitální tuner _[`Si4703`](https://pmdway.com/products/si4703-rds-fm-radio-tuner-evaluation-breakout-board?srsltid=AYCX9vKLGemZAaw2HZfW6TDdMDwJ-ylaad4x8F2DHs_wG2OiNv1dP0B4)_, který s mikrokontrolérem komunikuje přes sběrnici I2C a řídicí resetovací pin.
- **Zpracování signálu**: Čip se stará o kompletní příjem, demodulaci a stereofonní dekódování FM signálu v pásmu 87,5–108,0 MHz.

- **Dekódování RDS (Radio Data System)**: Kromě samotného zvuku přijímač průběžně čte digitální datový tok RDS. Z něj software extrahuje PS (Program Service) – tedy oficiální název aktuálně poslouchané rozhlasové stanice (např. _EVROPA 2_, _ČRo 1_), který se následně předává k zobrazení na displej.
  
- _Hardwarová regulace hlasitosti_: Nastavení hlasitosti probíhá digitálně zápisem do vnitřních registrů čipu Si4703 (v rozsahu 0–15), čímž je zachována maximální kvalita výstupního signálu bez nutnosti vnějšího analogového potenciometru.

- _Anténa_: Stínění připojeného audio kabelu slouží jako přijímací FM anténa.


### _Manuální ladění frekvence_
Pro plynulé a přesné manuální přelaďování stanic je použit rotační enkodér _[`KY-040`](https://botland.store/encoders/16558-rotation-sensor-encoder-20-pulses-okystar-ky-040-5904422366278.html#product_tab_description)_ připojený na digitální vstupy CLK a DT.
- _Obsluha v reálném čase_: Snímání otáčení je v MicroPythonu řešeno pomocí hardwarových přerušení (IRQ) na sestupnou/vzestupnou hranu signálu CLK. Díky tomu mikrokontrolér spolehlivě zachytí každý mechanický krok enkodéru i při rychlém otáčení, bez ohledu na to, zda právě překresluje displej.
- _Krokování frekvence_: Každý detekovaný pulz vpravo či vlevo posune naladěnou frekvenci o pevně definovaný krok (standardně **0,1 MHz**) a odešle příkaz k přeladění do modulu Si4703. Integrované tlačítko enkodéru (SW) lze volitelně využít pro rychlé ztlumení zvuku (Mute).


### _Ovládání hlasitosti a správa předvoleb_
Modul _[`ADKeyboard v3`](https://botland.store/keyboards/3560-adkeyboard-v3-keyboard-module-with-colorful-buttons-6959420901197.html)_ sdružuje 5 mikrospínačů na jediný analogový výstup připojený na ADC0 mikrokontroléru. Každé tlačítko spíná jiný odporový dělič, takže po stisku vznikne na vstupu ADC unikátní napěťová úroveň (v rozsahu 0–3,3 V). Software tyto hodnoty filtruje (ošetření zákmitů – *debouncing*) a rozděluje tlačítka do tří logických skupin:

- _Tlačítka 1 a 2 (VOL+ a VOL-)_: Slouží k přímé regulaci hlasitosti. Každý stisk inkrementuje nebo dekrementuje aktuální úroveň hlasitosti v registru čipu Si4703 a okamžitě aktualizuje indikátor na obrazovce.

- _Tlačítka 3 a 4 (UP a DOWN – výběr ze seznamu)_: Slouží k listování (posunu kurzoru) v uloženém seznamu předvolených stanic na displeji. Samotné listování ještě nemění naladěnou frekvenci – uživatel si nejprve vybere požadovanou stanici z nabídky.

- _Tlačítko 5 (prostřední tlačítko – OK / ENTER)_: Slouží k potvrzení výběru. Po jeho stisknutí systém načte frekvenci označené stanice ze seznamu předvoleb a okamžitě přeladí tuner Si4703 na tuto stanici.


### _Uživatelské rozhraní_
Vizuální zpětnou vazbu zajišťuje LCD displej _[`Nokia 5110`](https://naylampmechatronics.com/lcd-alfanumerico/989-display-lcd-nokia-5110.html)_ s rozlišením 84×48 pixelů, připojený přes rychlou sběrnici SPI0. Obrazovka je rozdělena do několika přehledných informačních zón:

- _Hlavní údaj o frekvenci_: Dominantní zobrazení aktuálně naladěné frekvence v MHz (např. **105.5 MHz**).

- _Identifikace stanice (RDS / Paměť)_: Řádek zobrazující název stanice dekódovaný ze signálu RDS (pokud je RDS k dispozici), případně uložený název z paměti předvoleb.

- _Indikátor hlasitosti_: Grafický ukazatel (sloupcový graf nebo číselná hodnota VOL: 0–15) reagující na stisk tlačítek VOL+ / VOL-.

- _Seznam předvoleb (Preset List)_: Spodní část displeje zobrazuje položky ze seznamu uložených stanic s vizuálním kurzorem (zvýrazněním), který se pohybuje při ovládání tlačítky na ADKeyboard v3 a čeká na potvrzení prostředním tlačítkem.



### Blokové schéma

Blokové schéma znázorňuje propojení jednotlivých komponent FM přijímače a použitá rozhraní I²C, SPI, GPIO a ADC.

![Blokové schéma FM přijímače](images/blockdiagram.png)

### Simulace ve Wokwi

V prostředí Wokwi bylo vytvořeno zapojení komponent a vlastní simulace FM modulu Si4703. Byla otestována komunikace I2C a digitální ladění frekvence pomocí MicroPythonu.

**Odkaz na simulaci:** https://wokwi.com/projects/480485965769085953


### Tabulka mapování hardwarových pinů 

| Komponenta | Pin komponenty | Pico Pin Name | Blok / Konektor na Gravity Board | Funkce / Popis zapojení |
| :--- | :--- | :--- | :--- | :--- |
| **FM přijímač Si4703** | VCC (3.3V) | 3V3 | Blok **I2C0** (Pin 3V3) | Napájení modulu (3,3 V) |
| | GND | GND | Blok **I2C0** (Pin GND) | Společná zem |
| | SDIO (SDA) | GP4 | Blok **I2C0** (Pin D/4) | I2C datová sběrnice |
| | SCLK (SCL) | GP5 | Blok **I2C0** (Pin C/5) | I2C hodinová sběrnice |
| | RST | GP6 | Vnitřní lišta (GP6) | Resetovací pin pro aktivaci I2C režimu čipu |
| **Nokia 5110 LCD** | VCC | 3V3 | Blok **SPI0** (Pin 3V3) | Napájení displeje (3,3 V) |
| | GND | GND | Blok **SPI0** (Pin GND) | Společná zem |
| | CLK (SCK) | GP18 | Blok **SPI0** (Pin SCK/18) | SPI hodiny (Serial Clock) |
| | DIN (MOSI) | GP19 | Blok **SPI0** (Pin MO/19) | SPI data (Master Out / Data In) |
| | CE (CS) | GP17 | Blok **SPI0** (Pin SS/17) | Chip Select / Aktivace displeje |
| | DC | GP16 | Blok **SPI0** (Pin MI/16) | Přepínání Data / Příkaz (využit MISO pin) |
| | RST | GP20 | Blok **Digital** (Pin GP20) | Hardwarový reset displeje |
| | BL (LIGHT) | 3V3 | Blok **Digital** (Pin GP20 / 3V3) | Podsvícení displeje (připojeno na 3,3 V) |
| **ADKeyboard v3** | VCC | 3V3 | Blok **Analog** (Pin GP26 / 3V3) | Napájení odporové sítě tlačítek (3,3 V) |
| | GND | GND | Blok **Analog** (Pin GP26 / GND) | Společná zem |
| | OUT (S) | GP26 | Blok **Analog** (Pin GP26 / A) | Analogový vstup ADC0 pro čtení 5 tlačítek |
| **Rotační enkodér KY-040** | + (VCC) | 3V3 | Blok **Digital** (Pin GP14 / 3V3) | Napájení pull-up rezistorů enkodéru (3,3 V) |
| | GND | GND | Blok **Digital** (Pin GP14 / GND) | Společná zem |
| | CLK | GP14 | Blok **Digital** (Pin GP14 / D) | Kanál A kvadraturního signálu (pro IRQ) |
| | DT | GP15 | Blok **Digital** (Pin GP15 / D) | Kanál B kvadraturního signálu |
| | SW | GP13 | Blok **Digital** (Pin GP13 / D) | Integrované tlačítko enkodéru (např. pro Mute) |


### Časování a plán souběžnosti

| Činnost (Aktivita) | Zamýšlený interval | Způsob běhu / Implementace | Popis a účel |
| :--- | :--- | :--- | :--- |
| **Čtení enkodéru (KY-040)** | Krátký (10–20 ms) | Blokující cyklus v hlavní smyčce s `time.sleep_ms(10)` | Zajišťuje okamžitou a plynulou detekci otáčení hřídele a stisku tlačítka bez znatelné odezvy. |
| **Obnovení displeje (Nokia 5110)** | Dynamický / cca 100 ms | Synchronní vykreslení v každém cyklu změny stavu | Přepisuje paměťový buffer a odesílá data přes SPI na displej pouze tehdy, dojde-li ke změně hodnot (nebo v pravidelném taktu), což šetří výkon procesoru. |
| **Dotazování FM tuneru / RDS (Si4703)** | Delší (200–500 ms) | Periodické čtení přes I2C sběrnici | Kontroluje stav ladění, sílu signálu a aktualizuje názvy stanic (RDS). Interval brání nadměrnému zasycení I2C sběrnice. |


# Požadavky

- [ ] Návrh blokového schématu a případné jeho přepracování do finální verze
- [ ] Otestování samostatných bloků projektu (FM přijímač, LCD displej, enkodér a tlačítka)
- [ ] Sestavení na desku se všemi částmi a její finální otestování
- [ ] Finální zpracování Githubu + README
- [ ] Plakát
- [ ] Demonstrační video


# Plán práce

### 1. Týden
- [x] Zjištění problematiky projektu a domluva na funkcích
- [x] Založení Github repozitáře
- [x] Vytvoření seznamu komponent + přiložit odkazy
- [x] Návrh blokové schématu zapojení (případně jej pak upravit)
- [ ] Plán časování a souběžnosti

### 2. Týden 
- [ ] Vytvoření a otestování kódu pro displej (pro zobrazení přijímaného signálu -> zobrazení čísel (frekvence a hlasitost))
- [ ] Vytvoření a otestování kódu pro tlačítka (zjistit, jak fungují + datasheet)
- [ ] Vytvoření a otestování kódu pro FM přijímač (rozchodit knihovnu a otestovat v laboratoři)
- [ ] Vytvoření záznamu testovaných částí (foto či video)
- [ ] Uložení funkčních komponentů na Github
- [ ] Aktualizování schématu zapojení (blokové i ve Wowki)

###  3. Týden
- [ ] Sestavení prototypu s klíčovými funkcemi
- [ ] Záznamy a řešené problémy integrace

### 4. Týden
- [ ] Výsledky testů
- [ ] Ověření stability prototypu
- [ ] Návrh plakátu a osnova ukázky

### 5. Týden
- [ ] Kompletní finalizace projektu
- [ ] Dokončení plakátu
- [ ] Dokončení Githubu
- [ ] Natočení demonstračního videa a vložení na Github

## Reference
1. [Gravity: Expansion Board for Raspberry Pi Pico / Pico 2](https://www.dfrobot.com/product-2393.html)
2. [Si4703 FM Radio Receiver](https://pmdway.com/products/si4703-rds-fm-radio-tuner-evaluation-breakout-board?srsltid=AYCX9vKLGemZAaw2HZfW6TDdMDwJ-ylaad4x8F2DHs_wG2OiNv1dP0B4)
3. [Graphic LCD 84x48 - Nokia 5110](https://naylampmechatronics.com/lcd-alfanumerico/989-display-lcd-nokia-5110.html)
4. [ADKeyboard v3](https://botland.store/keyboards/3560-adkeyboard-v3-keyboard-module-with-colorful-buttons-6959420901197.html)
5. [Rotační enkodér KY-040](https://botland.store/encoders/16558-rotation-sensor-encoder-20-pulses-okystar-ky-040-5904422366278.html#product_tab_description)
