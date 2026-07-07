#!/usr/bin/env python3
"""
Oppo A33w 3D Sensor Calibration Tool
Calculates static zero-G bias offsets for Accelerometer and Hard-Iron/Soft-Iron
offsets for Magnetometer from recorded calibration datasets.
"""

import sys
import os
import argparse
import csv
import json

try:
    import numpy as np
except ImportError:
    print("Error: numpy is required. Run 'pip install numpy'")
    sys.exit(1)

def calibrate_accelerometer(csv_path, expected_g=9.80665):
    """
    Computes static zero-G bias offsets assuming the phone was placed stationary
    on a flat surface (Z-axis pointing up against gravity).
    """
    print(f"\n--- Accelerometer Zero-G Bias Calibration ---")
    x_vals, y_vals, z_vals = [], [], []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) >= 6:
                try:
                    stype = int(row[1])
                    if stype == 1: # Accelerometer
                        x_vals.append(float(row[3]))
                        y_vals.append(float(row[4]))
                        z_vals.append(float(row[5]))
                except ValueError:
                    pass

    if not x_vals:
        print("No Accelerometer (Type 1) data found in file.")
        return None

    x_arr = np.array(x_vals)
    y_arr = np.array(y_vals)
    z_arr = np.array(z_vals)

    bias_x = np.mean(x_arr)
    bias_y = np.mean(y_arr)
    bias_z = np.mean(z_arr) - expected_g

    noise_x = np.std(x_arr)
    noise_y = np.std(y_arr)
    noise_z = np.std(z_arr)

    print(f"Samples analyzed : {len(x_arr)}")
    print(f"Calculated Bias  : X_offset = {bias_x:+.4f} m/s² | Y_offset = {bias_y:+.4f} m/s² | Z_offset = {bias_z:+.4f} m/s²")
    print(f"Sensor Noise (1σ): σX = {noise_x:.4f} m/s² | σY = {noise_y:.4f} m/s² | σZ = {noise_z:.4f} m/s²")

    return {
        "sensor": "Accelerometer",
        "bias_offsets": [float(bias_x), float(bias_y), float(bias_z)],
        "noise_std": [float(noise_x), float(noise_y), float(noise_z)]
    }

def calibrate_magnetometer(csv_path):
    """
    Computes Hard-Iron bias offsets (center of magnetic sphere/ellipsoid)
    by rotating the phone 360 degrees in all orientations.
    """
    print(f"\n--- Magnetometer Hard-Iron Calibration ---")
    x_vals, y_vals, z_vals = [], [], []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) >= 6:
                try:
                    stype = int(row[1])
                    if stype == 2: # Magnetometer
                        x_vals.append(float(row[3]))
                        y_vals.append(float(row[4]))
                        z_vals.append(float(row[5]))
                except ValueError:
                    pass

    if not x_vals:
        print("No Magnetometer (Type 2) data found in file.")
        return None

    x_arr = np.array(x_vals)
    y_arr = np.array(y_vals)
    z_arr = np.array(z_vals)

    # Hard-iron offset is the center of the bounding sphere
    offset_x = (np.max(x_arr) + np.min(x_arr)) / 2.0
    offset_y = (np.max(y_arr) + np.min(y_arr)) / 2.0
    offset_z = (np.max(z_arr) + np.min(z_arr)) / 2.0

    # Radius estimation (field strength in µT)
    cal_x = x_arr - offset_x
    cal_y = y_arr - offset_y
    cal_z = z_arr - offset_z
    radii = np.sqrt(cal_x**2 + cal_y**2 + cal_z**2)
    mean_strength = np.mean(radii)

    print(f"Samples analyzed : {len(x_arr)}")
    print(f"Hard-Iron Offsets: X_offset = {offset_x:+.2f} µT | Y_offset = {offset_y:+.2f} µT | Z_offset = {offset_z:+.2f} µT")
    print(f"Mean Geomagnetic Field Strength: {mean_strength:.2f} µT")

    return {
        "sensor": "Magnetometer",
        "hard_iron_offsets": [float(offset_x), float(offset_y), float(offset_z)],
        "field_strength_uT": float(mean_strength)
    }

def main():
    parser = argparse.ArgumentParser(description="Oppo A33w Sensor Calibration Suite")
    parser.add_argument("csv_file", help="Path to stationary or rotation CSV recording")
    parser.add_argument("--save-json", help="Save calibration parameters to JSON file", default="oppo_calibration.json")
    args = parser.parse_args()

    if not os.path.exists(args.csv_file):
        print(f"Error: File '{args.csv_file}' not found.")
        return

    print("=============================================================")
    print(" OPPO A33w SENSOR PRECISION CALIBRATION ENGINE")
    print("=============================================================")
    
    results = {}
    acc_res = calibrate_accelerometer(args.csv_file)
    if acc_res: results["accelerometer"] = acc_res
    
    mag_res = calibrate_magnetometer(args.csv_file)
    if mag_res: results["magnetometer"] = mag_res

    if results:
        with open(args.save_json, 'w') as f:
            json.dump(results, f, indent=4)
        print(f"\nSaved calibration profile to: {args.save_json}")
    print("=============================================================\n")

if __name__ == "__main__":
    main()
