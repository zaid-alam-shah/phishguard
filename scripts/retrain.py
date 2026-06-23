#!/usr/bin/env python3
"""Wrapper to invoke auto_retrain from project root or via cron/scheduler."""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
os.chdir(str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR))

from backend.auto_retrain import main

if __name__ == '__main__':
    main()
