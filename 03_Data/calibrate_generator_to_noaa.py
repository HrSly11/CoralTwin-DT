"""
01_Data/calibrate_generator_to_noaa.py
======================================
Canonical entrypoint requested by Reviewer (FASE 1 — FON-01).
Delegates directly to `03_Data/calibrate_generator_to_noaa.py` so both `01_Data/`
and `03_Data/` paths are supported seamlessly.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "03_Data"))

from calibrate_generator_to_noaa import main

if __name__ == "__main__":
    main()
