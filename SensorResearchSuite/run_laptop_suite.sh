#!/usr/bin/env bash
# Quick Launcher for Oppo A33w SensorMax Laptop Research Suite

echo "============================================================"
echo "  OPPO A33w SENSORMAX LAPTOP RESEARCH SUITE LAUNCHER"
echo "============================================================"
echo "Select the tool you wish to run:"
echo "  1) Desktop GUI Receiver & Waveform Plotter (sensor_studio.py)"
echo "  2) Web Gateway & WebSocket Broadcast Server (web_server.py)"
echo "  3) Live FFT Frequency Spectrum Waterfall Studio (live_spectrum_studio.py)"
echo "  4) Interactive Terminal REPL Data Explorer (cli_explorer.py)"
echo "  5) Real-Time Safety & Vibration Threshold Monitor (realtime_alarm_monitor.py)"
echo "  6) 3D AHRS Attitude Processor (imu_ahrs_3d.py)"
echo "  7) Pedestrian Dead Reckoning (PDR) 2D Trajectory Tracker (dead_reckoning_2d.py)"
echo "  8) Structural & Mechanical Modal Vibration Analyzer (vibration_modal_analysis.py)"
echo "  9) Biomechanical Gait Kinematics & Symmetry Analyzer (gait_symmetry_analyzer.py)"
echo " 10) Ballistocardiography (BCG) Cardiac Heart Rate Estimator (ballistocardiography.py)"
echo " 11) Vehicle Ride Comfort & Smoothness Evaluator ISO 2631 (ride_comfort_iso2631.py)"
echo " 12) Nocturnal Sleep Actigraphy & Tremor Monitor (sleep_tremor_monitor.py)"
echo " 13) Motion & Activity Recognition Engine (activity_recognition.py)"
echo " 14) Digital Signal Processing (DSP) Filter Suite (digital_filters.py)"
echo " 15) Machine Learning Feature Extractor (ml_feature_extractor.py)"
echo " 16) Machine Learning Activity Classifier Engine (ml_activity_classifier.py)"
echo " 17) Quality Assurance & Anomaly Detector (anomaly_detector.py)"
echo " 18) Dataset FFT & Jitter Analysis Tool (data_analysis.py)"
echo " 19) 3D Sensor Precision Calibration Engine (sensor_calibration.py)"
echo " 20) CSV to Multi-Sheet Excel (.xlsx) Exporter (export_converter.py)"
echo " 21) CSV to Academic MATLAB Script (.m) Exporter (matlab_exporter.py)"
echo " 22) Automated HTML Research Report Generator (generate_html_report.py)"
echo " 23) Synthetic IMU Dataset Generator (synthetic_sensor_generator.py)"
echo " 24) Master Batch Dataset Comparator (batch_dataset_processor.py)"
echo " 25) Run Complete End-to-End Integration Pipeline Test (test_all_pipelines.py)"
echo " 26) Run Suite Health Verification Self-Test (verify_suite_health.py)"
echo " 27) Setup USB ADB Port Forwarding (adb forward tcp:5005 tcp:5005)"
echo "============================================================"

read -p "Enter selection [1-27]: " choice

case $choice in
    1) python3 LaptopSuite/sensor_studio.py ;;
    2) echo "Starting Web Gateway Server on UDP 5005 / WebSocket 8765..."; python3 LaptopSuite/web_server.py ;;
    3) python3 LaptopSuite/live_spectrum_studio.py ;;
    4) read -e -p "Enter path to CSV recording: " p; python3 LaptopSuite/cli_explorer.py "$p" ;;
    5) python3 LaptopSuite/realtime_alarm_monitor.py ;;
    6) read -e -p "Enter path to CSV recording: " p; python3 LaptopSuite/imu_ahrs_3d.py "$p" ;;
    7) read -e -p "Enter path to CSV recording: " p; python3 LaptopSuite/dead_reckoning_2d.py "$p" ;;
    8) read -e -p "Enter path to CSV recording: " p; python3 LaptopSuite/vibration_modal_analysis.py "$p" ;;
    9) read -e -p "Enter path to CSV recording: " p; python3 LaptopSuite/gait_symmetry_analyzer.py "$p" ;;
   10) read -e -p "Enter path to CSV recording: " p; python3 LaptopSuite/ballistocardiography.py "$p" ;;
   11) read -e -p "Enter path to CSV recording: " p; python3 LaptopSuite/ride_comfort_iso2631.py "$p" ;;
   12) read -e -p "Enter path to CSV recording: " p; python3 LaptopSuite/sleep_tremor_monitor.py "$p" ;;
   13) read -e -p "Enter path to CSV dataset: " p; python3 LaptopSuite/activity_recognition.py "$p" ;;
   14) read -e -p "Enter path to CSV dataset: " p; python3 LaptopSuite/digital_filters.py "$p" ;;
   15) read -e -p "Enter path to CSV dataset: " p; python3 LaptopSuite/ml_feature_extractor.py "$p" ;;
   16) read -e -p "Enter training features CSV: " t; read -e -p "Enter test features CSV: " s; python3 LaptopSuite/ml_activity_classifier.py "$t" "$s" ;;
   17) read -e -p "Enter path to CSV dataset: " p; python3 LaptopSuite/anomaly_detector.py "$p" ;;
   18) read -e -p "Enter path to CSV dataset: " p; python3 LaptopSuite/data_analysis.py "$p" ;;
   19) read -e -p "Enter path to calibration CSV: " p; python3 LaptopSuite/sensor_calibration.py "$p" ;;
   20) read -e -p "Enter path to CSV recording: " p; python3 LaptopSuite/export_converter.py "$p" ;;
   21) read -e -p "Enter path to CSV recording: " p; python3 LaptopSuite/matlab_exporter.py "$p" --output oppo_data.m && echo "Generated oppo_data.m!" ;;
   22) read -e -p "Enter path to CSV recording: " p; python3 LaptopSuite/generate_html_report.py "$p" --output oppo_research_report.html && echo "Generated oppo_research_report.html!" ;;
   23) python3 LaptopSuite/synthetic_sensor_generator.py --profile walking --output synthetic_dataset.csv ;;
   24) read -e -p "Enter directory containing trial CSVs: " p; python3 LaptopSuite/batch_dataset_processor.py "$p" ;;
   25) python3 LaptopSuite/test_all_pipelines.py ;;
   26) python3 LaptopSuite/verify_suite_health.py ;;
   27) echo "Forwarding local port 5005 to Oppo A33w via USB ADB..."; adb forward tcp:5005 tcp:5005 && echo "Success!" ;;
    *) echo "Invalid selection." ;;
esac
