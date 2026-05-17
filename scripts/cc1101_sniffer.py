#!/usr/bin/env python3

# cc1101_sniffer.py
# Listens for packets on a specified Sub-GHz frequency using CC1101.

import spidev
import time
import sys
import signal # To handle Ctrl+C gracefully

print("Starting CC1101 Sniffer...")

# --- Configuration ---
SPI_BUS = 0
SPI_DEVICE = 0 # CE0 (Pi Pin 24)
SPI_SPEED = 500000 # Use speed that worked
SPI_MODE = 1 # Use mode that worked

# --- CC1101 Commands (Strobes) ---
SRES = 0x30 # Reset chip
SIDLE = 0x36 # Go to IDLE state
SRX = 0x34 # Enable RX
SFRX = 0x3A # Flush RX FIFO

# --- CC1101 Registers ---
REG_IOCFG0 = 0x02
REG_FIFOTHR = 0x03
REG_PKTCTRL0 = 0x08
REG_FSCTRL1 = 0x0B
REG_FREQ2 = 0x0D
REG_FREQ1 = 0x0E
REG_FREQ0 = 0x0F
REG_MDMCFG4 = 0x10
REG_MDMCFG3 = 0x11
REG_MDMCFG2 = 0x12
REG_DEVIATN = 0x15
REG_MCSM1 = 0x17
REG_MCSM0 = 0x18
REG_FOCCFG = 0x19
REG_AGCCTRL2 = 0x1B
REG_WORCTRL = 0x1E
REG_FREND0 = 0x22
REG_FSCAL3 = 0x25
REG_FSCAL1 = 0x27
REG_FSCAL0 = 0x29
REG_TEST2 = 0x2C
REG_TEST1 = 0x2D
REG_TEST0 = 0x2E
REG_PATABLE = 0x3E

# --- Configuration Values (Example: 433.92MHz, ASK/OOK, ~4.8kBaud) ---
FREQ_BYTES = [0x10, 0xB0, 0x71] # For 433.919830 MHz
CONFIG_REGS = [
    (REG_FSCTRL1, 0x06), (REG_MDMCFG4, 0x58), (REG_MDMCFG3, 0x93),
    (REG_MDMCFG2, 0x30), (REG_DEVIATN, 0x15), (REG_MCSM1,   0x0C),
    (REG_MCSM0,   0x18), (REG_FOCCFG,  0x14), (REG_AGCCTRL2,0x43),
    (REG_WORCTRL, 0xFB), (REG_FREND0,  0x11), (REG_FSCAL3,  0xE9),
    (REG_FSCAL1,  0x2A), (REG_FSCAL0,  0x1F), (REG_TEST2,   0x81),
    (REG_TEST1,   0x35), (REG_TEST0,   0x09), (REG_IOCFG0,  0x06),
    (REG_FIFOTHR, 0x47), (REG_PKTCTRL0,0x00),
]
# Status Registers
STATUS_RXBYTES = 0x3B | 0x80

# --- SPI Setup ---
spi = spidev.SpiDev()
spi_active = False

# --- Signal Handler ---
def cleanup(signum, frame):
    global spi_active
    print("\nCaught signal, cleaning up...")
    if spi_active:
        try:
            spi_strobe(SIDLE)
            time.sleep(0.1)
            spi.close()
            spi_active = False
            print("SPI closed.")
        except Exception as e:
            print(f"Error during SPI cleanup: {e}")
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# --- Helper Functions ---
def spi_strobe(strobe_cmd):
    response = spi.xfer2([strobe_cmd, 0x00])
    return response[0]

def spi_write_register(reg_address, value):
    spi.xfer2([reg_address, value])

def spi_read_register(reg_address):
    read_address = reg_address | 0x80
    response = spi.xfer2([read_address, 0x00])
    return response[1]

def spi_read_burst(start_address, num_bytes):
    read_address = start_address | 0xC0
    command = [read_address] + [0x00] * num_bytes
    response = spi.xfer2(command)
    return response[1:]

# --- Main Logic ---
try:
    print(f"Opening SPI {SPI_BUS}.{SPI_DEVICE}...")
    spi.open(SPI_BUS, SPI_DEVICE)
    spi.max_speed_hz = SPI_SPEED
    spi.mode = SPI_MODE
    spi_active = True
    print("SPI opened.")

    print("Resetting CC1101...")
    spi_strobe(SRES)
    time.sleep(0.1)

    print("Configuring CC1101 registers...")
    spi_write_register(REG_FREQ2, FREQ_BYTES[0])
    spi_write_register(REG_FREQ1, FREQ_BYTES[1])
    spi_write_register(REG_FREQ0, FREQ_BYTES[2])
    print(f"Frequency set to approx 433.92 MHz.")
    for reg, value in CONFIG_REGS:
        spi_write_register(reg, value)
    print("Configuration registers written.")

    print("Flushing RX FIFO...")
    spi_strobe(SIDLE); time.sleep(0.05)
    spi_strobe(SFRX); time.sleep(0.05)
    print("Entering RX mode...")
    spi_strobe(SRX); time.sleep(0.05)

    print("-" * 30)
    print("Listening for packets... Press Ctrl+C to stop.")
    print("-" * 30)

    packet_count = 0
    while True:
        rx_bytes = spi_read_register(STATUS_RXBYTES) & 0x7F
        if rx_bytes > 0:
            received_data = spi_read_burst(0x3F, rx_bytes) # RXFIFO address
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            hex_payload = bytes(received_data).hex().upper()
            packet_count += 1
            print(f"[{timestamp}] PKT {packet_count} ({rx_bytes} bytes): {hex_payload}")

            # Flush and re-enter RX
            spi_strobe(SIDLE); time.sleep(0.01)
            spi_strobe(SFRX); time.sleep(0.01)
            spi_strobe(SRX)
        time.sleep(0.05)

except Exception as e:
    print(f"\nAn error occurred: {e}", file=sys.stderr)
    cleanup(None, None)
