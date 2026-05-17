#!/usr/bin/env python3

# esp32_logger.py
# Version 3: Handles RFID, NFC, BTClassic, and BLE JSON messages.
# Listens on Pi's GPIO serial port /dev/ttyS0

import serial
import json
import time
import sqlite3
import csv
import os
from pathlib import Path

# --- Configuration ---
SERIAL_PORT = '/dev/ttyS0' # Use Pi's GPIO serial
BAUD_RATE = 115200
PROJECT_DIR = Path.home() / "proxnet"
LOG_DIR = PROJECT_DIR / "logs"
DB_FILE = LOG_DIR / "proxnet_log.db"
CSV_FILE = LOG_DIR / "proxnet_log.csv"

# --- Ensure log directory exists ---
LOG_DIR.mkdir(parents=True, exist_ok=True)

# --- Database Setup (Updated Schema) ---
def setup_database():
    """Creates/Updates the SQLite table."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Add new columns if they don't exist (handles upgrading from old schema)
    try:
        cursor.execute("ALTER TABLE scans ADD COLUMN mac TEXT")
    except sqlite3.OperationalError: pass # Column likely already exists
    try:
        cursor.execute("ALTER TABLE scans ADD COLUMN name TEXT")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE scans ADD COLUMN rssi INTEGER")
    except sqlite3.OperationalError: pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            timestamp TEXT NOT NULL,
            module_type TEXT,
            protocol TEXT,
            uid TEXT,
            uid_len INTEGER,
            mac TEXT,       -- Added for BT/BLE
            name TEXT,      -- Added for BT/BLE
            rssi INTEGER    -- Added for BT/BLE
        )
    ''')
    conn.commit()
    conn.close()
    print(f"Database initialized/verified at: {DB_FILE}")

def log_to_db(timestamp, data):
    """Logs scan data (RFID/NFC/BT/BLE) to SQLite."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO scans (timestamp, module_type, protocol, uid, uid_len, mac, name, rssi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            data.get('type', 'Unknown'),
            data.get('protocol', None),
            data.get('uid', None),
            data.get('uid_len', None),
            data.get('mac', None),
            data.get('name', None),
            data.get('rssi', None)
        ))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"[{timestamp}] DB_ERROR: Failed to log to SQLite - {e}")

# --- CSV Setup (Updated Headers) ---
CSV_FIELDNAMES = ['timestamp', 'module_type', 'protocol', 'uid', 'uid_len', 'mac', 'name', 'rssi']

def log_to_csv(timestamp, data):
    """Appends scan data to the CSV file."""
    file_exists = CSV_FILE.is_file()
    try:
        with open(CSV_FILE, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDNAMES)

            if not file_exists or os.path.getsize(CSV_FILE) == 0:
                writer.writeheader() # Write header if file is new or empty

            row_data = {
                'timestamp': timestamp,
                'module_type': data.get('type', 'Unknown'),
                'protocol': data.get('protocol', ''),
                'uid': data.get('uid', ''),
                'uid_len': data.get('uid_len', ''),
                'mac': data.get('mac', ''),
                'name': data.get('name', ''),
                'rssi': data.get('rssi', '')
            }
            writer.writerow(row_data)
    except IOError as e:
        print(f"[{timestamp}] CSV_ERROR: Failed to log to CSV - {e}")

# --- Main Logger Function ---
def start_logger():
    print("Starting ProxNet ESP32 Logger (v3 - UART)...")
    setup_database() # Initialize/Update DB
    print(f"CSV logging to: {CSV_FILE}")
    print(f"Connecting to {SERIAL_PORT} at {BAUD_RATE} baud.")
    ser = None

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print("Waiting for ESP32 to initialize...")
        time.sleep(2) # Give ESP32 time to boot and send READY message
        ser.reset_input_buffer()
        print("Connection successful. Waiting for JSON data...")
        print("="*30)

        while True:
            if ser.in_waiting > 0:
                line = ""
                try:
                    line = ser.readline().decode('utf-8').rstrip()
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

                    if line:
                        data = json.loads(line)
                        print(f"[{timestamp}] LOG: {data}")

                        # Log scan data, skip status/error messages
                        if 'status' not in data and 'error' not in data:
                            log_to_db(timestamp, data)
                            log_to_csv(timestamp, data)

                except json.JSONDecodeError:
                    if line: print(f"[{timestamp}] RAW: {line}")
                except UnicodeDecodeError:
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[{timestamp}] ERROR: Garbled data received")
                except Exception as e:
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[{timestamp}] ERROR: Unexpected error - {e}")

            time.sleep(0.05)

    except serial.SerialException as e:
        print(f"\nCRITICAL ERROR connecting to {SERIAL_PORT}: {e}")
        print("Is the ESP32 wired correctly (TX2->Pi RXD, GND->GND)?")
        print("Did you enable serial port in raspi-config (disable console login)?")
    except KeyboardInterrupt:
        print("\nLogger stopped by user.")
    except Exception as e:
         print(f"\nCRITICAL UNEXPECTED ERROR: {e}")
    finally:
        if ser and ser.is_open:
            ser.close()
            print(f"Port {SERIAL_PORT} closed.")

if __name__ == "__main__":
    start_logger()
