#!/usr/bin/env python3

# nrf24_sniffer.py
# Listens for packets on a specified nRF24L01+ channel and prints them.
# Final version with specific error handling.

import time
import sys
import signal

# --- Configuration ---
CE_PIN = 22
CSN_PIN = 1 # Corresponds to SPI CE1 (Pi Pin 26)
RF_CHANNEL = 76
DATA_RATE_ENUM = None # Placeholder
PAYLOAD_SIZE = 32
PIPE_ADDRESS = b"\x01\x02\x03\x04\x01"

# --- Import RF24 Library ---
try:
    from pyrf24 import RF24, RF24_PA_LOW, RF24_1MBPS, RF24_2MBPS, RF24_250KBPS
    DATA_RATE_ENUM = RF24_1MBPS # Assign actual enum value
    print("DEBUG: pyRF24 library imported successfully.")
except ImportError:
    print("CRITICAL ERROR: pyRF24 library not found.", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"CRITICAL ERROR: Failed to import pyRF24 - {e}", file=sys.stderr)
    sys.exit(1)

# --- Global Radio Object ---
radio = None

# --- Signal Handler ---
def cleanup(signum, frame):
    global radio
    print("\nCaught signal, cleaning up...")
    if radio:
        try:
            print("Powering down radio.")
            # Check if radio object seems valid before calling methods
            if hasattr(radio, 'isPVariant') and radio.isPVariant():
                radio.powerDown()
        except Exception as final_e:
             print(f"Error during radio powerDown: {final_e}", file=sys.stderr)
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# --- Main Logic ---
try:
    print("Starting nRF24L01+ Sniffer...")

    # --- Step 1: Create RF24 object ---
    try:
        radio = RF24(CE_PIN, CSN_PIN)
        print("DEBUG: RF24 object created.")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to create RF24 object - {e}", file=sys.stderr)
        sys.exit(1)

    # --- Step 2: Initialize Radio ---
    try:
        if not radio.begin():
            print("CRITICAL ERROR: radio.begin() failed. Check wiring/power.", file=sys.stderr)
            sys.exit(1)
        print("DEBUG: radio.begin() successful.")
    except Exception as e:
         print(f"CRITICAL ERROR: Exception during radio.begin() - {e}", file=sys.stderr)
         sys.exit(1)

    # --- Configure Radio for Sniffing ---
    print("DEBUG: Configuring radio...")
    radio.setPALevel(RF24_PA_LOW)
    radio.setDataRate(DATA_RATE_ENUM)
    radio.setChannel(RF_CHANNEL)
    radio.setAutoAck(False)
    radio.disableCRC()
    radio.setPayloadSize(PAYLOAD_SIZE)
    radio.openReadingPipe(1, PIPE_ADDRESS)
    radio.startListening()
    print("DEBUG: Radio configured.")

    # --- Ready ---
    print(f"Listening started on Channel {RF_CHANNEL}, Data Rate: {DATA_RATE_ENUM.name if DATA_RATE_ENUM else 'Unknown'}")
    print(f"Payload Size: {PAYLOAD_SIZE} bytes")
    print("Press Ctrl+C to stop.")
    print("-" * 30)

    # --- Main Sniffing Loop ---
    while True:
        if radio.available():
            payload = radio.read(PAYLOAD_SIZE)
            payload_len = len(payload)
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            hex_payload = payload.hex().upper()
            print(f"[{timestamp}] RX ({payload_len} bytes): {hex_payload}")
        time.sleep(0.01)

except KeyboardInterrupt:
    # Cleanup is handled by the signal handler
    pass
except Exception as e:
    print(f"\nAn error occurred during setup or loop: {e}", file=sys.stderr)
    cleanup(None, None) # Attempt cleanup
