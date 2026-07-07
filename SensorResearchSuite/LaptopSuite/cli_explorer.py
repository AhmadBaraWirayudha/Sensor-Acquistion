#!/usr/bin/env python3
"""
Oppo A33w Interactive Terminal REPL Data Explorer
An interactive command-line shell interface for quick dataset loading,
statistical inspection, ascii plotting, and pipeline execution.
"""

import sys
import os
import csv

try:
    import numpy as np
except ImportError:
    print("Error: numpy is required.")
    sys.exit(1)

def ascii_plot(arr, width=50, height=10):
    if len(arr) == 0: return "No data."
    sub = arr[::max(1, len(arr)//width)]
    min_v, max_v = np.min(sub), np.max(sub)
    span = max(max_v - min_v, 1e-5)
    
    grid = [[" " for _ in range(len(sub))] for _ in range(height)]
    for col, val in enumerate(sub):
        row = height - 1 - int(((val - min_v) / span) * (height - 1))
        row = max(0, min(height - 1, row))
        grid[row][col] = "*"
    
    out = f"Max: {max_v:+.4f}\n"
    for r in grid: out += " |" + "".join(r) + "|\n"
    out += f"Min: {min_v:+.4f}\n"
    return out

def run_explorer(initial_csv=None):
    print("=============================================================")
    print(" OPPO A33w INTERACTIVE TERMINAL REPL DATA EXPLORER")
    print(" Type 'help' for commands, 'exit' to quit.")
    print("=============================================================")

    current_csv = initial_csv
    ts_arr, xa, ya, za = [], [], [], []

    def load_file(fpath):
        nonlocal current_csv, ts_arr, xa, ya, za
        if not os.path.exists(fpath):
            print(f"Error: File '{fpath}' not found.")
            return False
        ts, x, y, z = [], [], [], []
        with open(fpath, 'r', encoding='utf-8') as f:
            r = csv.reader(f)
            next(r, None)
            for row in r:
                if len(row)>=6 and int(row[1])==1:
                    ts.append(float(row[0]))
                    x.append(float(row[3]))
                    y.append(float(row[4]))
                    z.append(float(row[5]))
        ts_arr, xa, ya, za = np.array(ts), np.array(x), np.array(y), np.array(z)
        current_csv = fpath
        print(f"Loaded '{os.path.basename(fpath)}': {len(xa)} Accelerometer samples.")
        return True

    if initial_csv: load_file(initial_csv)

    while True:
        try:
            cmd_line = input(f"\n({os.path.basename(current_csv) if current_csv else 'none'})> ").strip().split()
            if not cmd_line: continue
            cmd = cmd_line[0].lower()

            if cmd in ["exit", "quit"]: break
            elif cmd == "help":
                print("Commands: load <file.csv>, stats, plot <x|y|z>, fft, exit")
            elif cmd == "load":
                if len(cmd_line)>1: load_file(cmd_line[1])
                else: print("Usage: load <filename.csv>")
            elif cmd == "stats":
                if len(xa)==0: print("No data loaded.")
                else:
                    print(f"Samples: {len(xa)} | Duration: {(ts_arr[-1]-ts_arr[0])/1000:.2f}s")
                    print(f"Axis X: Mean={np.mean(xa):+.4f}, RMS={np.sqrt(np.mean(xa**2)):.4f}, Range=[{np.min(xa):+.3f}, {np.max(xa):+.3f}]")
                    print(f"Axis Y: Mean={np.mean(ya):+.4f}, RMS={np.sqrt(np.mean(ya**2)):.4f}, Range=[{np.min(ya):+.3f}, {np.max(ya):+.3f}]")
                    print(f"Axis Z: Mean={np.mean(za):+.4f}, RMS={np.sqrt(np.mean(za**2)):.4f}, Range=[{np.min(za):+.3f}, {np.max(za):+.3f}]")
            elif cmd == "plot":
                if len(xa)==0: print("No data loaded.")
                else:
                    axis = cmd_line[1].lower() if len(cmd_line)>1 else "x"
                    arr = xa if axis=="x" else ya if axis=="y" else za
                    print(ascii_plot(arr))
            elif cmd == "fft":
                if len(xa)==0: print("No data loaded.")
                else:
                    fft_v = np.abs(np.fft.rfft(xa - np.mean(xa)))
                    freqs = np.fft.rfftfreq(len(xa), d=0.01)
                    idx = np.argmax(fft_v) if len(fft_v)>0 else 0
                    print(f"Dominant Resonant Frequency Axis X: {freqs[idx]:.2f} Hz")
            else:
                print("Unknown command. Type 'help'.")
        except (KeyboardInterrupt, EOFError): break

    print("\nExiting explorer.")

if __name__ == "__main__":
    init_f = sys.argv[1] if len(sys.argv)>1 else None
    run_explorer(init_f)
