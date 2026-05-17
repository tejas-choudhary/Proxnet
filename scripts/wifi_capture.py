#!/usr/bin/env python3

# wifi_capture.py
# Version 2: Uses tcpdump instead of tshark.

import subprocess
import signal
import time
import sys
import os
from pathlib import Path

# --- Configuration ---
MONITOR_INTERFACE = "wlan1" # Make sure this matches your monitor interface
PCAP_DIR = Path.home() / "proxnet" / "pcaps"
TCPDUMP_PATH = "/usr/bin/tcpdump" # Verify path with 'which tcpdump'

# Ensure pcap directory exists
PCAP_DIR.mkdir(parents=True, exist_ok=True)

# Global variable for the tcpdump process
tcpdump_process = None

# --- Signal Handler ---
def cleanup(signum, frame):
    global tcpdump_process
    print("\nCaught signal, stopping capture...")
    if tcpdump_process and tcpdump_process.poll() is None:
        try:
            os.killpg(os.getpgid(tcpdump_process.pid), signal.SIGTERM)
            time.sleep(1)
            if tcpdump_process.poll() is None:
                 os.killpg(os.getpgid(tcpdump_process.pid), signal.SIGKILL)
                 print("tcpdump killed forcefully.")
        except ProcessLookupError:
             print("tcpdump process already stopped.")
        except Exception as e:
            print(f"Error stopping tcpdump: {e}")
        print("Capture stopped.")
        tcpdump_process = None
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# --- Main Capture Function ---
def start_capture():
    global tcpdump_process
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    pcap_file = PCAP_DIR / f"wifi_capture_{timestamp}.pcap"

    if not Path(TCPDUMP_PATH).is_file():
        print(f"Error: tcpdump not found at {TCPDUMP_PATH}", file=sys.stderr)
        sys.exit(1)

    if not Path(f"/sys/class/net/{MONITOR_INTERFACE}").exists():
         print(f"Error: Monitor interface '{MONITOR_INTERFACE}' not found.", file=sys.stderr)
         sys.exit(1)

    command = [
        TCPDUMP_PATH, # Run directly as script will be sudo'd
        "-i", MONITOR_INTERFACE,
        "-I",
        "-w", str(pcap_file),
        "-U",
    ]

    print(f"Starting Wi-Fi capture on {MONITOR_INTERFACE} using tcpdump...")
    print(f"Saving packets to: {pcap_file}")
    print("Command:", " ".join(command))
    print("Press Ctrl+C to stop.")
    print("-" * 30)

    try:
        tcpdump_process = subprocess.Popen(command, preexec_fn=os.setsid)
        tcpdump_process.wait()
    except FileNotFoundError:
         print(f"Error: '{TCPDUMP_PATH}' command not found.", file=sys.stderr)
    except PermissionError:
         print(f"Error: Permission denied running tcpdump.", file=sys.stderr)
         print("Try running this script with 'sudo'.", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred while running tcpdump: {e}", file=sys.stderr)
    finally:
        if tcpdump_process and tcpdump_process.poll() is None:
            cleanup(None, None)

if __name__ == "__main__":
    # Script now expects to be run with sudo
    if os.geteuid() != 0:
        print("Error: This script needs root privileges to run tcpdump.", file=sys.stderr)
        print("Please run using: sudo python3 wifi_capture.py", file=sys.stderr)
        sys.exit(1)
    start_capture()
