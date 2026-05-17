
# ProxNet Wiring Diagram

This document details the hardware connections between the Raspberry Pi 4, ESP32, radio modules, and peripherals.

**⚠️ Critical Hardware Safety Notes:**
* **Common Ground:** ALL `GND` pins must tie to a single common ground rail. Without this, logic signals will float.
* **Power Isolation (Anti-Backfeeding):** The ESP32 is powered **externally** via USB. Do **NOT** route 5V from the Pi to the ESP32's 5V/VIN pin.
* **Kill Switch Routing:** The switch cuts the 5V line going to the **LM2596 buck converter** and **RDM6300**. It does **NOT** cut main power to the Pi.
* **Logic Level Converter (LLC):** Mandatory for dropping the 5V RDM6300 TX signal to 3.3V for the ESP32 RX pin.
* **Radio Power:** The nRF24L01+ and CC1101 are powered exclusively via the LM2596 tuned to **3.3V** (the Pi's 3V3 rail cannot supply enough peak current during TX).
* **Wi-Fi Adapter:** Connects directly to a Pi USB 2.0 port.

## 1. Power Distribution

```mermaid
flowchart TD
	Ext_USB[External 5V USB Adapter] --> ESP32(ESP32 Development Board)
	Pi_Pwr[Pi Official Type-C] --> RPi4(Raspberry Pi 4)

	RPi4 -->|Pin 2: 5V Out| KillSwitch(Peripheral Kill Switch)
	KillSwitch -->|Switched 5V| Peri_5V_Rail(Switched 5V Rail)

	Peri_5V_Rail --> RDM_VCC(RDM6300 VCC)
	Peri_5V_Rail --> LLC_HV(LLC HV Power)
	Peri_5V_Rail --> LM2596_IN(LM2596 Buck IN)

	LM2596_IN -->|Regulated 3.3V| RadioPwr3V3(Radio 3.3V Rail)
	RadioPwr3V3 --> NRF_VCC(nRF24 VCC)
	RadioPwr3V3 --> CC_VCC(CC1101 VCC)

	ESP32 -->|3.3V Out| LLC_LV(LLC LV Power)
	ESP32 -->|3.3V Out| RC522_VCC(RC522 VCC)
```

## 2. Signal Routing

```mermaid
flowchart TD
	%% Host UART Link
	ESP32_TX[ESP32 GPIO 17 TX] -->|3.3V UART| Pi_RX[RPi4 Pin 10 RX]

	%% 125kHz RFID Logic Translation
	RDM_TX[RDM6300 TX 5V] --> LLC_HV1(LLC HV1)
	LLC_HV1 --> LLC_LV1(LLC LV1 3.3V)
	LLC_LV1 --> ESP32_RX[ESP32 GPIO 16 RX]

	%% 13.56MHz RFID
	RC522[RC522 SPI] <-->|GPIO 5,18,19,23| ESP32_SPI[ESP32]

	%% Shared High-Freq SPI Bus
	RPi4_SPI[RPi4 SPI0: Pins 19, 21, 23] <--> NRF24_SPI(nRF24 SPI)
	RPi4_SPI <--> CC1101_SPI(CC1101 SPI - Faulty)
	
	RPi4_CE1[RPi4 Pin 26 CE1] --> NRF_CSN(nRF24 CSN)
	RPi4_CE0[RPi4 Pin 24 CE0] --> CC_CSN(CC1101 CSN)
	RPi4_GPIO[RPi4 Pin 15 GPIO] --> NRF_CE(nRF24 CE)
```

## 3. Common Ground Network

```mermaid
flowchart TD
	GND_Rail[Unified Common GND Rail]
	
	RPi4_GND[RPi4 Pin 6/9] --> GND_Rail
	ESP32_GND[ESP32 GND] --> GND_Rail
	LLC_GND[LLC GND] --> GND_Rail
	RC522_GND[RC522 GND] --> GND_Rail
	RDM_GND[RDM6300 GND] --> GND_Rail
	LM2596_GND[LM2596 GND] --> GND_Rail
	NRF_GND[nRF24 GND] --> GND_Rail
	CC_GND[CC1101 GND] --> GND_Rail
```