"""Prefer the local backend src layout when running from the repo root."""

from __future__ import annotations

import sys
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parent / "backend" / "src"

if SRC_PATH.is_dir():
    src_str = str(SRC_PATH)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)
