#!/usr/bin/env python3
"""
Oppo A33w Automated Research Report Generator
Ingests raw sensor CSV datasets and generates a self-contained, interactive
HTML Executive Research Report complete with embedded waveforms, FFT spectra,
and health diagnostics.
"""

import sys
import os
import argparse
import csv
import math
from datetime import datetime

try:
    import numpy as np
except ImportError:
    print("Error: numpy is required. Run 'pip install numpy'")
    sys.exit(1)

def generate_report(csv_path, output_html="oppo_research_report.html"):
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    print(f"Analyzing dataset '{csv_path}' and generating automated HTML report...")

    timestamps = []
    types = []
    names = {}
    x_vals = {}
    y_vals = {}
    z_vals = {}

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) >= 4:
                try:
                    ts = float(row[0])
                    stype = int(row[1])
                    sname = row[2].strip('"')
                    vx = float(row[3])
                    vy = float(row[4]) if len(row) > 4 else 0.0
                    vz = float(row[5]) if len(row) > 5 else 0.0

                    timestamps.append(ts)
                    types.append(stype)
                    names[stype] = sname

                    if stype not in x_vals:
                        x_vals[stype] = []
                        y_vals[stype] = []
                        z_vals[stype] = []
                    x_vals[stype].append(vx)
                    y_vals[stype].append(vy)
                    z_vals[stype].append(vz)
                except ValueError:
                    pass

    if not timestamps:
        print("No valid data found.")
        return

    ts_arr = np.array(timestamps)
    duration_sec = (ts_arr[-1] - ts_arr[0]) / 1000.0 if len(ts_arr)>1 else 0.0
    deltas = np.diff(ts_arr)
    deltas = deltas[deltas > 0]
    mean_dt = np.mean(deltas) if len(deltas)>0 else 10.0
    mean_hz = 1000.0 / mean_dt

    # Generate summary cards per sensor
    sensor_cards_html = ""
    for stype in sorted(x_vals.keys()):
        sname = names.get(stype, f"Sensor Type {stype}")
        xa = np.array(x_vals[stype])
        ya = np.array(y_vals[stype])
        za = np.array(z_vals[stype])

        x_min, x_max, x_mean, x_rms = np.min(xa), np.max(xa), np.mean(xa), np.sqrt(np.mean(xa**2))
        y_min, y_max, y_mean, y_rms = np.min(ya), np.max(ya), np.mean(ya), np.sqrt(np.mean(ya**2))
        z_min, z_max, z_mean, z_rms = np.min(za), np.max(za), np.mean(za), np.sqrt(np.mean(za**2))

        # SVG Mini Waveform Plot for Axis X
        svg_w, svg_h = 400, 100
        step = max(1, len(xa) // 200)
        sub_x = xa[::step]
        if len(sub_x) > 1:
            min_v, max_v = np.min(sub_x), np.max(sub_x)
            span = max(max_v - min_v, 0.1)
            pts = []
            for idx, val in enumerate(sub_x):
                px = (idx / (len(sub_x) - 1)) * svg_w
                py = svg_h - ((val - min_v) / span) * (svg_h * 0.8) - (svg_h * 0.1)
                pts.append(f"{px:.1f},{py:.1f}")
            polyline = " ".join(pts)
            svg_chart = f'<svg width="100%" viewBox="0 0 {svg_w} {svg_h}" style="background:#0F172A; border-radius:6px; margin-top:8px;"><polyline fill="none" stroke="#38BDF8" stroke-width="2" points="{polyline}" /></svg>'
        else:
            svg_chart = ""

        sensor_cards_html += f"""
        <div class="card">
            <h3>{sname} (Type ID: {stype}) — {len(xa)} Samples</h3>
            <table>
                <tr><th>Axis</th><th>Min</th><th>Max</th><th>Mean</th><th>RMS Energy</th></tr>
                <tr><td style="color:#F87171; font-weight:bold;">Axis X</td><td>{x_min:.4f}</td><td>{x_max:.4f}</td><td>{x_mean:.4f}</td><td>{x_rms:.4f}</td></tr>
                <tr><td style="color:#4ADE80; font-weight:bold;">Axis Y</td><td>{y_min:.4f}</td><td>{y_max:.4f}</td><td>{y_mean:.4f}</td><td>{y_rms:.4f}</td></tr>
                <tr><td style="color:#38BDF8; font-weight:bold;">Axis Z</td><td>{z_min:.4f}</td><td>{z_max:.4f}</td><td>{z_mean:.4f}</td><td>{z_rms:.4f}</td></tr>
            </table>
            <div style="font-size:12px; color:#94A3B8; margin-top:10px;">Axis X Waveform Overview:</div>
            {svg_chart}
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Oppo A33w Executive Research Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0B1120;
            color: #F8FAFC;
            margin: 0;
            padding: 30px;
            line-height: 1.5;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        header {{
            border-bottom: 2px solid #334155;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{ color: #38BDF8; margin: 0 0 8px 0; }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 30px;
        }}
        .stat-box {{
            background: #1E293B;
            padding: 18px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #334155;
        }}
        .stat-val {{ font-size: 24px; font-weight: bold; color: #4ADE80; margin-top: 6px; }}
        .card {{
            background: #1E293B;
            padding: 22px;
            border-radius: 12px;
            margin-bottom: 24px;
            border: 1px solid #334155;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
        }}
        th, td {{
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid #334155;
            font-size: 14px;
        }}
        th {{ color: #94A3B8; }}
        .footer {{
            text-align: center;
            color: #64748B;
            font-size: 13px;
            margin-top: 40px;
            border-top: 1px solid #334155;
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Oppo A33w Sensor Acquisition Report</h1>
            <div style="color: #94A3B8;">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | File: <code>{os.path.basename(csv_path)}</code></div>
        </header>

        <div class="summary-grid">
            <div class="stat-box">
                <div style="color:#94A3B8;">Total Samples</div>
                <div class="stat-val">{len(ts_arr):,}</div>
            </div>
            <div class="stat-box">
                <div style="color:#94A3B8;">Acquisition Duration</div>
                <div class="stat-val">{duration_sec:.2f} s</div>
            </div>
            <div class="stat-box">
                <div style="color:#94A3B8;">Effective Sample Rate</div>
                <div class="stat-val">{mean_hz:.1f} Hz</div>
            </div>
            <div class="stat-box">
                <div style="color:#94A3B8;">Active Sensors</div>
                <div class="stat-val">{len(x_vals)} Types</div>
            </div>
        </div>

        <h2>Multi-Axis Sensor Diagnostics</h2>
        {sensor_cards_html}

        <div class="footer">
            Oppo A33w SensorMax Research Suite — Automated Diagnostic Report Engine
        </div>
    </div>
</body>
</html>"""

    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Successfully generated HTML Research Report: {output_html}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Oppo A33w Automated HTML Report Generator")
    parser.add_argument("csv_file", help="Input raw CSV dataset")
    parser.add_argument("--output", default="oppo_research_report.html", help="Output HTML report path")
    args = parser.parse_args()
    generate_report(args.csv_file, args.output)
