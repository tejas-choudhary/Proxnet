# ProxNet 📡 
**Wireless IoT Security & Protocol Analysis Testbed**

ProxNet is a portable, hardware-accelerated testbed designed for authorized wireless security auditing, reverse engineering, and protocol analysis. It utilizes a distributed architecture: a **Raspberry Pi 4** acts as the high-level host controller and data logger, while an externally powered **ESP32** handles low-latency edge scanning for RFID, NFC, and BLE.

**⚠️ Rules of Engagement (ROE) & Safety Note:** All active radio transmissions (sniffing, replay, jamming) are intended **strictly** for use within a Faraday-shielded lab environment on authorized devices. Ensure all external power supplies and logic-level translation circuits are verified before operating to prevent hardware backfeeding.

---

## 🏗️ System Architecture

ProxNet segregates tasks between a Linux host and a real-time microcontroller to prevent bus contention and OS-level latency:

* **Host Controller (Raspberry Pi 4):** Manages the Flask Web UI, SQLite database logging, `tcpdump` packet captures, and high-frequency SPI radio arrays (nRF24/CC1101).
* **Edge Scanner (ESP32):** Handles real-time, low-level polling of 13.56MHz and 125kHz RFID modules, alongside Bluetooth Classic/BLE discovery. Data is piped back to the Pi via a dedicated 3.3V UART cross-link.

## 🧰 Hardware Stack

**Core Compute**
* **Host:** Raspberry Pi 4 Model B (4GB) 
* **Target/Edge:** ESP32 Dev Module (WROOM)

**RF & Sensor Array**
* **13.56 MHz (RFID/NFC):** MFRC522 (ESP32 SPI)
* **125 kHz (RFID):** RDM6300 (ESP32 UART via LLC)
* **2.4 GHz:** nRF24L01+ PA/LNA (Pi SPI0)
* **Sub-GHz:** CC1101 (Pi SPI0 - *Note: Currently marked for diagnostic review*)
* **802.11 Wi-Fi:** Monitor-mode capable USB Adapter (e.g., RTL8188EUS)

**Power & Interface**
* **Power Regulation:** LM2596 Buck Converter (Calibrated to 3.3V for Pi radios)
* **Logic Leveling:** 8-Channel Bi-Directional Logic Level Converter (LLC)
* **Display:** 5" HDMI Touch Display (Kiosk Mode)
* **Safety:** Physical 5V Peripheral Kill Switch

---

## ⚙️ Features

* **Multi-Band Scanning:** Automated UID logging across 13.56MHz and 125kHz tags.
* **BLE/BT Discovery:** Background discovery of nearby Bluetooth/BLE broadcast packets.
* **Raw Packet Sniffing:** Passive capture on specific 2.4GHz channels (nRF24) and 802.11 monitor mode frames (`tcpdump`).
* **Centralized Dashboard:** A Flask-based Web UI to start/stop daemons, switch frequency bands, and view real-time logs.
* **Persistent Logging:** SQLite (`logs/proxnet_log.db`) for structured data and CSV/Log files for raw dumps.

---

## 🚀 Quick Start Guide

### 1. Host (Raspberry Pi) Setup
Flash Raspberry Pi OS (Lite/64-bit recommended) and enable SPI/I2C/Serial via `sudo raspi-config`. 

Install system dependencies:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3-venv aircrack-ng tshark tcpdump sqlite3 lsof
```

Configure user groups for network sniffing:
```bash
sudo usermod -a -G dialout,wireshark $USER
sudo setcap cap_net_raw,cap_net_admin=eip /usr/sbin/tcpdump
sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/dumpcap
```
### 2. Edge (ESP32) Firmware
 - Open the firmware/ directory in Arduino IDE or PlatformIO.
 - Select your specific ESP32 board variant.
 - Flash the .ino or .cpp source to the ESP32. (Ensure the ESP32 is disconnected from the Pi's UART pins during flashing).

### 3. Software Env
Clone the repository and spin up the Python environment:
```bash
git clone [https://github.com/Nishant-404/Proxnet.git](https://github.com/Nishant-404/Proxnet.git)
cd Proxnet

# Initialize virtual environment
python3 -m venv venv
source venv/bin/activate

# Install core dependencies
pip install -r requirements.txt
```

### 4. Boot the interface
```bash
python3 scripts/web_ui.py
```
Navigate to `http://<Pi_IP_Address>:5000` on any device within the local network to access the ProxNet dashboard.

---

## 📂 Project Structure
```
ProxNet/
├── firmware/                 # ESP32 C++ source code (.ino/.cpp)
├── host/                     # Raspberry Pi Python modules
│   ├── modules/              # Sub-modules (nRF24, CC1101, UART parsers)
│   └── web_ui.py             # Main Flask application entry point
├── logs/                     # SQLite databases and raw packet captures
├── docs/
│   └── Wiring.md             # Pin-to-pin mapping and electrical safety guidelines
├── requirements.txt          # Python dependencies
└── README.md
```