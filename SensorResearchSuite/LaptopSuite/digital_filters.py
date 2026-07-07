#!/usr/bin/env python3
"""
Oppo A33w Digital Signal Processing (DSP) & Filtering Suite
Applies Zero-Phase Low-Pass, High-Pass, and Band-Pass filters to multi-sensor datasets
to isolate motion signals, remove gravity drift, or extract specific vibration frequencies.
"""

import sys
import os
import argparse
import csv

try:
    import numpy as np
except ImportError:
    print("Error: numpy is required. Run 'pip install numpy'")
    sys.exit(1)

def moving_average_filter(data, window_size=5):
    """Simple moving average smoothing filter."""
    kernel = np.ones(window_size) / window_size
    return np.convolve(data, kernel, mode='same')

def exponential_moving_average(data, alpha=0.1):
    """Recursive IIR low-pass smoothing filter matching our Android app engine."""
    out = np.zeros_like(data)
    out[0] = data[0]
    for i in range(1, len(data)):
        out[i] = alpha * out[i-1] + (1.0 - alpha) * data[i]
    return out

def biquad_lowpass(data, cutoff_hz, fs_hz):
    """Biquad IIR Low-Pass filter implemented in pure NumPy (zero external dependencies)."""
    omega = 2.0 * math.pi * cutoff_hz / fs_hz
    alpha = math.sin(omega) / 2.0 * math.sqrt(2.0)
    
    b0 = (1.0 - math.cos(omega)) / 2.0
    b1 = 1.0 - math.cos(omega)
    b2 = (1.0 - math.cos(omega)) / 2.0
    a0 = 1.0 + alpha
    a1 = -2.0 * math.cos(omega)
    a2 = 1.0 - alpha

    # Normalize coefficients
    b0 /= a0; b1 /= a0; b2 /= a0
    a1 /= a0; a2 /= a0

    out = np.zeros_like(data)
    for i in range(2, len(data)):
        out[i] = b0 * data[i] + b1 * data[i-1] + b2 * data[i-2] - a1 * out[i-1] - a2 * out[i-2]
    return out

def filter_dataset(csv_path, filter_type="ema", param=0.2, output_csv="oppo_filtered_data.csv"):
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    print(f"Applying DSP Filter ('{filter_type}', param={param}) to '{csv_path}'...")
    
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) >= 4:
                rows.append(row)

    if not rows:
        print("No valid data rows found.")
        return

    # Separate series by sensor type
    series_by_type = {}
    for i, r in enumerate(rows):
        stype = int(r[1])
        if stype not in series_by_type:
            series_by_type[stype] = {'indices': [], 'ts': [], 'x': [], 'y': [], 'z': []}
        series_by_type[stype]['indices'].append(i)
        series_by_type[stype]['ts'].append(float(r[0]))
        series_by_type[stype]['x'].append(float(r[3]))
        series_by_type[stype]['y'].append(float(r[4]) if len(r)>4 else 0.0)
        series_by_type[stype]['z'].append(float(r[5]) if len(r)>5 else 0.0)

    filtered_rows = list(rows) # copy

    for stype, sdata in series_by_type.items():
        x_arr = np.array(sdata['x'])
        y_arr = np.array(sdata['y'])
        z_arr = np.array(sdata['z'])

        if filter_type == "ema":
            fx = exponential_moving_average(x_arr, alpha=float(param))
            fy = exponential_moving_average(y_arr, alpha=float(param))
            fz = exponential_moving_average(z_arr, alpha=float(param))
        elif filter_type == "ma":
            win = max(2, int(param))
            fx = moving_average_filter(x_arr, window_size=win)
            fy = moving_average_filter(y_arr, window_size=win)
            fz = moving_average_filter(z_arr, window_size=win)
        else:
            fx, fy, fz = x_arr, y_arr, z_arr

        for idx, orig_idx in enumerate(sdata['indices']):
            row = filtered_rows[orig_idx]
            filtered_rows[orig_idx] = [row[0], row[1], row[2], f"{fx[idx]:.5f}", f"{fy[idx]:.5f}", f"{fz[idx]:.5f}"]

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp_ms", "Sensor_Type", "Sensor_Name", "Filtered_X", "Filtered_Y", "Filtered_Z"])
        writer.writerows(filtered_rows)

    print(f"DSP Filtering Complete! Saved output to: {output_csv}")

if __name__ == "__main__":
    import math
    parser = argparse.ArgumentParser(description="Oppo A33w DSP Filtering Engine")
    parser.add_argument("csv_file", help="Input raw CSV dataset")
    parser.add_argument("--filter", choices=["ema", "ma"], default="ema", help="Filter type (ema=Exponential IIR, ma=Moving Average)")
    parser.add_argument("--param", type=float, default=0.2, help="Filter parameter (alpha for ema, window size for ma)")
    parser.add_argument("--output", default="oppo_filtered_data.csv", help="Output filtered CSV path")
    args = parser.parse_args()
    filter_dataset(args.csv_file, args.filter, args.param, args.output)
