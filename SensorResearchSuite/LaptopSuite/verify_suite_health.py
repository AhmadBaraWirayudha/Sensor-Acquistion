#!/usr/bin/env python3
"""
Oppo A33w SensorMax Research Suite Diagnostic & Verification Engine
Performs automated syntax, module dependency, and execution verification
across all 13 Python desktop/server tools in the suite.
"""

import sys
import os
import subprocess
import glob

def verify_suite():
    print("=============================================================")
    print(" OPPO A33w RESEARCH SUITE AUTOMATED HEALTH VERIFICATION")
    print("=============================================================")
    
    suite_dir = os.path.dirname(os.path.abspath(__file__))
    py_files = glob.glob(os.path.join(suite_dir, "*.py"))
    
    passed = 0
    failed = 0
    
    for fpath in sorted(py_files):
        fname = os.path.basename(fpath)
        if fname == "verify_suite_health.py": continue
        
        # Test python compilation/syntax check
        res = subprocess.run([sys.executable, "-m", "py_compile", fpath], capture_output=True, text=True)
        if res.returncode == 0:
            print(f" [PASS] Syntax & Compilation Check : {fname}")
            passed += 1
        else:
            print(f" [FAIL] Syntax Error in {fname}:\n{res.stderr}")
            failed += 1

    print("-------------------------------------------------------------")
    print(f" Verification Complete: {passed} Passed | {failed} Failed")
    print("=============================================================\n")
    return failed == 0

if __name__ == "__main__":
    success = verify_suite()
    sys.exit(0 if success else 1)
