#!/usr/bin/env python3

# web_ui.py
# Milestone 5, Action 7 (Final)
# Disables CC1101 functionality due to hardware fault.

import subprocess
import signal
import time
import sqlite3
import os
# NOTE: spidev is no longer needed here as CC1101 check is removed
from pathlib import Path
from flask import Flask, render_template_string, redirect, url_for, flash, request

# --- Configuration ---
HOST_IP = '0.0.0.0'
HOST_PORT = 5000
PROJECT_DIR = Path.home() / "proxnet"
LOG_DIR = PROJECT_DIR / "logs"
DB_FILE = LOG_DIR / "proxnet_log.db"
LOGGER_SCRIPT = PROJECT_DIR / "scripts" / "esp32_logger.py"
NRF24_SNIFFER_SCRIPT = PROJECT_DIR / "scripts" / "nrf24_sniffer.py"
# CC1101_SNIFFER_SCRIPT path is no longer needed
VENV_PYTHON = PROJECT_DIR / "venv" / "bin" / "python3"

# --- Global process trackers ---
logger_process = None
nrf24_sniffer_process = None
# cc1101_sniffer_process is no longer needed

# --- Create Flask App ---
app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Database Setup ---
def setup_database():
    if not DB_FILE.is_file():
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Database file not found, creating at: {DB_FILE}")
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scans (
                timestamp TEXT NOT NULL, module_type TEXT, protocol TEXT,
                uid TEXT, uid_len INTEGER, mac TEXT, name TEXT, rssi INTEGER
            )
        ''')
        conn.commit()
        conn.close()
        print(f"Database initialized/verified at: {DB_FILE}")
    except sqlite3.Error as e:
        print(f"DB_ERROR: Failed to initialize database - {e}")

# --- Helper Functions ---
def is_logger_running():
    global logger_process
    return logger_process is not None and logger_process.poll() is None

def get_latest_scans(limit=15):
    scans = []
    if not DB_FILE.is_file():
        print(f"DB_WARN: Database file {DB_FILE} not found.")
        return scans
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scans ORDER BY timestamp DESC LIMIT ?", (limit,))
        scans = cursor.fetchall()
        conn.close()
    except sqlite3.Error as e:
        print(f"DB_ERROR: Failed to fetch scans - {e}")
        flash(f"Error reading database: {e}", "error")
    return scans

# --- nRF24 Sniffer Control Helpers ---
def is_nrf24_sniffer_running():
    global nrf24_sniffer_process
    if nrf24_sniffer_process:
         poll_result = nrf24_sniffer_process.poll()
         is_running = poll_result is None
         if not is_running: nrf24_sniffer_process = None
    else: is_running = False
    return is_running

# --- Hardware Status Check Functions (REMOVED CC1101) ---
# NOTE: check_cc1101_connection function is REMOVED

# --- HTML Template (Removed CC1101 Section) ---
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ProxNet Control</title>
    <style>
        body { font-family: sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
        .container { background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 900px; margin: auto; }
        h1, h2 { color: #333; border-bottom: 1px solid #eee; padding-bottom: 10px; }
        button { padding: 10px 15px; margin: 5px 10px 5px 0; border: none; border-radius: 4px; cursor: pointer; font-size: 1em; }
        button:disabled { background-color: #ccc; cursor: not-allowed; }
        .start-btn { background-color: #28a745; color: white; }
        .stop-btn { background-color: #dc3545; color: white; }
        .status { margin-bottom: 15px; font-weight: bold; font-size: 1.1em; }
        .status.running { color: green; }
        .status.stopped { color: red; }
        .hw-status { margin-left: 10px; font-weight: normal; font-size: 0.9em; padding: 2px 6px; border-radius: 4px; color: white; }
        .hw-status.ok { background-color: #28a745; } /* Green */
        .hw-status.error { background-color: #dc3545; } /* Red */
        .hw-status.warn { background-color: #ffc107; color: #333; } /* Yellow */
        .hw-status.disabled { background-color: #6c757d; } /* Grey */
        table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 0.9em; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #e9ecef; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .flash { padding: 10px; margin-bottom: 15px; border-radius: 4px; border: 1px solid transparent; }
        .flash.error { background-color: #f8d7da; color: #721c24; border-color: #f5c6cb; }
        .flash.success { background-color: #d4edda; color: #155724; border-color: #c3e6cb; }
    </style>
    <meta http-equiv="refresh" content="10">
</head>
<body>
    <div class="container">
        <h1>ProxNet - Wireless IoT Security Testbed</h1>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <hr>
        <h2>Hardware Status</h2>
         <p>ESP32 Scanner Link: <span class="hw-status {{ 'ok' if esp32_status == 'Ready' else 'error' }}">{{ esp32_status }}</span></p>
         <p>nRF24L01+ (2.4GHz): <span class="hw-status {{ 'ok' if nrf24_status == 'Ready (Check Manually)' else 'error' }}">{{ nrf24_status }}</span></p>
         <p>CC1101 (Sub-GHz): <span class="hw-status disabled">{{ cc1101_status }}</span></p>
        <hr>

        <h2>ESP32 RFID/NFC/BT/BLE Logger Control</h2>
        <div class="status {{ 'running' if logger_running else 'stopped' }}">Status: {{ 'Running' if logger_running else 'Stopped' }}</div>
        <div>
            <form action="{{ url_for('start_logger') }}" method="post" style="display: inline;"><button type="submit" class="start-btn" {{ 'disabled' if logger_running else '' }}>Start Logger</button></form>
            <form action="{{ url_for('stop_logger') }}" method="post" style="display: inline;"><button type="submit" class="stop-btn" {{ '' if logger_running else 'disabled' }}>Stop Logger</button></form>
        </div>
        <hr>

        <h2>nRF24L01+ (2.4GHz) Sniffer Control</h2>
        <div class="status {{ 'running' if nrf24_sniffer_running else 'stopped' }}">Status: {{ 'Running' if nrf24_sniffer_running else 'Stopped' }}</div>
         {% if nrf24_status == 'Ready (Check Manually)' %}
         <div>
            <form action="{{ url_for('start_nrf24_sniffer') }}" method="post" style="display: inline;"><button type="submit" class="start-btn" {{ 'disabled' if nrf24_sniffer_running else '' }}>Start Sniffer</button></form>
            <form action="{{ url_for('stop_nrf24_sniffer') }}" method="post" style="display: inline;"><button type="submit" class="stop-btn" {{ '' if nrf24_sniffer_running else 'disabled' }}>Stop Sniffer</button></form>
         </div>
         {% else %}
         <p style="color: grey;">Module status indicates an issue. Controls disabled.</p>
         {% endif %}
        <hr>

        <h2>Latest Scans (Last {{ scans|length }})</h2>
        {% if scans %}
        <table>
            <thead><tr><th>Timestamp</th><th>Module</th><th>Protocol</th><th>UID</th><th>UID Len</th><th>MAC</th><th>Name</th><th>RSSI</th></tr></thead>
            <tbody>
                {% for scan in scans %}
                <tr>
                    <td>{{ scan['timestamp'] }}</td><td>{{ scan['module_type'] }}</td>
                    <td>{{ scan['protocol'] if scan['protocol'] else 'N/A' }}</td>
                    <td>{{ scan['uid'] if scan['uid'] else 'N/A' }}</td>
                    <td>{{ scan['uid_len'] if scan['uid_len'] is not none else 'N/A' }}</td>
                    <td>{{ scan['mac'] if scan['mac'] else 'N/A' }}</td>
                    <td>{{ scan['name'] if scan['name'] else 'N/A' }}</td>
                    <td>{{ scan['rssi'] if scan['rssi'] is not none else 'N/A' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p>No scans found in the database yet, or the database file cannot be read.</p>
        {% endif %}
    </div>
</body>
</html>
"""

# --- Routes ---
@app.route('/')
def index():
    running = is_logger_running()
    nrf24_running = is_nrf24_sniffer_running()
    latest_scans = get_latest_scans()
    esp32_dev_path = Path("/dev/ttyS0") # Using UART now
    esp32_status_check = "Ready" if esp32_dev_path.exists() else "Not Found" # Basic check
    nrf24_status_check = "Ready (Check Manually)" # Static status
    cc1101_status_check = "Disabled (Faulty?)" # Static status
    return render_template_string(
        HTML_TEMPLATE,
        logger_running=running,
        nrf24_sniffer_running=nrf24_running,
        scans=latest_scans,
        esp32_status=esp32_status_check,
        nrf24_status=nrf24_status_check,
        cc1101_status=cc1101_status_check
    )

# --- ESP32 Logger Routes ---
@app.route('/start_logger', methods=['POST'])
def start_logger():
    global logger_process
    if is_logger_running(): flash("Logger is already running.", "error")
    else:
        try:
            setup_database()
            logger_process = subprocess.Popen([str(VENV_PYTHON), str(LOGGER_SCRIPT)])
            flash("Logger started successfully!", "success"); print("Logger process started.")
            time.sleep(1)
        except Exception as e:
            flash(f"Error starting logger: {e}", "error"); print(f"Error starting logger: {e}")
            logger_process = None
    return redirect(url_for('index'))

@app.route('/stop_logger', methods=['POST'])
def stop_logger():
    global logger_process
    if is_logger_running():
        try:
            logger_process.terminate()
            try: logger_process.wait(timeout=5)
            except subprocess.TimeoutExpired: logger_process.kill(); print("Logger process killed.")
            flash("Logger stopped successfully!", "success"); print("Logger process stopped.")
        except Exception as e:
            flash(f"Error stopping logger: {e}", "error"); print(f"Error stopping logger: {e}")
        finally: logger_process = None
    else: flash("Logger is not running.", "error")
    return redirect(url_for('index'))

# --- nRF24 Sniffer Routes ---
@app.route('/start_nrf24_sniffer', methods=['POST'])
def start_nrf24_sniffer():
    global nrf24_sniffer_process
    if is_nrf24_sniffer_running(): flash("nRF24 Sniffer is already running.", "error")
    elif not NRF24_SNIFFER_SCRIPT.is_file(): flash(f"Error: Script not found {NRF24_SNIFFER_SCRIPT}", "error")
    else:
        try:
            log_file = LOG_DIR / "nrf24_sniffer.log"
            with open(log_file, 'w') as f: f.write(f"Starting nRF24 Sniffer at {time.strftime('%Y-%m-%d %H:%M:%S')}...\n")
            nrf24_sniffer_process = subprocess.Popen([str(VENV_PYTHON), str(NRF24_SNIFFER_SCRIPT)], stdout=open(log_file, 'a'), stderr=subprocess.STDOUT)
            flash("nRF24 Sniffer started! Outputting to log file.", "success"); print("nRF24 Sniffer process started.")
        except Exception as e:
            flash(f"Error starting nRF24 Sniffer: {e}", "error"); print(f"Error starting nRF24 Sniffer: {e}")
            nrf24_sniffer_process = None
    return redirect(url_for('index'))

@app.route('/stop_nrf24_sniffer', methods=['POST'])
def stop_nrf24_sniffer():
    global nrf24_sniffer_process
    if is_nrf24_sniffer_running():
        try:
            nrf24_sniffer_process.terminate()
            try: nrf24_sniffer_process.wait(timeout=5)
            except subprocess.TimeoutExpired: nrf24_sniffer_process.kill(); print("nRF24 Sniffer killed.")
            flash("nRF24 Sniffer stopped successfully!", "success"); print("nRF24 Sniffer process stopped.")
        except Exception as e:
            flash(f"Error stopping nRF24 Sniffer: {e}", "error"); print(f"Error stopping nRF24 Sniffer: {e}")
        finally: nrf24_sniffer_process = None
    else: flash("nRF24 Sniffer is not running.", "error")
    return redirect(url_for('index'))

# --- REMOVED CC1101 Sniffer Routes ---

# --- Main Execution ---
if __name__ == '__main__':
    print(f"Starting ProxNet Web UI...")
    setup_database()
    print(f"Using database: {DB_FILE}")
    print(f"Controlling script: {LOGGER_SCRIPT}")
    print(f"nRF24 sniffer script: {NRF24_SNIFFER_SCRIPT}")
    # Removed CC1101 script path printout
    print(f"Access it at: http://<Your_Pi_IP_Address>:{HOST_PORT}")
    print(f"Or from the Pi itself: http://localhost:{HOST_PORT}")
    print("Press Ctrl+C to stop.")
    app.run(host=HOST_IP, port=HOST_PORT, debug=False)
