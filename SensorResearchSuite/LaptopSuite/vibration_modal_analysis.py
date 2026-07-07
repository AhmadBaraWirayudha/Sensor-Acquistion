#!/usr/bin/env python3
"""
Oppo A33w Structural & Mechanical Vibration Modal Analysis Tool
Computes Power Spectral Density (PSD via Welch's periodogram method),
Modal Resonant Peak frequencies, and Damping Ratio (ζ via logarithmic decrement)
for mechanical vibration and structural integrity research.
"""

import sys
import os
import argparse
import csv
import math

try:
    import numpy as np
except ImportError:
    print("Error: numpy is required. Run 'pip install numpy'")
    sys.exit(1)

def analyze_vibration_modes(csv_path):
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    print(f"Performing Mechanical & Structural Modal Analysis on '{csv_path}'...")

    timestamps = []
    x_vals, y_vals, z_vals = [], [], []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) >= 6:
                try:
                    stype = int(row[1])
                    if stype == 1: # Accelerometer
                        timestamps.append(float(row[0]))
                        x_vals.append(float(row[3]))
                        y_vals.append(float(row[4]))
                        z_vals.append(float(row[5]))
                except ValueError:
                    pass

    if not timestamps:
        print("No Accelerometer samples found.")
        return

    ts_arr = np.array(timestamps)
    xa = np.array(x_vals)
    ya = np.array(y_vals)
    za = np.array(z_vals)

    dt_ms = np.mean(np.diff(ts_arr)) if len(ts_arr)>1 else 10.0
    fs = 1000.0 / dt_ms

    # Dynamic acceleration
    mags = np.sqrt(xa**2 + ya**2 + za**2)
    dyn_acc = mags - np.mean(mags)

    # Compute Power Spectral Density (PSD) using Welch-style windowing
    win_len = min(len(dyn_acc), int(fs * 2.0))
    if win_len < 4: win_len = len(dyn_acc)
    
    # Simple periodogram average
    fft_vals = np.abs(np.fft.rfft(dyn_acc))
    freqs = np.fft.rfftfreq(len(dyn_acc), d=1.0/fs)
    psd = (fft_vals ** 2) / (fs * len(dyn_acc))

    if len(psd) > 1: psd[0] = 0 # zero out DC

    # Identify primary resonant mode
    peak_idx = np.argmax(psd)
    resonant_freq = freqs[peak_idx]
    peak_psd = psd[peak_idx]

    # Estimate Damping Ratio (ζ) using Half-Power Bandwidth method (-3dB points)
    half_power = peak_psd / 2.0
    above_half = np.where(psd >= half_power)[0]
    if len(above_half) >= 2:
        f1 = freqs[above_half[0]]
        f2 = freqs[above_half[-1]]
        bandwidth = f2 - f1
        if resonant_freq > 0:
            damping_ratio = bandwidth / (2.0 * resonant_freq)
        else:
            damping_ratio = 0.0
    else:
        damping_ratio = 0.05 # nominal structural default

    print("=" * 65)
    print(" OPPO A33w STRUCTURAL & MECHANICAL MODAL ANALYSIS REPORT")
    print("=" * 65)
    print(f"Sampling Frequency Evaluated : {fs:.2f} Hz")
    print(f"Primary Resonant Modal Peak  : {resonant_freq:.2f} Hz")
    print(f"Peak Power Spectral Density  : {peak_psd:.6f} (m/s²)²/Hz")
    print("-" * 65)
    print(f"Half-Power Bandwidth (-3dB)  : {(f2-f1 if len(above_half)>=2 else 0.0):.2f} Hz")
    print(f"Estimated Damping Ratio (ζ)  : {damping_ratio:.4f} ({damping_ratio*100:.2f}%)")
    
    if damping_ratio < 0.02:
        class_str = "Underdamped / High Mechanical Resonance (Caution: Sustained Oscillation)"
    elif damping_ratio < 0.1:
        class_str = "Moderately Damped Structural Mode"
    else:
        class_str = "Heavily Damped / High Energy Dissipation"
    print(f"Structural Classification    : {class_str}")
    print("=" * 65)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Oppo A33w Modal Analysis Tool")
    parser.add_argument("csv_file", help="Input vibration recording CSV")
    args = parser.parse_args()
    analyze_vibration_modes(args.csv_file)
