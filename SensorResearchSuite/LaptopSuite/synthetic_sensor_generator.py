#!/usr/bin/env python3
"""
Oppo A33w Synthetic IMU Dataset Generator
Generates realistic multi-sensor CSV datasets simulating the MediaTek MT6582 hardware
under various physical motion profiles (Stationary, Walking, Running, 3D Rotation, Tremor)
for laptop algorithm development and pipeline benchmarking.
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

def generate_synthetic_dataset(profile="walking", duration_sec=10.0, rate_hz=100.0, output_csv="synthetic_oppo_dataset.csv"):
    print(f"Generating synthetic dataset Profile='{profile}' ({duration_sec}s at {rate_hz} Hz)...")
    
    n_samples = int(duration_sec * rate_hz)
    dt_ms = 1000.0 / rate_hz
    start_ts = 1700000000000.0 # arbitrary epoch timestamp

    rows = [["Timestamp_ms", "Sensor_Type", "Sensor_Name", "Value_X", "Value_Y", "Value_Z"]]

    t = np.linspace(0, duration_sec, n_samples)

    if profile == "stationary":
        # Flat on desk with slight Gaussian sensor noise
        acc_x = np.random.normal(0.0, 0.05, n_samples)
        acc_y = np.random.normal(9.80665, 0.05, n_samples)
        acc_z = np.random.normal(0.1, 0.05, n_samples)
        
        gyro_x = np.random.normal(0.0, 0.005, n_samples)
        gyro_y = np.random.normal(0.0, 0.005, n_samples)
        gyro_z = np.random.normal(0.0, 0.005, n_samples)
        
        mag_x = np.random.normal(20.0, 0.2, n_samples)
        mag_y = np.random.normal(-15.0, 0.2, n_samples)
        mag_z = np.random.normal(35.0, 0.2, n_samples)

    elif profile == "walking":
        # 1.8 Hz step cadence with harmonic overtones
        step_freq = 1.8
        acc_x = 1.2 * np.sin(2 * np.pi * step_freq * t) + 0.3 * np.sin(2 * np.pi * step_freq * 2 * t) + np.random.normal(0, 0.1, n_samples)
        acc_y = 9.80665 + 2.5 * np.cos(2 * np.pi * step_freq * t) + np.random.normal(0, 0.1, n_samples)
        acc_z = 0.8 * np.sin(2 * np.pi * step_freq * t + 0.5) + np.random.normal(0, 0.1, n_samples)

        gyro_x = 0.8 * np.cos(2 * np.pi * step_freq * t) + np.random.normal(0, 0.02, n_samples)
        gyro_y = 0.4 * np.sin(2 * np.pi * step_freq * t) + np.random.normal(0, 0.02, n_samples)
        gyro_z = 0.6 * np.sin(2 * np.pi * step_freq * t * 0.5) + np.random.normal(0, 0.02, n_samples)

        mag_x = 20.0 + 3.0 * np.sin(2 * np.pi * 0.2 * t) + np.random.normal(0, 0.3, n_samples)
        mag_y = -15.0 + 3.0 * np.cos(2 * np.pi * 0.2 * t) + np.random.normal(0, 0.3, n_samples)
        mag_z = 35.0 + np.random.normal(0, 0.3, n_samples)

    elif profile == "running":
        # 2.8 Hz high-impact step cadence
        step_freq = 2.8
        acc_x = 3.5 * np.sin(2 * np.pi * step_freq * t) + np.random.normal(0, 0.3, n_samples)
        acc_y = 9.80665 + 6.0 * np.cos(2 * np.pi * step_freq * t) + np.random.normal(0, 0.3, n_samples)
        acc_z = 2.5 * np.sin(2 * np.pi * step_freq * t + 0.8) + np.random.normal(0, 0.3, n_samples)

        gyro_x = 2.2 * np.cos(2 * np.pi * step_freq * t) + np.random.normal(0, 0.05, n_samples)
        gyro_y = 1.5 * np.sin(2 * np.pi * step_freq * t) + np.random.normal(0, 0.05, n_samples)
        gyro_z = 1.8 * np.sin(2 * np.pi * step_freq * t) + np.random.normal(0, 0.05, n_samples)

        mag_x = 20.0 + 5.0 * np.sin(2 * np.pi * 0.5 * t) + np.random.normal(0, 0.5, n_samples)
        mag_y = -15.0 + 5.0 * np.cos(2 * np.pi * 0.5 * t) + np.random.normal(0, 0.5, n_samples)
        mag_z = 35.0 + np.random.normal(0, 0.5, n_samples)

    elif profile == "rotation_3d":
        # Phone spinning 360 degrees in all axes
        rot_speed = 0.5 # 0.5 Hz full spin
        acc_x = 9.80665 * np.sin(2 * np.pi * rot_speed * t) + np.random.normal(0, 0.05, n_samples)
        acc_y = 9.80665 * np.cos(2 * np.pi * rot_speed * t) * np.cos(2 * np.pi * rot_speed * 0.5 * t) + np.random.normal(0, 0.05, n_samples)
        acc_z = 9.80665 * np.cos(2 * np.pi * rot_speed * t) * np.sin(2 * np.pi * rot_speed * 0.5 * t) + np.random.normal(0, 0.05, n_samples)

        gyro_x = np.full(n_samples, 2 * np.pi * rot_speed) + np.random.normal(0, 0.01, n_samples)
        gyro_y = np.full(n_samples, 2 * np.pi * rot_speed * 0.5) + np.random.normal(0, 0.01, n_samples)
        gyro_z = np.full(n_samples, 2 * np.pi * rot_speed * 0.25) + np.random.normal(0, 0.01, n_samples)

        mag_x = 40.0 * np.sin(2 * np.pi * rot_speed * t) + np.random.normal(0, 0.2, n_samples)
        mag_y = 40.0 * np.cos(2 * np.pi * rot_speed * t) + np.random.normal(0, 0.2, n_samples)
        mag_z = 20.0 * np.sin(2 * np.pi * rot_speed * 0.5 * t) + np.random.normal(0, 0.2, n_samples)

    elif profile == "tremor":
        # 6.5 Hz Parkinsonian / essential tremor profile
        tremor_freq = 6.5
        acc_x = 0.8 * np.sin(2 * np.pi * tremor_freq * t) + np.random.normal(0, 0.05, n_samples)
        acc_y = 9.80665 + 0.8 * np.cos(2 * np.pi * tremor_freq * t) + np.random.normal(0, 0.05, n_samples)
        acc_z = 0.5 * np.sin(2 * np.pi * tremor_freq * t + 1.2) + np.random.normal(0, 0.05, n_samples)

        gyro_x = 0.6 * np.cos(2 * np.pi * tremor_freq * t) + np.random.normal(0, 0.01, n_samples)
        gyro_y = 0.6 * np.sin(2 * np.pi * tremor_freq * t) + np.random.normal(0, 0.01, n_samples)
        gyro_z = 0.3 * np.sin(2 * np.pi * tremor_freq * t) + np.random.normal(0, 0.01, n_samples)

        mag_x = np.full(n_samples, 20.0) + np.random.normal(0, 0.2, n_samples)
        mag_y = np.full(n_samples, -15.0) + np.random.normal(0, 0.2, n_samples)
        mag_z = np.full(n_samples, 35.0) + np.random.normal(0, 0.2, n_samples)

    else:
        acc_x, acc_y, acc_z = np.zeros(n_samples), np.full(n_samples, 9.8), np.zeros(n_samples)
        gyro_x, gyro_y, gyro_z = np.zeros(n_samples), np.zeros(n_samples), np.zeros(n_samples)
        mag_x, mag_y, mag_z = np.full(n_samples, 20.0), np.full(n_samples, -15.0), np.full(n_samples, 35.0)

    # Interleave sensor packets simulating realistic multi-sensor polling
    for i in range(n_samples):
        ts = start_ts + i * dt_ms
        # Write Accelerometer (Type 1)
        rows.append([f"{ts:.1f}", 1, "MTK Accelerometer", f"{acc_x[i]:.5f}", f"{acc_y[i]:.5f}", f"{acc_z[i]:.5f}"])
        # Write Gyroscope (Type 4)
        rows.append([f"{ts+0.2:.1f}", 4, "MTK Gyroscope", f"{gyro_x[i]:.5f}", f"{gyro_y[i]:.5f}", f"{gyro_z[i]:.5f}"])
        # Write Magnetometer at 1/5th rate (20 Hz)
        if i % 5 == 0:
            rows.append([f"{ts+0.5:.1f}", 2, "MTK Magnetometer", f"{mag_x[i]:.5f}", f"{mag_y[i]:.5f}", f"{mag_z[i]:.5f}"])

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"Generated {len(rows)-1} synthetic sensor packets -> {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Oppo A33w Synthetic IMU Generator")
    parser.add_argument("--profile", choices=["stationary", "walking", "running", "rotation_3d", "tremor"], default="walking", help="Physical motion profile")
    parser.add_argument("--duration", type=float, default=10.0, help="Duration in seconds")
    parser.add_argument("--rate", type=float, default=100.0, help="Sampling frequency in Hz")
    parser.add_argument("--output", default="synthetic_oppo_dataset.csv", help="Output CSV path")
    args = parser.parse_args()
    generate_synthetic_dataset(args.profile, args.duration, args.rate, args.output)
