#!/usr/bin/env python3
"""
Oppo A33w Live FFT Spectrum Studio
Receives real-time sensor streams (UDP/TCP/Serial) and displays both
the live time-domain waveform AND the real-time Fast Fourier Transform (FFT)
frequency spectrum (0 to 50 Hz bins) for vibration analysis.
"""

import sys
import os
import time
import socket
import threading
import queue
import tkinter as tk
from tkinter import ttk

try:
    import numpy as np
except ImportError:
    print("Error: numpy is required. Run 'pip install numpy'")
    sys.exit(1)

class LiveSpectrumApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Oppo A33w Real-Time FFT Spectrum Studio")
        self.root.geometry("950x700")
        
        self.data_queue = queue.Queue(maxsize=5000)
        self.running = False
        self.sock = None
        self.thread = None

        # Data buffer for FFT (last 256 samples of Accelerometer X, Y, Z)
        self.buffer_size = 256
        self.buf_x = [0.0] * self.buffer_size
        self.buf_y = [9.8] * self.buffer_size
        self.buf_z = [0.0] * self.buffer_size
        
        self.setup_ui()
        self.root.after(40, self.process_and_draw)

    def setup_ui(self):
        ctrl_frame = ttk.LabelFrame(self.root, text=" Connection Controls ", padding=10)
        ctrl_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(ctrl_frame, text="UDP Port:").pack(side=tk.LEFT, padx=5)
        self.port_entry = ttk.Entry(ctrl_frame, width=8)
        self.port_entry.insert(0, "5005")
        self.port_entry.pack(side=tk.LEFT, padx=5)

        self.btn_listen = ttk.Button(ctrl_frame, text="Start Listening", command=self.toggle_listen)
        self.btn_listen.pack(side=tk.LEFT, padx=10)

        self.btn_sim = ttk.Button(ctrl_frame, text="Start 6.5Hz Tremor Simulation", command=self.toggle_sim)
        self.btn_sim.pack(side=tk.LEFT, padx=10)

        self.lbl_peak = ttk.Label(ctrl_frame, text="Dominant Peak Frequency: 0.0 Hz", font=("Arial", 11, "bold"), foreground="#38BDF8")
        self.lbl_peak.pack(side=tk.RIGHT, padx=15)

        # Split canvases: Top = Waveform, Bottom = FFT Spectrum
        paned = ttk.Panedwindow(self.root, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        wave_frame = ttk.LabelFrame(paned, text=" Time-Domain Accelerometer Waveform (Last 256 Samples) ", padding=5)
        paned.add(wave_frame, weight=1)
        self.wave_canvas = tk.Canvas(wave_frame, bg="#0F172A", height=220)
        self.wave_canvas.pack(fill=tk.BOTH, expand=True)

        fft_frame = ttk.LabelFrame(paned, text=" Real-Time Fast Fourier Transform (FFT) Frequency Spectrum (0 - 50 Hz) ", padding=5)
        paned.add(fft_frame, weight=1)
        self.fft_canvas = tk.Canvas(fft_frame, bg="#0B1120", height=220)
        self.fft_canvas.pack(fill=tk.BOTH, expand=True)

        self.sim_active = False
        self.sim_t = 0.0

    def toggle_listen(self):
        if not self.running:
            port = int(self.port_entry.get())
            self.running = True
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.sock.bind(('0.0.0.0', port))
                self.thread = threading.Thread(target=self._udp_receiver, daemon=True)
                self.thread.start()
                self.btn_listen.config(text="Stop Listening")
            except Exception as e:
                self.running = False
                print(f"Error starting UDP: {e}")
        else:
            self.running = False
            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass
                self.sock = None
            self.btn_listen.config(text="Start Listening")

    def _udp_receiver(self):
        while self.running and self.sock:
            try:
                data, _ = self.sock.recvfrom(4096)
                line = data.decode('utf-8', errors='ignore').strip()
                if line: self.data_queue.put(line)
            except Exception:
                break

    def toggle_sim(self):
        self.sim_active = not self.sim_active
        self.btn_sim.config(text="Stop Simulation" if self.sim_active else "Start 6.5Hz Tremor Simulation")

    def process_and_draw(self):
        # Generate simulation samples if active
        if self.sim_active:
            for _ in range(4):
                self.sim_t += 0.01
                # 6.5 Hz tremor harmonic
                vx = 2.0 * math.sin(2 * math.pi * 6.5 * self.sim_t) + np.random.normal(0, 0.1)
                vy = 9.8 + 1.0 * math.cos(2 * math.pi * 13.0 * self.sim_t) + np.random.normal(0, 0.1)
                vz = 0.5 * math.sin(2 * math.pi * 3.2 * self.sim_t) + np.random.normal(0, 0.1)
                self.buf_x.append(vx); self.buf_x.pop(0)
                self.buf_y.append(vy); self.buf_y.pop(0)
                self.buf_z.append(vz); self.buf_z.pop(0)

        # Drain incoming UDP packets
        while not self.data_queue.empty():
            line = self.data_queue.get()
            parts = [p.strip().strip('"') for p in line.split(',')]
            if len(parts) >= 6 and int(parts[1]) == 1: # Accelerometer
                try:
                    self.buf_x.append(float(parts[3])); self.buf_x.pop(0)
                    self.buf_y.append(float(parts[4])); self.buf_y.pop(0)
                    self.buf_z.append(float(parts[5])); self.buf_z.pop(0)
                except ValueError: pass

        self.draw_wave()
        self.draw_fft()
        self.root.after(40, self.process_and_draw)

    def draw_wave(self):
        c = self.wave_canvas
        c.delete("all")
        w = c.winfo_width(); h = c.winfo_height()
        if w <= 1 or h <= 1: return

        # Grid
        c.create_line(0, h//2, w, h//2, fill="#334155", width=2)
        
        all_vals = self.buf_x + self.buf_y + self.buf_z
        min_v, max_v = min(all_vals), max(all_vals)
        span = max(max_v - min_v, 2.0)
        scale_y = (h * 0.7) / span
        mid_v = (max_v + min_v) / 2.0
        step_x = w / max(self.buffer_size - 1, 1)

        def coords(arr):
            pts = []
            for i, v in enumerate(arr):
                pts.extend([i * step_x, h//2 - (v - mid_v) * scale_y])
            return pts

        c.create_line(*coords(self.buf_x), fill="#F87171", width=2)
        c.create_line(*coords(self.buf_y), fill="#4ADE80", width=2)
        c.create_line(*coords(self.buf_z), fill="#38BDF8", width=2)

    def draw_fft(self):
        c = self.fft_canvas
        c.delete("all")
        w = c.winfo_width(); h = c.winfo_height()
        if w <= 1 or h <= 1: return

        # Compute FFT on dynamic Acc X
        arr = np.array(self.buf_x)
        centered = arr - np.mean(arr)
        fft_vals = np.abs(np.fft.rfft(centered))
        freqs = np.fft.rfftfreq(len(arr), d=0.01) # Assume ~100 Hz sampling

        if len(fft_vals) > 1:
            fft_vals[0] = 0 # zero out DC
            peak_idx = np.argmax(fft_vals)
            dom_hz = freqs[peak_idx]
            self.lbl_peak.config(text=f"Dominant Peak Frequency: {dom_hz:.1f} Hz")

            max_fft = max(np.max(fft_vals), 1.0)
            n_bins = len(fft_vals)
            bar_w = w / max(n_bins, 1)

            for i in range(1, min(n_bins, 50)):
                bar_h = (fft_vals[i] / max_fft) * (h * 0.85)
                px1 = i * bar_w
                py1 = h - bar_h
                px2 = px1 + bar_w - 2
                color = "#F87171" if i == peak_idx else "#38BDF8"
                c.create_rectangle(px1, py1, px2, h, fill=color, outline="")
                if i % 5 == 0:
                    c.create_text(px1 + bar_w/2, h - 10, text=f"{int(freqs[i])}Hz", fill="#94A3B8", font=("Arial", 8))

if __name__ == "__main__":
    root = tk.Tk()
    app = LiveSpectrumApp(root)
    root.mainloop()
