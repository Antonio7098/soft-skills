"""Repo-level pytest bootstrap for backend tests from the repo root."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
BACKEND_SRC = BACKEND / "src"

for candidate in (BACKEND_SRC, BACKEND):
    candidate_str = str(candidate)
    if candidate.is_dir() and candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

os.chdir(BACKEND)
