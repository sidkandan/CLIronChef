#!/usr/bin/env python3
"""CLIronChef pretty-printed device status.

Standalone equivalent of `cliron-chef status`. Useful before `pip install`.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if SRC.is_dir() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import argparse

from cliron_chef.cli import cmd_status

if __name__ == "__main__":
    cmd_status(argparse.Namespace())
