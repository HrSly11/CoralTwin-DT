"""
08_GIS_and_Remote_Sensing/srpi_sensitivity_analysis.py
======================================================
Delegates directly to `08_GIS_and_Remote_Sensing/srpi_sensitivity.py` so both entrypoints
produce the exact same sensitivity, bootstrap-10,000, and leave-one-station-out (LOSO) artifacts.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from srpi_sensitivity import main

if __name__ == "__main__":
    main()
