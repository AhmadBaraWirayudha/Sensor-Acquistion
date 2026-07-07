#!/usr/bin/env python3
"""
Oppo A33w MATLAB & SciPy Exporter
Converts raw multi-sensor CSV recordings into a ready-to-run MATLAB script (.m)
containing structured vectors and automated plotting code for academic publication figures.
"""

import sys
import os
import argparse
import csv

def convert_to_matlab(csv_path, m_path="oppo_data.m"):
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    print(f"Converting '{csv_path}' -> MATLAB Script '{m_path}'...")
    
    ts_list, x_list, y_list, z_list = [], [], [], []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) >= 6:
                try:
                    stype = int(row[1])
                    if stype == 1: # Accelerometer
                        ts_list.append(float(row[0]))
                        x_list.append(float(row[3]))
                        y_list.append(float(row[4]))
                        z_list.append(float(row[5]))
                except ValueError:
                    pass

    if not ts_list:
        print("No Accelerometer data found.")
        return

    start_ts = ts_list[0]
    rel_t = [(t - start_ts)/1000.0 for t in ts_list]

    ts_str = " ".join([f"{val:.4f}" for val in rel_t])
    x_str = " ".join([f"{val:.5f}" for val in x_list])
    y_str = " ".join([f"{val:.5f}" for val in y_list])
    z_str = " ".join([f"{val:.5f}" for val in z_list])

    m_code = f"""% Oppo A33w Research Dataset — MATLAB Script
% Generated automatically by SensorMax Laptop Suite
% Contains Accelerometer time-series vectors and publication figure layout

time_s = [{ts_str}];
acc_x = [{x_str}];
acc_y = [{y_str}];
acc_z = [{z_str}];

figure('Name', 'Oppo A33w Multi-Axis Accelerometer Waveform', 'Color', [1 1 1]);
subplot(3,1,1);
plot(time_s, acc_x, 'r', 'LineWidth', 1.5);
title('Axis X Acceleration'); ylabel('m/s^2'); grid on;

subplot(3,1,2);
plot(time_s, acc_y, 'g', 'LineWidth', 1.5);
title('Axis Y Acceleration'); ylabel('m/s^2'); grid on;

subplot(3,1,3);
plot(time_s, acc_z, 'b', 'LineWidth', 1.5);
title('Axis Z Acceleration'); xlabel('Time (s)'); ylabel('m/s^2'); grid on;

disp('Oppo A33w dataset loaded successfully!');
"""

    with open(m_path, 'w', encoding='utf-8') as f:
        f.write(m_code)

    print(f"Successfully generated academic MATLAB script: {m_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Oppo A33w MATLAB Exporter")
    parser.add_argument("csv_file", help="Input raw CSV dataset")
    parser.add_argument("--output", default="oppo_data.m", help="Output MATLAB script path (.m)")
    args = parser.parse_args()
    convert_to_matlab(args.csv_file, args.output)
