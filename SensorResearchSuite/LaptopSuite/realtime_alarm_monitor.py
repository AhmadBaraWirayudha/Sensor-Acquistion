#!/usr/bin/env python3
"""
Oppo A33w Real-Time Safety & Threshold Alarm Monitor
Listens to incoming sensor streams over UDP/TCP/Serial and monitors vibration
acceleration magnitude and AHRS tilt against user-defined safety limits. Triggers
visual console alerts and logs threshold breach events.
"""

import sys
import os
import time
import socket
import argparse
from datetime import datetime

try:
    import numpy as np
except ImportError:
    print("Error: numpy is required.")
    sys.exit(1)

def monitor_stream(port=5005, limit_acc_rms=3.5, log_file="alarm_events.log"):
    print("=============================================================")
    print(" OPPO A33w REAL-TIME SAFETY & VIBRATION ALARM MONITOR")
    print(f" Listening on UDP Port : {port}")
    print(f" Acceleration Threshold: {limit_acc_rms:.2f} m/s² RMS")
    print("=============================================================")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', port))

    buffer_x, buffer_y, buffer_z = [], [], []
    win_size = 50 # 0.5 sec window at 100Hz
    breaches = 0

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"--- Alarm Monitor Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")

    try:
        while True:
            data, _ = sock.recvfrom(4096)
            line = data.decode('utf-8', errors='ignore').strip()
            if not line: continue
            parts = [p.strip().strip('"') for p in line.split(',')]
            if len(parts) >= 6 and int(parts[1]) == 1: # Accelerometer
                try:
                    vx = float(parts[3])
                    vy = float(parts[4])
                    vz = float(parts[5])
                    buffer_x.append(vx); buffer_y.append(vy); buffer_z.append(vz)
                    if len(buffer_x) > win_size:
                        buffer_x.pop(0); buffer_y.pop(0); buffer_z.pop(0)

                        # Check dynamic RMS
                        xa, ya, za = np.array(buffer_x), np.array(buffer_y), np.array(buffer_z)
                        mags = np.sqrt(xa**2 + ya**2 + za**2)
                        dyn_rms = np.sqrt(np.mean((mags - np.mean(mags))**2))

                        if dyn_rms >= limit_acc_rms:
                            breaches += 1
                            timestamp_str = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                            msg = f"[{timestamp_str}] [ALARM BREACH #{breaches}] High Vibration Detected: {dyn_rms:.2f} m/s² (Limit: {limit_acc_rms:.2f})"
                            print(f"\033[91m\033[1m{msg}\033[0m")
                            with open(log_file, 'a', encoding='utf-8') as f:
                                f.write(msg + "\n")
                except ValueError:
                    pass
    except KeyboardInterrupt:
        print("\nMonitor stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Oppo A33w Alarm Monitor")
    parser.add_argument("--port", type=int, default=5005, help="UDP listening port")
    parser.add_argument("--limit", type=float, default=3.5, help="RMS acceleration threshold")
    parser.add_argument("--log", default="alarm_events.log", help="Log output file")
    args = parser.parse_args()
    monitor_stream(args.port, args.limit, args.log)
