#!/usr/bin/env python3
"""
Oppo A33w Quality Assurance & Anomaly Detector
Scans sensor recordings for hardware saturation/clipping, packet drop gaps,
and statistical outliers using Z-score and inter-sample timing thresholds.
"""

import sys
import os
import argparse
import csv

try:
    import numpy as np
except ImportError:
    print("Error: numpy is required.")
    sys.exit(1)

def detect_anomalies(csv_path, z_threshold=4.0, gap_threshold_ms=50.0):
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    print(f"Running Quality Assurance & Anomaly Scan on '{csv_path}'...")
    
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

    # 1. Check Packet Gaps
    deltas = np.diff(ts_arr)
    gaps = np.where(deltas > gap_threshold_ms)[0]

    # 2. Check Hardware Clipping (e.g. Accelerometer standard range +-19.6 m/s^2 or +-39.2 m/s^2)
    clipping_limit = 19.5
    clip_x = np.where(np.abs(xa) >= clipping_limit)[0]
    clip_y = np.where(np.abs(ya) >= clipping_limit)[0]
    clip_z = np.where(np.abs(za) >= clipping_limit)[0]

    # 3. Check Statistical Z-Score Outliers
    z_x = np.abs((xa - np.mean(xa)) / (np.std(xa) + 1e-6))
    outliers_x = np.where(z_x > z_threshold)[0]

    print("=" * 65)
    print(" OPPO A33w DATASET QUALITY ASSURANCE & ANOMALY REPORT")
    print("=" * 65)
    print(f"Total Samples Analyzed : {len(ts_arr):,}")
    print(f"Mean Interval          : {np.mean(deltas):.2f} ms ({1000.0/np.mean(deltas):.1f} Hz)")
    print("-" * 65)
    print(f"Packet Drop Gaps (>{gap_threshold_ms}ms) : {len(gaps)} instances")
    if len(gaps) > 0:
        max_gap = np.max(deltas)
        print(f"  -> Maximum Inter-Sample Gap Observed: {max_gap:.1f} ms")
    print(f"Hardware Clipping / Saturation Found:")
    print(f"  -> Axis X: {len(clip_x)} | Axis Y: {len(clip_y)} | Axis Z: {len(clip_z)}")
    print(f"Statistical Outliers (Z > {z_threshold}σ)  : {len(outliers_x)} instances")
    
    health_score = 100.0 - (len(gaps)*2.0 + len(clip_x)*1.5 + len(outliers_x)*0.5) / max(len(ts_arr)/100.0, 1.0)
    health_score = max(0.0, min(100.0, health_score))
    
    grade = "A+ (Excellent)" if health_score >= 95 else "B (Good)" if health_score >= 85 else "C (Warning)" if health_score >= 70 else "D/F (Severe Anomalies)"
    print("-" * 65)
    print(f"OVERALL DATASET HEALTH SCORE : {health_score:.1f}% [{grade}]")
    print("=" * 65)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Oppo A33w Anomaly Detector")
    parser.add_argument("csv_file", help="Input raw CSV dataset")
    parser.add_argument("--z-threshold", type=float, default=4.0, help="Z-score outlier threshold")
    args = parser.parse_args()
    detect_anomalies(args.csv_file, args.z_threshold)
