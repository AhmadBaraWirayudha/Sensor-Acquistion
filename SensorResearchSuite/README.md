# Complete Oppo A33w (Neo 7) Real-Time Sensor Research Suite

This workspace contains an exhaustive, production-grade engineering and research suite specifically optimized for pushing the **Oppo A33w (Android 5.1 Lollipop / API 22)** sensors to their absolute hardware limits.

---

## Workspace Structure

```
OppoSensorResearchSuite/
├── README.md                      # Detailed Setup Guide & Transmission Reference
├── run_laptop_suite.sh            # Unified interactive launcher for all 25 research tools
├── oppo_research_report.html      # Sample Executive Diagnostic HTML Report with embedded SVG charts
├── master_batch_comparison.xlsx   # Sample Multi-Trial Batch Comparison Excel Workbook
├── oppo_data.m                    # Academic MATLAB publication script with vector arrays
├── AndroidApp/                    # Complete Android Studio project for Oppo A33w (API 22+)
│   ├── app/src/main/java/.../     # Kotlin source code (MainActivity, SensorEngine, StreamClient)
│   └── app/build.gradle           # Configured for Android 5.1 compatibility
└── LaptopSuite/                   # Python Real-Time Acquisition & Research Software
    ├── sensor_studio.py           # Desktop GUI application with real-time waveform plotting & CSV logger
    ├── live_spectrum_studio.py    # Desktop GUI application with live 0-50 Hz FFT spectrum waterfall
    ├── cli_explorer.py            # Interactive terminal REPL shell for quick inspection & ascii plotting
    ├── realtime_alarm_monitor.py  # Real-time safety & threshold alarmer with console alerts
    ├── web_server.py              # Gateway server bridging UDP/TCP streams to WebSockets
    ├── web_dashboard.html         # Interactive multi-axis waveform Web Dashboard
    ├── web_3d_viewer.html         # Real-Time 3D Digital Twin rotating phone orientation visualizer
    ├── imu_ahrs_3d.py             # Madgwick AHRS 6-DOF/9-DOF sensor fusion (Roll, Pitch, Yaw, Quaternions)
    ├── dead_reckoning_2d.py       # Pedestrian Dead Reckoning (PDR) 2D trajectory tracking engine
    ├── vibration_modal_analysis.py # Structural & mechanical modal resonance & damping ratio analyzer
    ├── gait_symmetry_analyzer.py  # Biomechanical step symmetry index (SSI) & impact evaluation
    ├── ballistocardiography.py    # Cardiac Heart Rate (BPM) & HRV estimator from micro-recoil
    ├── ride_comfort_iso2631.py    # Vehicle & transport comfort evaluator (ISO 2631-1 weighted RMS)
    ├── sleep_tremor_monitor.py    # Nocturnal sleep actigraphy staging & 4-8Hz neurological tremor monitor
    ├── activity_recognition.py    # Step counting cadence & motion state classification engine
    ├── digital_filters.py         # DSP Zero-phase IIR & Moving Average filtering engine
    ├── ml_feature_extractor.py    # Sliding-window AI feature extractor (29 time & spectral features)
    ├── ml_activity_classifier.py  # Pure NumPy K-Nearest Neighbors (KNN) activity classifier
    ├── anomaly_detector.py        # Quality assurance & outlier detector (Hardware clipping & packet drops)
    ├── generate_html_report.py    # Automated executive HTML diagnostic report generator
    ├── matlab_exporter.py         # Academic MATLAB script (.m) exporter for publication figures
    ├── synthetic_sensor_generator.py # Realistic hardware simulation generator (Walking, Running, Tremor)
    ├── batch_dataset_processor.py # Multi-trial comparator & Master Excel summary builder
    ├── test_all_pipelines.py      # Automated 12-step sequential integration pipeline tester
    ├── verify_suite_health.py     # Automated syntax & dependency diagnostic self-test
    ├── data_analysis.py           # Offline research tool for FFT frequency & jitter analysis
    ├── sensor_calibration.py      # 3D static bias calibration engine (Zero-G & Hard-Iron compensation)
    ├── export_converter.py        # Multi-sheet Excel (.xlsx) workbook generator
    └── requirements.txt           # Python dependencies
```

---

## 1. Android App Setup (`SensorMax Research`)

### Features
* **Dynamic Hardware Discovery**: Automatically scans and lists all physical and virtual sensors exposed by the Mediatek MT6582 kernel on Oppo A33w (Accelerometer, Gyroscope, Magnetometer, Light, Proximity).
* **Hardware Limit Sampling Rates**: Switch instantly between `Fastest (0ms)` (hardware maximum rate), `Game (~20ms)`, `UI (~60ms)`, and `Normal (~200ms)`.
* **Real-Time Sensitivity Tuning**:
  * **Dead Zone $\Delta$ Threshold**: Filter out micro-noise by dropping samples where change < threshold $\Delta$.
  * **Low-Pass Smoothing $\alpha$**: Adjust real-time digital filtering coefficient ($\alpha \in [0.00, 0.95]$) where `0.00` passes raw hardware output and higher values smooth high-frequency vibration.
* **Dual Simultaneous Logging**: Records high-speed CSV files directly to local SD card storage (`/sdcard/SensorMax_Records/`) while streaming over wireless or wired links.

### Building & Installing on Oppo A33w
1. Open the `AndroidApp/` directory in **Android Studio**.
2. Connect your Oppo A33w via USB. Enable **USB Debugging** under `Settings > Developer Options`.
3. Click **Run** or run `./gradlew assembleDebug` to build and install the APK.

---

## 2. Laptop Software & Transmission Modes

Launch any tool instantly via `./OppoSensorResearchSuite/run_laptop_suite.sh`:

### Mode A: WiFi UDP Stream (Highest Wireless Throughput)
1. Ensure your laptop and Oppo A33w are on the same WiFi network (or phone hotspot).
2. Find your laptop's local IP address (e.g., `192.168.1.100`).
3. In the Android app, select **WiFi (UDP)**, enter your laptop IP and port `5005`.
4. Run `python3 LaptopSuite/sensor_studio.py` or `python3 LaptopSuite/web_server.py`.

### Mode B: USB OTG / ADB Forwarding (Zero Packet Loss & Lowest Latency)
1. Connect Oppo A33w via USB cable to your laptop with USB Debugging enabled.
2. Open a terminal on your laptop and run port forwarding:
   ```bash
   adb forward tcp:5005 tcp:5005
   ```
3. In the Android app, select **USB / ADB**, set port to `5005`, and press **Start Streaming**.
4. In `sensor_studio.py`, select **USB ADB Socket** mode and click **Start Listening**.
