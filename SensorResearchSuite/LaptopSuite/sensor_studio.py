#!/usr/bin/env python3
"""
SensorMax Studio — Laptop Research Suite
For receiving, recording, and analyzing real-time sensor streams from Oppo A33w over:
1. WiFi UDP Stream
2. USB ADB Socket Forwarding (adb forward tcp:5005 tcp:5005)
3. Bluetooth SPP / COM Port (pyserial)
"""

import sys
import os
import time
import socket
import threading
import queue
import csv
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import serial
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class SensorDataReceiver:
    """Background receiver engine for UDP, TCP (USB ADB), and Serial (Bluetooth)."""
    def __init__(self, data_queue, log_callback):
        self.data_queue = data_queue
        self.log_callback = log_callback
        self.running = False
        self.sock = None
        self.ser = None
        self.thread = None

    def start_udp(self, port=5005):
        self.stop()
        self.running = True
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(('0.0.0.0', port))
            self.log_callback(f"[UDP] Listening on port {port}...")
            self.thread = threading.Thread(target=self._udp_loop, daemon=True)
            self.thread.start()
        except Exception as e:
            self.log_callback(f"[UDP Error] {e}")

    def start_tcp_usb(self, port=5005, host='127.0.0.1'):
        """Connects to USB ADB forwarded port (adb forward tcp:5005 tcp:5005)."""
        self.stop()
        self.running = True
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, port))
            self.log_callback(f"[USB/ADB TCP] Connected to {host}:{port}")
            self.thread = threading.Thread(target=self._stream_loop, daemon=True)
            self.thread.start()
        except Exception as e:
            self.log_callback(f"[USB/ADB Error] Ensure 'adb forward tcp:{port} tcp:{port}' is run. {e}")

    def start_serial(self, com_port='COM3', baudrate=115200):
        if not HAS_SERIAL:
            self.log_callback("[Serial Error] 'pyserial' package not installed.")
            return
        self.stop()
        self.running = True
        try:
            self.ser = serial.Serial(com_port, baudrate, timeout=1)
            self.log_callback(f"[Bluetooth/Serial] Opened {com_port} at {baudrate} baud")
            self.thread = threading.Thread(target=self._serial_loop, daemon=True)
            self.thread.start()
        except Exception as e:
            self.log_callback(f"[Serial Error] {e}")

    def _udp_loop(self):
        while self.running and self.sock:
            try:
                data, addr = self.sock.recvfrom(4096)
                line = data.decode('utf-8', errors='ignore').strip()
                if line:
                    self.data_queue.put(line)
            except Exception:
                break

    def _stream_loop(self):
        buffer = ""
        while self.running and self.sock:
            try:
                chunk = self.sock.recv(4096).decode('utf-8', errors='ignore')
                if not chunk:
                    break
                buffer += chunk
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        self.data_queue.put(line)
            except Exception:
                break

    def _serial_loop(self):
        while self.running and self.ser and self.ser.is_open:
            try:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    self.data_queue.put(line)
            except Exception:
                break

    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None


class SensorHubApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SensorMax Studio — Oppo A33w Laptop Research Hub")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        self.data_queue = queue.Queue(maxsize=10000)
        self.receiver = SensorDataReceiver(self.data_queue, self.log)

        # Recording state
        self.recording = False
        self.csv_file = None
        self.csv_writer = None
        self.sample_count = 0
        self.last_rate_calc = time.time()
        self.rate_count = 0
        self.current_hz = 0.0

        # Sensor data buffers for plotting (last 200 samples per sensor type)
        # Type 1 = Accelerometer, Type 4 = Gyroscope
        self.plot_buffers = {
            1: {'x': [], 'y': [], 'z': []},
            4: {'x': [], 'y': [], 'z': []}
        }
        self.selected_plot_type = 1 # Default plot Accelerometer

        self.setup_ui()
        self.root.after(30, self.process_queue)

    def setup_ui(self):
        top_frame = ttk.LabelFrame(self.root, text=" 1. Connection Mode & Receiver Settings ", padding=10)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(top_frame, text="Mode:").pack(side=tk.LEFT, padx=5)
        self.mode_var = tk.StringVar(value="UDP")
        mode_cb = ttk.Combobox(top_frame, textvariable=self.mode_var, values=["UDP (WiFi)", "USB ADB Socket", "Bluetooth Serial (COM)"], width=18, state="readonly")
        mode_cb.pack(side=tk.LEFT, padx=5)

        ttk.Label(top_frame, text="Port / COM:").pack(side=tk.LEFT, padx=5)
        self.port_entry = ttk.Entry(top_frame, width=10)
        self.port_entry.insert(0, "5005")
        self.port_entry.pack(side=tk.LEFT, padx=5)

        self.btn_connect = ttk.Button(top_frame, text="Start Listening", command=self.toggle_connect)
        self.btn_connect.pack(side=tk.LEFT, padx=10)

        self.lbl_hz = ttk.Label(top_frame, text="Data Rate: 0.0 Hz | Total Samples: 0", font=("Arial", 10, "bold"))
        self.lbl_hz.pack(side=tk.RIGHT, padx=10)

        # Recording frame
        rec_frame = ttk.LabelFrame(self.root, text=" 2. High-Speed Laptop CSV Recording ", padding=10)
        rec_frame.pack(fill=tk.X, padx=10, pady=5)

        self.lbl_rec_status = ttk.Label(rec_frame, text="Status: Not Recording", foreground="red", font=("Arial", 10, "bold"))
        self.lbl_rec_status.pack(side=tk.LEFT, padx=5)

        self.btn_record = ttk.Button(rec_frame, text="Start CSV Recording", command=self.toggle_record)
        self.btn_record.pack(side=tk.LEFT, padx=15)

        self.btn_browse = ttk.Button(rec_frame, text="Set Output Directory...", command=self.set_output_dir)
        self.btn_browse.pack(side=tk.LEFT, padx=5)
        self.output_dir = os.path.join(os.path.expanduser("~"), "OppoSensorRecords")
        os.makedirs(self.output_dir, exist_ok=True)
        ttk.Label(rec_frame, text=f"Dir: {self.output_dir}").pack(side=tk.LEFT, padx=10)

        # Main splitter: Live Plot & Stats vs Log
        paned = ttk.Panedwindow(self.root, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        plot_frame = ttk.LabelFrame(paned, text=" 3. Real-Time Waveform & Signal Analysis ", padding=5)
        paned.add(plot_frame, weight=3)

        ctrl_bar = ttk.Frame(plot_frame)
        ctrl_bar.pack(fill=tk.X, pady=2)
        ttk.Label(ctrl_bar, text="Display Sensor Waveform:").pack(side=tk.LEFT, padx=5)
        self.plot_type_var = tk.StringVar(value="1 - Accelerometer")
        plot_type_cb = ttk.Combobox(ctrl_bar, textvariable=self.plot_type_var, values=["1 - Accelerometer", "4 - Gyroscope", "2 - Magnetometer", "5 - Light Sensor", "8 - Proximity Sensor"], width=22, state="readonly")
        plot_type_cb.pack(side=tk.LEFT, padx=5)
        plot_type_cb.bind("<<ComboboxSelected>>", self.on_plot_type_change)

        self.canvas = tk.Canvas(plot_frame, bg="#1E1E1E", height=240)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        log_frame = ttk.LabelFrame(paned, text=" Live Console & Diagnostic Log ", padding=5)
        paned.add(log_frame, weight=1)

        self.txt_log = tk.Text(log_frame, bg="#0F172A", fg="#38BDF8", font=("Consolas", 9), height=6)
        self.txt_log.pack(fill=tk.BOTH, expand=True)

    def log(self, msg):
        self.txt_log.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.txt_log.see(tk.END)

    def toggle_connect(self):
        if not self.receiver.running:
            mode = self.mode_var.get()
            port_val = self.port_entry.get().strip()
            if "UDP" in mode:
                port = int(port_val)
                self.receiver.start_udp(port)
            elif "USB" in mode:
                port = int(port_val)
                self.receiver.start_tcp_usb(port)
            else:
                self.receiver.start_serial(com_port=port_val)
            self.btn_connect.config(text="Stop Listening")
        else:
            self.receiver.stop()
            self.btn_connect.config(text="Start Listening")
            self.log("Disconnected receiver.")

    def set_output_dir(self):
        folder = filedialog.askdirectory(title="Select Output Folder for CSV Records")
        if folder:
            self.output_dir = folder
            self.log(f"Set output directory to: {folder}")

    def toggle_record(self):
        if not self.recording:
            filename = f"OppoA33w_SensorData_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(self.output_dir, filename)
            try:
                self.csv_file = open(filepath, 'w', newline='', encoding='utf-8')
                self.csv_writer = csv.writer(self.csv_file)
                self.csv_writer.writerow(["Timestamp_ms", "Sensor_Type", "Sensor_Name", "Value_X", "Value_Y", "Value_Z"])
                self.recording = True
                self.btn_record.config(text="Stop CSV Recording")
                self.lbl_rec_status.config(text=f"Recording -> {filename}", foreground="green")
                self.log(f"Started high-speed CSV recording: {filepath}")
            except Exception as e:
                messagebox.showerror("Recording Error", str(e))
        else:
            self.recording = False
            if self.csv_file:
                try:
                    self.csv_file.close()
                except Exception:
                    pass
                self.csv_file = None
            self.btn_record.config(text="Start CSV Recording")
            self.lbl_rec_status.config(text="Status: Not Recording", foreground="red")
            self.log("Stopped CSV recording.")

    def on_plot_type_change(self, event=None):
        val = self.plot_type_var.get()
        type_id = int(val.split(" - ")[0])
        self.selected_plot_type = type_id
        if type_id not in self.plot_buffers:
            self.plot_buffers[type_id] = {'x': [], 'y': [], 'z': []}

    def process_queue(self):
        batch_size = 0
        now = time.time()
        while not self.data_queue.empty() and batch_size < 500:
            line = self.data_queue.get()
            batch_size += 1
            self.sample_count += 1
            self.rate_count += 1

            # Parse line: timestamp_ms,type,"Name",val0,val1,val2
            parts = [p.strip().strip('"') for p in line.split(',')]
            if len(parts) >= 4:
                try:
                    ts = int(parts[0])
                    stype = int(parts[1])
                    sname = parts[2]
                    vals = [float(x) for x in parts[3:]]

                    if self.recording and self.csv_writer:
                        row = [ts, stype, sname] + vals + [0.0]*(3-len(vals))
                        self.csv_writer.writerow(row[:6])

                    # Buffer for plotting
                    if stype not in self.plot_buffers:
                        self.plot_buffers[stype] = {'x': [], 'y': [], 'z': []}
                    buf = self.plot_buffers[stype]
                    buf['x'].append(vals[0] if len(vals)>0 else 0.0)
                    buf['y'].append(vals[1] if len(vals)>1 else 0.0)
                    buf['z'].append(vals[2] if len(vals)>2 else 0.0)
                    if len(buf['x']) > 200:
                        buf['x'].pop(0)
                        buf['y'].pop(0)
                        buf['z'].pop(0)
                except ValueError:
                    pass

        # Update data rate display
        if now - self.last_rate_calc >= 1.0:
            self.current_hz = self.rate_count / (now - self.last_rate_calc)
            self.lbl_hz.config(text=f"Data Rate: {self.current_hz:.1f} Hz | Total Samples: {self.sample_count}")
            self.rate_count = 0
            self.last_rate_calc = now

        # Redraw canvas
        self.draw_plot()
        self.root.after(30, self.process_queue)

    def draw_plot(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1:
            return

        # Grid lines
        for y in range(0, h, 40):
            self.canvas.create_line(0, y, w, y, fill="#2D3748")
        self.canvas.create_line(0, h//2, w, h//2, fill="#4A5568", width=2)

        stype = self.selected_plot_type
        if stype not in self.plot_buffers or not self.plot_buffers[stype]['x']:
            self.canvas.create_text(w//2, h//2, text=f"Waiting for live samples of Type {stype}...", fill="#A0AEC0", font=("Arial", 14))
            return

        buf = self.plot_buffers[stype]
        n = len(buf['x'])
        if n < 2:
            return

        # Scale graph
        all_vals = buf['x'] + buf['y'] + buf['z']
        min_v = min(all_vals)
        max_v = max(all_vals)
        span = max(max_v - min_v, 2.0)
        scale_y = (h * 0.8) / span
        center_y = h // 2
        mid_v = (max_v + min_v) / 2.0

        step_x = w / max(n - 1, 1)

        def coords(arr):
            pts = []
            for i, val in enumerate(arr):
                px = i * step_x
                py = center_y - (val - mid_v) * scale_y
                pts.extend([px, py])
            return pts

        if len(buf['x']) > 1:
            self.canvas.create_line(*coords(buf['x']), fill="#F56565", width=2) # Red X
        if len(buf['y']) > 1:
            self.canvas.create_line(*coords(buf['y']), fill="#48BB78", width=2) # Green Y
        if len(buf['z']) > 1:
            self.canvas.create_line(*coords(buf['z']), fill="#4299E1", width=2) # Blue Z

        # Legend
        self.canvas.create_text(50, 15, text=f"X: {buf['x'][-1]:.2f}", fill="#F56565", font=("Arial", 10, "bold"))
        self.canvas.create_text(130, 15, text=f"Y: {buf['y'][-1]:.2f}", fill="#48BB78", font=("Arial", 10, "bold"))
        self.canvas.create_text(210, 15, text=f"Z: {buf['z'][-1]:.2f}", fill="#4299E1", font=("Arial", 10, "bold"))


if __name__ == "__main__":
    root = tk.Tk()
    app = SensorHubApp(root)
    root.mainloop()
