"""Repo-root shim for the backend src-layout package."""

from __future__ import annotations

from pathlib import Path
from typing import Any

_PKG_DIR = Path(__file__).resolve().parents[1] / "backend" / "src" / "soft_skills_backend"

__path__ = [str(_PKG_DIR)]
__all__ = ["app", "create_app"]


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(name)
    from soft_skills_backend.app import app, create_app

    return {"app": app, "create_app": create_app}[name]
