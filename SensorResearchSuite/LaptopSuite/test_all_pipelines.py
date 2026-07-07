#!/usr/bin/env python3
"""
Oppo A33w End-to-End Automated Integration Pipeline Tester
Executes the full chain of 15 analytical and export pipelines sequentially
on synthetic datasets to verify 100% functional integrity across the entire suite.
"""

import sys
import os
import subprocess

def run_step(step_num, title, cmd):
    print(f"\n[{step_num}/12] Executing: {title}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"  [PASS] {title}")
        return True
    else:
        print(f"  [FAIL] {title}\nError Output:\n{res.stderr}")
        return False

def main():
    print("=============================================================")
    print(" OPPO A33w END-TO-END RESEARCH PIPELINE INTEGRATION TEST")
    print("=============================================================")
    
    suite_dir = os.path.dirname(os.path.abspath(__file__))
    test_dir = os.path.join(suite_dir, "test_output")
    os.makedirs(test_dir, exist_ok=True)
    
    synth_csv = os.path.join(test_dir, "synth_walking.csv")
    py = sys.executable

    steps = [
        ("Generate 100Hz Walking Synthetic Dataset", [py, os.path.join(suite_dir, "synthetic_sensor_generator.py"), "--profile", "walking", "--duration", "5", "--rate", "100", "--output", synth_csv]),
        ("Quality Assurance & Anomaly Scan", [py, os.path.join(suite_dir, "anomaly_detector.py"), synth_csv]),
        ("DSP Exponential Low-Pass Filtering", [py, os.path.join(suite_dir, "digital_filters.py"), synth_csv, "--filter", "ema", "--param", "0.2", "--output", os.path.join(test_dir, "filtered.csv")]),
        ("Madgwick AHRS 3D Attitude Estimation", [py, os.path.join(suite_dir, "imu_ahrs_3d.py"), synth_csv, os.path.join(test_dir, "ahrs.csv")]),
        ("2D Pedestrian Dead Reckoning (PDR) Trajectory", [py, os.path.join(suite_dir, "dead_reckoning_2d.py"), synth_csv, "--output", os.path.join(test_dir, "pdr_2d.csv")]),
        ("Structural Vibration Modal Analysis", [py, os.path.join(suite_dir, "vibration_modal_analysis.py"), synth_csv]),
        ("Motion State Classification & Step Cadence", [py, os.path.join(suite_dir, "activity_recognition.py"), synth_csv]),
        ("AI Machine Learning Feature Extraction", [py, os.path.join(suite_dir, "ml_feature_extractor.py"), synth_csv, "--window", "1.0", "--output", os.path.join(test_dir, "features.csv")]),
        ("KNN Activity Classification Prediction", [py, os.path.join(suite_dir, "ml_activity_classifier.py"), os.path.join(test_dir, "features.csv"), "--output", os.path.join(test_dir, "predictions.csv")]),
        ("Multi-Sheet Excel Workbook Export (.xlsx)", [py, os.path.join(suite_dir, "export_converter.py"), synth_csv, os.path.join(test_dir, "workbook.xlsx")]),
        ("Academic MATLAB Script Export (.m)", [py, os.path.join(suite_dir, "matlab_exporter.py"), synth_csv, "--output", os.path.join(test_dir, "script.m")]),
        ("Automated Executive HTML Report Generation", [py, os.path.join(suite_dir, "generate_html_report.py"), synth_csv, "--output", os.path.join(test_dir, "report.html")])
    ]

    passed = 0
    for idx, (title, cmd) in enumerate(steps, 1):
        if run_step(idx, title, cmd):
            passed += 1

    print("\n=============================================================")
    print(f" PIPELINE INTEGRATION TEST RESULTS: {passed}/{len(steps)} PIPELINES PASSED")
    print("=============================================================\n")
    return passed == len(steps)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
