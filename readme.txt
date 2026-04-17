# Proxnet: Wireless IoT Security Testbed 🛜🔒

Proxnet (internally "flipper zero") is a portable testbed designed for authorized wireless IoT security analysis within a controlled lab environment.

## ⚠️ Safety Note
All active radio transmissions (sniffing, replay, jamming) are intended strictly for use within a Faraday-shielded lab environment on authorized devices, following established Rules of Engagement (ROE).

## 🛠️ Overview
The system uses a Raspberry Pi 4 as the central controller, paired with an ESP32 for RFID/NFC and Bluetooth/BLE scanning. [cite_start]It features direct SPI connections for nRF24L01+ (2.4GHz) and CC1101 (Sub-GHz) analysis.

## ⚙️ Hardware Components
* [cite_start]**Controller:** Raspberry Pi 4 Model B (4GB) [cite: 71]
* [cite_start]**Microcontroller:** ESP32 Dev Module (WROOM, UART data link to Pi) [cite: 71]
* [cite_start]**RFID/NFC:** MFRC522 (13.56 MHz) & RDM6300 (125 kHz) [cite: 71]
* [cite_start]**2.4 GHz:** nRF24L01+ PA/LNA [cite: 71]
* [cite_start]**Sub-GHz:** CC1101 (Note: Module currently disabled/suspected faulty) [cite: 71, 73]
* [cite_start]**Wi-Fi:** Monitor-mode capable USB Adapter (e.g., RTL8188EUS) [cite: 71]
* [cite_start]**Power/Safety:** LM2596 Buck Converter, Logic Level Converter, Physical Kill Switch [cite: 71]

## 🚀 Functionality
* [cite_start]**RFID/NFC:** Scans and logs UIDs from 13.56MHz and 125kHz tags.
* [cite_start]**Bluetooth/BLE:** Discovers nearby Classic and BLE devices.
* [cite_start]**Radio Sniffing:** Captures raw 2.4GHz packets (and Sub-GHz, pending module replacement)[cite: 72, 73].
* [cite_start]**Wi-Fi Capture:** Captures 802.11 packets using tcpdump.
* [cite_start]**Web UI:** Flask-based interface for managing scanners and viewing logs[cite: 75].
* [cite_start]**Logging:** Stores results in SQLite and CSV formats[cite: 76].

## 📝 Setup (Quickstart)
1.  [cite_start]Assemble hardware as per the `Wiring.md`[cite: 77].
2.  [cite_start]Flash Raspberry Pi OS Lite and install dependencies (`git`, `python3-venv`, `aircrack-ng`, etc.)[cite: 78].
3.  [cite_start]Configure Pi SPI/I2C/Serial via `raspi-config`[cite: 79].
4.  [cite_start]Flash ESP32 with the provided `.ino` sketch[cite: 80].
5.  Clone and run:
    ```bash
    git clone [https://github.com/Nishant-404/Proxnet.git](https://github.com/Nishant-404/Proxnet.git)
    cd Proxnet
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python3 scripts/web_ui.py
    ```
6.  Access the UI at `http://<Pi_IP_Address>:5000`[cite: 81].

*For detailed wiring schematics, see `Wiring.md`.*
